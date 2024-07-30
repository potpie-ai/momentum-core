import os
import shutil
import logging
import traceback
from typing import List, Optional
import difflib


from git import Repo, GitCommandError

from server.auth import check_auth
from server.blast_radius_detection import get_paths_from_identifiers
from server.change_detection import get_updated_function_list
from server.dependencies import Dependencies
from server.endpoint_detection import EndpointManager
from fastapi import Depends, HTTPException
from server.utils.APIRouter import APIRouter
from fastapi.requests import Request
from github import Github
from server.models.repo_details import (
    PreferenceDetails,
    ProjectStatusEnum,
    RepoDetails,
    TestPlanDetails,
)
from server.parse import (
    analyze_directory,
    get_flow,
    get_graphical_flow_structure,
    get_node,
    get_values,
)
from server.plan import Plan
from server.projects import ProjectManager
from pydantic import BaseModel

from server.blast_radius_detection import get_paths_from_identifiers
from server.utils.github_helper import GithubService
from server.utils.graph_db_helper import Neo4jGraph
from server.utils.parse_helper import setup_project_directory, reparse_cleanup
from server.dependencies import Dependencies
from server.auth import check_auth
from server.test_agent.crew import GenerateTest
from server.utils.auth_service import AuthService
from server.utils.test_detail_handler import UserTestDetailsManager

use_test_details_manager = UserTestDetailsManager()
project_manager = ProjectManager()

api_router = APIRouter()
auth_service = AuthService()
neo4j_graph = Neo4jGraph()

repo_not_found_message = "Repository not found"

@api_router.post("/parse")
async def parse_directory(
        request: Request, repo_details: RepoDetails, user=Depends(check_auth)
):
    dir_details = ""
    user_id = user["user_id"]
    repo = None
    owner = None
    app_auth = None
    project_id = None

    # Check if development mode is enabled
    if os.getenv("isDevelopmentMode") != "enabled" and repo_details.repo_path:
        raise HTTPException(status_code=403, detail="Development mode is not enabled, cannot parse local repository.")
    
     # Check if development mode is enabled
    if user_id == os.getenv("defaultUsername") and repo_details.repo_name:
        raise HTTPException(status_code=403, detail="Cannot parse remote repository without auth token")

    project_path = os.getenv("PROJECT_PATH")
    local_repo_path = os.path.join(project_path, f"{repo_details.repo_name or os.path.basename(repo_details.repo_path)}-{user_id}")

    if repo_details.repo_path:
        if not os.path.exists(repo_details.repo_path):
            raise HTTPException(status_code=400, detail="Local repository does not exist on given path")
        try:
            shutil.copytree(repo_details.repo_path, local_repo_path)
            repo = Repo(local_repo_path)
            if repo_details.branch_name not in repo.heads:
                raise HTTPException(status_code=400, detail="Branch not found in local repository")
            current_dir = os.getcwd()
            os.chdir(local_repo_path)
            repo.git.checkout(repo_details.branch_name)
            os.chdir(current_dir)
        except GitCommandError as e:
            raise HTTPException(status_code=400, detail="Failed to access or switch branch in local repository")
    else:
        response, auth, owner = GithubService.get_github_repo_details(repo_details.repo_name)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get installation ID")
        project_id = None
        app_auth = auth.get_installation_auth(response.json()["id"])
        github = Github(auth=app_auth)
        try:
            repo = github.get_repo(repo_details.repo_name)
        except Exception as e:
            raise HTTPException(status_code=400, detail=repo_not_found_message)

    message = ""
    repo_name = repo_details.repo_name.split("/")[-1] if repo_details.repo_name else os.path.basename(repo_details.repo_path)
    branch_name = repo_details.branch_name
    project_details = project_manager.get_project_from_db(f"{repo_name}-{branch_name}", user_id)
    project_deleted = None
    if project_details:
        project_deleted = project_details.is_deleted

    try:
        new_project = True
        if project_details is None:
            dir_details, project_id, should_parse_repo = setup_project_directory(
                owner, repo_name, branch_name, app_auth, repo, user_id, project_id
            )
            if should_parse_repo:
                await analyze_directory(dir_details, user_id, project_id)
                new_project = True
                message = "The project has been parsed successfully"
                project_manager.update_project_status(project_id, ProjectStatusEnum.READY)
            else:
                project_manager.update_project_status(project_id, ProjectStatusEnum.ERROR)
                message = "Repository doesn't consist of a language currently supported."
        else:
            dir_details = project_details.directory
            project_id = project_details.id
            if project_deleted:
                message = project_manager.restore_project(project_id, user_id)
            else:
                message = "The project has been re-parsed successfully"
            if repo_details.repo_path:
                dir_details, project_id, should_parse_repo = setup_project_directory(
                    owner, repo_name, branch_name, app_auth, repo, user_id, project_id
                )
                if should_parse_repo:
                    await analyze_directory(dir_details, user_id, project_id)
                    new_project = False
                    message = "The project has been re-parsed successfully"
                    project_manager.update_project_status(project_id, ProjectStatusEnum.READY)
                else:
                    project_manager.update_project_status(project_id, ProjectStatusEnum.ERROR)
                    message = "Repository doesn't consist of a language currently supported."
            else:
                if GithubService.check_is_commit_added(repo, project_details, branch_name):
                    reparse_cleanup(project_details, user_id)
                    dir_details, project_id, should_parse_repo = setup_project_directory(
                        owner, repo_name, branch_name, app_auth, repo, user_id, project_id
                    )
                    if should_parse_repo:
                        await analyze_directory(dir_details, user_id, project_id)
                        new_project = False
                        message = "The project has been re-parsed successfully"
                        project_manager.update_project_status(project_id, ProjectStatusEnum.READY)
                    else:
                        project_manager.update_project_status(project_id, ProjectStatusEnum.ERROR)
                        message = "Repository doesn't consist of a language currently supported."
                else:
                    return {"message": "No new commits have been added to the branch since the last parsing. The database is up to date.",
                            "project_id": project_id}
    except Exception as e:
        tb_str = "".join(traceback.format_exception(None, e, e.__traceback__))
        project_manager.update_project_status(
            project_id, ProjectStatusEnum.ERROR
        )
        raise HTTPException(
            status_code=500, detail=f"{str(e)}\nTraceback: {tb_str}"
        )
    
    request.state.additional_data = {
        "repository_name": repo_details.repo_name or repo_details.repo_path,
        "branch_name": branch_name,
        "project_id": project_id,
        "size": repo.size / 1024 if repo_details.repo_name else 0,
        "new_project": new_project
    }
    
    if repo_details.repo_name:
        github.close()
    
    return {
        "message": message,
        "id": project_id
    }

@api_router.get("/endpoints/list")
def get_endpoints(request: Request, project_id: int, user=Depends(check_auth)):
    user_id = user["user_id"]
    project_details = project_manager.get_project_from_db_by_id_and_user_id(
        project_id, user_id
    )
    if project_details is not None:
        endpoint_details = EndpointManager(
            project_details["directory"]
        ).display_endpoints(project_details["id"])
        request.state.additional_data = {
            "number_of_endpoints": sum(len(endpoint_details[filename]) for filename in endpoint_details)
        }
        return endpoint_details
    else:
        return HTTPException(
            status_code=400, detail="Project Details not found."
        )


@api_router.get("/endpoints/blast")
def get_blast_radius_details(
        request: Request, project_id: int, base_branch: Optional[str] = "master", user=Depends(check_auth)
):
    global patches_dict, repo
    patches_dict = {}
    user_id = user["user_id"]
    project_details = project_manager.get_project_repo_details_from_db(project_id, user_id)

    if project_details is None:
        raise HTTPException(status_code=400, detail="Project Details not found.")

    repo_name = project_details["repo_name"]
    branch_name = project_details["branch_name"]
    repo_path = project_details.get("directory")
    github = None

    is_local_repo = user_id == os.getenv("defaultUsername") and repo_path and os.path.exists(repo_path)
    if is_local_repo:
        try:
            repo = Repo(repo_path)
            if branch_name not in repo.heads:
                raise HTTPException(status_code=400, detail="Branch not found in local repository")
            repo.git.checkout(branch_name)
            repo_details = {
                "name": repo_name,
                "path": repo_path
            }
        except GitCommandError:
            raise HTTPException(status_code=400, detail="Failed to access or switch branch in local repository")
    else:
        response, auth, owner = GithubService.get_github_repo_details(repo_name)
        app_auth = auth.get_installation_auth(response.json()['id'])
        github = Github(auth=app_auth)
        try:
            repo = github.get_repo(repo_name)
            repo_details = repo
        except Exception:
            raise HTTPException(status_code=400, detail=repo_not_found_message)

    try:
        if is_local_repo:
            base_commit = repo.commit(base_branch)
            branch_commit = repo.commit(branch_name)

            added_commits = sum(1 for _ in repo.iter_commits(f"{base_branch}..{branch_name}"))
            additions = deletions = 0

            for diff_item in base_commit.diff(branch_commit):
                if diff_item.a_blob and diff_item.b_blob:
                    a_blob = diff_item.a_blob.data_stream.read().decode('utf-8').splitlines(keepends=True)
                    b_blob = diff_item.b_blob.data_stream.read().decode('utf-8').splitlines(keepends=True)
                    diff = difflib.unified_diff(a_blob, b_blob, lineterm='')
                    patch = '\n'.join(diff)
                    patches_dict[diff_item.a_path] = patch
                    for line in patch.split('\n'):
                        if line.startswith('+') and not line.startswith('+++'):
                            additions += 1
                        elif line.startswith('-') and not line.startswith('---'):
                            deletions += 1
                elif diff_item.a_blob:
                    deletions += sum(1 for _ in diff_item.a_blob.data_stream.read().decode('utf-8').splitlines(keepends=True))
                elif diff_item.b_blob:
                    additions += sum(1 for _ in diff_item.b_blob.data_stream.read().decode('utf-8').splitlines(keepends=True))
        else:
            git_diff = repo.compare(base_branch, branch_name)
            added_commits = git_diff.total_commits
            additions = sum(file.additions for file in git_diff.files)
            deletions = sum(file.deletions for file in git_diff.files)
            patches_dict = {file.filename: file.patch for file in git_diff.files if file.patch}

        lines_impacted = additions + deletions
        logging.info(f"project_id: {project_id}, added_commits: {added_commits}, lines_impacted: {lines_impacted}")
        request.state.additional_data = {
            "added_commits": added_commits,
            "lines_impacted": lines_impacted
        }

    except Exception:
        raise HTTPException(status_code=400, detail=repo_not_found_message)
    finally:
        if project_details is not None:
            directory = project_details["directory"]
            identifiers = []
            try:
                identifiers = get_updated_function_list(patches_dict, directory, repo_details, branch_name)
            except Exception as e:
                logging.error(f"project_id: {project_id}, error: {str(e)}")
                if "path not in the working tree" in str(e):
                    base_branch = "main"
                    identifiers = get_updated_function_list(patches_dict, directory, repo_details, branch_name)
            if len(identifiers) == 0:
                if github:
                    github.close()
                return []
            paths = get_paths_from_identifiers(identifiers, directory, project_details["id"])
            if github:
                github.close()
            return paths

    
@api_router.get("/endpoints/flow/graph")
def get_flow_graph(
        project_id: int, endpoint_id: str, user=Depends(check_auth)
):
    user_id = user["user_id"]
    project_details = project_manager.get_project_from_db_by_id_and_user_id(
        project_id, user_id
    )
    if project_details is not None:
        graph_structure = get_graphical_flow_structure(
            endpoint_id, project_details["directory"], project_details["id"]
        )
        return graph_structure
    else:
        return HTTPException(
            status_code=400, detail="Project Details not found."
        )


@api_router.get("/endpoints/dependencies")
def get_dependencies(
        project_id: int, endpoint_id: str, user=Depends(check_auth)
):
    user_id = user["user_id"]
    project_details = project_manager.get_project_from_db_by_id_and_user_id(
        project_id, user_id
    )
    if project_details is not None:
        flow = get_flow(endpoint_id, project_details["id"])
        return [x.split(":")[1] for x in flow if x != endpoint_id]
    else:
        return HTTPException(
            status_code=400, detail="Project Details not found."
        )


@api_router.get("/endpoints/dependencies/more")
async def get_more_dependencies_ai(
        project_id: int, endpoint_id: str, user=Depends(check_auth)
):
    user_id = user["user_id"]
    project_details = project_manager.get_project_from_db_by_id_and_user_id(
        project_id, user_id
    )
    if project_details is not None:
        graph_structure = await Dependencies(user["user_id"]).get_dependencies(
            project_details, endpoint_id
        )
        return graph_structure
    else:
        return HTTPException(
            status_code=400, detail="Project Details not found."
        )


@api_router.get("/code/node")
def get_code_node(project_id: int, node_id: str, user=Depends(check_auth)):
    user_id = user["user_id"]
    project_details = project_manager.get_project_from_db_by_id_and_user_id(
        project_id, user_id
    )
    if project_details is not None:
        graph_structure = get_node(node_id, project_details)
        return graph_structure
    else:
        return HTTPException(
            status_code=400, detail="Project Details not found."
        )


class TestPlan(BaseModel):
    happy_path: List[str]
    edge_case: List[str]


@api_router.put("/test/plan")
def set_plan(test_plan: TestPlanDetails, user=Depends(check_auth)):
    identifier = test_plan.identifier
    project_id = test_plan.project_id
    project_details = project_manager.get_project_from_db_by_id_and_user_id(
        project_id, user["user_id"]
    )
    if project_details is not None:
        directory = project_details["directory"]
        if test_plan:
            updated_test_plan = EndpointManager(
                directory
            ).update_test_plan(
                identifier,
                test_plan.plan.model_dump_json(),
                project_details["id"],
            )
            return updated_test_plan
        else:
            raise HTTPException(status_code=400, detail="Plan is empty")
    else:
        return HTTPException(
            status_code=400, detail="Project Details not found."
        )


@api_router.put("/endpoints/preference")
def set_preferences(preference: PreferenceDetails, user=Depends(check_auth)):
    project_id = preference.project_id
    project_details = project_manager.get_project_from_db_by_id_and_user_id(
        project_id, user["user_id"]
    )
    identifier = preference.identifier
    if project_details is not None:
        preference = preference.preference
        if preference and preference != {}:
            return EndpointManager(
                project_details["directory"]
            ).update_test_preferences(
                identifier, preference, project_details["id"]
            )
        else:
            raise HTTPException(
                status_code=400, detail="Configuration is empty"
            )
    else:
        raise HTTPException(
            status_code=400, detail="Project Details not found."
        )


@api_router.get("/test/plan")
async def get_test_plan(
        project_id: int, identifier: str, user=Depends(check_auth)
):
    user_id = user["user_id"]
    project_details = project_manager.get_project_from_db_by_id_and_user_id(
        project_id, user_id
    )
    if project_details is not None:
        test_plan = EndpointManager(
            project_details["directory"]
        ).get_test_plan(identifier, project_details["id"])
        if test_plan is None:
            test_plan = await Plan(
                user["user_id"]
            ).generate_test_plan_for_endpoint(identifier, project_details)
        return test_plan


@api_router.get("/endpoints/preference")
async def get_test_preferences(
        project_id: int, identifier: str, user=Depends(check_auth)
):
    user_id = user["user_id"]

    project_details = project_manager.get_project_from_db_by_id_and_user_id(
        project_id, user_id
    )
    if project_details is not None:
        preference = EndpointManager(
            project_details["directory"]
        ).get_preferences(identifier, project_details["id"])
        return preference
    else:
        raise HTTPException(
            status_code=400, detail="Project Details not found."
        )


@api_router.get("/test/generate")
async def generate_test(
        identifier: str,
        endpoint_path: str,
        project_id: int,
        user=Depends(check_auth),
):
    user_id = user["user_id"]
    test_max_count = 200 if use_test_details_manager.is_pro_plan(user_id) else 50
    if use_test_details_manager.get_test_count_last_month(user_id) < test_max_count:
        project_details = project_manager.get_project_repo_details_from_db(
            project_id,
            user_id
        )
        if project_details is not None:
            project_dir = project_details["directory"]
            project_id = project_details["id"]
            test_plan, preferences = EndpointManager(
                project_dir
            ).get_test_plan_preferences(identifier, project_id)
            if test_plan is None:
                test_plan = await Plan(
                    user["user_id"]
                ).generate_test_plan_for_endpoint(identifier, project_details, preferences)
            no_of_test_generated = (len(test_plan["happy_path"] if "happy_path" in test_plan else 0)
                                    + len(test_plan["edge_case"] if "edge_case" in test_plan else 0))
            return await GenerateTest(
                identifier,
                endpoint_path,
                str(test_plan),
                user["user_id"],
                project_dir,
                project_id,
                preferences
            ).write_tests(identifier, no_of_test_generated, project_details, user_id)
        else:
            raise HTTPException(
                status_code=400, detail="Project Details not found."
            )
    else:
        raise HTTPException(status_code=429, detail="Test generation limit reached")


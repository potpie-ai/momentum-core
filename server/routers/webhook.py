import json
import os
import time
from asyncio import create_task

from fastapi import HTTPException, Request, Response
from github import Github
from github.Auth import AppAuth

from server.models.repo_details import RepoDetails, ProjectStatusEnum
from server.parse import analyze_directory, get_values
from server.projects import ProjectManager
from server.utils.github_helper import GithubService
from server.utils.parse_helper import setup_project_directory
from server.utils.APIRouter import APIRouter


from server.utils.parse_helper import reparse_cleanup
from server.utils.user_service import get_user_id_by_username

router = APIRouter()
project_manager = ProjectManager()


@router.post("/webhook")
async def github_app(request: Request):
    payload = await request.body()
    create_task(parse_repos(payload, request))
    return Response(status_code=200)


async def parse_repos(payload, request: Request):
    start_time = time.time()
    payload = json.loads(payload)

    repository_field = {
        "added": "repositories_added",
        "created": "repositories",
        "removed": "repositories_removed"
    }.get(payload["action"], None)

    if ("installation" in payload and "action" in payload and
        (payload["action"] == "added" or payload["action"] == "created"))\
            or ("commits" in payload):
        auth, installation_auth, user_details, github = GithubService.get_app_auth_details(payload)
        user_id = user_details[0]
        user_state_value = {
            "user_id": user_details[0],
            "email": user_details[1]
        }
        request.state.user = user_state_value
        request.state.additional_data = {}
        if repository_field in payload:
            repositories_added = payload[repository_field]
            for repo in repositories_added:
                repo_details = github.get_repo(repo['full_name'])
                repo_branch = RepoDetails(repo_name=repo_details.full_name, branch_name=repo_details.default_branch)
                project_id = None
                repo_name, branch_name, is_deleted, project_details = get_values(repo_branch, project_manager, user_details[0])
                owner = repo_details.owner.login
                try:
                    if project_details is None:
                        dir_details, project_id = setup_project_directory(
                            owner,
                            repo_name,
                            branch_name,
                            installation_auth,
                            repo_details,
                            user_id
                        )
                        analyze_directory(dir_details, user_id, project_id)
                        project_manager.update_project_status(
                            project_id, ProjectStatusEnum.READY
                        )
                        request.state.additional_data[repo_name] = {
                            "repository_name": repo_name,
                            "branch_name": branch_name,
                            "project_id": project_id,
                            "size": repo_details.size / 1024,
                            "new_project": True
                        }
                    else:
                        project_id = project_details[2]
                        if is_deleted:
                            project_manager.restore_all_project(repo_branch.repo_name, user_id)
                        if GithubService.check_is_commit_added(repo_details, project_details, branch_name):
                            reparse_cleanup(project_details, user_id)
                            dir_details, project_id = setup_project_directory(owner, repo_name,
                                                                              branch_name, auth, repo_details, user_id,
                                                                              project_id)
                            analyze_directory(dir_details, user_id, project_id)
                except Exception as e:
                    project_manager.update_project_status(project_id, ProjectStatusEnum.ERROR)
                    raise HTTPException(status_code=500, detail=f"{str(e)}")
                finally:
                    github.close()
        elif "commits" in payload and "head_commit" in payload:
            repository = payload['repository']
            repo_name = repository['full_name']
            branch_name = payload['ref'].split("/")[-1]
            repo_branch = RepoDetails(repo_name=repo_name, branch_name=branch_name)
            repo_details = github.get_repo(repo_name)
            repo_name, branch_name, is_deleted, project_details = get_values(repo_branch, project_manager, user_id)
            if project_details is not None:
                owner = repo_details.owner.login
                reparse_cleanup(project_details, user_id)
                project_id = project_details[2]
                dir_details, project_id = setup_project_directory(
                    owner,
                    repo_name,
                    branch_name,
                    installation_auth,
                    repo_details,
                    user_id,
                    project_id
                )
                analyze_directory(dir_details, user_id, project_id)
                request.state.additional_data[repo_name] = {
                    "repository_name": repo_name,
                    "branch_name": branch_name,
                    "project_id": project_id,
                    "size": repo_details.size / 1024,
                    "new_project": False
                }
            project_manager.update_project_status(
                project_id, ProjectStatusEnum.READY
            )
            github.close()
    elif "action" in payload and payload["action"] == "removed":
        auth, installation_auth, user_details, github = GithubService.get_app_auth_details(payload)
        user_id = user_details[0]
        if repository_field in payload:
            repositories_deleted = payload[repository_field]
            for repo in repositories_deleted:
                repo_name = github.get_repo(repo['full_name'])
                project_manager.delete_all_project_by_repo_name(repo_name.full_name, user_id)
        github.close()


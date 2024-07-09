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
        "created": "repositories"
    }.get(payload["action"], None)

    if ("installation" in payload and "action" in payload and
        (payload["action"] == "added" or payload["action"] == "created"))\
            or ("commits" in payload):
        private_key = "-----BEGIN RSA PRIVATE KEY-----\n" + os.environ[
            'GITHUB_PRIVATE_KEY'] + "\n-----END RSA PRIVATE KEY-----\n"
        app_id = os.environ["GITHUB_APP_ID"]
        auth = AppAuth(app_id=app_id, private_key=private_key)
        installation_auth = auth.get_installation_auth(payload['installation']['id'])
        github = Github(auth=installation_auth)
        user = github.get_user_by_id(payload['sender']['id'])
        username = user.login
        user_details = get_user_id_by_username(username)
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
                repo_name, branch_name, project_details = get_values(repo_branch, project_manager, user_details[0])
                owner = repo_details.owner.login
                try:
                    if project_details is None:
                        dir_details, project_id, should_parse_repo = setup_project_directory(
                            owner,
                            repo_name,
                            branch_name,
                            installation_auth,
                            repo_details,
                            user_id
                        )
                        if should_parse_repo:
                            await analyze_directory(dir_details, user_id, project_id)
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
                            project_manager.update_project_status(
                                project_id, ProjectStatusEnum.ERROR
                            )
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
            repo_name, branch_name, project_details = get_values(repo_branch, project_manager, user_id)
            if project_details is not None:
                owner = repo_details.owner.login
                reparse_cleanup(project_details, user_id)
                project_id = project_details[2]
                dir_details, project_id, should_parse_repo = setup_project_directory(
                    owner,
                    repo_name,
                    branch_name,
                    installation_auth,
                    repo_details,
                    user_id,
                    project_id
                )
                if should_parse_repo:
                    await analyze_directory(dir_details, user_id, project_id)
                    request.state.additional_data.append({
                        "repository_name": repo_name,
                        "branch_name": branch_name,
                        "project_id": project_id,
                        "size": repo_details.size / 1024,
                        "new_project": False
                    })
                    project_manager.update_project_status(
                        project_id, ProjectStatusEnum.READY
                    )
                else:
                    project_manager.update_project_status(
                        project_id, ProjectStatusEnum.ERROR
                    )
            github.close()

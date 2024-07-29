import logging
import os
from typing import Optional

import requests
from fastapi import Depends, HTTPException
from github import Github
from github.Auth import AppAuth
from starlette.responses import JSONResponse

from server.auth import check_auth
from server.projects import ProjectManager
from server.utils.APIRouter import APIRouter

api_router_project = APIRouter()
project_manager = ProjectManager()

if os.getenv("isDevelopmentMode") == "enabled":
    github=None
else:
    github = Github(os.environ["GITHUB_PRIVATE_KEY"])


def get_github_client(repo_name: str):
    private_key = (
        "-----BEGIN RSA PRIVATE KEY-----\n"
        + os.environ["GITHUB_PRIVATE_KEY"]
        + "\n-----END RSA PRIVATE KEY-----\n"
    )
    app_id = os.environ["GITHUB_APP_ID"]
    auth = AppAuth(app_id=app_id, private_key=private_key)
    jwt = auth.create_jwt()
    owner = repo_name.split("/")[0]
    repo = repo_name.split("/")[1]
    url = f"https://api.github.com/repos/{owner}/{repo}/installation"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {jwt}",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(
            status_code=400, detail="Failed to get installation ID"
        )
    app_auth = auth.get_installation_auth(response.json()["id"])
    github = Github(auth=app_auth)
    return github


@api_router_project.get("/get-branch-list")
def get_branch_list(repo_name: str, user=Depends(check_auth)):
    try:
        repo = get_github_client(repo_name).get_repo(repo_name)
        branches = repo.get_branches()
        branch_list = [branch.name for branch in branches]
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Repository not found or error fetching branches: {str(e)}"
            ),
        )
    return {"branches": branch_list}


@api_router_project.get("/projects/list")
def get_branch_list(
    repo_name: Optional[str] = None,
    default: Optional[bool] = None,
    user=Depends(check_auth),
):
    user_id = user["user_id"]
    try:
        branch_list = []
        project_details = project_manager.get_parsed_project_branches(
            repo_name, user_id, default
        )
        branch_list.extend(
            {
                "project_id": branch[0],
                "branch_name": branch[1],
                "repo_name": branch[2],
                "last_updated_at": branch[3],
                "is_default": branch[4],
                "project_status": branch[5],
            }
            for branch in project_details
        )
        return branch_list
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"{str(e)}")


@api_router_project.delete("/projects")
def delete_project(project_id: int, user=Depends(check_auth)):
    user_id = user["user_id"]
    try:
        project_manager.delete_project(project_id, user_id)
        return JSONResponse(status_code=200,
                            content={
                                "message": "Project deleted successfully.",
                                "id": project_id
                            })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{str(e)}")
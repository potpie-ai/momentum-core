import base64
import logging
import os

import requests
from fastapi import HTTPException
from github import Github
from github.Auth import AppAuth

from server.models.repo_details import ProjectStatusEnum
from server.projects import ProjectManager
from server.utils.user_service import get_user_id_by_username

project_manager = ProjectManager()
logger = logging.getLogger(__name__)

class GithubService:

    @staticmethod
    def get_github_repo_details(repo_name):
        private_key = "-----BEGIN RSA PRIVATE KEY-----\n" + os.environ[
            'GITHUB_PRIVATE_KEY'] + "\n-----END RSA PRIVATE KEY-----\n"
        app_id = os.environ["GITHUB_APP_ID"]
        auth = AppAuth(app_id=app_id, private_key=private_key)
        jwt = auth.create_jwt()
        owner = repo_name.split('/')[0]
        repo = repo_name.split('/')[1]
        url = f"https://api.github.com/repos/{owner}/{repo}/installation"
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {jwt}",
            "X-GitHub-Api-Version": "2022-11-28"
        }

        return requests.get(url, headers=headers), auth, owner

    @staticmethod
    def check_is_commit_added(repo_details, project_details, branch_name):
        branch = repo_details.get_branch(branch_name)
        latest_commit_sha = branch.commit.sha
        if latest_commit_sha == project_details["commit_id"] and project_details["status"] == ProjectStatusEnum.READY:
            return False
        else:
            return True

    @staticmethod
    def fetch_method_from_repo(node):
        method_content = None
        try:
            project_id = node["project_id"]
            project_manager = ProjectManager()
            repo_details = project_manager.get_repo_and_branch_name(project_id=project_id)
            repo_name = repo_details[0]
            branch_name = repo_details[1]

            file_path = node["id"].split(':')[0].lstrip('/')
            start_line = node["start"]
            end_line = node["end"]

            response, auth, owner = GithubService.get_github_repo_details(
                repo_name
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=400, detail="Failed to get installation ID"
                )
            app_auth = auth.get_installation_auth(response.json()["id"])
            github = Github(auth=app_auth)
            repo = github.get_repo(repo_name)
            file_contents = repo.get_contents(file_path.replace("\\","/"), ref=branch_name)
            decoded_content = base64.b64decode(file_contents.content).decode('utf-8')
            lines = decoded_content.split('\n')
            method_lines = lines[start_line - 1:end_line]
            method_content = '\n'.join(method_lines)
        except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True)
        finally:
            github.close()
            return method_content
        
    @staticmethod
    def comment_on_pr(repo_name, issue_number, comment, installation_auth):
        owner = repo_name.split('/')[0]
        repo = repo_name.split('/')[1]
        data = {
            "body":comment
        }
        url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments"
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {installation_auth.token}",
            "X-GitHub-Api-Version": "2022-11-28"
        }

        return requests.post(url, headers=headers, json=data)

    @staticmethod
    def get_app_auth_details(payload):
        private_key = "-----BEGIN RSA PRIVATE KEY-----\n" + os.environ[
            'GITHUB_PRIVATE_KEY'] + "\n-----END RSA PRIVATE KEY-----\n"
        app_id = os.environ["GITHUB_APP_ID"]
        auth = AppAuth(app_id=app_id, private_key=private_key)
        installation_auth = auth.get_installation_auth(payload['installation']['id'])
        github = Github(auth=installation_auth)
        user = github.get_user_by_id(payload['sender']['id'])
        username = user.login
        user_details = get_user_id_by_username(username)
        return auth, installation_auth, user_details, github

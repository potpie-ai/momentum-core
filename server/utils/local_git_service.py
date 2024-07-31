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

from git import Repo, GitCommandError

class LocalGitService:

    @staticmethod
    def get_local_repo_details(repo_path):
        if not os.path.isdir(repo_path):
            raise HTTPException(status_code=400, detail="Repository path does not exist")

        return repo_path

    @staticmethod
    def check_is_commit_added(repo_path, project_details, branch_name):
        try:
            repo = Repo(repo_path)
            branch = repo.branches[branch_name]
            latest_commit_sha = branch.commit.hexsha
            if latest_commit_sha == project_details[3] and project_details[4] == ProjectStatusEnum.READY:
                return False
            else:
                return True
        except GitCommandError as e:
            logger.error(f"An error occurred while checking the latest commit: {e}", exc_info=True)
            return False
        except IndexError:
            logger.error(f"Branch '{branch_name}' not found in repository '{repo_path}'", exc_info=True)
            return False

    @staticmethod
    def fetch_method_from_repo(node):
        method_content = None
        try:
            project_id = node["project_id"]
            project_manager = ProjectManager()
            repo_details = project_manager.get_repo_and_branch_name(project_id=project_id)
            repo_path = repo_details[0]
            branch_name = repo_details[1]
            repo_path_local = repo_details[2]
            defaultUsername = os.getenv("defaultUsername")
            if repo_path_local and repo_path_local.endswith(f'-{defaultUsername}'):
                repo_path = repo_path_local

            file_path = os.path.join(repo_path, node["id"].split(':')[0].lstrip('/'))
            start_line = node["start"]
            end_line = node["end"]

            repo = Repo(repo_path)
            repo.git.checkout(branch_name)

            with open(file_path, 'r') as file:
                lines = file.readlines()
                method_lines = lines[start_line - 1:end_line]
                method_content = ''.join(method_lines)
                
        except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True)
        
        return method_content

from server.db.session import SessionManager
from server.crud import crud_utils
from server.models.repo_details import ProjectStatusEnum
from server.utils.model_helper import model_to_dict
from server.schemas import Project
import logging
from fastapi import HTTPException
from datetime import datetime
import os
import shutil
class ProjectManager:
    def register_project(self, directory: str, project_name: str, repo_name: str, branch_name: str, user_id: str, commit_id: str, default: bool,
                         project_metadata, project_id: int = None):
        with SessionManager() as db:
            if project_id:
                crud_utils.update_project(db, project_id, commit_id=commit_id)
                message = f"Project '{project_id}' updated successfully."
            else:
                project = Project(directory=directory, project_name=project_name, repo_name=repo_name,
                                     branch_name=branch_name, user_id=user_id, commit_id=commit_id, is_default=default,
                                  properties=project_metadata)
                project = crud_utils.create_project(db, project)
                message = f"Project '{project_name}' registered successfully."
                project_id = project.id
            logging.info(message)
        return project_id

    def list_projects(self, user_id: str):
        with SessionManager() as db:
            projects = crud_utils.get_projects_by_user_id(db, user_id)
        project_list = []
        for project in projects:
            project_dict = {
                "id": project.id,
                "directory": project.directory,
                "active": project.is_default,
            }
            project_list.append(project_dict)
        return project_list

    def update_project_status(self, project_id: int, status: ProjectStatusEnum):
        with SessionManager() as db:
            crud_utils.update_project(db, project_id, status=status.value)
            logging.info(f"Project with ID {project_id} has now been updated with status {status}.")

    def get_active_project(self, user_id: str):
        with SessionManager() as db:
            project = db.query(Project).filter(Project.is_default == True, Project.user_id == user_id).first()
            if project:
                return project.id
            else:
                return None

    def get_active_dir(self, user_id: str):
        with SessionManager() as db:
            project = db.query(Project).filter(Project.is_default == True, Project.user_id == user_id).first()
            if project:
                return project.directory
            else:
                return None

    def get_project_from_db(self, project_name: str, user_id: str):
        with SessionManager() as db:
            project = db.query(Project).filter(Project.project_name == project_name, Project.user_id == user_id).first()
            if project:
                return project
            else:
                return None

    def get_project_from_db_by_id(self, project_id: int):
        with SessionManager() as db:
            project = crud_utils.get_project_by_id(db, project_id)
            if project:
                return {
                    "project_name": project.project_name,
                    "directory": project.directory,
                    "id": project.id,
                    "commit_id": project.commit_id,
                    "status": project.status
                }
            else:
                return None

    def get_project_repo_details_from_db(self, project_id: int, user_id: str):
        with SessionManager() as db:
            project = db.query(Project).filter(Project.id == project_id, Project.user_id == user_id).first()
            if project:
                return {
                    "project_name": project.project_name,
                    "directory": project.directory,
                    "id": project.id,
                    "repo_name": project.repo_name,
                    "branch_name": project.branch_name
                }
            else:
                return None

    def get_repo_and_branch_name(self, project_id: int):
        with SessionManager() as db:
            project = crud_utils.get_project_by_id(db, project_id)
            if project:
                return project.repo_name, project.branch_name , project.directory
            else:
                return None

    def get_project_from_db_by_id_and_user_id(self, project_id: int, user_id: str):
        with SessionManager() as db:
            project = db.query(Project).filter(Project.id == project_id, Project.user_id == user_id).first()
            if project:
                return {
                    'project_name': project.project_name,
                    'directory': project.directory,
                    'id': project.id,
                    'commit_id': project.commit_id,
                    'status': project.status
                }
            else:
                return None

    def get_first_project_from_db_by_repo_name_branch_name(self, repo_name, branch_name):
        with SessionManager() as db:
            project = db.query(Project).filter(Project.repo_name == repo_name, Project.branch_name == branch_name).first()
            if project:
                return model_to_dict(project)
            else:
                return None

    def get_first_user_id_from_project_repo_name(self, repo_name):
        with SessionManager() as db:
            project = db.query(Project).filter(Project.repo_name == repo_name).first()
            if project:
                return project.user_id
            else:
                return None

    def get_parsed_project_branches(self, repo_name: str = None, user_id: str = None, default: bool = None):
        with SessionManager() as db:
            query = db.query(Project).filter(Project.user_id == user_id)
            if default is not None:
                query = query.filter(Project.is_default == default)
            if repo_name is not None:
                query = query.filter(Project.repo_name == repo_name)
            projects = query.all()
        return [(p.id, p.branch_name, p.repo_name, p.updated_at, p.is_default, p.status) for p in projects]


    def delete_project(self, project_id: int, user_id: str):
        with SessionManager() as db:
            try:
                result = crud_utils.update_project(
                    db,
                    project_id,
                    is_deleted=True,
                    updated_at=datetime.utcnow(),
                    user_id=user_id
                )
                if not result:
                    raise HTTPException(
                        status_code=404,
                        detail="No matching project found or project is already deleted."
                    )
                else:
                    is_local_repo = os.getenv("isDevelopmentMode") == "enabled" and user_id == os.getenv("defaultUsername")
                    if is_local_repo:
                        project_path = self.get_project_repo_details_from_db(project_id,user_id)['directory']
                        if os.path.exists(project_path):
                            shutil.rmtree(project_path)
                            logging.info(f"Deleted local project folder: {project_path}")
                        else:
                            logging.warning(f"Local project folder not found: {project_path}")


                    logging.info(f"Project {project_id} deleted successfully.")

            except Exception as e:
                db.rollback()
                raise HTTPException(
                    status_code=500,
                    detail=f"An error occurred while deleting the project: {str(e)}"
                )

    def restore_project(self, project_id: int, user_id: str):
        with SessionManager() as db:
            try:
                result = crud_utils.update_project(
                    db,
                    project_id,
                    is_deleted=False,
                    user_id=user_id
                )
                if result:
                    message = f"Project with ID {project_id} restored successfully."
                else:
                    message = "Project not found or already restored."
                logging.info(message)
                return message
            except Exception as e:
                db.rollback()
                logging.error(f"An error occurred: {e}")
                return "Error occurred during restoration."

    def restore_all_project(self, repo_name: str, user_id: str):
        with SessionManager() as db:
            try:
                projects = crud_utils.get_projects_by_repo_name(db, repo_name, user_id, is_deleted=True)
                for project in projects:
                    crud_utils.update_project(db, project.id, is_deleted=False)
                if projects:
                    message = f"Projects with repo_name {repo_name} restored successfully."
                else:
                    message = "Projects not found or already restored."
                logging.info(message)
                return message
            except Exception as e:
                db.rollback()
                logging.error(f"An error occurred: {e}")
                return "Error occurred during restoration."

    def delete_all_project_by_repo_name(self, repo_name: str, user_id: str):
        with SessionManager() as db:
            try:
                projects = crud_utils.get_projects_by_repo_name(db, repo_name, user_id, is_deleted=False)
                for project in projects:
                    crud_utils.update_project(db, project.id, is_deleted=True)
                if projects:
                    message = f"Projects with repo_name {repo_name} deleted successfully."
                else:
                    message = "Projects not found or already deleted."
                logging.info(message)
                return message
            except Exception as e:
                db.rollback()
                logging.error(f"An error occurred: {e}")
                return "Error occurred during deletion."
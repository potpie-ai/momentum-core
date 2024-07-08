from server.db.session import SessionManager
from server.crud import crud_utils
from server.models.repo_details import ProjectStatusEnum
from server.schemas import Project
import logging

class ProjectManager:
    def register_project(self, directory: str, project_name: str, repo_name: str, branch_name: str, user_id: str, commit_id: str, default: bool, project_id: int = None):
        with SessionManager() as db:
            if project_id:
                crud_utils.update_project(db, project_id, commit_id=commit_id)
                message = f"Project '{project_id}' updated successfully."
            else:
                project = Project(directory=directory, project_name=project_name, repo_name=repo_name, 
                                     branch_name=branch_name, user_id=user_id, commit_id=commit_id, is_default=default)
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
                return project.project_name, project.directory, project.id, project.commit_id, project.status
            else:
                return None

    def get_project_from_db_by_id(self, project_id: int):
        with SessionManager() as db:
            project = crud_utils.get_project_by_id(db, project_id)
            if project:
                return project.project_name, project.directory, project.id, project.commit_id, project.status
            else:
                return None

    def get_project_repo_details_from_db(self, project_id: int, user_id: str):
        with SessionManager() as db:
            project = db.query(Project).filter(Project.id == project_id, Project.user_id == user_id).first()
            if project:
                return project.project_name, project.directory, project.id, project.repo_name, project.branch_name
            else:
                return None

    def get_repo_and_branch_name(self, project_id: int):
        with SessionManager() as db:
            project = crud_utils.get_project_by_id(db, project_id)
            if project:
                return project.repo_name, project.branch_name
            else:
                return None

    def get_project_from_db_by_id_and_user_id(self, project_id: int, user_id: str):
        with SessionManager() as db:
            project = db.query(Project).filter(Project.id == project_id, Project.user_id == user_id).first()
            if project:
                return project.project_name, project.directory, project.id, project.commit_id, project.status
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

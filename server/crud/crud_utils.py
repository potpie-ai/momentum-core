from sqlalchemy.orm import Session
from sqlalchemy import and_
from server.schemas import User, Project, Endpoint, Explanation, Pydantic

# User CRUD operations
def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.provider_username == username).first()

def create_user(db: Session, user: User):
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def update_user(db: Session, user_id: str, **kwargs):
    db.query(User).filter(User.uid == user_id).update(kwargs)
    db.commit()

def delete_user(db: Session, user_id: str):
    db.query(User).filter(User.uid == user_id).delete()
    db.commit()

# Project CRUD operations
def get_project_by_id(db: Session, project_id: int):
    return db.query(Project).filter(Project.id == project_id).first()

def get_projects_by_user_id(db: Session, user_id: str):
    return db.query(Project).filter(Project.user_id == user_id).all()

def create_project(db: Session, project: Project):
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def update_project(db: Session, project_id: int, **kwargs):
    project = db.query(Project).filter(Project.id == project_id).first()

    if project is None:
        return None  # Project doesn't exist

    result = db.query(Project).filter(Project.id == project_id).update(kwargs)

    if result > 0:
        db.commit()
        return result

    return None

def delete_project(db: Session, project_id: int):
    db.query(Project).filter(Project.id == project_id).delete()
    db.commit()


def get_projects_by_repo_name(db: Session, repo_name: str, user_id: str, is_deleted: bool = False):
    try:
        projects = db.query(Project).filter(
            and_(
                Project.repo_name == repo_name,
                Project.user_id == user_id,
                Project.is_deleted == is_deleted
            )
        ).all()

        return projects
    except Exception as e:
        db.rollback()
        # Log the error
        print(f"Error fetching projects: {str(e)}")
        # You might want to raise a custom exception here instead of returning None
        return None


# Endpoint CRUD operations
def get_endpoint_by_identifier(db: Session, identifier: str, project_id: int):
    return db.query(Endpoint).filter(Endpoint.identifier == identifier, Endpoint.project_id == project_id).first()

def get_endpoints_by_project_id(db: Session, project_id: int):
    return db.query(Endpoint).filter(Endpoint.project_id == project_id).all()

def create_endpoint(db: Session, endpoint: Endpoint):
    db.add(endpoint)
    db.commit()
    db.refresh(endpoint)
    return endpoint

def update_endpoint(db: Session, identifier: str, project_id: int, **kwargs):
    db.query(Endpoint).filter(Endpoint.identifier == identifier, Endpoint.project_id == project_id).update(kwargs)
    db.commit()

def delete_endpoint(db: Session, identifier: str, project_id: int):
    db.query(Endpoint).filter(Endpoint.identifier == identifier, Endpoint.project_id == project_id).delete()
    db.commit()

# Explanation CRUD operations
def get_explanation_by_identifier(db: Session, identifier: str, hash: str):
    return db.query(Explanation).filter(Explanation.identifier == identifier, Explanation.hash == hash).first()

def get_explanations_by_project_id(db: Session, project_id: int):
    return db.query(Explanation).filter(Explanation.project_id == project_id).all()

def create_explanation(db: Session, explanation: Explanation):
    db.add(explanation)
    db.commit()
    db.refresh(explanation)
    return explanation

def update_explanation(db: Session, identifier: str, project_id: int, **kwargs):
    db.query(Explanation).filter(Explanation.identifier == identifier, Explanation.project_id == project_id).update(kwargs)
    db.commit()

def delete_explanation(db: Session, identifier: str, project_id: int):
    db.query(Explanation).filter(Explanation.identifier == identifier, Explanation.project_id == project_id).delete()
    db.commit()

# Pydantic CRUD operations
def get_pydantic_by_filepath(db: Session, filepath: str, classname: str):
    return db.query(Pydantic).filter(Pydantic.filepath == filepath, Pydantic.classname == classname).first()

def get_pydantics_by_project_id(db: Session, project_id: int):
    return db.query(Pydantic).filter(Pydantic.project_id == project_id).all()

def create_pydantic(db: Session, pydantic: Pydantic):
    db.add(pydantic)
    db.commit()
    db.refresh(pydantic)
    return pydantic

def update_pydantic(db: Session, filepath: str, classname: str, **kwargs):
    db.query(Pydantic).filter(Pydantic.filepath == filepath, Pydantic.classname == classname).update(kwargs)
    db.commit()

def delete_pydantic(db: Session, filepath: str, classname: str):
    db.query(Pydantic).filter(Pydantic.filepath == filepath, Pydantic.classname == classname).delete()
    db.commit()
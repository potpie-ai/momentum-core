import json
import logging
import os
import shutil
import tarfile
import requests
from fastapi import HTTPException
from git import Repo, GitCommandError
from server.models.repo_details import ProjectStatusEnum
from server.utils.graph_db_helper import Neo4jGraph
from server.endpoint_detection import EndpointManager
from server.projects import ProjectManager

project_manager = ProjectManager()
neo4j_graph = Neo4jGraph()

def download_and_extract_tarball(owner, repo, branch, target_dir, auth, repo_details, user_id):
    try:
        tarball_url = repo_details.get_archive_link("tarball", branch)
        response = requests.get(
            tarball_url,
            stream=True,
            headers={"Authorization": f"{auth.token}"},
        )
        response.raise_for_status()  # Check for request errors
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching tarball: {e}")
        return e

    tarball_path = os.path.join(target_dir, f"{repo}-{branch}.tar.gz")
    try:
        with open(tarball_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
    except IOError as e:
        logging.error(f"Error writing tarball to file: {e}")
        return e

    final_dir = os.path.join(target_dir, f'{repo}-{branch}-{user_id}')
    try:
        with tarfile.open(tarball_path, "r:gz") as tar:
            for member in tar.getmembers():
                member_path = os.path.join(
                    final_dir,
                    os.path.relpath(member.name, start=member.name.split("/")[0]),
                )
                if member.isdir():
                    os.makedirs(member_path, exist_ok=True)
                else:
                    member_dir = os.path.dirname(member_path)
                    if not os.path.exists(member_dir):
                        os.makedirs(member_dir)
                    with open(member_path, "wb") as f:
                        if member.size > 0:
                            f.write(tar.extractfile(member).read())
    except (tarfile.TarError, IOError) as e:
        logging.error(f"Error extracting tarball: {e}")
        return e

    try:
        os.remove(tarball_path)
    except OSError as e:
        logging.error(f"Error removing tarball: {e}")
        return e

    return final_dir

def setup_project_directory(owner, repo, branch, auth, repo_details, user_id, project_id=None):
    should_parse_repo = True
    default = False

    if isinstance(repo_details, Repo):
        extracted_dir = repo_details.working_tree_dir
        try:
            current_dir = os.getcwd()
            os.chdir(extracted_dir)  # Change to the cloned repo directory
            repo_details.git.checkout(branch)
        except GitCommandError as e:
            logging.error(f"Error checking out branch: {e}")
            raise HTTPException(status_code=400, detail=f"Failed to checkout branch {branch}")
        finally:
            os.chdir(current_dir)  # Restore the original working directory
        branch_details = repo_details.head.commit
        latest_commit_sha = branch_details.hexsha
    else:
        if branch == repo_details.default_branch:
            default = True
        extracted_dir = download_and_extract_tarball(
            owner, repo, branch, os.getenv("PROJECT_PATH"), auth, repo_details, user_id
        )
        branch_details = repo_details.get_branch(branch)
        latest_commit_sha = branch_details.commit.sha

    momentum_dir = os.path.join(extracted_dir, ".momentum")
    os.makedirs(momentum_dir, exist_ok=True)
    with open(os.path.join(momentum_dir, "momentum.db"), "w") as fp:
        pass

    repo_metadata = extract_repository_metadata(repo_details)
    repo_metadata['error_message'] = None
    
    if(os.getenv("isDevelopmentMode") == "disabled"):
        python_percentage = (repo_metadata["languages"]["breakdown"]["Python"] /
                            repo_metadata["languages"]["total_bytes"] * 100) \
            if "Python" in repo_metadata["languages"]["breakdown"] else 0
        if python_percentage < 50:
            repo_metadata['error_message'] = "Repository doesn't consist of a language currently supported."
            should_parse_repo = False
        else:
            repo_metadata['error_message'] = None

    project_id = project_manager.register_project(
        extracted_dir,
        f"{repo}-{branch}",
        f"{owner}/{repo}",
        branch,
        user_id,
        latest_commit_sha,
        default,
        json.dumps(repo_metadata).encode('utf-8'),
        project_id
    )
    project_manager.update_project_status(project_id, ProjectStatusEnum.CREATED)
    return extracted_dir, project_id, should_parse_repo

def reparse_cleanup(project_details, user_id):
    directory = project_details.directory
    project_id = project_details.id
    EndpointManager(directory).delete_endpoints(project_id, user_id)
    neo4j_graph.delete_nodes_by_project_id(project_id)
    delete_folder(directory)

def extract_repository_metadata(repo):
    if isinstance(repo, Repo):
        metadata = extract_local_repo_metadata(repo)
    else:
        metadata = extract_remote_repo_metadata(repo)
    return metadata

def extract_local_repo_metadata(repo):
    languages = get_local_repo_languages(repo.working_tree_dir)
    total_bytes = sum(languages.values())

    metadata = {
        "basic_info": {
            "full_name": os.path.basename(repo.working_tree_dir),
            "description": None,
            "created_at": None,
            "updated_at": None,
            "default_branch": repo.head.ref.name,
        },
        "metrics": {
            "size": get_directory_size(repo.working_tree_dir),
            "stars": None,
            "forks": None,
            "watchers": None,
            "open_issues": None,
        },
        "languages": {
            "breakdown": languages,
            "total_bytes": total_bytes,
        },
        "commit_info": {
            "total_commits": len(list(repo.iter_commits()))
        },
        "contributors": {
            "count": len(list(repo.iter_commits('--all'))),
        },
        "topics": [],
    }

    return metadata

def get_local_repo_languages(path):
    total_bytes = 0
    python_bytes = 0

    for dirpath, _, filenames in os.walk(path):
        for filename in filenames:
            file_extension = os.path.splitext(filename)[1]
            file_path = os.path.join(dirpath, filename)
            file_size = os.path.getsize(file_path)
            total_bytes += file_size
            if file_extension == '.py':
                python_bytes += file_size

    languages = {}
    if total_bytes > 0:
        languages['Python'] = python_bytes
        languages['Other'] = total_bytes - python_bytes

    return languages

def extract_remote_repo_metadata(repo):
    languages = repo.get_languages()
    total_bytes = sum(languages.values())

    metadata = {
        "basic_info": {
            "full_name": repo.full_name,
            "description": repo.description,
            "created_at": repo.created_at.isoformat(),
            "updated_at": repo.updated_at.isoformat(),
            "default_branch": repo.default_branch,
        },
        "metrics": {
            "size": repo.size,
            "stars": repo.stargazers_count,
            "forks": repo.forks_count,
            "watchers": repo.watchers_count,
            "open_issues": repo.open_issues_count,
        },
        "languages": {
            "breakdown": languages,
            "total_bytes": total_bytes,
        },
        "commit_info": {
            "total_commits": repo.get_commits().totalCount
        },
        "contributors": {
            "count": repo.get_contributors().totalCount,
        },
        "topics": repo.get_topics(),
    }

    return metadata

def get_directory_size(path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size

def delete_folder(folder_path):
    if(os.getenv("isDevelopmentMode") == "enabled"):
        logging.info("Not deleting local git repo to support knowledge graph")
        return
    try:
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            shutil.rmtree(folder_path, ignore_errors=True)
            logging.info(f"deleted {folder_path}")
    except Exception as e:
        logging.exception(f"Error in deleting folder: {str(e)}")

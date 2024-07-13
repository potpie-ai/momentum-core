import logging
import os
import shutil
import tarfile
import logging
import requests
from fastapi import HTTPException

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
    if branch == repo_details.default_branch:
        default = True
    else:
        default = False
    projects_dir = os.getenv("PROJECT_PATH")
    extracted_dir = download_and_extract_tarball(
        owner, repo, branch, projects_dir, auth, repo_details, user_id
    )
    momentum_dir = os.path.join(extracted_dir, ".momentum")
    os.makedirs(momentum_dir, exist_ok=True)
    with open(os.path.join(momentum_dir, "momentum.db"), "w") as fp:
        pass
    branch_details = repo_details.get_branch(branch)
    latest_commit_sha = branch_details.commit.sha
    project_id = project_manager.register_project(
        extracted_dir,
        f"{repo}-{branch}",
        f"{owner}/{repo}",
        branch,
        user_id,
        latest_commit_sha,
        default,
        project_id
    )
    return extracted_dir, project_id


def reparse_cleanup(project_details, user_id):
    directory = project_details[1]
    project_id = project_details[2]
    EndpointManager(directory).delete_endpoints(project_id, user_id)
    neo4j_graph.delete_nodes_by_project_id(project_id)
    delete_folder(directory)


def delete_folder(folder_path):
    try:
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            shutil.rmtree(folder_path, ignore_errors=True)
            logging.info(f"deleted {folder_path}")
        # else:
            # raise HTTPException(status_code=404, detail="Project Folder not found")
    except Exception as e:
        logging.exception(f"Error in deleting folder: {str(e)}")
        # raise HTTPException(status_code=400, detail="Error deleting Project Folder.")
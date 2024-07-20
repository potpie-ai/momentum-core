import json
import os
import time
from asyncio import create_task
import logging
import requests


from fastapi import HTTPException, Request, Response
from github import Github
from github.Auth import AppAuth

from server.utils.github_helper import GithubService
from server.models.repo_details import RepoDetails, ProjectStatusEnum
from server.parse import analyze_directory, get_values
from server.projects import ProjectManager
from server.utils.parse_helper import setup_project_directory
from server.utils.APIRouter import APIRouter
from server.change_detection import get_updated_function_list
from server.blast_radius_detection import get_paths_from_identifiers
from server.endpoint_detection import EndpointManager

from server.utils.parse_helper import reparse_cleanup
from server.utils.user_service import get_user_id_by_username
from server.plan import Plan

router = APIRouter()
project_manager = ProjectManager()


@router.post("/webhook")
async def github_app(request: Request):
    github_event = request.headers.get("X-GitHub-Event")
    payload = await request.body()
    logging.info(f"Received webhook event: {payload}")
    create_task(handle_request(request, github_event, payload))
    return Response(status_code=200)


async def parse_repos(payload, request: Request):
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
                        dir_details, project_id = setup_project_directory(
                            owner,
                            repo_name,
                            branch_name,
                            installation_auth,
                            repo_details,
                            user_id
                        )
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
                dir_details, project_id = setup_project_directory(
                    owner,
                    repo_name,
                    branch_name,
                    installation_auth,
                    repo_details,
                    user_id,
                    project_id
                )
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
            github.close()

async def handle_request(request, github_event, payload):
    json_payload = json.loads(payload)
    github_action = json_payload.get("action")

    if github_event == "issue_comment":
        state = json_payload.get("issue").get("state")
        comment = json_payload.get("comment").get("body")
        bot_name = os.environ["GITHUB_BOT_NAME"]
        if state == "open" and "/plan" in comment.lower() and f"@{bot_name}" in comment.lower():
            await handle_comment_with_mention(json_payload, comment)
    elif github_event == "pull_request":
        if github_action == "opened" :
            await handle_open_pr(json_payload)
        elif github_action == "synchronize" or github_action == "reopened":
            await handle_update_pr(json_payload)
        elif github_action == "closed":
            pass
        elif github_action == "reopened":
            pass
    elif github_event == "create":
        pass
    elif github_event == "push":
        pass
    else:
        create_task(parse_repos(payload, request))

async def handle_update_pr(payload):
    #Parsing payload to fetch the necessary details
    repo_name = payload['repository']['full_name']
    branch_name = payload['pull_request']['head']['ref']
    base_branch_name = payload['pull_request']['base']['ref']
    pr_number = payload['pull_request']['number']

    #generating auth & creating github object
    installation_auth = get_installation_auth(payload)

    #Fetching project details from database
    project_details = project_manager.get_first_project_from_db_by_repo_name_branch_name(repo_name, branch_name)

    #Get blast radius using project id and base branch name
    blast_radius = get_blast_radius_details(project_details[2], repo_name, branch_name, installation_auth, base_branch_name)

    #Parsing the blast radius as a markdown table
    blast_radius = parse_blast_radius_to_markdown(blast_radius)

    #Commenting on PR with blast radius info.
    if(len(blast_radius)> 0):
        GithubService.comment_on_pr(repo_name, pr_number, blast_radius, installation_auth)


async def handle_open_pr(payload):
    #Parsing payload to fetch the necessary details
    repo_name = payload['repository']['full_name']
    branch_name = payload['pull_request']['head']['ref']
    base_branch_name = payload['pull_request']['base']['ref']
    owner = payload["pull_request"]["head"]["repo"]["owner"]["login"]
    pr_number = payload["pull_request"]["number"]

    #creating github object & fetching repo details
    installation_auth = get_installation_auth(payload)
    github = Github(auth=installation_auth)
    repo_details = github.get_repo(repo_name)
    github.close()

    #Fetching user id from database
    user_id = project_manager.get_first_user_id_from_project_repo_name(repo_name)
    #Fetching project details from database if exists:
    project_details = project_manager.get_first_project_from_db_by_repo_name_branch_name(repo_name, branch_name)
    if project_details is None:
        #Create project for the branch & parsing it
        dir_details, project_id = setup_project_directory(
            owner,
            repo_name.split("/")[-1],
            branch_name,
            installation_auth,
            repo_details,
            user_id[0],
            project_id=None
        )
        await analyze_directory(dir_details, user_id, project_id)
        logging.info("The project has been parsed successfully")
        project_manager.update_project_status(
            project_id, ProjectStatusEnum.READY
        )
    else:
        project_id = project_details[2]
        if GithubService.check_is_commit_added(repo_details, project_details, branch_name):
            reparse_cleanup(project_details, user_id)
            dir_details, project_id = setup_project_directory(owner, repo_name.split("/")[-1],
                                                                branch_name, installation_auth, repo_details, user_id,
                                                                project_id)
            await analyze_directory(dir_details, user_id, project_id)
            logging.info("The project has been re-parsed successfully")
            project_manager.update_project_status(
                project_id, ProjectStatusEnum.READY
            )

    #Get blast radius using base branch name
    blast_radius = get_blast_radius_details(project_id, repo_name, branch_name, installation_auth, base_branch_name)
    #Parsing the blast radius as a markdown table
    blast_radius = parse_blast_radius_to_markdown(blast_radius)

    #Commenting on PR with blast radius info.
    if(len(blast_radius)> 0):
        GithubService.comment_on_pr(repo_name, pr_number, blast_radius, installation_auth)
    
async def handle_comment_with_mention(payload, comment):
    #Parsing payload to fetch the necessary details
    repo_name = payload['repository']['full_name']
    issue_number = payload['issue']['number']
    comment_list = comment.split(" ")

    #generating auth & creating github object
    installation_auth = get_installation_auth(payload)
    github = Github(auth=installation_auth)
    repo = github.get_repo(repo_name)
    pull_request = repo.get_pull(issue_number)
    branch_name = pull_request.head.ref
    #Fetching project details & userid from database
    project_details = project_manager.get_first_project_from_db_by_repo_name_branch_name(repo_name, branch_name)
    endpoint_path = " ".join(comment_list[comment_list.index("/plan") + 1:])
    user_id = project_details[3]
    
    identifier = EndpointManager(
        project_details[1]
    ).get_endpoint_id_from_path(endpoint_path, project_details[2])

    #Fetch test plan for specified identifier
    test_plan = EndpointManager(
        project_details[1]
    ).get_test_plan(identifier, project_details[2])
    if test_plan is None:
        try:
            test_plan = await Plan(
                user_id
            ).generate_test_plan_for_endpoint(identifier, project_details)
        except Exception:
            test_plan = {}
        
    #Commenting on PR with test plan info.
    if test_plan != "":
        test_plan_comment = f"Test plan for {endpoint_path}:\n" + test_plan_to_markdown(test_plan)
        pull_request.create_issue_comment(test_plan_comment)
        github.close()
        

def test_plan_to_markdown(test_plan):
    # Extract the keys from the dictionary
    keys = list(test_plan.keys())

    # Initialize the markdown table string with the "Category" column
    table = "| Category | Description |\n"
    table += "|----------|-------------|\n"

    # Iterate over the keys and their corresponding values
    for key in keys:
        for item in test_plan[key]:
            table += f"| {key} | {item} |\n"

    return table

def get_installation_auth(payload):
    private_key = "-----BEGIN RSA PRIVATE KEY-----\n" + os.environ[
        'GITHUB_PRIVATE_KEY'] + "\n-----END RSA PRIVATE KEY-----\n"
    app_id = os.environ["GITHUB_APP_ID"]
    auth = AppAuth(app_id=app_id, private_key=private_key)
    return auth.get_installation_auth(payload['installation']['id'])

def parse_blast_radius_to_markdown(blast_radius):
    markdown_output = "| Filename | Entry Point |\n"
    markdown_output += "| --- | --- |\n"
    
    for filename, endpoints in blast_radius.items():
        for endpoint in endpoints:
            entry_point = endpoint["entryPoint"]
            markdown_output += f"| {filename} | {entry_point} |\n"
    
    return "## Blast Radius:\n"+ markdown_output

def get_blast_radius_details(project_id: int, repo_name: str, branch_name: str, installation_auth, base_branch
    ):
    global patches_dict, repo
    project_details = project_manager.get_project_from_db_by_id(project_id)
    github = Github(auth=installation_auth)
    try:
        repo = github.get_repo(repo_name)
        git_diff = repo.compare(base_branch, branch_name)
        patches_dict = {file.filename: file.patch for file in git_diff.files if file.patch}
    except Exception:
        logging.error("Repository not found")
    else:
        if project_details is not None:
            directory = project_details[1]
            identifiers = []
            try:
                identifiers = get_updated_function_list(patches_dict, directory, repo, branch_name)
            except Exception as e:
                logging.error(f"project_id: {project_id}, error: {str(e)}")
                if "path not in the working tree" in str(e):
                    base_branch = "main"
                    identifiers = get_updated_function_list(patches_dict, directory, repo, branch_name)
            if identifiers.count == 0:
                return []
            paths = get_paths_from_identifiers(
                identifiers, directory, project_details[2]
            )
            return paths
        else:
            return []
    finally:
        github.close()
        
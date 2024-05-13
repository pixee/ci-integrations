import os
import sys
import json
import subprocess

from dotenv import load_dotenv
from secrets import token_hex

import whatthepatch
load_dotenv()

from providers.bitbucket_provider import BitbucketProvider
from providers.github_provider import GitHubProvider

from git_provider import GitProvider

def get_provider():
    
    access_token = get_access_token()
    provider = {
        "pr_id": None,
        "client": None,
        "source_branch": None    
    }

    if os.getenv('GITLAB_FEATURES'):
        return None
    elif os.getenv('GITHUB_ACTIONS'):
        repo = os.environ.get("GITHUB_REPOSITORY")
        provider["client"] = GitProvider.create_client(GitHubProvider(repo, access_token))

        # Path to the JSON file with the full event details
        event_path = os.getenv('GITHUB_EVENT_PATH')

        # Read and parse the JSON file
        with open(event_path, 'r') as file:
            event = json.load(file)

        #pr_id = event['pull_request']['id']
        pr_number = event['pull_request']['number']
        provider["source_branch"] = event['pull_request']['head']['ref']
        provider["pr_id"] = pr_number

        #return None
    elif os.getenv('BITBUCKET_WORKSPACE'):
        workspace = os.environ.get("BITBUCKET_WORKSPACE")
        bitbucket_url = os.environ.get("BITBUCKET_API_URL") or "https://api.bitbucket.org/2.0/"
        repo = os.environ.get("BITBUCKET_REPO_SLUG")
        provider["client"] = GitProvider.create_client(BitbucketProvider(workspace, repo, access_token, bitbucket_url))
    else:
        return None

    return provider

def get_access_token():
    # List of possible environment variables that can contain the access token
    token_keys = [
        'BITBUCKET_ACCESS_TOKEN_PIXEE',
        'GITLAB_API_TOKEN_PIXEE',
        'GITHUB_TOKEN'
    ]

    # Iterate over the list of token keys and return the first one found
    for key in token_keys:
        access_token = os.getenv(key)
        if access_token:
            return access_token

    # If no token was found, print available environment variables and exit
    print("Available environment variables:", dict(os.environ))
    sys.exit(f'Error: Missing Access Token. Please set the access token in one of the following environment variables: {", ".join(token_keys)}')


def get_code_tf_results(file_path="/tmp/results.codetf.json"):
    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)
        return data

def main():

    provider = get_provider()
    git_service = provider["client"]
    pr_id = provider["pr_id"]

    if provider["client"]:
        print("Service Found")
        print(provider)
        command = ["pixee", "fix", "--apply-fixes", "--output", "/tmp/results.codetf.json"]

        # TODO - Add support for other options
        #if(os.getenv('PIXEE_OPTS')):
        #    command.append(os.getenv('PIXEE_OPTS'))

        pr = git_service.get_pr(pr_id)
        if(pr.changed_files):
            command.append( "--path-include")
            command.append(",".join(pr.changed_files))
        
        command.append(os.getcwd())
        print(command)

        process = subprocess.run(command, text=True, capture_output=True, check=True)
        # Output the result
        if process.returncode == 0:
            print("Output:", process.stdout)
        else:
            print("Error:", process.stderr)
            # exit the program
            sys.exit(1)

        # check if /tmp/results.codetf.json exists
        if os.path.exists("/tmp/results.codetf.json"):
            data = get_code_tf_results()
            source_title = pr.title
            pr_title = f"Hardening Suggestions for: '{source_title}'."
            # create a new branch with a unique name
            new_branch_name = f"pixee_{pr_id}_{token_hex(4)}"

            branch = git_service.create_branch(new_branch_name, provider["source_branch"])
            print(f"Created a new branch: {branch.name}")
            made_change = False
            
            description = ""
            for result in data["results"]:
                if len(result["changeset"]):
                    description += "## {}\n{}\n\n".format(result["summary"], result["description"])

                    if len(result["changeset"]) >= 1:
                        made_change = True

                for entry in result["changeset"]:
                    try:
                        file_path = entry["path"]
                        
                        original_file_content = git_service.get_file(file_path, new_branch_name)

                        diff = list(whatthepatch.parse_patch(entry["diff"]))
                        diff = diff[0]

                        new_file = whatthepatch.apply_diff(
                            diff, original_file_content, use_patch=True
                        )
                        new_file = "\n".join(new_file[0])
                        git_service.create_commit(file_path, new_branch_name, new_file, result["summary"])
                    except Exception as e:
                        print(e)
                        print("Error creating commit")
            
            if(made_change):
                new_pr = git_service.create_pr(new_branch_name, provider["source_branch"], pr_title, description)
                comment = f"Pixee has reviewed the code made [some suggestions]({new_pr.web_url})."
                git_service.create_pr_comment(pr_id, comment)
        else:
            print("File not found")    

    else:
        print("service not found")

if __name__ == "__main__":
    main()
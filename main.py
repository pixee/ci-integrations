import os
import sys
import git

from dotenv import load_dotenv

#import whatthepatch
load_dotenv()

from providers.bitbucket_provider import BitbucketProvider
from git_provider import GitProvider

def get_provider():
    
    access_token = os.getenv('BITBUCKET_ACCESS_TOKEN_PIXEE') or os.environ.get("GITLAB_API_TOKEN_PIXEE") or os.environ.get("GITHUB_API_TOKEN_PIXEE")
    if not access_token:
        print(os.environ)
        sys.exit('Error: Missing Access Token. Please set the access token in the environment variable BITBUCKET_ACCESS_TOKEN_PIXEE, GITLAB_API_TOKEN_PIXEE or GITHUB_API_TOKEN_PIXEE')

    if os.getenv('GITLAB_FEATURES'):
        return None
    elif os.getenv('GITHUB_ACTIONS'):
        return None
    elif os.getenv('BITBUCKET_WORKSPACE'):
        workspace = os.environ.get("BITBUCKET_WORKSPACE")
        bitbucket_url = os.environ.get("BITBUCKET_API_URL") or "https://api.bitbucket.org/2.0/"
        repo = os.environ.get("BITBUCKET_REPO_SLUG")
        return GitProvider.create_client(BitbucketProvider(workspace, repo, access_token, bitbucket_url))
    else:
        return None

def main():

    print(os.environ)

    git_service = get_provider()
     
    if git_service:
        print("service found")
        print(git_service)
        # Initialize the repo object, specifying the path to your repository
        repo_path = '.'  # Adjust this to the path of your repository if not currently in the directory
        repo = git.Repo(repo_path)

        # Define the branches
        base_branch = os.getenv('BITBUCKET_PR_DESTINATION_BRANCH') #'main' #BITBUCKET_PR_DESTINATION_BRANCH
        feature_branch = os.getenv('BITBUCKET_BRANCH') #'test_pixee_36853e69' #BITBUCKET_BRANCH

        # Fetch the latest changes for up-to-date comparison
        
        
        #repo.git.execute(['git', 'config', '--unset', f"http.{os.getenv('BITBUCKET_ACCESS_TOKEN_PIXEE')}.proxy"])


        #repo.git.fetch()
        
        command_result = repo.git.diff(f'{base_branch}..{feature_branch}', name_only=True)
        file_list = command_result.splitlines()

        print(file_list)

    else:
        print("service not found")

if __name__ == "__main__":
    main()



import os
import requests

class GitHubClient:
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        self.headers = {"Authorization": f"token {self.token}"}

    def post_pr_comment(self, owner: str, repo: str, pr_number: int, body: str):
        url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
        resp = requests.post(url, json={"body": body}, headers=self.headers)
        if resp.status_code == 201:
            print("✅ AI review posted to PR!")
        else:
            print(f"❌ Failed to comment: {resp.text}")
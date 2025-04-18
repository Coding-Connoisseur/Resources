from flask import Flask, request, jsonify
from flask import Flask, request, jsonify
import os
import requests
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}
API_BASE = "https://api.github.com"

def github(method, endpoint, **kwargs):
    response = requests.request(method, f"{API_BASE}{endpoint}", headers=HEADERS, **kwargs)
    return jsonify(response.json()), response.status_code


# ========== ISSUES ==========
@app.route("/create_github_issue", methods=["POST"])
def create_issue():
    data = request.json
    return github_api("POST", f"/repos/{USERNAME}/{data['repo']}/issues", json={
        "title": data["title"],
        "body": data.get("body", "")
    })

@app.route("/list_issues", methods=["GET"])
def list_issues():
    repo = request.args["repo"]
    return github_api("GET", f"/repos/{USERNAME}/{repo}/issues")

@app.route("/close_issue", methods=["POST"])
def close_issue():
    data = request.json
    return github_api("PATCH", f"/repos/{USERNAME}/{data['repo']}/issues/{data['issue_number']}", json={
        "state": "closed"
    })

@app.route("/comment_issue", methods=["POST"])
def comment_issue():
    data = request.json
    return github_api("POST", f"/repos/{USERNAME}/{data['repo']}/issues/{data['issue_number']}/comments", json={
        "body": data["comment"]
    })


# ========== PULL REQUESTS ==========
@app.route("/create_pull_request", methods=["POST"])
def create_pr():
    data = request.json
    return github_api("POST", f"/repos/{USERNAME}/{data['repo']}/pulls", json={
        "head": data["head"],
        "base": data["base"],
        "title": data["title"],
        "body": data.get("body", "")
    })

@app.route("/list_pull_requests", methods=["GET"])
def list_prs():
    repo = request.args["repo"]
    return github_api("GET", f"/repos/{USERNAME}/{repo}/pulls")

@app.route("/merge_pull_request", methods=["POST"])
def merge_pr():
    data = request.json
    return github_api("PUT", f"/repos/{USERNAME}/{data['repo']}/pulls/{data['pull_number']}/merge")


# ========== FILE CONTENTS ==========
@app.route("/commit_file", methods=["POST"])
def commit_file():
    data = request.json
    url = f"/repos/{USERNAME}/{data['repo']}/contents/{data['path']}"
    json_data = {
        "message": data["message"],
        "content": data["content"],
        "branch": data.get("branch", "main")
    }
    return github_api("PUT", url, json=json_data)

@app.route("/list_repo_contents", methods=["GET"])
def list_contents():
    repo = request.args["repo"]
    path = request.args.get("path", "")
    return github_api("GET", f"/repos/{USERNAME}/{repo}/contents/{path}")

@app.route("/get_file_contents", methods=["GET"])
def get_file_contents():
    repo = request.args["repo"]
    path = request.args["path"]
    ref = request.args.get("ref")
    params = {"ref": ref} if ref else {}
    return github_api("GET", f"/repos/{USERNAME}/{repo}/contents/{path}", params=params)

@app.route("/create_file", methods=["POST"])
def create_file():
    data = request.json
    return github_api("PUT", f"/repos/{USERNAME}/{data['repo']}/contents/{data['path']}", json={
        "message": data["message"],
        "content": data["content"],
        "branch": data.get("branch", "main")
    })

@app.route("/update_file", methods=["PUT"])
def update_file():
    data = request.json
    return github_api("PUT", f"/repos/{USERNAME}/{data['repo']}/contents/{data['path']}", json={
        "message": data["message"],
        "content": data["content"],
        "sha": data["sha"],
        "branch": data.get("branch", "main")
    })

@app.route("/delete_file", methods=["DELETE"])
def delete_file():
    data = request.json
    return github_api("DELETE", f"/repos/{USERNAME}/{data['repo']}/contents/{data['path']}", json={
        "message": data["message"],
        "sha": data["sha"],
        "branch": data.get("branch", "main")
    })


# ========== COMMITS ==========
@app.route("/list_commits", methods=["GET"])
def list_commits():
    repo = request.args["repo"]
    params = {
        "sha": request.args.get("sha"),
        "path": request.args.get("path")
    }
    return github_api("GET", f"/repos/{USERNAME}/{repo}/commits", params={k: v for k, v in params.items() if v})

@app.route("/get_commit", methods=["GET"])
def get_commit():
    repo = request.args["repo"]
    sha = request.args["sha"]
    return github_api("GET", f"/repos/{USERNAME}/{repo}/commits/{sha}")

@app.route("/comment_commit", methods=["POST"])
def comment_commit():
    data = request.json
    json_data = {
        "body": data["body"]
    }
    if "path" in data and "position" in data:
        json_data["path"] = data["path"]
        json_data["position"] = data["position"]
    return github_api("POST", f"/repos/{USERNAME}/{data['repo']}/commits/{data['sha']}/comments", json=json_data)


# ========== REPOS ==========
@app.route("/list_user_repos", methods=["GET"])
def list_user_repos():
    return github_api("GET", f"/users/{USERNAME}/repos")

# === CODESPACES ROUTES ===

@app.route("/list_codespaces", methods=["GET"])
def list_codespaces():
    return github("GET", "/user/codespaces")

@app.route("/create_codespace", methods=["POST"])
def create_codespace():
    data = request.json
    return github("POST", "/user/codespaces", json=data)

@app.route("/get_codespace", methods=["GET"])
def get_codespace():
    name = request.args["codespace_name"]
    return github("GET", f"/user/codespaces/{name}")

@app.route("/update_codespace", methods=["PATCH"])
def update_codespace():
    name = request.args["codespace_name"]
    return github("PATCH", f"/user/codespaces/{name}", json=request.json)

@app.route("/delete_codespace", methods=["DELETE"])
def delete_codespace():
    name = request.args["codespace_name"]
    return github("DELETE", f"/user/codespaces/{name}")

@app.route("/export_codespace", methods=["POST"])
def export_codespace():
    name = request.args["codespace_name"]
    return github("POST", f"/user/codespaces/{name}/exports")

@app.route("/get_codespace_export_details", methods=["GET"])
def get_codespace_export_details():
    export_id = request.args["export_id"]
    return github("GET", f"/user/codespaces/exports/{export_id}")

@app.route("/create_repo_from_unpublished_codespace", methods=["POST"])
def create_repo_from_codespace():
    name = request.args["codespace_name"]
    return github("POST", f"/user/codespaces/{name}/publish")

@app.route("/start_codespace", methods=["POST"])
def start_codespace():
    name = request.args["codespace_name"]
    return github("POST", f"/user/codespaces/{name}/start")

@app.route("/stop_codespace", methods=["POST"])
def stop_codespace():
    name = request.args["codespace_name"]
    return github("POST", f"/user/codespaces/{name}/stop")

@app.route("/list_repo_codespaces", methods=["GET"])
def list_repo_codespaces():
    owner = request.args["owner"]
    repo = request.args["repo"]
    return github("GET", f"/repos/{owner}/{repo}/codespaces")

@app.route("/create_repo_codespace", methods=["POST"])
def create_repo_codespace():
    data = request.json
    owner = data["owner"]
    repo = data["repo"]
    body = {
        "ref": data["branch"],
        "location": data.get("location"),
        "machine": data.get("machine")
    }
    return github("POST", f"/repos/{owner}/{repo}/codespaces", json=body)

# Example machine type support (optional)
@app.route("/list_repo_machines", methods=["GET"])
def list_repo_machines():
    owner = request.args["owner"]
    repo = request.args["repo"]
    return github("GET", f"/repos/{owner}/{repo}/codespaces/machines")

@app.route("/list_codespace_machines", methods=["GET"])
def list_codespace_machines():
    name = request.args["codespace_name"]
    return github("GET", f"/user/codespaces/{name}/machines")


# ========== MAIN ==========
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

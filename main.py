import os
import re
import sys
import time
import json
import errno
import requests
import subprocess
import urllib.parse
from datetime import datetime

def get_json(url, token):
    while True:
        response = requests.get(
            url, headers={"Authorization": "token {0}".format(token)}
        )
        response.raise_for_status()
        yield response.json()

        if "next" not in response.links:
            break
        url = response.links["next"]["url"]

def check_name(name):
    if not re.match(r"^\w[-\.\w]*$", name):
        raise RuntimeError("invalid name '{0}'".format(name))
    return name

def mkdir(path):
    try:
        os.makedirs(path, 0o770)
    except OSError as ose:
        if ose.errno != errno.EEXIST:
            raise
        return False
    return True

def mirror(repo_name, repo_url, to_path, username, token):
    parsed = urllib.parse.urlparse(repo_url)
    modified = list(parsed)
    modified[1] = "{username}:{token}@{netloc}".format(
        username=username, token=token, netloc=parsed.netloc
    )
    repo_url = urllib.parse.urlunparse(modified)

    repo_path = os.path.join(to_path, repo_name)
    mkdir(repo_path)

    subprocess.call(["git", "init", "--bare", "--quiet"], cwd=repo_path)

    subprocess.call(
        [
            "git",
            "fetch",
            "--force",
            "--prune",
            "--tags",
            repo_url,
            "refs/heads/*:refs/heads/*",
        ],
        cwd=repo_path,
    )

def backup(config_path):
    with open(config_path, "rb") as f:
        config = json.loads(f.read())

    owners = config.get("owners")
    token = config["token"]
    path = os.path.expanduser(config["directory"])
    if mkdir(path):
        print("Created directory {0}".format(path), file=sys.stderr)

    user = next(get_json("https://api.github.com/user", token))
    for page in get_json("https://api.github.com/user/repos", token):
        for repo in page:
            name = check_name(repo["name"])
            owner = check_name(repo["owner"]["login"])
            clone_url = repo["clone_url"]

            if owners and owner not in owners:
                continue

            owner_path = os.path.join(path, owner)
            mkdir(owner_path)
            mirror(name, clone_url, owner_path, user["login"], token)

if __name__ == "__main__":
    configs = []
    while True:
        for config in configs:
            try:
                backup(config)
            except Exception as e:
                with open('./error.log' , 'a+') as f:
                    f.write(datetime.today().strftime('%Y-%m-%d-%H:%M:%S') + ": " + str(e) + '\n')
        time.sleep(900)

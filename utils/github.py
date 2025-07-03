import os, time
from pathlib import Path
from git import Repo, GitCommandError           # GitPython
from github import Github                       # PyGithub
import configparser

config = configparser.ConfigParser()
print("Loaded sections:", config.sections())

config_path = os.path.join(os.path.dirname(__file__), '..', 'config.ini')
config.read(config_path)

if "GITHUB" not in config or "TOKEN" not in config["GITHUB"]:
    raise RuntimeError("Missing GITHUB.TOKEN in config.ini")

GITHUB_TOKEN = config["GITHUB"]["TOKEN"]

REPO_URL       = "https://github.com/tejojith/scripts.git"
DEFAULT_BRANCH = "main"                         # or 'master'

def push_file_and_open_pr(local_repo_path: str, new_file: str, pr_title: str,
                          pr_body: str | None = None) -> str:
    """
    • writes/commits <new_file> (relative to project root)
    • pushes to a fresh branch
    • opens a (draft) pull-request
    • returns the PR html_url
    """
    ts          = time.strftime("%Y%m%d%H%M%S")
    branch_name = f"auto-validation-{ts}"

    ## ---- local Git actions -------------------------------------------------
    repo   = Repo(local_repo_path)
    origin = repo.remote("origin")
    # Make sure our remote URL contains the token once (HTTPS form):
    origin_url_pat = REPO_URL.replace("https://",
                                      f"https://{GITHUB_TOKEN}@")
    origin.set_url(origin_url_pat)

    repo.git.checkout(DEFAULT_BRANCH)      # start clean
    repo.git.pull("--ff-only")

    repo.git.checkout("-b", branch_name)
    repo.git.add(new_file)
    repo.index.commit(f"[auto] add {new_file}")

    try:
        origin.push(branch_name)
    except GitCommandError as exc:
        raise RuntimeError(f"Git push failed: {exc}") from exc

    ## ---- GitHub API actions ------------------------------------------------
    gh   = Github(GITHUB_TOKEN)
    repo = gh.get_repo("tejojith/scripts")

    pr = repo.create_pull(
        title = pr_title,
        body  = pr_body or "Automated PR - awaiting review ✅",
        head  = branch_name,
        base  = DEFAULT_BRANCH,
        draft = True                       # reviewers can mark ready later
    )

    return pr.html_url

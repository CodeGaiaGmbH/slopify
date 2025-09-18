import configparser
import os
import subprocess
from io import StringIO
import tempfile
import jira as jiralib
import sys


def get_project_map():
    files = {}
    all_git_files = (
        subprocess.check_output(
            ["git", "ls-files"],
        )
        .decode("utf-8")
        .splitlines()
    )
    ctags = subprocess.check_output(
        ["ctags", "-f-"] + all_git_files,
    ).decode("utf-8")
    for line in ctags.splitlines():
        tag, filename, *rest = line.split("\t")
        if "/migrations/" in filename:
            continue
        files.setdefault(filename, []).append(tag)
    files_map = StringIO()
    for filename, tags in files.items():
        files_map.write(f"{filename}: ")
        files_map.write(", ".join(tags))
        files_map.write("\n")
    files_map.seek(0)
    return files_map.read()


# Load config
def load_config():
    conf = configparser.ConfigParser()
    conf.optionxform = str
    conf.read(os.path.expanduser("~/.slopify.ini"))
    return conf


def clone(repo):
    print(f"Cloning {repo}")
    tmpdir = tempfile.TemporaryDirectory(delete=False)
    os.chdir(tmpdir.name)
    subprocess.run(
        [
            "git",
            "clone",
            "--depth=1",
            "git@github.com:" + repo,
            ".",
        ]
    )


def load_jira(conf):
    # Configure jira
    return jiralib.JIRA(
        server=conf.get("jira", "url"),
        basic_auth=(
            conf.get("jira", "user"),
            conf.get("jira", "api_token"),
        ),
    )


def load_and_clone_issue():
    try:
        ticket_id = sys.argv[1]
    except IndexError:
        print("error: first argument must be a jira ticket", file=sys.stderr)
        sys.exit(1)

    conf = load_config()
    jira = load_jira(conf)
    try:
        issue = jira.issue(ticket_id)
    except jiralib.exceptions.JIRAError as exc:
        msg = str(exc).splitlines()[0]
        print(f"Jira error: {msg}", file=sys.stderr)
        sys.exit(1)

    # Find repo from ticket labels
    matching_labels = set(
        issue.fields.labels,
    ).intersection(
        set(conf["jira_labels"].keys()),
    )
    try:
        repo = conf.get("jira_labels", matching_labels.pop())
    except KeyError:
        print(f"Could not find a repo for this ticket, labels: {issue.fields.labels}")
        sys.exit(1)

    clone(repo)

    return issue


def readFile(file: str) -> str:
    """Read file"""
    print(f"read_file({file})")
    with open(file) as f:
        return f.read()


def writeFile(file: str, content: str) -> None:
    """Write file"""
    print(f"write_file({file})")
    with open(file, "w") as f:
        f.write(content)

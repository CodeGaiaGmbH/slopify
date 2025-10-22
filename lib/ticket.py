import sys
import os
import configparser
import subprocess
import llm
import utils
import json

import jira


PROMPT_IMPLEMENT_TEMPLATE = """
# Persona
You are a senior software developer.

# Task
Write down your implementation.

## Ticket title
{title}

## Ticket description
```
{description}
```
"""

PROMPT_WRITE_FILES = """
Apply the changes with writeFile:

{changes}
"""

PROMPT_ASK_TEMPLATE = """
# Task
{ask}

# Project overview
```
{project_map}
```

## Ticket title
{title}

## Ticket description
{description}
"""


def edit(file_path, old_string, new_string):
    with open(file_path, "r") as f:
        content = f.read()
    content = content.replace(old_string, new_string)
    with open(file_path, "w") as f:
        f.write(content)


def load():
    if not len(sys.argv) > 2:
        print("error: first argument must be a jira ticket", file=sys.stderr)
        sys.exit(1)

    ticket_id = sys.argv[2]

    conf = configparser.ConfigParser()
    conf.optionxform = str
    conf.read(os.path.expanduser("~/.slopify.ini"))

    j = jira.JIRA(
        server=conf.get("jira", "url"),
        basic_auth=(
            conf.get("jira", "user"),
            conf.get("jira", "api_token"),
        ),
    )
    return j.issue(ticket_id)


def get_relevant_files_ask(issue, ask):
    model = llm.get_model("claude-sonnet-4.5")
    prompt = PROMPT_ASK_TEMPLATE.format(
        ask=ask,
        project_map=utils.get_project_map(),
        title=issue.fields.summary,
        description=issue.fields.description.strip(" \n"),
    )
    response = model.prompt(prompt, schema=llm.schema_dsl("file", multi=True))

    print()
    print(ask)
    try:
        response_json = json.loads(response.text())
        files = [i["file"] for i in response_json["items"]]
    except TypeError as exc:
        print(f"Error: {exc} - {response.text()}", file=sys.stderr)
        return []
    print(files)
    return files


def files_to_fragments(files):
    fragments = []
    for file in files:
        try:
            content = utils.readFile(file)
        except FileNotFoundError:
            fragments.append(f"# File not found: {file}")
        else:
            fragments.append(f"# {file}\n\n{content}")
    return fragments


def get_context_files(issue):
    files = set()
    files.update(
        get_relevant_files_ask(
            issue,
            "Which new files must be created for this ticket?",
        )
    )
    files.update(
        get_relevant_files_ask(
            issue,
            "Which files are relevant to the ticket?",
        )
    )
    files.update(
        get_relevant_files_ask(
            issue,
            "Which files one should not forget about when implementing the ticket?",
        )
    )
    files.update(
        get_relevant_files_ask(
            issue,
            "Which files should be studied to understand the ticket?",
        )
    )
    files.update(
        get_relevant_files_ask(
            issue,
            f"I forgot files to look into for the ticket. So far we have these: {', '.join(files)}",
        )
    )
    return files


def implement(issue):
    files = get_context_files(issue)
    fragments = files_to_fragments(sorted(files))
    print()
    print("Now implementing...")
    model = llm.get_model("claude-sonnet-4.5")
    response = model.prompt(
        PROMPT_IMPLEMENT_TEMPLATE.format(
            title=issue.fields.summary,
            description=issue.fields.description.strip(" \n"),
        ),
        fragments=fragments,
    )

    changes = ""
    for chunk in response:
        print(chunk, end="", flush=True)
        changes += chunk
    print()

    print()
    print("Writing files:")
    response = llm.get_model("claude-haiku-4.5").chain(
        PROMPT_WRITE_FILES.format(changes=changes),
        fragments=fragments,
        tools=[utils.writeFile, edit],
    )

    for chunk in response:
        print(chunk, end="", flush=True)

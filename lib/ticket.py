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
Implement the ticket.

## Ticket title
{title}

## Ticket description
```
{description}
```

## Notes
- Use the writeFile tool to write the files.
"""

# PROMPT_PLAN_TEMPLATE = """
# # Task
# Implement the ticket
#
# # Project overview
# ```
# {project_map}
# ```
#
# ## Ticket title
# {title}
#
# ## Ticket description
# {description}
# """


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


# Fake
def writeFile(file: str, content: str) -> None:
    """write file"""
    print(f"writeFile({file}, ...) (Fake)")


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


# def get_relevant_files(issue):
#     """
#     Pretend to implement the ticket with cheaper model to gather relevant files.
#     """
#     model = llm.get_model("claude-3.5-haiku")
#     prompt = PROMPT_PLAN_TEMPLATE.format(
#         project_map=utils.get_project_map(),
#         title=issue.fields.summary,
#         description=issue.fields.description.strip(" \n"),
#     )
#     conversation = model.conversation()
#     response = conversation.chain(
#         prompt,
#         tools=[utils.readFiles, writeFile],
#     )
#     print(response.text())
#     files = set()
#     for conversation in conversation.responses:
#         for tc in conversation.tool_calls():
#             if tc.name == "readFiles":
#                 files.update(tc.arguments["files"])
#             elif tc.name == "writeFile":
#                 files.add(tc.arguments["file"])
#     print(files)
#     return list(sorted(files))


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


def implement(issue):
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
    prompt = PROMPT_IMPLEMENT_TEMPLATE.format(
        title=issue.fields.summary,
        description=issue.fields.description.strip(" \n"),
    )

    print()
    print("Now implementing...")
    model = llm.get_model("claude-sonnet-4.5")
    response = model.chain(
        prompt,
        fragments=files_to_fragments(sorted(files)),
        tools=[utils.writeFile],
    )
    response.text()

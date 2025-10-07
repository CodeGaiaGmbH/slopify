import sys
import os
import configparser
import llm
import utils
import json

import jira

PROMPT_TEMPLATE = """
# Persona
You are a senior software developer.

# Task
List all files that are related to this changes.

## Ticket title
{title}

## Ticket description
```
{description}
```

# Project overview
```
{project_map}
```
"""


PROMPT2_TEMPLATE = """
# Persona
You are a senior software developer.

# Task
Implement the ticket

## Ticket title
{title}

## Ticket description
```
{description}
```

## Notes
- Use the writeFile tool to write the files.
"""


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


def implement(issue):
    model = llm.get_model("claude-3.5-haiku")
    prompt = PROMPT_TEMPLATE.format(
        project_map=utils.get_project_map(),
        title=issue.fields.summary,
        description=issue.fields.description.strip(" \n"),
    )

    response = model.prompt(
        prompt,
        schema=llm.schema_dsl("file", multi=True),
    )
    files = json.loads(response.text())
    fragments = []
    for item in files["items"]:
        # print(item["file"])
        try:
            content = utils.readFile(item["file"])
        except FileNotFoundError:
            fragments.append(f"# File not found: {item['file']}")
        else:
            fragments.append(f"# {item['file']}\n\n{content}")

    prompt = PROMPT2_TEMPLATE.format(
        title=issue.fields.summary,
        description=issue.fields.description.strip(" \n"),
    )

    model = llm.get_model("claude-sonnet-4.5")
    response = model.chain(
        prompt,
        # schema=llm.schema_dsl("file, content", multi=True),
        fragments=fragments,
        tools=[utils.writeFile],
    )
    response.text()

    # files_content = json.loads(response.text())
    # for item in files_content["items"]:
    #     breakpoint()
    #     utils.writeFile(item["file"], item["content"])

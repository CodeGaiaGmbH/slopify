import sys
import os
import configparser
import llm
import utils

import jira

PROMPT_TEMPLATE = """
# Persona
You are a senior software developer.

# Task
Implement the following ticket.

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

# Notes
- Understand project conventions by reading files.
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
    model = llm.get_model("claude-sonnet-4.5")
    prompt = PROMPT_TEMPLATE.format(
        project_map=utils.get_project_map(),
        title=issue.fields.summary,
        description=issue.fields.description.strip(" \n"),
    )

    response = model.chain(
        prompt,
        tools=[utils.readFiles, utils.writeFile],
    )

    # Don't print out the plan
    response.text()

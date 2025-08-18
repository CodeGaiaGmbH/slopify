import sys
import os
import configparser

import jira


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

# Slopify

Your AI non-agent.

A wrapper around [siesta scripts](https://github.com/ihucos/siesta) to automate workflows.

## Open Source
Be carefull to not push company data in here.

## Subcommands

| | |
| -------- | ------- |
| fix-ci-simple | Fix simple CI errors     |
| pick-comment  | Change local files to comply with request in GitHub comment     |
| pick-ticket   | Implement a ticket in Jira    |
| scan-tickets   | Implement Jira tickets with `slopify` label    |
| gui   | Open the GUI   |

## Install
### 1. Clone this repo
```
git clone git@github.com:Spenoki-Solutions-GmbH/slopify.git
```

### 2. Add to `$PATH`
```
export PATH="/path/to/slopify/bin:$PATH"
```
### 3. Install nix
The only thing you need to install is [nix](https://nix.dev/install-nix)

### 4. Login at GitHub
* Run: `nix-shell -p gh --run 'gh auth login'` 

### 4. Configure
```ini
# ~/.slopify.ini
[jira]
org=example
url=https://example.atlassian.net
user=user@example.com
api_token=...

[jira_labels]
label1=owner/repo1
label2=owner/repo2

[env]
GEMINI_API_KEY=...
```

## Example usage
```
slopify pick-ticket ABC-123
```

## Notes on writing AI-Ready Jira tickets
slopify's `pick-ticket` subcommand is designed to handle small, technical subtickets that where purposoly created for it. The anticipated workflow is the following:
1. Spec out a bigger ticket into small subtickets
2. Run the small subtickets on slopify. Tipically I still need one more iteration to adapt the ticket description once. But with some training this should not be necessary.

Here are some tips:
  - Micromanage as much as possible
  - Slopify pick-ticket "knows" the basics of the source code, but it does not know much about the product and language only applicable to a higher level product view.
  - Ideally the subtickets are one sentence (Just the title), for example "Expose model X to the API", "Make the field X on model Y filterable in the admin" and similiar
  - Look into the source and try to understand what the LLM "knows" and what it does not "know"
  - Treat unexpected completions as user errors and try to learn from them.

 That being said, it is really possible to for example just throw a huge ticket into it and maybe the results are usable, but in order to get predictable results follow the mentioned instructions.
 It might also work well to write a detailed specification on a big ticket. But I would not recommend that because it leads to huge PRs, which is generally not optimal.


## A case for more non-agentic workflows

### Security
* No literally random arbitrary shell command execution (A traditional no-go in software development)
* Code can be audited


### Simplicity
* No sandboxing needed
* It's just a few hundert lines of script.
  
### Environmental impact / Costs
* Forseable costs. A fixed number of API calls to the big models.
* Certain LLM completions can be handled locally.
* Hand-pick the most economical model for the job.

### Control
* Error cases can be handled sanely at all.
* Precisely curate the context to the LLMs -> Better performance.
* Plan beforehand the best way to accomplish a task.
* No Vendor lock-in - plug and play different models depending on your needs.

### UX
* Discoverability: users can see what your tool can do.
* No need for users to oversee and rubber-stamp AIs intermediate steps.


## Development Guidelines
* Apply the "Rule of three". Copy and paste three times before refactoring.
* Use the smallest model fit for the job.
* Use local models when practicable.
* Balance development speed, completion quality and model size.
* Use clear common sense prompts that solve one task at a time.
* Proper prompt formating does matter.
* This is a general but opiniated solution.

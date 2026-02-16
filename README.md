# ghmulti

`ghmulti` helps you manage multiple GitHub identities for local Git work.
It includes:

- A Python CLI for account management, linking, git remote workflows, and diagnostics.
- A VS Code extension that shows and switches the active account from the status bar.

## Installation

1. Clone:
```bash
git clone https://github.com/nyigoro/ghmulti.git
cd ghmulti
```

2. Install CLI (editable, with runtime deps):
```bash
pip install -e .
```

3. Optional: install test/dev tools:
```bash
pip install -r requirements-dev.txt
```

## Quick Start

```bash
ghmulti add
ghmulti list
ghmulti use work
ghmulti link work
ghmulti status
```

## CLI Commands

### Account Management

- `ghmulti add`: Add an account (username + token and/or SSH key).
- `ghmulti list`: List accounts.
- `ghmulti use [ACCOUNT]`: Set global active account.
- `ghmulti update ACCOUNT`: Update username, token, GPG key, SSH key, active status.
- `ghmulti rename OLD_NAME NEW_NAME`: Rename account alias.
- `ghmulti remove ACCOUNT`: Remove account.
- `ghmulti account ...`: Group shortcut with subcommands `add/list/use/update/remove/rename`.

### Repository Linking

- `ghmulti link [ACCOUNT]`: Link current repository to an account and set local git identity.
- `ghmulti unlink [--json] [--reset-local-git]`: Remove repository-level link to an account.
- `ghmulti clone REPO_URL [--account ACCOUNT] [--link/--no-link]`: Clone and optionally link immediately.

### Git Operations

- `ghmulti pull [--remote REMOTE] [--branch BRANCH]`
- `ghmulti push [--remote REMOTE] [--branch BRANCH] [--message MSG]`
- `ghmulti remote add --account ACCOUNT --url URL`
- `ghmulti remote remove --account ACCOUNT`
- `ghmulti list-remote [--all-branches]`
- `ghmulti check-remote`

### Diagnostics

- `ghmulti status`: Human-readable status.
- `ghmulti status --json`: Machine-readable status for automation/integrations.
- `ghmulti doctor`: Environment and dependency diagnostics.

## Machine-Readable Output

Use JSON output for scripts and extension integrations:

```bash
ghmulti list --json
ghmulti status --json --skip-token-check
ghmulti use work --json
```

## VS Code Extension

From `vscode-extension/`:

```bash
npm install
npm run compile
npm test
```

Then open `vscode-extension` in VS Code and press `F5` to launch an Extension Development Host.

Extension commands:

- `ghmulti: Open Menu`
- `ghmulti: Add Account`
- `ghmulti: Switch Account`
- `ghmulti: Link Account to Repository`
- `ghmulti: Unlink Repository Account`
- `ghmulti: Show Status`
- `ghmulti: Run Doctor`

Notes:

- The extension supports multi-root workspaces and prompts for the target repository when needed.
- Set `ghmulti.commandPath` in VS Code settings if CLI auto-detection is not correct for your environment.

## Testing

```bash
python -m pytest -q
```

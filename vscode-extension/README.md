# ghmulti for VS Code

Manage and switch GitHub identities from VS Code using the `ghmulti` CLI.

## Features

- Status bar indicator for the current effective account.
- Quick action menu for:
  - Add account
  - Switch account
  - Link repository to account
  - Unlink repository account
  - Show status
  - Run doctor diagnostics
- Multi-root workspace support with repository picker for link/unlink/status flows.
- Command palette commands:
  - `ghmulti: Open Menu`
  - `ghmulti: Add Account`
  - `ghmulti: Switch Account`
  - `ghmulti: Link Account to Repository`
  - `ghmulti: Unlink Repository Account`
  - `ghmulti: Show Status`
  - `ghmulti: Run Doctor`

## Requirements

- `ghmulti` CLI installed and available in your environment.
- A configured `ghmulti` account set (for switching/linking).

Install CLI from the project root:

```bash
pip install -e .
```

## Extension Settings

- `ghmulti.commandPath`
  - Optional absolute path to `ghmulti` executable.
  - Leave empty to use auto-detection (`ghmulti`, `python -m ghmulti`, `python3 -m ghmulti`, `py -m ghmulti`).

## Usage

1. Open a git repository in VS Code.
2. Click the ghmulti status bar item.
3. Pick an action from the menu.

For repository-specific identity, use **Link Repository** and **Unlink Repository**.

## Development Testing

From `vscode-extension/`:

```bash
npm install
npm run compile
npm test
```

## Troubleshooting

- Run `ghmulti: Run Doctor` and check the `ghmulti` output channel.
- Run `ghmulti: Show Status` to inspect effective/global/link states.
- If CLI detection fails, set `ghmulti.commandPath` explicitly.

## Publish To VS Code Marketplace

1. Create/verify your publisher in Visual Studio Marketplace.
2. Create a Personal Access Token with Marketplace publish permissions.
3. Login once:

```bash
npx @vscode/vsce login nyigoro
```

4. Package locally:

```bash
npm run package
```

5. Publish:

```bash
npm run publish:vsce
```

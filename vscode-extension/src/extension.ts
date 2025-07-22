import * as vscode from 'vscode';
import * as cp from 'child_process';
import * as fs from 'fs';
import * as path from 'path';

let statusBarItem: vscode.StatusBarItem;

export function activate(context: vscode.ExtensionContext) {
    statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
    context.subscriptions.push(statusBarItem);

    context.subscriptions.push(vscode.commands.registerCommand('ghmulti-vscode.switchAccount', async () => {
        const accounts = getAccounts();
        const selectedAccount = await vscode.window.showQuickPick(accounts, { placeHolder: 'Select a GitHub account to use' });
        if (selectedAccount) {
            switchAccount(selectedAccount);
        }
    }));

    context.subscriptions.push(vscode.commands.registerCommand('ghmulti-vscode.linkAccount', async () => {
        const accounts = getAccounts();
        const selectedAccount = await vscode.window.showQuickPick(accounts, { placeHolder: 'Select an account to link to this repository' });
        if (selectedAccount) {
            linkAccount(selectedAccount);
        }
    }));

    // Initial update
    updateStatusBar();

    // Update when the active window changes
    vscode.window.onDidChangeActiveTextEditor(() => updateStatusBar());

    // Update when a terminal is closed (could be a git command)
    vscode.window.onDidCloseTerminal(() => updateStatusBar());

    // Check for linking opportunity on startup
    checkAndPromptForLink();
}

function updateStatusBar(): void {
    const accountInfo = getActiveAccountInfo();
    if (accountInfo) {
        const icon = accountInfo.isLinked ? '$(plug)' : '$(github-inverted)';
        statusBarItem.text = `${icon} ${accountInfo.name}`;
        statusBarItem.tooltip = `ghmulti: ${accountInfo.name} (${accountInfo.isLinked ? 'Linked' : 'Global'})`;
        statusBarItem.command = 'ghmulti-vscode.switchAccount';
        statusBarItem.show();
    } else {
        statusBarItem.hide();
    }
}

function getActiveAccountInfo(): { name: string; isLinked: boolean } | undefined {
    const workspaceFolder = vscode.workspace.workspaceFolders?.[0].uri.fsPath;
    if (!workspaceFolder) { return; }

    try {
        const result = cp.execSync('ghmulti status', { cwd: workspaceFolder }).toString().trim();
        const linkedMatch = result.match(/Repository linked to: '([\w-]+)'/);
        const activeMatch = result.match(/Active account: '([\w-]+)'/);

        if (linkedMatch) {
            return { name: linkedMatch[1], isLinked: true };
        } else if (activeMatch) {
            return { name: activeMatch[1], isLinked: false };
        }
        return undefined;
    } catch (error) {
        // Silently fail if ghmulti is not installed or repo is not a git repo
        return undefined;
    }
}

function getAccounts(): string[] {
    try {
        const result = cp.execSync('ghmulti list').toString().trim();
        // Assumes format is `  marker name (username)`
        return result.split('\n').slice(1).map(line => line.trim().split(' ')[1]);
    } catch (error) {
        vscode.window.showErrorMessage('Could not fetch ghmulti accounts. Is ghmulti installed and in your PATH?');
        return [];
    }
}

function switchAccount(accountName: string): void {
    try {
        // The `use` command should be run globally, so no cwd
        cp.execSync(`ghmulti use ${accountName}`);
        updateStatusBar();
    } catch (error) {
        vscode.window.showErrorMessage(`Error switching ghmulti account: ${error}`);
    }
}

function linkAccount(accountName: string): void {
    const workspaceFolder = vscode.workspace.workspaceFolders?.[0].uri.fsPath;
    if (!workspaceFolder) { return; }

    try {
        cp.execSync(`ghmulti link ${accountName}`, { cwd: workspaceFolder });
        updateStatusBar();
        vscode.window.showInformationMessage(`Successfully linked '${accountName}' to this repository.`);
    } catch (error) {
        vscode.window.showErrorMessage(`Error linking ghmulti account: ${error}`);
    }
}

async function checkAndPromptForLink() {
    const workspaceFolder = vscode.workspace.workspaceFolders?.[0].uri.fsPath;
    if (!workspaceFolder) { return; }

    // Only prompt if it's a git repo and not already linked
    const isGitRepo = fs.existsSync(path.join(workspaceFolder, '.git'));
    const isLinked = fs.existsSync(path.join(workspaceFolder, '.ghmulti'));

    if (isGitRepo && !isLinked) {
        const choice = await vscode.window.showInformationMessage(
            'This repository isn\'t linked to a ghmulti account. Would you like to link one?',
            'Link Account', 'Ignore'
        );

        if (choice === 'Link Account') {
            vscode.commands.executeCommand('ghmulti-vscode.linkAccount');
        }
    }
}

export function deactivate() {}
"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = require("vscode");
const cp = require("child_process");
let statusBarItem;
function activate(context) {
    statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
    context.subscriptions.push(statusBarItem);
    context.subscriptions.push(vscode.commands.registerCommand('ghmulti-vscode.switchAccount', async () => {
        const accounts = getAccounts();
        const selectedAccount = await vscode.window.showQuickPick(accounts, { placeHolder: 'Select a GitHub account to use' });
        if (selectedAccount) {
            switchAccount(selectedAccount);
        }
    }));
    updateStatusBar();
    vscode.workspace.onDidChangeConfiguration(() => updateStatusBar());
}
function updateStatusBar() {
    const activeAccount = getActiveAccount();
    if (activeAccount) {
        statusBarItem.text = `$(github-inverted) ${activeAccount}`;
        statusBarItem.tooltip = `ghmulti: ${activeAccount}`;
        statusBarItem.command = 'ghmulti-vscode.switchAccount';
        statusBarItem.show();
    }
    else {
        statusBarItem.hide();
    }
}
function getActiveAccount() {
    try {
        const result = cp.execSync('ghmulti list').toString().trim();
        const activeLine = result.split('\n').find(line => line.startsWith('👉'));
        return activeLine ? activeLine.split(' ')[1] : undefined;
    }
    catch (error) {
        console.error('Error getting active ghmulti account:', error);
        return undefined;
    }
}
function getAccounts() {
    try {
        const result = cp.execSync('ghmulti list').toString().trim();
        return result.split('\n').slice(1).map(line => line.trim().split(' ')[1]);
    }
    catch (error) {
        console.error('Error getting ghmulti accounts:', error);
        return [];
    }
}
function switchAccount(accountName) {
    try {
        cp.execSync(`ghmulti use ${accountName}`);
        updateStatusBar();
    }
    catch (error) {
        console.error(`Error switching ghmulti account to ${accountName}:`, error);
    }
}
function deactivate() { }
//# sourceMappingURL=extension.js.map
"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const cp = require("child_process");
const fs = require("fs");
const path = require("path");
const vscode = require("vscode");
let statusBarItem;
let outputChannel;
let cachedGhMultiCommand;
let isTestMode = false;
function activate(context) {
    isTestMode = context.extensionMode === vscode.ExtensionMode.Test;
    statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
    outputChannel = vscode.window.createOutputChannel('ghmulti');
    context.subscriptions.push(statusBarItem, outputChannel);
    context.subscriptions.push(vscode.commands.registerCommand('ghmulti-vscode.manage', showManageMenu));
    context.subscriptions.push(vscode.commands.registerCommand('ghmulti-vscode.addAccount', addAccountFlow));
    context.subscriptions.push(vscode.commands.registerCommand('ghmulti-vscode.switchAccount', switchAccountFlow));
    context.subscriptions.push(vscode.commands.registerCommand('ghmulti-vscode.linkAccount', linkAccountFlow));
    context.subscriptions.push(vscode.commands.registerCommand('ghmulti-vscode.unlinkAccount', unlinkAccountFlow));
    context.subscriptions.push(vscode.commands.registerCommand('ghmulti-vscode.migrateLegacyLink', migrateLegacyLinkFlow));
    context.subscriptions.push(vscode.commands.registerCommand('ghmulti-vscode.showStatus', showStatus));
    context.subscriptions.push(vscode.commands.registerCommand('ghmulti-vscode.runDoctor', runDoctor));
    context.subscriptions.push(vscode.workspace.onDidChangeConfiguration(event => {
        if (event.affectsConfiguration('ghmulti.commandPath')) {
            cachedGhMultiCommand = undefined;
        }
    }));
    updateStatusBar();
    context.subscriptions.push(vscode.window.onDidChangeActiveTextEditor(() => updateStatusBar()));
    context.subscriptions.push(vscode.window.onDidCloseTerminal(() => updateStatusBar()));
    context.subscriptions.push(vscode.workspace.onDidChangeWorkspaceFolders(() => updateStatusBar()));
    checkAndPromptForLink();
}
function deactivate() { }
function updateStatusBar() {
    const preferredFolder = getPreferredWorkspaceFolder();
    const accountInfo = getActiveAccountInfo(preferredFolder?.uri.fsPath);
    if (!accountInfo) {
        statusBarItem.text = '$(account) ghmulti';
        statusBarItem.tooltip = 'ghmulti: no active account. Click to add, switch, or link an account.';
        statusBarItem.command = 'ghmulti-vscode.manage';
        statusBarItem.show();
        return;
    }
    const icon = accountInfo.isLinked ? '$(key)' : '$(account)';
    statusBarItem.text = `${icon} ${accountInfo.name}`;
    statusBarItem.tooltip = accountInfo.isLegacyLinked
        ? `ghmulti: ${accountInfo.name} (Linked via legacy git config)`
        : `ghmulti: ${accountInfo.name} (${accountInfo.isLinked ? 'Linked' : 'Global'})`;
    statusBarItem.command = 'ghmulti-vscode.manage';
    statusBarItem.show();
}
function getActiveAccountInfo(workspaceFolderPath) {
    const options = workspaceFolderPath ? { cwd: workspaceFolderPath } : {};
    try {
        const jsonResult = tryParseJson(runGhMulti(['status', '--json', '--skip-token-check'], options));
        if (jsonResult?.linked_account) {
            return { name: jsonResult.linked_account, isLinked: true };
        }
        if (jsonResult?.linked_account_from_git_config) {
            return {
                name: jsonResult.linked_account_from_git_config,
                isLinked: true,
                isLegacyLinked: true
            };
        }
        const activeName = jsonResult?.effective_active_account?.name ?? jsonResult?.global_active_account?.name;
        if (activeName) {
            return { name: activeName, isLinked: false };
        }
        if (workspaceFolderPath) {
            const linkedAccount = getLinkedAccountFromProjectConfig(workspaceFolderPath);
            if (linkedAccount) {
                return { name: linkedAccount, isLinked: true };
            }
        }
    }
    catch {
        // Fall through to text parsing for backwards compatibility.
    }
    try {
        const result = runGhMulti(['status'], options);
        const linkedMatch = result.match(/Repository linked to:\s*'([^']+)'/);
        const effectiveMatch = result.match(/Effective active account(?: for this repository)?:\s*'([^']+)'/);
        const globalMatch = result.match(/Global active account:\s*'([^']+)'/);
        if (linkedMatch?.[1]) {
            return { name: linkedMatch[1], isLinked: true };
        }
        const activeName = effectiveMatch?.[1] ?? globalMatch?.[1];
        if (activeName) {
            return { name: activeName, isLinked: false };
        }
    }
    catch {
        return undefined;
    }
    return undefined;
}
function getLinkedAccountFromProjectConfig(workspaceFolderPath) {
    const projectConfigPath = path.join(workspaceFolderPath, '.ghmulti');
    if (!fs.existsSync(projectConfigPath)) {
        return undefined;
    }
    try {
        const raw = fs.readFileSync(projectConfigPath, 'utf8');
        const parsed = JSON.parse(raw);
        if (typeof parsed.account === 'string' && parsed.account.trim()) {
            return parsed.account.trim();
        }
    }
    catch {
        return undefined;
    }
    return undefined;
}
function getAccounts() {
    try {
        const jsonResult = tryParseJson(runGhMulti(['list', '--json']));
        if (jsonResult?.accounts?.length) {
            return jsonResult.accounts
                .map(account => account.name?.trim())
                .filter((name) => Boolean(name));
        }
        const fallback = runGhMulti(['list']).trim();
        return fallback
            .split(/\r?\n/)
            .map(line => line.trim())
            .map(line => line.match(/^(?:👉\s+)?(.+?)\s+\([^)]+\)\s*$/))
            .filter((match) => match !== null)
            .map(match => match[1]);
    }
    catch (error) {
        vscode.window.showErrorMessage(`Could not fetch ghmulti accounts. ${formatExecError(error)}`);
        return [];
    }
}
async function showManageMenu() {
    const actions = [
        { label: '$(plus) Add Account', command: 'ghmulti-vscode.addAccount' },
        { label: '$(account) Switch Account', command: 'ghmulti-vscode.switchAccount' },
        { label: '$(plug) Link Repository', command: 'ghmulti-vscode.linkAccount' },
        { label: '$(debug-disconnect) Unlink Repository', command: 'ghmulti-vscode.unlinkAccount' },
        { label: '$(sync) Migrate Legacy Link', command: 'ghmulti-vscode.migrateLegacyLink' },
        { label: '$(info) Show Status', command: 'ghmulti-vscode.showStatus' },
        { label: '$(pulse) Run Doctor', command: 'ghmulti-vscode.runDoctor' }
    ];
    const selected = await vscode.window.showQuickPick(actions, { placeHolder: 'Choose a ghmulti action' });
    if (selected) {
        await vscode.commands.executeCommand(selected.command);
    }
}
async function addAccountFlow() {
    const name = await promptRequired('Account alias (e.g., work, personal)');
    if (!name) {
        return;
    }
    const username = await promptRequired('GitHub username');
    if (!username) {
        return;
    }
    const authMethod = await vscode.window.showQuickPick([
        { label: 'Token', detail: 'Use GitHub Personal Access Token' },
        { label: 'SSH Key Path', detail: 'Use SSH key path for this account' }
    ], { placeHolder: 'Choose authentication method' });
    if (!authMethod) {
        return;
    }
    let token;
    let sshKeyPath;
    if (authMethod.label === 'Token') {
        const tokenInput = await vscode.window.showInputBox({
            prompt: 'GitHub Personal Access Token',
            password: true,
            ignoreFocusOut: true
        });
        if (tokenInput === undefined || tokenInput.trim() === '') {
            vscode.window.showWarningMessage('Token is required for token-based account setup.');
            return;
        }
        token = tokenInput.trim();
    }
    else {
        const sshPathInput = await promptRequired('SSH key path (e.g., ~/.ssh/id_ed25519_work)');
        if (!sshPathInput) {
            return;
        }
        sshKeyPath = sshPathInput;
    }
    const gpgKeyId = await vscode.window.showInputBox({
        prompt: 'GPG signing key ID (optional)',
        ignoreFocusOut: true
    });
    if (gpgKeyId === undefined) {
        return;
    }
    const setActiveChoice = await vscode.window.showQuickPick([
        { label: 'Yes', detail: 'Set this account as active now' },
        { label: 'No', detail: 'Keep the current active account' }
    ], { placeHolder: 'Set this account as the active account?' });
    if (!setActiveChoice) {
        return;
    }
    try {
        const args = ['add', '--name', name, '--username', username];
        if (token) {
            args.push('--token', token);
        }
        if (sshKeyPath) {
            args.push('--ssh-key-path', sshKeyPath);
        }
        const trimmedGpg = gpgKeyId.trim();
        if (trimmedGpg) {
            args.push('--gpg-key-id', trimmedGpg);
        }
        if (setActiveChoice.label === 'Yes') {
            args.push('--set-active');
        }
        runGhMulti(args);
        updateStatusBar();
        vscode.window.showInformationMessage(`Added account '${name}'.`);
    }
    catch (error) {
        vscode.window.showErrorMessage(`Error adding ghmulti account: ${formatExecError(error)}`);
    }
}
async function switchAccountFlow() {
    const accounts = getAccounts();
    if (accounts.length === 0) {
        vscode.window.showWarningMessage('No ghmulti accounts found. Add one first.');
        return;
    }
    const selectedAccount = await vscode.window.showQuickPick(accounts, {
        placeHolder: 'Select a GitHub account to use'
    });
    if (!selectedAccount) {
        return;
    }
    try {
        runGhMulti(['use', selectedAccount, '--json']);
        updateStatusBar();
        vscode.window.showInformationMessage(`Switched active account to '${selectedAccount}'.`);
    }
    catch (error) {
        vscode.window.showErrorMessage(`Error switching ghmulti account: ${formatExecError(error)}`);
    }
}
async function linkAccountFlow() {
    const workspaceFolder = await selectWorkspaceFolder('Select repository to link');
    if (!workspaceFolder) {
        return;
    }
    await linkAccountInFolder(workspaceFolder);
}
async function linkAccountInFolder(workspaceFolder, preferredAccountName) {
    const workspacePath = workspaceFolder.uri.fsPath;
    if (!isGitWorkspace(workspacePath)) {
        vscode.window.showWarningMessage(`'${workspaceFolder.name}' is not a git repository.`);
        return;
    }
    const accounts = getAccounts();
    if (accounts.length === 0) {
        vscode.window.showWarningMessage('No ghmulti accounts found. Add one first.');
        return;
    }
    let selectedAccount = preferredAccountName;
    if (!selectedAccount) {
        selectedAccount = await vscode.window.showQuickPick(accounts, {
            placeHolder: `Select an account to link to '${workspaceFolder.name}'`
        });
    }
    if (!selectedAccount) {
        return;
    }
    try {
        runGhMulti(['link', selectedAccount], { cwd: workspacePath });
        updateStatusBar();
        vscode.window.showInformationMessage(`Successfully linked '${selectedAccount}' to '${workspaceFolder.name}'.`);
    }
    catch (error) {
        vscode.window.showErrorMessage(`Error linking ghmulti account: ${formatExecError(error)}`);
    }
}
async function unlinkAccountFlow() {
    const workspaceFolder = await selectWorkspaceFolder('Select repository to unlink');
    if (!workspaceFolder) {
        return;
    }
    const workspacePath = workspaceFolder.uri.fsPath;
    if (!isGitWorkspace(workspacePath)) {
        vscode.window.showWarningMessage(`'${workspaceFolder.name}' is not a git repository.`);
        return;
    }
    try {
        const raw = runGhMulti(['unlink', '--json'], { cwd: workspacePath });
        const parsed = tryParseJson(raw);
        updateStatusBar();
        if (parsed?.previously_linked_account) {
            vscode.window.showInformationMessage(`Unlinked '${workspaceFolder.name}' from '${parsed.previously_linked_account}'.`);
        }
        else {
            vscode.window.showInformationMessage(`'${workspaceFolder.name}' is no longer linked.`);
        }
    }
    catch (error) {
        vscode.window.showErrorMessage(`Error unlinking repository: ${formatExecError(error)}`);
    }
}
async function migrateLegacyLinkFlow() {
    const workspaceFolder = await selectWorkspaceFolder('Select repository to migrate legacy link');
    if (!workspaceFolder) {
        return;
    }
    await migrateLegacyLinkInFolder(workspaceFolder, true);
}
async function showStatus() {
    const workspaceFolder = await selectWorkspaceFolder('Select repository to show status', true);
    const options = workspaceFolder ? { cwd: workspaceFolder.uri.fsPath } : {};
    try {
        const result = runGhMultiWithResult(['status', '--json', '--skip-token-check'], options);
        const raw = result.stdout || result.stderr;
        const parsed = tryParseJson(raw);
        outputChannel.appendLine('=== ghmulti status ===');
        if (workspaceFolder) {
            outputChannel.appendLine(`Workspace: ${workspaceFolder.name} (${workspaceFolder.uri.fsPath})`);
        }
        else {
            outputChannel.appendLine('Workspace: global');
        }
        if (parsed) {
            outputChannel.appendLine(`Linked: ${parsed.linked_account ?? 'none'}`);
            outputChannel.appendLine(`Global: ${parsed.global_active_account?.name ?? 'none'}`);
            outputChannel.appendLine(`Effective: ${parsed.effective_active_account?.name ?? 'none'}`);
            if (parsed.token?.message) {
                outputChannel.appendLine(`Token: ${parsed.token.message}`);
            }
            if (parsed.warnings?.length) {
                outputChannel.appendLine('Warnings:');
                for (const warning of parsed.warnings) {
                    outputChannel.appendLine(`- ${warning}`);
                }
            }
            outputChannel.appendLine('');
            outputChannel.show(true);
            const effectiveName = parsed.effective_active_account?.name ?? parsed.global_active_account?.name ?? 'none';
            vscode.window.showInformationMessage(`ghmulti status: active '${effectiveName}'.`);
            return;
        }
        outputChannel.appendLine(raw || 'No status output was returned.');
        outputChannel.appendLine('');
        outputChannel.show(true);
        vscode.window.showWarningMessage('ghmulti status could not be parsed as JSON. See ghmulti output channel.');
    }
    catch (error) {
        vscode.window.showErrorMessage(`Error showing ghmulti status: ${formatExecError(error)}`);
    }
}
async function runDoctor() {
    try {
        const result = runGhMultiWithResult(['doctor', '--json']);
        const raw = result.stdout || result.stderr;
        const parsed = tryParseJson(raw);
        outputChannel.appendLine('=== ghmulti doctor ===');
        if (parsed?.checks?.length) {
            for (const check of parsed.checks) {
                const marker = check.status === 'ok' ? 'OK' : 'ERROR';
                outputChannel.appendLine(`[${marker}] ${check.name ?? 'unknown'}: ${check.detail ?? ''}`);
            }
            outputChannel.appendLine('');
            outputChannel.show(true);
            if (parsed.ok) {
                vscode.window.showInformationMessage('ghmulti doctor completed successfully.');
            }
            else {
                vscode.window.showWarningMessage('ghmulti doctor found issues. See ghmulti output channel.');
            }
            return;
        }
        outputChannel.appendLine(raw || 'No doctor output was returned.');
        outputChannel.appendLine('');
        outputChannel.show(true);
        if (result.exitCode === 0) {
            vscode.window.showInformationMessage('ghmulti doctor completed.');
        }
        else {
            vscode.window.showWarningMessage('ghmulti doctor failed. See ghmulti output channel.');
        }
    }
    catch (error) {
        vscode.window.showErrorMessage(`Error running ghmulti doctor: ${formatExecError(error)}`);
    }
}
async function checkAndPromptForLink() {
    if (isTestMode) {
        return;
    }
    const workspaceFolder = getPreferredWorkspaceFolder();
    if (!workspaceFolder) {
        return;
    }
    const workspacePath = workspaceFolder.uri.fsPath;
    if (!isGitWorkspace(workspacePath)) {
        return;
    }
    const isLinked = fs.existsSync(path.join(workspacePath, '.ghmulti'));
    if (isLinked) {
        return;
    }
    const legacyLinkedAccount = getLegacyLinkedAccountFromGitConfig(workspacePath);
    if (legacyLinkedAccount) {
        await migrateLegacyLinkInFolder(workspaceFolder, false);
        return;
    }
    const choice = await vscode.window.showInformationMessage(`Repository '${workspaceFolder.name}' is not linked to a ghmulti account. Link now?`, 'Link Account', 'Ignore');
    if (choice === 'Link Account') {
        await linkAccountInFolder(workspaceFolder);
    }
}
function getPreferredWorkspaceFolder() {
    const activeEditor = vscode.window.activeTextEditor;
    if (activeEditor) {
        const fromActiveEditor = vscode.workspace.getWorkspaceFolder(activeEditor.document.uri);
        if (fromActiveEditor) {
            return fromActiveEditor;
        }
    }
    return vscode.workspace.workspaceFolders?.[0];
}
async function selectWorkspaceFolder(placeHolder, allowNoWorkspace = false) {
    const folders = vscode.workspace.workspaceFolders;
    if (!folders || folders.length === 0) {
        if (!allowNoWorkspace) {
            vscode.window.showWarningMessage('Open a workspace folder first.');
        }
        return undefined;
    }
    if (folders.length === 1) {
        return folders[0];
    }
    const preferred = getPreferredWorkspaceFolder();
    const orderedFolders = [...folders].sort((a, b) => {
        if (preferred && a.uri.fsPath === preferred.uri.fsPath) {
            return -1;
        }
        if (preferred && b.uri.fsPath === preferred.uri.fsPath) {
            return 1;
        }
        return a.name.localeCompare(b.name);
    });
    const items = orderedFolders.map(folder => ({
        label: folder.name,
        description: folder.uri.fsPath,
        detail: preferred && folder.uri.fsPath === preferred.uri.fsPath ? 'Active editor folder' : '',
        folder
    }));
    const picked = await vscode.window.showQuickPick(items, { placeHolder });
    return picked?.folder;
}
function isGitWorkspace(workspaceFolderPath) {
    return fs.existsSync(path.join(workspaceFolderPath, '.git'));
}
async function migrateLegacyLinkInFolder(workspaceFolder, explicitCommand) {
    const workspacePath = workspaceFolder.uri.fsPath;
    if (!isGitWorkspace(workspacePath)) {
        if (explicitCommand) {
            vscode.window.showWarningMessage(`'${workspaceFolder.name}' is not a git repository.`);
        }
        return;
    }
    const legacyLinkedAccount = getLegacyLinkedAccountFromGitConfig(workspacePath);
    if (!legacyLinkedAccount) {
        if (explicitCommand) {
            vscode.window.showInformationMessage(`No legacy link found in '${workspaceFolder.name}'.`);
        }
        return;
    }
    let shouldMigrate = explicitCommand;
    if (!explicitCommand) {
        const migrateChoice = await vscode.window.showInformationMessage(`Repository '${workspaceFolder.name}' has a legacy link '${legacyLinkedAccount}' in local git config. Migrate it to .ghmulti now?`, 'Migrate Link', 'Ignore');
        shouldMigrate = migrateChoice === 'Migrate Link';
    }
    if (!shouldMigrate) {
        return;
    }
    try {
        runGhMulti(['link', legacyLinkedAccount], { cwd: workspacePath });
        updateStatusBar();
        vscode.window.showInformationMessage(`Migrated legacy link '${legacyLinkedAccount}' to .ghmulti for '${workspaceFolder.name}'.`);
    }
    catch (error) {
        vscode.window.showErrorMessage(`Could not migrate legacy link '${legacyLinkedAccount}'. Ensure the account exists, then link again. ${formatExecError(error)}`);
    }
}
function getLegacyLinkedAccountFromGitConfig(workspaceFolderPath) {
    try {
        const output = cp.execFileSync('git', ['config', '--local', '--get', 'ghmulti.linkedaccount'], { cwd: workspaceFolderPath, encoding: 'utf8', stdio: 'pipe' });
        const trimmed = output.trim();
        return trimmed || undefined;
    }
    catch {
        return undefined;
    }
}
async function promptRequired(prompt) {
    const value = await vscode.window.showInputBox({
        prompt,
        ignoreFocusOut: true
    });
    if (value === undefined) {
        return undefined;
    }
    const trimmed = value.trim();
    if (!trimmed) {
        vscode.window.showWarningMessage(`${prompt} is required.`);
        return undefined;
    }
    return trimmed;
}
function runGhMulti(args, options = {}) {
    const command = getGhMultiCommand();
    if (!command) {
        throw new Error("ghmulti CLI was not found. Install it (`pip install --editable .`) or ensure `ghmulti`/`python` is on PATH, then restart VS Code.");
    }
    return cp.execFileSync(command.executable, [...command.baseArgs, ...args], {
        ...options,
        encoding: 'utf8'
    });
}
function runGhMultiWithResult(args, options = {}) {
    const command = getGhMultiCommand();
    if (!command) {
        throw new Error("ghmulti CLI was not found. Install it (`pip install --editable .`) or ensure `ghmulti`/`python` is on PATH, then restart VS Code.");
    }
    try {
        const stdout = cp.execFileSync(command.executable, [...command.baseArgs, ...args], {
            ...options,
            encoding: 'utf8'
        });
        return { stdout, stderr: '', exitCode: 0 };
    }
    catch (error) {
        const execError = error;
        return {
            stdout: execError.stdout ? execError.stdout.toString() : '',
            stderr: execError.stderr ? execError.stderr.toString() : '',
            exitCode: typeof execError.status === 'number' ? execError.status : 1
        };
    }
}
function getGhMultiCommand() {
    if (cachedGhMultiCommand !== undefined) {
        return cachedGhMultiCommand;
    }
    const configuredCommand = vscode.workspace.getConfiguration('ghmulti').get('commandPath')?.trim();
    if (configuredCommand) {
        const configuredCandidates = getConfiguredCommandCandidates(configuredCommand);
        for (const candidate of configuredCandidates) {
            if (isUsableGhMultiCommand(candidate)) {
                cachedGhMultiCommand = candidate;
                return cachedGhMultiCommand;
            }
        }
        vscode.window.showWarningMessage(`Configured ghmulti.commandPath is not usable: ${configuredCommand}. Use an executable path (for example C:\\Python\\python.exe) or a command with args (for example py -m ghmulti). Falling back to auto-detection.`);
    }
    const candidates = [
        { executable: 'python', baseArgs: ['-m', 'ghmulti'] },
        { executable: 'py', baseArgs: ['-m', 'ghmulti'] },
        { executable: 'python3', baseArgs: ['-m', 'ghmulti'] },
        { executable: 'ghmulti', baseArgs: [] }
    ];
    for (const candidate of candidates) {
        if (isUsableGhMultiCommand(candidate)) {
            cachedGhMultiCommand = candidate;
            return candidate;
        }
    }
    cachedGhMultiCommand = null;
    return null;
}
function isUsableGhMultiCommand(candidate) {
    try {
        cp.execFileSync(candidate.executable, [...candidate.baseArgs, '--help'], { stdio: 'pipe' });
    }
    catch {
        return false;
    }
    try {
        const stdout = cp.execFileSync(candidate.executable, [...candidate.baseArgs, 'list', '--json'], { stdio: 'pipe', encoding: 'utf8' });
        return tryParseJson(stdout) !== undefined;
    }
    catch {
        return false;
    }
}
function getConfiguredCommandCandidates(configuredCommand) {
    const candidates = [{ executable: configuredCommand, baseArgs: [] }];
    const parsed = splitCommandLine(configuredCommand);
    if (parsed.length > 0) {
        const parsedCandidate = {
            executable: parsed[0],
            baseArgs: parsed.slice(1)
        };
        if (!isSameCommand(parsedCandidate, candidates[0])) {
            candidates.push(parsedCandidate);
        }
    }
    return candidates;
}
function splitCommandLine(rawCommand) {
    const tokens = [];
    let current = '';
    let quote = null;
    for (const char of rawCommand.trim()) {
        if (quote) {
            if (char === quote) {
                quote = null;
                continue;
            }
            current += char;
            continue;
        }
        if (char === '"' || char === "'") {
            quote = char;
            continue;
        }
        if (/\s/.test(char)) {
            if (current) {
                tokens.push(current);
                current = '';
            }
            continue;
        }
        current += char;
    }
    if (current) {
        tokens.push(current);
    }
    return tokens;
}
function isSameCommand(a, b) {
    if (a.executable !== b.executable) {
        return false;
    }
    if (a.baseArgs.length !== b.baseArgs.length) {
        return false;
    }
    return a.baseArgs.every((arg, index) => arg === b.baseArgs[index]);
}
function formatExecError(error) {
    const execError = error;
    const stderr = execError.stderr ? execError.stderr.toString().trim() : '';
    const stdout = execError.stdout ? execError.stdout.toString().trim() : '';
    if (stderr) {
        return stderr;
    }
    if (stdout) {
        return stdout;
    }
    if (execError.message) {
        return execError.message;
    }
    return String(error);
}
function tryParseJson(raw) {
    try {
        return JSON.parse(raw);
    }
    catch {
        return undefined;
    }
}
//# sourceMappingURL=extension.js.map
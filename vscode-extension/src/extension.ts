import * as cp from 'child_process';
import * as fs from 'fs';
import * as path from 'path';
import * as vscode from 'vscode';

let statusBarItem: vscode.StatusBarItem;
let outputChannel: vscode.OutputChannel;
let cachedGhMultiCommand: GhmultiCommand | null | undefined;

type GhmultiCommand = { executable: string; baseArgs: string[] };
type GhmultiListResponse = { accounts?: Array<{ name?: string | null }> };
type GhmultiStatusResponse = {
    linked_account?: string | null;
    global_active_account?: { name?: string | null; username?: string | null } | null;
    effective_active_account?: { name?: string | null; username?: string | null } | null;
    warnings?: string[];
    token?: { present?: boolean; valid?: boolean | null; message?: string | null } | null;
};
type GhmultiDoctorResponse = {
    ok?: boolean;
    checks?: Array<{ name?: string; status?: string; detail?: string }>;
};
type GhmultiUnlinkResponse = {
    previously_linked_account?: string | null;
    unlinked?: boolean;
    reset_local_git?: boolean;
};
type GhmultiRunResult = {
    stdout: string;
    stderr: string;
    exitCode: number;
};
type FolderQuickPickItem = vscode.QuickPickItem & {
    folder: vscode.WorkspaceFolder;
};

export function activate(context: vscode.ExtensionContext) {
    statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
    outputChannel = vscode.window.createOutputChannel('ghmulti');
    context.subscriptions.push(statusBarItem, outputChannel);

    context.subscriptions.push(vscode.commands.registerCommand('ghmulti-vscode.manage', showManageMenu));
    context.subscriptions.push(vscode.commands.registerCommand('ghmulti-vscode.addAccount', addAccountFlow));
    context.subscriptions.push(vscode.commands.registerCommand('ghmulti-vscode.switchAccount', switchAccountFlow));
    context.subscriptions.push(vscode.commands.registerCommand('ghmulti-vscode.linkAccount', linkAccountFlow));
    context.subscriptions.push(vscode.commands.registerCommand('ghmulti-vscode.unlinkAccount', unlinkAccountFlow));
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

export function deactivate() {}

function updateStatusBar(): void {
    const preferredFolder = getPreferredWorkspaceFolder();
    const accountInfo = getActiveAccountInfo(preferredFolder?.uri.fsPath);
    if (!accountInfo) {
        statusBarItem.hide();
        return;
    }

    const icon = accountInfo.isLinked ? '$(plug)' : '$(github-inverted)';
    statusBarItem.text = `${icon} ${accountInfo.name}`;
    statusBarItem.tooltip = `ghmulti: ${accountInfo.name} (${accountInfo.isLinked ? 'Linked' : 'Global'})`;
    statusBarItem.command = 'ghmulti-vscode.manage';
    statusBarItem.show();
}

function getActiveAccountInfo(workspaceFolderPath?: string): { name: string; isLinked: boolean } | undefined {
    const options = workspaceFolderPath ? { cwd: workspaceFolderPath } : {};
    try {
        const jsonResult = tryParseJson<GhmultiStatusResponse>(
            runGhMulti(['status', '--json', '--skip-token-check'], options)
        );
        if (jsonResult?.linked_account) {
            return { name: jsonResult.linked_account, isLinked: true };
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
    } catch {
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
    } catch {
        return undefined;
    }

    return undefined;
}

function getLinkedAccountFromProjectConfig(workspaceFolderPath: string): string | undefined {
    const projectConfigPath = path.join(workspaceFolderPath, '.ghmulti');
    if (!fs.existsSync(projectConfigPath)) {
        return undefined;
    }
    try {
        const raw = fs.readFileSync(projectConfigPath, 'utf8');
        const parsed = JSON.parse(raw) as { account?: unknown };
        if (typeof parsed.account === 'string' && parsed.account.trim()) {
            return parsed.account.trim();
        }
    } catch {
        return undefined;
    }
    return undefined;
}

function getAccounts(): string[] {
    try {
        const jsonResult = tryParseJson<GhmultiListResponse>(runGhMulti(['list', '--json']));
        if (jsonResult?.accounts?.length) {
            return jsonResult.accounts
                .map(account => account.name?.trim())
                .filter((name): name is string => Boolean(name));
        }
        const fallback = runGhMulti(['list']).trim();
        return fallback
            .split(/\r?\n/)
            .map(line => line.trim())
            .map(line => line.match(/^(?:👉\s+)?(.+?)\s+\([^)]+\)\s*$/))
            .filter((match): match is RegExpMatchArray => match !== null)
            .map(match => match[1]);
    } catch (error) {
        vscode.window.showErrorMessage(`Could not fetch ghmulti accounts. ${formatExecError(error)}`);
        return [];
    }
}

async function showManageMenu(): Promise<void> {
    const actions: Array<{ label: string; command: string }> = [
        { label: '$(plus) Add Account', command: 'ghmulti-vscode.addAccount' },
        { label: '$(account) Switch Account', command: 'ghmulti-vscode.switchAccount' },
        { label: '$(plug) Link Repository', command: 'ghmulti-vscode.linkAccount' },
        { label: '$(debug-disconnect) Unlink Repository', command: 'ghmulti-vscode.unlinkAccount' },
        { label: '$(info) Show Status', command: 'ghmulti-vscode.showStatus' },
        { label: '$(pulse) Run Doctor', command: 'ghmulti-vscode.runDoctor' }
    ];
    const selected = await vscode.window.showQuickPick(actions, { placeHolder: 'Choose a ghmulti action' });
    if (selected) {
        await vscode.commands.executeCommand(selected.command);
    }
}

async function addAccountFlow(): Promise<void> {
    const name = await promptRequired('Account alias (e.g., work, personal)');
    if (!name) {
        return;
    }
    const username = await promptRequired('GitHub username');
    if (!username) {
        return;
    }

    const authMethod = await vscode.window.showQuickPick(
        [
            { label: 'Token', detail: 'Use GitHub Personal Access Token' },
            { label: 'SSH Key Path', detail: 'Use SSH key path for this account' }
        ],
        { placeHolder: 'Choose authentication method' }
    );
    if (!authMethod) {
        return;
    }

    let token: string | undefined;
    let sshKeyPath: string | undefined;
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
    } else {
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

    const setActiveChoice = await vscode.window.showQuickPick(
        [
            { label: 'Yes', detail: 'Set this account as active now' },
            { label: 'No', detail: 'Keep the current active account' }
        ],
        { placeHolder: 'Set this account as the active account?' }
    );
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
    } catch (error) {
        vscode.window.showErrorMessage(`Error adding ghmulti account: ${formatExecError(error)}`);
    }
}

async function switchAccountFlow(): Promise<void> {
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
    } catch (error) {
        vscode.window.showErrorMessage(`Error switching ghmulti account: ${formatExecError(error)}`);
    }
}

async function linkAccountFlow(): Promise<void> {
    const workspaceFolder = await selectWorkspaceFolder('Select repository to link');
    if (!workspaceFolder) {
        return;
    }
    await linkAccountInFolder(workspaceFolder);
}

async function linkAccountInFolder(workspaceFolder: vscode.WorkspaceFolder, preferredAccountName?: string): Promise<void> {
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
        vscode.window.showInformationMessage(
            `Successfully linked '${selectedAccount}' to '${workspaceFolder.name}'.`
        );
    } catch (error) {
        vscode.window.showErrorMessage(`Error linking ghmulti account: ${formatExecError(error)}`);
    }
}

async function unlinkAccountFlow(): Promise<void> {
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
        const parsed = tryParseJson<GhmultiUnlinkResponse>(raw);
        updateStatusBar();

        if (parsed?.previously_linked_account) {
            vscode.window.showInformationMessage(
                `Unlinked '${workspaceFolder.name}' from '${parsed.previously_linked_account}'.`
            );
        } else {
            vscode.window.showInformationMessage(`'${workspaceFolder.name}' is no longer linked.`);
        }
    } catch (error) {
        vscode.window.showErrorMessage(`Error unlinking repository: ${formatExecError(error)}`);
    }
}

async function showStatus(): Promise<void> {
    const workspaceFolder = await selectWorkspaceFolder('Select repository to show status', true);
    const options = workspaceFolder ? { cwd: workspaceFolder.uri.fsPath } : {};
    try {
        const result = runGhMultiWithResult(['status', '--json', '--skip-token-check'], options);
        const raw = result.stdout || result.stderr;
        const parsed = tryParseJson<GhmultiStatusResponse>(raw);

        outputChannel.appendLine('=== ghmulti status ===');
        if (workspaceFolder) {
            outputChannel.appendLine(`Workspace: ${workspaceFolder.name} (${workspaceFolder.uri.fsPath})`);
        } else {
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
    } catch (error) {
        vscode.window.showErrorMessage(`Error showing ghmulti status: ${formatExecError(error)}`);
    }
}

async function runDoctor(): Promise<void> {
    try {
        const result = runGhMultiWithResult(['doctor', '--json']);
        const raw = result.stdout || result.stderr;
        const parsed = tryParseJson<GhmultiDoctorResponse>(raw);

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
            } else {
                vscode.window.showWarningMessage('ghmulti doctor found issues. See ghmulti output channel.');
            }
            return;
        }

        outputChannel.appendLine(raw || 'No doctor output was returned.');
        outputChannel.appendLine('');
        outputChannel.show(true);
        if (result.exitCode === 0) {
            vscode.window.showInformationMessage('ghmulti doctor completed.');
        } else {
            vscode.window.showWarningMessage('ghmulti doctor failed. See ghmulti output channel.');
        }
    } catch (error) {
        vscode.window.showErrorMessage(`Error running ghmulti doctor: ${formatExecError(error)}`);
    }
}

async function checkAndPromptForLink(): Promise<void> {
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

    const choice = await vscode.window.showInformationMessage(
        `Repository '${workspaceFolder.name}' is not linked to a ghmulti account. Link now?`,
        'Link Account',
        'Ignore'
    );
    if (choice === 'Link Account') {
        await linkAccountInFolder(workspaceFolder);
    }
}

function getPreferredWorkspaceFolder(): vscode.WorkspaceFolder | undefined {
    const activeEditor = vscode.window.activeTextEditor;
    if (activeEditor) {
        const fromActiveEditor = vscode.workspace.getWorkspaceFolder(activeEditor.document.uri);
        if (fromActiveEditor) {
            return fromActiveEditor;
        }
    }
    return vscode.workspace.workspaceFolders?.[0];
}

async function selectWorkspaceFolder(placeHolder: string, allowNoWorkspace = false): Promise<vscode.WorkspaceFolder | undefined> {
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

    const items: FolderQuickPickItem[] = orderedFolders.map(folder => ({
        label: folder.name,
        description: folder.uri.fsPath,
        detail: preferred && folder.uri.fsPath === preferred.uri.fsPath ? 'Active editor folder' : '',
        folder
    }));
    const picked = await vscode.window.showQuickPick(items, { placeHolder });
    return picked?.folder;
}

function isGitWorkspace(workspaceFolderPath: string): boolean {
    return fs.existsSync(path.join(workspaceFolderPath, '.git'));
}

async function promptRequired(prompt: string): Promise<string | undefined> {
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

function runGhMulti(args: string[], options: cp.ExecFileSyncOptions = {}): string {
    const command = getGhMultiCommand();
    if (!command) {
        throw new Error(
            "ghmulti CLI was not found. Install it (`pip install --editable .`) or ensure `ghmulti`/`python` is on PATH, then restart VS Code."
        );
    }

    return cp.execFileSync(
        command.executable,
        [...command.baseArgs, ...args],
        {
            ...options,
            encoding: 'utf8'
        }
    ) as string;
}

function runGhMultiWithResult(args: string[], options: cp.ExecFileSyncOptions = {}): GhmultiRunResult {
    const command = getGhMultiCommand();
    if (!command) {
        throw new Error(
            "ghmulti CLI was not found. Install it (`pip install --editable .`) or ensure `ghmulti`/`python` is on PATH, then restart VS Code."
        );
    }

    try {
        const stdout = cp.execFileSync(
            command.executable,
            [...command.baseArgs, ...args],
            {
                ...options,
                encoding: 'utf8'
            }
        ) as string;
        return { stdout, stderr: '', exitCode: 0 };
    } catch (error) {
        const execError = error as NodeJS.ErrnoException & {
            stdout?: Buffer | string;
            stderr?: Buffer | string;
            status?: number;
        };
        return {
            stdout: execError.stdout ? execError.stdout.toString() : '',
            stderr: execError.stderr ? execError.stderr.toString() : '',
            exitCode: typeof execError.status === 'number' ? execError.status : 1
        };
    }
}

function getGhMultiCommand(): GhmultiCommand | null {
    if (cachedGhMultiCommand !== undefined) {
        return cachedGhMultiCommand;
    }

    const configuredCommand = vscode.workspace.getConfiguration('ghmulti').get<string>('commandPath')?.trim();
    if (configuredCommand) {
        try {
            cp.execFileSync(configuredCommand, ['--help'], { stdio: 'pipe' });
            cachedGhMultiCommand = { executable: configuredCommand, baseArgs: [] };
            return cachedGhMultiCommand;
        } catch (error) {
            vscode.window.showWarningMessage(
                `Configured ghmulti.commandPath failed: ${configuredCommand}. ${formatExecError(error)} Falling back to auto-detection.`
            );
        }
    }

    const candidates: GhmultiCommand[] = [
        { executable: 'ghmulti', baseArgs: [] },
        { executable: 'python', baseArgs: ['-m', 'ghmulti'] },
        { executable: 'python3', baseArgs: ['-m', 'ghmulti'] },
        { executable: 'py', baseArgs: ['-m', 'ghmulti'] }
    ];

    for (const candidate of candidates) {
        try {
            cp.execFileSync(candidate.executable, [...candidate.baseArgs, '--help'], { stdio: 'pipe' });
            cachedGhMultiCommand = candidate;
            return candidate;
        } catch {
            continue;
        }
    }

    cachedGhMultiCommand = null;
    return null;
}

function formatExecError(error: unknown): string {
    const execError = error as NodeJS.ErrnoException & { stderr?: Buffer | string; stdout?: Buffer | string };
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

function tryParseJson<T>(raw: string): T | undefined {
    try {
        return JSON.parse(raw) as T;
    } catch {
        return undefined;
    }
}

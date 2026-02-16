import * as assert from 'assert';
import * as vscode from 'vscode';

suite('ghmulti Extension Smoke Tests', () => {
    test('registers expected commands', async () => {
        const extension = vscode.extensions.getExtension('nyigoro.ghmulti-vscode');
        assert.ok(extension, 'Extension nyigoro.ghmulti-vscode not found');
        if (extension && !extension.isActive) {
            await extension.activate();
        }

        const commands = await vscode.commands.getCommands(true);
        const expectedCommands = [
            'ghmulti-vscode.manage',
            'ghmulti-vscode.addAccount',
            'ghmulti-vscode.switchAccount',
            'ghmulti-vscode.linkAccount',
            'ghmulti-vscode.unlinkAccount',
            'ghmulti-vscode.showStatus',
            'ghmulti-vscode.runDoctor'
        ];

        for (const command of expectedCommands) {
            assert.ok(commands.includes(command), `Command not registered: ${command}`);
        }
    });

    test('executes non-interactive commands without throwing', async () => {
        await assert.doesNotReject(async () => {
            await vscode.commands.executeCommand('ghmulti-vscode.showStatus');
        });
        await assert.doesNotReject(async () => {
            await vscode.commands.executeCommand('ghmulti-vscode.runDoctor');
        });
    });
});

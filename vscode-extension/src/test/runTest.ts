import * as path from 'path';

import { runTests } from '@vscode/test-electron';

async function main() {
    try {
        const extensionDevelopmentPath = path.resolve(__dirname, '../../');
        const extensionTestsPath = path.resolve(__dirname, './suite/index');
        await runTests({
            extensionDevelopmentPath,
            extensionTestsPath,
            extensionTestsEnv: {
                ELECTRON_RUN_AS_NODE: undefined,
                ELECTRON_NO_ATTACH_CONSOLE: undefined
            }
        });
    } catch (error) {
        console.error('Failed to run extension tests');
        if (error) {
            console.error(error);
        }
        process.exit(1);
    }
}

void main();

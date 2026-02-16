import * as fs from 'fs';
import * as path from 'path';

import * as Mocha from 'mocha';

function collectTestFiles(root: string): string[] {
    const entries = fs.readdirSync(root, { withFileTypes: true });
    const files: string[] = [];
    for (const entry of entries) {
        const fullPath = path.join(root, entry.name);
        if (entry.isDirectory()) {
            files.push(...collectTestFiles(fullPath));
            continue;
        }
        if (entry.isFile() && entry.name.endsWith('.test.js')) {
            files.push(fullPath);
        }
    }
    return files;
}

export function run(): Promise<void> {
    const mocha = new Mocha({
        ui: 'tdd',
        color: true
    });

    const testsRoot = path.resolve(__dirname, '..');
    const files = collectTestFiles(testsRoot);
    for (const file of files) {
        mocha.addFile(file);
    }

    return new Promise((resolve, reject) => {
        mocha.run(failures => {
            if (failures > 0) {
                reject(new Error(`${failures} tests failed.`));
            } else {
                resolve();
            }
        });
    });
}

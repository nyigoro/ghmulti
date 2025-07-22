# ghmulti

A CLI tool and VS Code extension to manage multiple GitHub accounts.

## Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/nyigoro/ghmulti.git
    ```
2.  Install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Install the CLI:
    ```bash
    pip install --editable .
    ```

## Usage

### CLI

*   `ghmulti add`: Add a new GitHub account.
*   `ghmulti list`: List all configured GitHub accounts.
*   `ghmulti use`: Switch the active GitHub account.
*   `ghmulti pull`: Pull from a remote repository using the active account.
*   `ghmulti push`: Push to a remote repository using the active account.

### VS Code Extension

The VS Code extension provides a status bar item that shows the currently active GitHub account. You can click on the status bar item to switch between accounts.

## Development

1.  Install the development dependencies:
    ```bash
    npm install -g yo generator-code
    ```
2.  Install the extension dependencies:
    ```bash
    cd vscode-extension
    npm install
    ```
3.  Compile the extension:
    ```bash
    npm run compile
    ```
4.  Open the `vscode-extension` directory in VS Code and press `F5` to start a new Extension Development Host window.

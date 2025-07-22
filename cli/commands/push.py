import subprocess
import sys
import click

def run(cmd):
    print(f"🚀 {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        sys.exit(result.returncode)

@click.command()
@click.option('--account', required=True, help='GitHub account to push with')
@click.option('--branch', default='main', help='Branch name (default: main)')
@click.option('--message', help='Commit message if committing before pushing')
def cli(account, branch, message):
    """Push to GitHub using the specified account's remote."""
    remote_name = f"origin-{account}"

    if message:
        print("📦 Staging changes...")
        run("git add .")
        run(f'git commit -m "{message}"')

    print(f"🚀 Pushing to {remote_name}/{branch}")
    run(f"git push {remote_name} {branch}")

if __name__ == "__main__":
    cli()

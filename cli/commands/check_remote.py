import subprocess
import click

@click.command("check-remote")
def check_remote():
    """Check connection status for all Git remotes."""
    print("🔍 Checking connectivity to remotes...\n")

    result = subprocess.run("git remote -v", shell=True, capture_output=True, text=True)
    remotes = {}

    for line in result.stdout.strip().splitlines():
        name, url, *_ = line.split()
        remotes[name] = url

    for name, url in remotes.items():
        if url.startswith("http"):
            status = "✅ HTTPS OK"
        elif url.startswith("git@"):
            try:
                subprocess.run(
                    ["ssh", "-T", url.split(":")[0]],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                status = "✅ SSH OK"
            except subprocess.CalledProcessError:
                status = "❌ SSH Failed"
        else:
            status = "❓ Unknown Protocol"

        print(f"• {name} → {url} [{status}]")

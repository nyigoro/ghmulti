# cli/__main__.py
import sys

from cli.commands import add, use, push

def main():
    if len(sys.argv) < 2:
        print("Usage: python -m cli <add|use|push>")
        return

    cmd = sys.argv[1]
    if cmd == "add":
        add.run()
    elif cmd == "use":
        use.run()
    elif cmd == "push":
        push.run()
    else:
        print(f"Unknown command: {cmd}")

if __name__ == "__main__":
    main()

import sys
from tfse.orchestrator import run


def main():
    if len(sys.argv) < 3 or sys.argv[1] != "run":
        print("Usage: python -m tfse run <path/to/client.json>")
        sys.exit(1)
    run(sys.argv[2])


if __name__ == "__main__":
    main()

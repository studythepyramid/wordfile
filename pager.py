import shutil
import subprocess
import sys


def resolve_pager_cmd() -> list[str]:
    """Prefer batcat (Ubuntu/debian bat); fall back to less."""
    if shutil.which("batcat"):
        return ["batcat", "-p", "-l", "markdown", "--paging=always"]
    if shutil.which("bat"):
        return ["bat", "-p", "-l", "markdown", "--paging=always"]
    return ["less", "-R"]


def pager(content: str) -> None:
    """Send formatted text to a terminal pager."""
    if not content.strip():
        return

    pager_cmd = resolve_pager_cmd()
    pager_name = pager_cmd[0]
    print(f"\nOpening {pager_name}...", file=sys.stderr)

    try:
        proc = subprocess.Popen(pager_cmd, stdin=subprocess.PIPE, text=True)
        assert proc.stdin is not None
        proc.stdin.write(content)
        proc.stdin.close()
        proc.wait()
    except BrokenPipeError:
        # User quit the pager before reading everything.
        pass
    except FileNotFoundError:
        print(content)

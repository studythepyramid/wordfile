#!/usr/bin/env -S .venv/bin/python

import difflib
import sys
import textwrap

import ollama

from settings import LINE_WIDTH, MODEL_NAME, VOCABULARY_LOG_FILE

Proofread_Instruction = """You are an expert English proofreader.
Below is a vocabulary learning log file.
Check it for typos and spelling errors.

Rules:
- Focus on misspelled words, not grammar or style.
- If a word looks like a typo, suggest the correct spelling.
- Group corrections by log entry (the ### timestamps).
- If everything looks correct, say so.

Log file content:
{log_content}"""

Diff_Instruction = """You are an expert English proofreader.
Return the corrected version of the vocabulary log below.
Fix all typos and spelling errors inline.
Do NOT add commentary — output ONLY the corrected log content.

Log file content:
{log_content}"""


def read_logfile() -> str:
    if not VOCABULARY_LOG_FILE.exists():
        return ""
    try:
        with open(VOCABULARY_LOG_FILE, "r", encoding="utf-8") as f:
            return f.read()
    except IOError as e:
        print(
            f"⚠️ Warning: Could not read vocabulary log {VOCABULARY_LOG_FILE}: {e}",
            file=sys.stderr,
        )
        return ""


def _get_corrected(log_content: str) -> str:
    """Ask the model for a corrected version of the log (no commentary)."""
    prompt = Diff_Instruction.format(log_content=log_content)
    print(f"Querying LLM {MODEL_NAME} for corrections...", file=sys.stderr)
    try:
        return ollama.chat(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.0, "top_k": 10},
        )["message"]["content"]
    except Exception as e:
        print(f"\n❌ Ollama Communication Failure: {e}", file=sys.stderr)
        sys.exit(1)


def diff() -> None:
    """Show a unified diff between the original log and the model's corrected version."""
    log_content = read_logfile()
    if not log_content.strip():
        print("📭 Vocabulary log is empty — nothing to diff.")
        return

    corrected = _get_corrected(log_content)

    original_lines = log_content.splitlines(keepends=True)
    corrected_lines = corrected.splitlines(keepends=True)

    diff_lines = list(
        difflib.unified_diff(
            original_lines,
            corrected_lines,
            fromfile="original",
            tofile="corrected",
        )
    )

    if not diff_lines:
        print("✅ No corrections — the log looks clean.")
        return

    wrapper = textwrap.TextWrapper(width=LINE_WIDTH)

    print("# Diff: original → corrected")
    print()
    for line in diff_lines:
        line = line.rstrip("\n")
        if line.startswith("---") or line.startswith("+++"):
            continue
        if line.startswith("@@"):
            print(f"\n{'─' * LINE_WIDTH}")
            print(f"  {line}")
            print(f"{'─' * LINE_WIDTH}")
        elif line.startswith("-"):
            formatted = wrapper.fill(line) if line.strip() else ""
            print(f"\033[31m{formatted}\033[0m" if formatted else "")
        elif line.startswith("+"):
            formatted = wrapper.fill(line) if line.strip() else ""
            print(f"\033[32m{formatted}\033[0m" if formatted else "")
        else:
            formatted = wrapper.fill(line) if line.strip() else ""
            print(formatted)

    print()
    print("-" * LINE_WIDTH)


def write_inplace() -> None:
    """Overwrite VOCABULARY_LOG_FILE with the model's corrected version."""
    log_content = read_logfile()
    if not log_content.strip():
        print("📭 Vocabulary log is empty — nothing to write.")
        return

    corrected = _get_corrected(log_content)

    if corrected.strip() == log_content.strip():
        print("✅ No corrections — file unchanged.")
        return

    try:
        with open(VOCABULARY_LOG_FILE, "w", encoding="utf-8") as f:
            f.write(corrected)
        print(f"✏️  Corrections written to {VOCABULARY_LOG_FILE}")
    except IOError as e:
        print(
            f"⚠️ Warning: Could not write to {VOCABULARY_LOG_FILE}: {e}",
            file=sys.stderr,
        )


def proofread() -> None:
    """Stream proofreading commentary from the model."""
    log_content = read_logfile()
    if not log_content.strip():
        print("📭 Vocabulary log is empty — nothing to check.")
        sys.exit(0)

    prompt = Proofread_Instruction.format(log_content=log_content)

    print(f"Querying LLM {MODEL_NAME}...", file=sys.stderr)

    try:
        stream = ollama.chat(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            options={"temperature": 0.4, "top_k": 20},
        )

        wrapper = textwrap.TextWrapper(width=LINE_WIDTH)
        buffer = ""

        print("# Proofreading: VOCABULARY_LOG_FILE")
        print()

        for chunk in stream:
            buffer += chunk["message"]["content"]
            while True:
                idx = buffer.find("\n")
                if idx == -1:
                    break
                line = buffer[:idx]
                formatted = wrapper.fill(line) if line.strip() else ""
                if formatted == "":
                    print("")
                else:
                    print(formatted)
                buffer = buffer[idx + 1 :]

        if buffer:
            formatted = wrapper.fill(buffer) if buffer.strip() else ""
            print(formatted)

        print()
        print("-" * LINE_WIDTH)

    except Exception as e:
        print(f"\n❌ Ollama Communication Failure: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--diff":
        diff()
    elif len(sys.argv) > 1 and sys.argv[1] == "--write":
        write_inplace()
    else:
        proofread()

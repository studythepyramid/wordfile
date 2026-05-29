"""Direct chat with the LLM — no vocabulary context or log injection."""

import sys
import textwrap

import ollama

from settings import LINE_WIDTH, MODEL_NAME


def _format_stream_line(line: str, wrapper: textwrap.TextWrapper) -> str:
    if line.strip() == "":
        return ""
    return wrapper.fill(line)


def run_chat(message: str) -> None:
    """Pass user text straight to the model and stream the reply."""
    print(f"Querying LLM {MODEL_NAME}...", file=sys.stderr)

    try:
        stream = ollama.chat(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": message}],
            stream=True,
            options={
                "temperature": 0.7,
                "top_k": 20,
            },
        )

        wrapper = textwrap.TextWrapper(width=LINE_WIDTH)
        buffer = ""

        print("# Chat")
        print()

        for chunk in stream:
            buffer += chunk["message"]["content"]
            while True:
                idx = buffer.find("\n")
                if idx == -1:
                    break
                line = buffer[:idx]
                formatted = _format_stream_line(line, wrapper)
                if formatted == "":
                    print("")
                else:
                    print(formatted)
                buffer = buffer[idx + 1 :]

        if buffer:
            formatted = _format_stream_line(buffer, wrapper)
            print(formatted)

        print("\n" + "-" * LINE_WIDTH)

    except Exception as e:
        print(f"\n❌ Ollama Communication Failure: {e}", file=sys.stderr)

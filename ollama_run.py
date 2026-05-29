"""Interactive Ollama session — like `ollama run model-name` in the terminal."""

import sys
import textwrap

import ollama

from settings import LINE_WIDTH, MODEL_NAME

_SESSION_EXIT = {"/bye", "/exit", "/quit", "/q"}


def _format_stream_line(line: str, wrapper: textwrap.TextWrapper) -> str:
    if line.strip() == "":
        return ""
    return wrapper.fill(line)


def _stream_reply(model: str, messages: list[dict]) -> str:
    """Stream assistant reply to stdout; return full text for history."""
    stream = ollama.chat(
        model=model,
        messages=messages,
        stream=True,
        options={"temperature": 0.7, "top_k": 20},
    )

    wrapper = textwrap.TextWrapper(width=LINE_WIDTH)
    buffer = ""
    parts: list[str] = []

    for chunk in stream:
        text = chunk["message"]["content"]
        parts.append(text)
        buffer += text
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

    print()
    return "".join(parts)


def run_ollama(model_name: str) -> None:
    """Drop into a multi-turn chat with an Ollama model until /bye or Ctrl+C."""
    model = model_name.strip()
    if not model:
        print("[!] No model name. Use: ollama gemma3:4b", file=sys.stderr)
        return

    messages: list[dict] = []
    print(f"Ollama session: {model}  (/bye to return to game)")
    print("-" * LINE_WIDTH)

    try:
        while True:
            try:
                user_input = input(">>> ").strip()
            except EOFError:
                print("\n[*] Leaving Ollama session.")
                break

            if not user_input:
                continue

            if user_input.lower() in _SESSION_EXIT:
                print("[*] Leaving Ollama session.")
                break

            messages.append({"role": "user", "content": user_input})

            try:
                reply = _stream_reply(model, messages)
            except Exception as e:
                print(f"\n❌ Ollama error: {e}", file=sys.stderr)
                messages.pop()
                continue

            messages.append({"role": "assistant", "content": reply})

    except KeyboardInterrupt:
        print("\n[*] Leaving Ollama session.")

    print("-" * LINE_WIDTH)


def run_ollama_default() -> None:
    """Start a session with MODEL_NAME from settings."""
    run_ollama(MODEL_NAME)

#!/usr/bin/env -S .venv/bin/python

# #!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#   "ollama",
# ]
# ///


import datetime
import sys
import textwrap

import ollama

from check_words import check_words, report_invalid_words
from settings import LINE_WIDTH, MODEL_NAME, VOCABULARY_LOG_FILE


def log_words_to_history(words: list[str]):
    """Appends the queried words and a timestamp to the vocabulary log."""

    VOCABULARY_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    words_str = ", ".join(words)

    log_entry = f"### {timestamp} - Interrogated \n {words_str}\n\n"

    try:
        with open(VOCABULARY_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except IOError as e:
        print(
            f"⚠️ Warning: Could not write to vocabulary log {VOCABULARY_LOG_FILE}: {e}",
            file=sys.stderr,
        )


def format_stream_line(line: str, wrapper: textwrap.TextWrapper) -> str:
    if line.strip() == "":
        return ""
    return wrapper.fill(line)


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


# Context Construction: The Tutor Persona and Challenge Logic
Vocabulary_Game_Instruction = """Firstly,
explain each word in this list inside the square bractets:
[{words_list_str}].

Keep the explaination concise, use synonyms and antonyms.
If there's no word in the bractets,
take the history logs: {word_logs},
challenge the user with 3 new words.

You are an expert English linguistics tutor,
for the input word list, do the followings:

How to:
- Provide an example sentence for each word.
- If an word in user input is a typo,
   identify the intended word side by side to make it clear.
- Provide the K-band level for each.

Here're some words that might be typos, {typos}
explain it and show user the correct spellings.

"""


def run_vocabulary_query(target_words: list[str]) -> None:
    """Check, log, and stream an LLM explanation for the given words."""
    invalid_words = check_words(*target_words)
    if invalid_words:
        report_invalid_words(invalid_words)

    words_list_str = ", ".join(target_words)
    typos = ", ".join(invalid_words) if invalid_words else "none"

    word_logs = read_logfile()
    user_prompt = Vocabulary_Game_Instruction.format(
        words_list_str=words_list_str,
        word_logs=word_logs,
        typos=typos,
    )

    print(f"📚 Logging new words {words_list_str}, to {VOCABULARY_LOG_FILE}...")
    log_words_to_history(target_words)

    print(f"Querying LLM {MODEL_NAME} for: {words_list_str}.", file=sys.stderr)

    try:
        stream = ollama.chat(
            model=MODEL_NAME,
            messages=[
                {"role": "user", "content": user_prompt},
            ],
            stream=True,
            options={
                "temperature": 0.4,
                "top_k": 20,
            },
        )

        wrapper = textwrap.TextWrapper(width=LINE_WIDTH)
        buffer = ""

        print(f"# Words: {words_list_str}")
        print()

        for chunk in stream:
            buffer += chunk["message"]["content"]
            while True:
                idx = buffer.find("\n")
                if idx == -1:
                    break
                line = buffer[:idx]
                formatted = format_stream_line(line, wrapper)
                if formatted == "":
                    print("")
                else:
                    print(formatted)
                buffer = buffer[idx + 1 :]

        if buffer:
            formatted = format_stream_line(buffer, wrapper)
            print(formatted)

        footer = "\n" + "-" * LINE_WIDTH
        print(footer)

    except Exception as e:
        print(f"\n❌ Ollama Communication Failure: {e}", file=sys.stderr)


def query():
    if len(sys.argv) < 2:
        print("Usage: wordfile.py <word1> [word2] [word3] ...")
        print("Example: wordfile.py slit slot slab slap snip")
        sys.exit(1)

    run_vocabulary_query(sys.argv[1:])

    from game_turns import start_turn_based_game

    start_turn_based_game(run_vocabulary_query)


if __name__ == "__main__":
    query()

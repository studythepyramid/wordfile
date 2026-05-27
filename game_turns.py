import re
import time
from collections.abc import Callable

# The Template
User_card_template = {
    "sequence": 0,
    "raw_input": "",
    "intent": "",
    "timestamp": 0,
}

KnowIntents = [
    "exit",
    "help",
    "chat",
    "word",
    "phrase",
    "idiom",
    "exec",
    "query",
    "find_cmd",
    "none",
    "slash-command",
]

before_input_prompt = """
 [h] -> Help   [w] -> type in new words
 [q] -> Quit   [y] -> User agree   [n] -> User not agree
 [/cmd] -> Slash command (e.g., /status, /help)
 [!cmd] -> Manual override (e.g., !ls -p)
 Or type words directly (e.g., slit slot slab)
"""


def make_user_card(raw: str, seq: int):
    uc = User_card_template.copy()
    uc["raw_input"] = raw
    uc["sequence"] = seq
    uc["timestamp"] = int(time.time())

    clean_raw = raw.strip().lower()

    if clean_raw.startswith("/"):
        if re.match(r"^/[a-z]+", clean_raw):
            uc["intent"] = "slash-command"
            return uc

    if clean_raw == "q":
        uc["intent"] = "exit"
    elif clean_raw == "h":
        uc["intent"] = "help"
    elif clean_raw == "w":
        uc["intent"] = "word"
    elif clean_raw == "y":
        uc["intent"] = "y"
    elif raw.startswith("!"):
        uc["intent"] = "exec"
    elif not clean_raw:
        uc["intent"] = "none"
    else:
        uc["intent"] = "word"

    return uc


def from_input_to_ucard(turn_count: int):
    print("\n" + "-" * 40)
    print(before_input_prompt)

    raw = input(">> ").strip()
    return make_user_card(raw, turn_count)


def start_turn_based_game(
    query_words: Callable[[list[str]], None],
) -> None:
    """Keep learning new words until the user types q."""
    turn_count = 0
    while True:
        turn_count += 1

        user_card = from_input_to_ucard(turn_count)
        intent = user_card["intent"]

        match intent:
            case "exit":
                print("[*] Game Over. Terminating.")
                break

            case "help":
                print(before_input_prompt)

            case "word":
                raw = user_card["raw_input"]
                if raw.strip().lower() == "w":
                    raw = input("Words> ").strip()
                words = raw.split()
                if not words:
                    print("[!] No words entered.")
                    continue
                query_words(words)

            case "y":
                print(
                    "[-] AI didn't suggest any code to run."
                    " Use 'text' to nudge it."
                )

            case "exec":
                cmd = user_card["raw_input"][1:]
                print(f"[!] Manual Override detected: Running '{cmd}'")

            case "none":
                print("[!] Empty input. Type words or q to quit.")

            case "slash-command":
                print(
                    "[#] System Command detected:"
                    f" {user_card['raw_input']}"
                )

            case "chat":
                print(
                    "[*] Feedback logged:"
                    f" {user_card['raw_input']}"
                )

            case _:
                print("\n Boss out, you need loop again. \n")


if __name__ == "__main__":
    from wordfile import run_vocabulary_query

    try:
        start_turn_based_game(run_vocabulary_query)
    except KeyboardInterrupt:
        print("\n[*] Interrupted by user. Closing.")

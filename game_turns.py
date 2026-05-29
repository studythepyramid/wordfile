import re
import time
from collections.abc import Callable

from chat import run_chat
from ollama_run import run_ollama

# The Template
User_card_template = {
    "sequence": 0,
    "raw_input": "",
    "intent": "",
    "timestamp": 0,
}

Known_Intents = {
    "exit": None,
    "help": None,
    "chat": run_chat,
    "ollama-run": run_ollama,
    "word": None,
    "phrase": None,
    "idiom": None,
    "exec": None,
    "query": None,
    "find_cmd": None,
    "none": None,
    "slash-command": None,
    "y": None,
    "n": None,
}

Input_Prompt = """
 [q] -> Quit   
 [w ...] -> type in new words
 [c ...] -> chat with AI
 [ollama model-name] -> drop to the same as 'ollama run model-name' the model
 [y] -> Yes, agree  [n] -> No, not agree
 [h] -> Help        
"""


def make_user_card(raw: str, turn_count: int) -> dict:
    """Classify input per Input_Prompt; default intent is 'word'."""
    uc = User_card_template.copy()
    uc["raw_input"] = raw
    uc["sequence"] = turn_count
    uc["timestamp"] = int(time.time())

    stripped = raw.strip()
    clean_raw = stripped.lower()

    if not clean_raw:
        uc["intent"] = "none"
        return uc

    if stripped.startswith("!"):
        uc["intent"] = "exec"
        return uc

    if clean_raw.startswith("/") and re.match(r"^/[a-z]+", clean_raw):
        uc["intent"] = "slash-command"
        return uc

    if clean_raw == "q":
        uc["intent"] = "exit"
    elif clean_raw == "h":
        uc["intent"] = "help"
    elif clean_raw == "y":
        uc["intent"] = "y"
    elif clean_raw == "n":
        uc["intent"] = "n"
    elif clean_raw == "w" or clean_raw.startswith("w "):
        uc["intent"] = "word"
    elif clean_raw.startswith("c "):
        uc["intent"] = "chat"
    elif clean_raw == "ollama" or clean_raw.startswith("ollama "):
        uc["intent"] = "ollama-run"
    else:
        uc["intent"] = "word"

    return uc


def word_input_from_card(raw: str) -> str:
    """Strip optional 'w' / 'w ...' prefix; prompt if only 'w'."""
    stripped = raw.strip()
    lower = stripped.lower()
    if lower == "w":
        return input("Words> ").strip()
    if lower.startswith("w "):
        return stripped[2:].strip()
    return stripped


def chat_content_from_card(raw: str) -> str:
    """Strip 'c ...' prefix to get chat body."""
    stripped = raw.strip()
    if stripped.lower().startswith("c "):
        return stripped[2:].strip()
    return stripped


def ollama_model_from_card(raw: str) -> str:
    """Strip 'ollama' / 'ollama model-name' prefix; prompt if only 'ollama'."""
    stripped = raw.strip()
    lower = stripped.lower()
    if lower == "ollama":
        return input("Model> ").strip()
    if lower.startswith("ollama "):
        return stripped[7:].strip()
    return stripped


def from_input_to_ucard(turn_count: int):
    print("\n" + "-" * 40)
    print(Input_Prompt)

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
                print(Input_Prompt)

            case "word":
                raw = word_input_from_card(user_card["raw_input"])
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
                ## todo
                cmd = user_card["raw_input"][1:]
                print(f"[!] Manual Override detected: Running '{cmd}'")

            case "none":
                print("[!] Empty input. Type words or q to quit.")

            case "slash-command":
                print(
                    "[#] System Command detected:"
                )

            case "n":
                print("[-] Noted: user does not agree.")

            case "chat":
                content = chat_content_from_card(user_card["raw_input"])
                if not content:
                    print("[!] Empty chat. Use: c your message")
                    continue
                Known_Intents["chat"](content)

            case "ollama-run":
                model = ollama_model_from_card(user_card["raw_input"])
                if not model:
                    print("[!] No model. Use: ollama gemma3:4b")
                    continue
                Known_Intents["ollama-run"](model)

            case _:
                print("\n Boss out, you need loop again. \n")


if __name__ == "__main__":
    from wordfile import run_vocabulary_query

    try:
        start_turn_based_game(run_vocabulary_query)
    except KeyboardInterrupt:
        print("\n[*] Interrupted by user. Closing.")

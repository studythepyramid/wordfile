from pathlib import Path

MODEL_NAME = "gemma3:4b"  # Adjust to your active local model
# MODEL_NAME = "gemma3:1b"  # Adjust to your active local model

LINE_WIDTH = 70
VOCABULARY_LOG_FILE = Path("~/tmp/learn.words.en.md").expanduser()
DICT_PATH = Path("/usr/share/dict/words")

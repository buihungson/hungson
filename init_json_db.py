import json
import os

DB_FILE = "anki_data.json"

# file tồn tại thì xóa
if os.path.exists(DB_FILE):
    os.remove(DB_FILE)

# bộ khung (Schema)
base_schema = {
    "decks": [],  # DECKS
    "notes": [],  # NOTES
    "cards": [],  # CARDS
    "revlog": []  # REVLOG (Lịch sử ôn tập)
}

# Lưu bộ khung xuống ổ cứng
with open(DB_FILE, "w", encoding="utf-8") as f:
# tự động xuống dòng và thụt lề cho dễ nhìn
    json.dump(base_schema, f, ensure_ascii=False, indent=4)


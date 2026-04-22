import json
import os
import time

DB_FILE = "anki_data.json"


# ==========================================
# HÀM TIỆN ÍCH TẠO ID TỰ TĂNG (1, 2, 3...)
# ==========================================
def get_next_id(danh_sach):
    """Tìm ID lớn nhất trong danh sách hiện tại và cộng thêm 1."""
    if not danh_sach:  # Nếu kho chưa có gì (danh sách rỗng)
        return 1
    # Tìm ID lớn nhất hiện có và cộng 1
    return max(item["id"] for item in danh_sach) + 1


class JsonDBManager:
    """Người quản lý Kho dữ liệu JSON"""

    @staticmethod
    def load_data():
        if not os.path.exists(DB_FILE):
            return {"decks": [], "notes": [], "cards": []}
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def save_data(data):
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)


class DeckDAO:
    """Anh Thủ kho chuyên quản lý danh sách 'decks' (Bộ thẻ)"""

    def get_all_decks(self):
        data = JsonDBManager.load_data()
        return data["decks"]

    def add_deck(self, name):
        """Thêm một bộ thẻ mới với ID tự tăng"""
        data = JsonDBManager.load_data()

        # Kiểm tra trùng tên
        if any(d["name"] == name for d in data["decks"]):
            print(f"Lỗi: Bộ thẻ mang tên '{name}' đã tồn tại!")
            return None

        # Lấy ID mới bằng cách quét danh sách decks
        new_id = get_next_id(data["decks"])

        data["decks"].append({"id": new_id, "name": name})
        JsonDBManager.save_data(data)
        return new_id

    def update_deck_name(self, deck_id, new_name):
        data = JsonDBManager.load_data()
        if any(d["name"] == new_name and d["id"] != deck_id for d in data["decks"]):
            print(f"Lỗi: Tên '{new_name}' đã bị trùng với bộ thẻ khác!")
            return False

        for d in data["decks"]:
            if d["id"] == deck_id:
                d["name"] = new_name
                JsonDBManager.save_data(data)
                return True
        return False

    def delete_deck(self, deck_id):
        data = JsonDBManager.load_data()
        data["decks"] = [d for d in data["decks"] if d["id"] != deck_id]
        data["notes"] = [n for n in data["notes"] if n["did"] != deck_id]
        data["cards"] = [c for c in data["cards"] if c["did"] != deck_id]
        JsonDBManager.save_data(data)
        return True


class NoteDAO:
    """Cô Thủ thư chuyên quản lý 'notes' và sinh 'cards'"""

    def get_deck_id_by_name(self, deck_name):
        data = JsonDBManager.load_data()
        for d in data["decks"]:
            if d["name"] == deck_name:
                return d["id"]
        return None

    def add_note_and_cards(self, deck_name, front, back, tags="", is_reversed=False):
        """Thêm Note và tự động đẻ ra 1 hoặc 2 Cards an toàn với ID tự tăng"""
        deck_id = self.get_deck_id_by_name(deck_name)
        if not deck_id:
            print("Lỗi: Không tìm thấy bộ thẻ!")
            return False

        data = JsonDBManager.load_data()

        # 1. TẠO NOTE MỚI (Lấy ID tự tăng từ danh sách notes)
        note_id = get_next_id(data["notes"])
        data["notes"].append({
            "id": note_id, "did": deck_id, "front": front, "back": back, "tags": tags
        })

        # 2. TẠO CARD SỐ 1 (Thẻ xuôi)
        # Quét danh sách cards để lấy ID mới, đảm bảo ID của Card độc lập hoàn toàn với Note
        card_id_1 = get_next_id(data["cards"])
        data["cards"].append({
            "id": card_id_1, "nid": note_id, "did": deck_id,
            "type": 0, "due": 0, "ivl": 0, "factor": 2500,
            "ord": 0  # Thẻ xuôi
        })

        # 3. TẠO CARD SỐ 2 (Nếu là chế độ Đảo mặt)
        if is_reversed:
            # Gọi hàm get_next_id lần nữa, nó sẽ tự quét và lấy số tiếp theo
            card_id_2 = get_next_id(data["cards"])
            data["cards"].append({
                "id": card_id_2, "nid": note_id, "did": deck_id,
                "type": 0, "due": 0, "ivl": 0, "factor": 2500,
                "ord": 1  # Thẻ ngược
            })

        JsonDBManager.save_data(data)
        return True

    def get_notes_by_deck(self, did):
        data = JsonDBManager.load_data()
        return [n for n in data["notes"] if n["did"] == did]

    def delete_note(self, note_id):
        data = JsonDBManager.load_data()
        data["notes"] = [n for n in data["notes"] if n["id"] != note_id]
        data["cards"] = [c for c in data["cards"] if c["nid"] != note_id]
        JsonDBManager.save_data(data)
        return True

    def get_all_notes_with_deck(self, deck_id=None):
        data = JsonDBManager.load_data()
        decks_dict = {d["id"]: d["name"] for d in data["decks"]}

        results = []
        for n in data["notes"]:
            if deck_id is None or n["did"] == deck_id:
                results.append({
                    "id": n["id"],
                    "front": n["front"],
                    "back": n["back"],
                    "deck_name": decks_dict.get(n["did"], "Unknown")
                })
        return results

    def update_note(self, note_id, front, back):
        data = JsonDBManager.load_data()
        for n in data["notes"]:
            if n["id"] == note_id:
                n["front"] = front
                n["back"] = back
                JsonDBManager.save_data(data)
                return True
        return False


class CardDAO:
    """Cậu Thủ kho chuyên quản lý Lịch trình học SM-2"""

    def count_cards_by_state(self, did):
        data = JsonDBManager.load_data()
        counts = {"new": 0, "learn": 0, "due": 0}

        # Bổ sung: Tính ngày hôm nay (số ngày từ mốc UNIX)
        today = int(time.time() / 86400)

        for c in data["cards"]:
            if c["did"] == did:
                if c["type"] == 0:
                    counts["new"] += 1
                elif c["type"] == 1:
                    counts["learn"] += 1
                elif c["type"] == 2 and c["due"] <= today:  # FIX LỖI Ở ĐÂY: Thêm điều kiện due <= today
                    counts["due"] += 1

        return counts

    def get_next_card_to_study(self, did, today):
        data = JsonDBManager.load_data()
        notes_dict = {n["id"]: n for n in data["notes"]}

        # ƯU TIÊN 1: Thẻ đang học dở hoặc đã đến hạn
        valid_cards_review = [
            c for c in data["cards"]
            if c["did"] == did and (c["type"] == 1 or (c["type"] == 2 and c["due"] <= today))
        ]
        if valid_cards_review:
            valid_cards_review.sort(key=lambda x: x["due"])
            best_card = valid_cards_review[0]
            note = notes_dict.get(best_card["nid"], {})
            return {**best_card, "front": note.get("front", ""), "back": note.get("back", "")}

        # ƯU TIÊN 2: Thẻ mới tinh
        valid_cards_new = [c for c in data["cards"] if c["did"] == did and c["type"] == 0]
        if valid_cards_new:
            # Sắp xếp theo ID (thêm trước học trước)
            valid_cards_new.sort(key=lambda x: x["id"])
            best_card = valid_cards_new[0]
            note = notes_dict.get(best_card["nid"], {})
            return {**best_card, "front": note.get("front", ""), "back": note.get("back", "")}

        return None

    def update_card_after_review(self, card_id, ease, current_ivl, current_factor, today):
        data = JsonDBManager.load_data()

        new_factor = current_factor
        new_ivl = current_ivl
        new_type = 2

        if ease == 1:
            new_type = 1
            new_ivl = 0
            new_factor = max(1300, current_factor - 200)
        elif ease == 2:
            new_ivl = max(1, int(current_ivl * 1.2))
            new_factor = max(1300, current_factor - 150)
        elif ease == 3:
            if current_ivl == 0:
                new_ivl = 1
            else:
                new_ivl = max(1, int(current_ivl * (current_factor / 1000.0)))
        elif ease == 4:
            if current_ivl == 0:
                new_ivl = 4
            else:
                new_ivl = max(1, int(current_ivl * (current_factor / 1000.0) * 1.3))
            new_factor = current_factor + 150

        new_due = today + new_ivl

        for c in data["cards"]:
            if c["id"] == card_id:
                c["type"] = new_type
                c["due"] = new_due
                c["ivl"] = new_ivl
                c["factor"] = new_factor
                JsonDBManager.save_data(data)
                return True

        return False



if __name__ == "__main__":
    deck_dao = DeckDAO()
    note_dao = NoteDAO()
    card_dao = CardDAO()
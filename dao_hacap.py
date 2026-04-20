import json
import os
import time

DB_FILE = "anki_data.json"


# Hàm tiện ích tạo ID duy nhất dựa trên thời gian thực
def get_id_thoi_gian_thuc():
    return int(time.time() * 1000)


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
        """Lấy toàn bộ danh sách bộ thẻ ra ngoài (Trả về Dictionary để UI dễ đọc)"""
        data = JsonDBManager.load_data()
        return data["decks"]

    def add_deck(self, name):
        """Thêm một bộ thẻ mới"""
        data = JsonDBManager.load_data()
        # Kiểm tra trùng tên
        if any(d["name"] == name for d in data["decks"]):
            print(f"Lỗi: Bộ thẻ mang tên '{name}' đã tồn tại!")
            return None

        new_id = get_id_thoi_gian_thuc()
        data["decks"].append({"id": new_id, "name": name})
        JsonDBManager.save_data(data)
        return new_id

    def update_deck_name(self, deck_id, new_name):
        """Đổi tên bộ thẻ"""
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
        """Xóa bộ thẻ VÀ tự động dọn dẹp các Note/Card nằm bên trong"""
        data = JsonDBManager.load_data()
        # Lọc bỏ deck cần xóa
        data["decks"] = [d for d in data["decks"] if d["id"] != deck_id]
        # Xóa luôn các note thuộc deck này
        data["notes"] = [n for n in data["notes"] if n["did"] != deck_id]
        # Xóa luôn các card thuộc deck này
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
        """Thêm Note và tự động đẻ ra 1 hoặc 2 Cards"""
        deck_id = self.get_deck_id_by_name(deck_name)
        if not deck_id:
            print("Lỗi: Không tìm thấy bộ thẻ!")
            return False

        data = JsonDBManager.load_data()
        note_id = get_id_thoi_gian_thuc()

        # 1. Lưu vào danh sách NOTES
        data["notes"].append({
            "id": note_id, "did": deck_id, "front": front, "back": back, "tags": tags
        })

        # 2. Tạo Card số 1 (Thẻ xuôi)
        card_id_1 = note_id
        data["cards"].append({
            "id": card_id_1, "nid": note_id, "did": deck_id,
            "type": 0, "due": 0, "ivl": 0, "factor": 2500
        })

        # 3. Nếu là chế độ Đảo mặt, đẻ thêm Card số 2
        if is_reversed:
            card_id_2 = card_id_1 + 1
            data["cards"].append({
                "id": card_id_2, "nid": note_id, "did": deck_id,
                "type": 0, "due": 0, "ivl": 0, "factor": 2500
            })

        JsonDBManager.save_data(data)
        return True

    def get_notes_by_deck(self, did):
        data = JsonDBManager.load_data()
        return [n for n in data["notes"] if n["did"] == did]

    def delete_note(self, note_id):
        """Xóa ghi chú (Tự động xóa luôn Card liên quan)"""
        data = JsonDBManager.load_data()
        data["notes"] = [n for n in data["notes"] if n["id"] != note_id]
        data["cards"] = [c for c in data["cards"] if c["nid"] != note_id]
        JsonDBManager.save_data(data)
        return True

    def get_all_notes_with_deck(self, deck_id=None):
        data = JsonDBManager.load_data()
        # Tạo một từ điển nhanh để tra tên bộ thẻ từ ID
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

        for c in data["cards"]:
            if c["did"] == did:
                if c["type"] == 0:
                    counts["new"] += 1
                elif c["type"] == 1:
                    counts["learn"] += 1
                elif c["type"] == 2:
                    counts["due"] += 1

        return counts

    def get_next_card_to_study(self, did, today):
        data = JsonDBManager.load_data()
        # Tạo từ điển Note để dễ dàng lấy front/back ghép vào thẻ
        notes_dict = {n["id"]: n for n in data["notes"]}

        # ƯU TIÊN 1: Thẻ đang học dở hoặc đã đến hạn
        valid_cards_review = [
            c for c in data["cards"]
            if c["did"] == did and (c["type"] == 1 or (c["type"] == 2 and c["due"] <= today))
        ]
        if valid_cards_review:
            # Sắp xếp theo ngày due tăng dần (đứa nào hẹn trước thì học trước)
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

        # Lục tìm thẻ và cập nhật
        for c in data["cards"]:
            if c["id"] == card_id:
                c["type"] = new_type
                c["due"] = new_due
                c["ivl"] = new_ivl
                c["factor"] = new_factor
                JsonDBManager.save_data(data)
                return True

        return False


# ==========================================
# KHU VỰC TEST (Giữ nguyên không đổi)
# ==========================================
if __name__ == "__main__":
    deck_dao = DeckDAO()
    note_dao = NoteDAO()
    card_dao = CardDAO()

    print("--- 1. TẠO BỘ THẺ MỚI ---")
    deck_dao.add_deck("JLPT N3 - Từ Vựng")

    print("\n--- 2. THÊM THẺ (Có và Không đảo mặt) ---")
    note_dao.add_note_and_cards("JLPT N3 - Từ Vựng", "犬", "Con chó (Inu)")
    note_dao.add_note_and_cards("JLPT N3 - Từ Vựng", "猫", "Con mèo (Neko)", is_reversed=True)

    print("✅ Đã thêm xong.")

    print("\n--- 3. THỐNG KÊ ---")
    did = note_dao.get_deck_id_by_name("JLPT N3 - Từ Vựng")
    if did:
        thong_ke = card_dao.count_cards_by_state(did)
        print(f"Bộ thẻ 'JLPT N3 - Từ Vựng' có tổng cộng: {thong_ke['new']} thẻ mới đang chờ học.")
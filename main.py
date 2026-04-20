from PyQt5 import QtWidgets, uic, QtCore
import sys, requests, traceback, time

from dao_hacap import DeckDAO, NoteDAO, CardDAO


class CuaSoDuyetThe(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        # Load giao diện bạn vừa tạo
        uic.loadUi('duyet_the.ui', self)
        self.setWindowTitle("Duyệt toàn bộ Thẻ")

        # Gọi các Thủ kho ra để lấy dữ liệu
        self.deck_dao = DeckDAO()
        self.note_dao = NoteDAO()

        # Biến để nhớ xem mình đang bấm vào thẻ nào để lát còn lưu
        self.current_edit_note_id = None

        # --- SETUP BẢNG CHÍNH (Cột Giữa) ---
        self.table_The.setColumnCount(2)
        self.table_The.setHorizontalHeaderLabels(["Mặt trước", "Bộ thẻ"])
        # Ép cột 1 (Mặt trước) phình to ra chiếm hết chỗ trống
        self.table_The.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        # Chống sửa trực tiếp trên bảng (Bắt buộc phải sửa ở cột bên phải)
        self.table_The.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        # Bấm 1 phát là bôi đen cả dòng luôn cho đẹp
        self.table_The.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)

        # --- BƠM DỮ LIỆU BAN ĐẦU ---
        self.tai_danh_sach_bo_the()
        self.tai_danh_sach_the(None)  # None = Tải TẤT CẢ các thẻ

        # --- NỐI DÂY ĐIỆN ---
        self.list_BoThe.itemClicked.connect(self.chon_bo_the)
        self.table_The.itemSelectionChanged.connect(self.chon_the)
        self.btn_LuuThayDoi.clicked.connect(self.luu_thay_doi)

        # Tính năng xịn: Gõ chữ đến đâu lọc danh sách đến đó
        self.txt_TimBoThe.textChanged.connect(self.loc_bo_the)
        self.txt_TimThe.textChanged.connect(self.loc_the)

    def tai_danh_sach_bo_the(self):
        self.list_BoThe.clear()

        # Nặn dòng "Tất cả các thẻ" để lên đầu tiên
        item_all = QtWidgets.QListWidgetItem("Tất cả các thẻ")
        item_all.setData(QtCore.Qt.UserRole, None)  # Giấu mã ID là None
        self.list_BoThe.addItem(item_all)

        # Kéo danh sách bộ thẻ từ DB lên
        danh_sach = self.deck_dao.get_all_decks()
        for bo in danh_sach:
            item = QtWidgets.QListWidgetItem(bo['name'])
            item.setData(QtCore.Qt.UserRole, bo['id'])  # Giấu ngầm ID bộ thẻ
            self.list_BoThe.addItem(item)

    def tai_danh_sach_the(self, deck_id):
        self.table_The.setRowCount(0)  # Xóa sạch bảng cũ
        danh_sach_the = self.note_dao.get_all_notes_with_deck(deck_id)

        for row, the in enumerate(danh_sach_the):
            self.table_The.insertRow(row)

            # Cột 1: Mặt trước (Và giấu luôn đồ nghề vào trong)
            item_truoc = QtWidgets.QTableWidgetItem(the['front'])
            item_truoc.setData(QtCore.Qt.UserRole, the['id'])  # Giấu ID thẻ
            item_truoc.setData(QtCore.Qt.UserRole + 1, the['back'])  # Giấu luôn Nghĩa mặt sau

            # Cột 2: Tên bộ thẻ
            item_bo = QtWidgets.QTableWidgetItem(the['deck_name'])

            self.table_The.setItem(row, 0, item_truoc)
            self.table_The.setItem(row, 1, item_bo)

    def chon_bo_the(self, item):
        """Khi bấm vào Tên bộ thẻ ở Cột Trái"""
        deck_id = item.data(QtCore.Qt.UserRole)
        self.tai_danh_sach_the(deck_id)

        # Dọn dẹp sạch sẽ Cột Phải
        self.txt_EditTruoc.clear()
        self.txt_EditSau.clear()
        self.current_edit_note_id = None

    def chon_the(self):
        """Khi bấm vào 1 dòng trong Bảng ở Cột Giữa"""
        dong_chon = self.table_The.currentRow()
        if dong_chon < 0:
            return

        item_truoc = self.table_The.item(dong_chon, 0)

        # Móc ID và dữ liệu đã giấu ra
        self.current_edit_note_id = item_truoc.data(QtCore.Qt.UserRole)
        mat_truoc = item_truoc.text()
        mat_sau = item_truoc.data(QtCore.Qt.UserRole + 1)

        # Đổ lên Cột Phải để sửa
        self.txt_EditTruoc.setText(mat_truoc)
        self.txt_EditSau.setText(mat_sau)

    def luu_thay_doi(self):
        """Bấm nút xanh Lưu Thay Đổi"""
        if not self.current_edit_note_id:
            QtWidgets.QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn 1 thẻ ở giữa để sửa!")
            return

        truoc_moi = self.txt_EditTruoc.toPlainText().strip()
        sau_moi = self.txt_EditSau.toPlainText().strip()

        if not truoc_moi or not sau_moi:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Bạn không được để trống thẻ!")
            return

        thanh_cong = self.note_dao.update_note(self.current_edit_note_id, truoc_moi, sau_moi)

        if thanh_cong:
            # Ảo thuật: Cập nhật trực tiếp chữ trên bảng để không phải chớp nháy màn hình tải lại
            dong_chon = self.table_The.currentRow()
            item_truoc = self.table_The.item(dong_chon, 0)
            item_truoc.setText(truoc_moi)
            item_truoc.setData(QtCore.Qt.UserRole + 1, sau_moi)

            QtWidgets.QMessageBox.information(self, "Thành công", "Đã lưu bản sửa mới nhất!")
        else:
            QtWidgets.QMessageBox.critical(self, "Lỗi", "Lưu thất bại do kẹt dữ liệu!")

    # --- 2 HÀM BONUS: Tìm kiếm siêu tốc ---
    def loc_bo_the(self, text):
        for i in range(self.list_BoThe.count()):
            item = self.list_BoThe.item(i)
            item.setHidden(text.lower() not in item.text().lower())

    def loc_the(self, text):
        for i in range(self.table_The.rowCount()):
            item_truoc = self.table_The.item(i, 0)
            item_bo = self.table_The.item(i, 1)
            # Ẩn dòng đi nếu chữ gõ vào không khớp với mặt trước hoặc tên bộ thẻ
            match = text.lower() in item_truoc.text().lower() or text.lower() in item_bo.text().lower()
            self.table_The.setRowHidden(i, not match)


class CuaSoTuDien(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        # Load giao diện từ điển
        uic.loadUi('tu_dien.ui', self)
        self.setWindowTitle("Tra cứu từ vựng Jdict")

        # --- FIX UX: Ép con trỏ chuột luôn là hình mũi tên ---
        self.chi_tiet.viewport().setCursor(QtCore.Qt.ArrowCursor)

        # --- FIX 1: Vừa mở app lên thì phải giấu danh sách gợi ý đi ---
        self.goi_y.hide()

        # ---------------------------------------------------------
        # TÍNH NĂNG LIVE SEARCH (GÕ ĐẾN ĐÂU TÌM ĐẾN ĐÓ + CHỐNG SPAM API)
        # ---------------------------------------------------------
        self.timer_tim_kiem = QtCore.QTimer()
        self.timer_tim_kiem.setSingleShot(True)  # Chỉ chạy 1 lần sau khi đếm ngược xong
        self.timer_tim_kiem.timeout.connect(self.tim_kiem_tu_api)

        # BẮT SỰ KIỆN: Cứ mỗi khi gõ 1 ký tự, hàm xu_ly_go_phim sẽ chạy
        self.input_tim_kiem.textChanged.connect(self.xu_ly_go_phim)

        # Nối dây: Khi bấm vào 1 dòng gợi ý thì gọi hàm xem chi tiết
        self.goi_y.itemClicked.connect(self.xem_chi_tiet_tu)

    def xu_ly_go_phim(self):
        """Hàm này chạy mỗi khi tay bạn chạm vào bàn phím"""
        tu_khoa = self.input_tim_kiem.text().strip()
        if not tu_khoa:
            self.goi_y.clear()
            self.goi_y.hide()  # FIX 1: Nếu xóa hết chữ thì giấu danh sách đi
            self.chi_tiet.clear()
            return

        # Reset đồng hồ về 500 mili-giây (0.5 giây).
        self.timer_tim_kiem.start(500)

    def tim_kiem_tu_api(self):
        tu_khoa = self.input_tim_kiem.text().strip()
        if not tu_khoa:
            return

        self.goi_y.clear()
        self.chi_tiet.setText("Đang tìm kiếm...")

        url = f"https://api.jdict.net/api/v1/suggest?keyword={tu_khoa}&keyword_position=start&type=word"

        try:
            response = requests.get(url).json()
            danh_sach_tu = response.get('list', [])

            if not danh_sach_tu:
                self.goi_y.hide()
                self.chi_tiet.setText("Không tìm thấy từ nào!")
                return

            for item in danh_sach_tu:
                word = item.get('word', '')
                kana = item.get('kana', '')
                mean = item.get('suggest_mean', '')
                slug = item.get('slug', '')

                chuoi_hien_thi = f"{word} ({kana}) - {mean}"

                list_item = QtWidgets.QListWidgetItem(chuoi_hien_thi)
                list_item.setData(QtCore.Qt.UserRole, slug)
                self.goi_y.addItem(list_item)

            self.goi_y.show()  # FIX 1: Có kết quả thì xổ danh sách ra che màn hình
            self.chi_tiet.setText(f"Tìm thấy {len(danh_sach_tu)} kết quả. Hãy chọn 1 từ bên dưới.")

        except Exception as e:
            self.chi_tiet.setText(f"Lỗi khi gọi API: {e}")

    def xem_chi_tiet_tu(self, item):
        slug = item.data(QtCore.Qt.UserRole)
        if not slug:
            return

        self.chi_tiet.setText("Đang tải chi tiết từ điển...")

        # FIX 1: Vừa bấm chọn xong phải GIẤU DANH SÁCH ĐI để nhìn thấy chi tiết bên dưới!
        self.goi_y.hide()

        url_chi_tiet = f"https://api.jdict.net/api/v1/words/{slug}?get_relate=1"

        try:
            response = requests.get(url_chi_tiet).json()

            word = response.get('word', '')
            kana = response.get('kana', '')

            # FIX 2: Nghĩa chính nằm ở ngay thẻ root, không phải trong mảng meanings
            nghia_tv = response.get('suggest_mean', '')

            # Lấy mảng kanjis ra an toàn (nếu không có thì trả về mảng rỗng [])
            kanjis = response.get('kanjis', [])

            # Duyệt qua mảng 'kanjis' vừa lấy, và dùng k.get() cho an toàn tuyệt đối
            danh_sach_han_viet = [k.get('hanviet', '') for k in kanjis]

            # Dùng hàm join() để nối mảng đó lại bằng dấu cách
            chuoi_han_viet = " ".join(danh_sach_han_viet)

            html_chi_tiet = f"""
            <h1 style='color: #d80000; font-size: 40px;'>{word}</h1>
            <h3>Cách đọc: <span style='color: #0055ff;'>{kana}</span></h3>
            <h3>Hán Việt: {chuoi_han_viet}</h3>
            <hr>
            <p style='font-size: 18px;'><b>Ý nghĩa:</b> <br>{nghia_tv}</p>
            """

            self.chi_tiet.setHtml(html_chi_tiet)

        except Exception as e:
            self.chi_tiet.setText(f"Lỗi tải chi tiết: {e}")


class AnkiApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi('item_bo_the.ui', self)

        self.deck_dao = DeckDAO()
        self.note_dao = NoteDAO()
        self.card_dao = CardDAO()

        self.pushButton_5.clicked.connect(self.mo_man_hinh_chinh)
        self.pushButton_6.clicked.connect(self.mo_cua_so_them_the)
        # Sửa thành nút btn_Duyet hoặc tên nút tương ứng trên UI của bạn
        self.btn_Duyet.clicked.connect(self.mo_cua_so_duyet_the)

        self.tai_du_lieu_len_man_hinh_chinh()

        # Biến để trí nhớ App biết mình đang học bộ thẻ nào và thẻ nào
        self.current_deck_id = None
        self.current_card = None

        # --- CODE MỚI: ĐỌC TRÍ NHỚ TỪ Ổ CỨNG ---
        self.settings = QtCore.QSettings("AppCuaSon", "AnkiClone")
        hom_nay = time.strftime("%Y-%m-%d")  # Lấy ngày hiện tại (VD: 2026-04-10)
        ngay_luu_cu = self.settings.value("ngay_hoc", "")

        # Kiểm tra: Nếu hôm nay vẫn là ngày cũ thì lấy số cũ ra đếm tiếp
        if ngay_luu_cu == hom_nay:
            self.so_the_da_hoc = int(self.settings.value("so_the", 0))
        else:
            # Nếu sang ngày mới, reset về 0 và lưu ngày mới vào
            self.so_the_da_hoc = 0
            self.settings.setValue("ngay_hoc", hom_nay)
            self.settings.setValue("so_the", 0)

        # =======================================================
        # 🛠️ FIX BUG Ở ĐÂY: In ra màn hình ngay khi vừa mở app lên
        # =======================================================
        self.lbl_ThongKeHomNay.setText(f"Đã học {self.so_the_da_hoc} thẻ trong hôm nay")

        # Nối dây các nút ở Trang 2 (Tổng quan) và Trang 3 (Học)
        self.btn_HocBayGio.clicked.connect(self.bat_dau_hoc)
        self.btn_HienDapAn.clicked.connect(self.hien_thi_dap_an)

        # Nối 4 nút đánh giá (Dùng lambda để truyền số 1, 2, 3, 4 thẳng vào thuật toán)
        self.btn_Lai.clicked.connect(lambda: self.danh_gia_the(1))
        self.btn_Kho.clicked.connect(lambda: self.danh_gia_the(2))
        self.btn_Tot.clicked.connect(lambda: self.danh_gia_the(3))
        self.btn_De.clicked.connect(lambda: self.danh_gia_the(4))

    def tai_du_lieu_len_man_hinh_chinh(self):
        # 🚀 THẦN CHÚ 1: Ép vùng cuộn tự động co giãn để chứa vừa nội dung
        self.scrollArea.setWidgetResizable(True)

        layout = self.scrollAreaWidgetContents.layout()
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    layout.removeItem(item)
        else:
            layout = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)

        danh_sach = self.deck_dao.get_all_decks()

        if not danh_sach:
            lbl_trong = QtWidgets.QLabel("Chưa có bộ thẻ nào. Hãy bấm 'Thêm' để tạo!")
            lbl_trong.setAlignment(QtCore.Qt.AlignCenter)
            layout.addWidget(lbl_trong)
            return

        for bo_the in danh_sach:
            deck_id = bo_the['id']
            deck_name = bo_the['name']

            row_widget = uic.loadUi('row_deck.ui')
            # 🚀 THẦN CHÚ 2: Chống bị bóp méo khi Scroll Area thu nhỏ
            row_widget.setMinimumHeight(60)

            row_widget.btn_TenBoThe.setText(deck_name)
            thong_ke = self.card_dao.count_cards_by_state(deck_id)

            row_widget.lbl_SoMoi.setText(str(thong_ke['new']))
            row_widget.lbl_SoHoc.setText(str(thong_ke['learn']))
            row_widget.lbl_SoDenHan.setText(str(thong_ke['due']))

            row_widget.lbl_SoMoi.setStyleSheet("color: #0000ff; font-weight: bold;")
            row_widget.lbl_SoHoc.setStyleSheet("color: #d80000; font-weight: bold;")
            row_widget.lbl_SoDenHan.setStyleSheet("color: #00aa00; font-weight: bold;")

            # Truyền ID và Tên bộ thẻ sang màn hình Tổng quan
            row_widget.btn_TenBoThe.clicked.connect(
                lambda checked, d_id=deck_id, d_name=deck_name: self.mo_man_hinh_tong_quan(d_id, d_name))

            menu = QtWidgets.QMenu(self)
            action_doi_ten = QtWidgets.QAction("Đổi tên", self)
            action_xoa = QtWidgets.QAction("Xóa", self)
            menu.addAction(action_doi_ten)
            menu.addAction(action_xoa)

            row_widget.btn_Settings.setMenu(menu)
            row_widget.btn_Settings.setPopupMode(QtWidgets.QToolButton.InstantPopup)

            # DÂY ĐIỆN BÁNH RĂNG
            action_doi_ten.triggered.connect(
                lambda checked, d_id=deck_id, old_name=deck_name: self.xu_ly_doi_ten(d_id, old_name))
            action_xoa.triggered.connect(lambda checked, d_id=deck_id: self.xu_ly_xoa_bo_the(d_id))

            layout.addWidget(row_widget)

            # 🚀 THẦN CHÚ 3: Ép cái khuôn phải hiện hình (Quan trọng nhất)
            row_widget.show()

        spacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        layout.addItem(spacer)

    # ====================================================
    # LUỒNG HỌC FLASHCARD (TRÁI TIM CỦA ỨNG DỤNG)
    # ====================================================
    def mo_man_hinh_tong_quan(self, deck_id, deck_name):
        """Bước đệm: Chuyển sang Trang 2 (Tổng quan)"""
        self.current_deck_id = deck_id
        self.lbl_TongQuan_TenBoThe.setText(deck_name)

        # Cập nhật 3 con số thống kê to đùng
        thong_ke = self.card_dao.count_cards_by_state(deck_id)
        self.lbl_TongQuan_SoMoi.setText(str(thong_ke['new']))
        self.lbl_TongQuan_SoHoc.setText(str(thong_ke['learn']))
        self.lbl_TongQuan_SoDenHan.setText(str(thong_ke['due']))

        # --- CODE THÊM MỚI: Bơm trí nhớ từ ổ cứng lên giao diện ngay lập tức ---
        self.lbl_ThongKeHomNay.setText(f"Đã học {self.so_the_da_hoc} thẻ trong hôm nay")

        self.stackedWidget.setCurrentIndex(1)  # Lật sang Trang 2

    def bat_dau_hoc(self):
        """Bấm 'Học Bây giờ' -> Lật sang Trang 3 và bốc thẻ đầu tiên"""
        self.stackedWidget.setCurrentIndex(2)  # Lật sang Trang 3
        self.tai_the_tiep_theo()

    def tai_the_tiep_theo(self):
        """Hành động bốc thẻ từ kho lên bảng đen (Đã lắp máy chống sốc)"""
        try:
            today = int(time.time() / 86400)
            self.current_card = self.card_dao.get_next_card_to_study(self.current_deck_id, today)

            if self.current_card:
                html_truoc = f"<div style='text-align: center; font-size: 32px; margin-top: 50px;'>{self.current_card['front']}</div>"

                # Đổi thành setText để dùng được cho cả QLabel và QTextBrowser
                self.txt_NoiDungThe.setText(html_truoc)

                thong_ke = self.card_dao.count_cards_by_state(self.current_deck_id)
                self.lbl_Hoc_Moi.setText(str(thong_ke['new']))
                self.lbl_Hoc_DangHoc.setText(str(thong_ke['learn']))
                self.lbl_Hoc_CanOn.setText(str(thong_ke['due']))

                self.frame_DanhGia.hide()
                self.btn_HienDapAn.show()
            else:
                self.stackedWidget.setCurrentIndex(3)
                self.tai_du_lieu_len_man_hinh_chinh()

        except Exception as e:
            # Nếu có lỗi, app sẽ không văng mà hiện bảng thông báo màu đỏ!
            error_msg = traceback.format_exc()
            QtWidgets.QMessageBox.critical(self, "Máy dò lỗi lật thẻ", f"App suýt văng vì lỗi:\n\n{error_msg}")

    def hien_thi_dap_an(self):
        """Lật mặt sau và tráo nút"""
        try:
            if self.current_card:
                html_day_du = f"""
                <div style='text-align: center; font-size: 32px; margin-top: 20px;'>
                    {self.current_card['front']}
                    <hr style='width: 80%; border: 1px solid #ccc; margin: 20px auto;'>
                    <span style='color: #0055ff;'>{self.current_card['back']}</span>
                </div>
                """
                self.txt_NoiDungThe.setText(html_day_du)  # Đổi thành setText

                self.btn_HienDapAn.hide()
                self.frame_DanhGia.show()
        except Exception as e:
            error_msg = traceback.format_exc()
            QtWidgets.QMessageBox.critical(self, "Máy dò lỗi Đáp án", f"App suýt văng vì lỗi:\n\n{error_msg}")

    def danh_gia_the(self, ease):
        if self.current_card:
            today = int(time.time() / 86400)
            c_id = self.current_card['id']
            c_ivl = self.current_card['ivl']
            c_factor = self.current_card['factor']

            self.card_dao.update_card_after_review(c_id, ease, c_ivl, c_factor, today)

            self.so_the_da_hoc += 1
            self.settings.setValue("so_the", self.so_the_da_hoc)
            self.lbl_ThongKeHomNay.setText(f"Đã học {self.so_the_da_hoc} thẻ trong hôm nay")

            self.tai_the_tiep_theo()

    # ====================================================
    # PHẦN GIAO DIỆN CHUNG & THÊM THẺ
    # ====================================================
    def mo_man_hinh_chinh(self):
        self.stackedWidget.setCurrentIndex(0)

    def xu_ly_doi_ten(self, deck_id, old_name):
        dialog = QtWidgets.QInputDialog(self)
        dialog.setWindowTitle("Đổi tên bộ thẻ")
        dialog.setLabelText("Nhập tên mới:")
        dialog.setTextValue(old_name)
        dialog.setWindowFlags(dialog.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)

        ok = dialog.exec_()
        ten_moi = dialog.textValue().strip()

        if ok and ten_moi and ten_moi != old_name:
            thanh_cong = self.deck_dao.update_deck_name(deck_id, ten_moi)
            if thanh_cong:
                self.tai_du_lieu_len_man_hinh_chinh()
            else:
                QtWidgets.QMessageBox.warning(self, "Lỗi", "Tên bộ thẻ đã tồn tại, vui lòng chọn tên khác!")

    def xu_ly_xoa_bo_the(self, deck_id):
        cau_hoi = QtWidgets.QMessageBox.question(
            self, "Xác nhận xóa",
            "Bạn có chắc chắn muốn xóa bộ thẻ này không?\nToàn bộ từ vựng bên trong sẽ bay màu vĩnh viễn!",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )

        if cau_hoi == QtWidgets.QMessageBox.Yes:
            self.deck_dao.delete_deck(deck_id)
            self.tai_du_lieu_len_man_hinh_chinh()

    def mo_cua_so_them_the(self):
        try:
            self.dialog_them = uic.loadUi('man_hinh_them.ui')
            self.dialog_them.setWindowFlags(self.dialog_them.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)

            self.dialog_them.combo_BoThe.clear()
            danh_sach = self.deck_dao.get_all_decks()
            if danh_sach:
                for bo_the in danh_sach:
                    self.dialog_them.combo_BoThe.addItem(bo_the['name'])
            else:
                self.dialog_them.combo_BoThe.addItem("Mặc định")

            self.dialog_them.combo_BoThe.addItem("➕ Tạo bộ thẻ mới...")

            def xu_ly_chon_bo_the(index):
                ten_muc_duoc_chon = self.dialog_them.combo_BoThe.itemText(index)

                if ten_muc_duoc_chon == "➕ Tạo bộ thẻ mới...":
                    dialog_nhap = QtWidgets.QInputDialog(self.dialog_them)
                    dialog_nhap.setWindowTitle("Thêm bộ thẻ")
                    dialog_nhap.setLabelText("Nhập tên bộ thẻ mới:")
                    dialog_nhap.setWindowFlags(dialog_nhap.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)

                    ok = dialog_nhap.exec_()
                    ten_moi = dialog_nhap.textValue().strip()

                    if ok and ten_moi:
                        deck_id_moi = self.deck_dao.add_deck(ten_moi)
                        if deck_id_moi:
                            vi_tri_cuoi = self.dialog_them.combo_BoThe.count() - 1
                            self.dialog_them.combo_BoThe.insertItem(vi_tri_cuoi, ten_moi)
                            self.dialog_them.combo_BoThe.setCurrentIndex(vi_tri_cuoi)
                            self.tai_du_lieu_len_man_hinh_chinh()
                        else:
                            QtWidgets.QMessageBox.warning(self.dialog_them, "Lỗi", "Tên bộ thẻ đã tồn tại!")
                            self.dialog_them.combo_BoThe.setCurrentIndex(0)
                    else:
                        self.dialog_them.combo_BoThe.setCurrentIndex(0)

            self.dialog_them.combo_BoThe.activated.connect(xu_ly_chon_bo_the)

            def chuyen_form_nhap_lieu(index):
                self.dialog_them.stackedWidget_Kieu.setCurrentIndex(index)

            self.dialog_them.combo_Kieu.currentIndexChanged.connect(chuyen_form_nhap_lieu)
            self.dialog_them.stackedWidget_Kieu.setCurrentIndex(0)

            self.dialog_them.btn_Dong.clicked.connect(self.dialog_them.close)

            def xu_ly_them():
                try:
                    che_do = self.dialog_them.combo_Kieu.currentIndex()
                    bo_the_chon = self.dialog_them.combo_BoThe.currentText()
                    nhan = self.dialog_them.txt_Nhan.text()

                    truoc = ""
                    sau = ""
                    is_reversed = False

                    if che_do == 0:
                        truoc = self.dialog_them.txt_MatTruoc_1.text().strip()
                        sau = self.dialog_them.txt_MatSau_1.text().strip()
                        self.dialog_them.txt_MatTruoc_1.clear()
                        self.dialog_them.txt_MatSau_1.clear()
                        self.dialog_them.txt_MatTruoc_1.setFocus()

                    elif che_do == 1:
                        truoc = self.dialog_them.txt_MatTruoc_2.text().strip()
                        sau = self.dialog_them.txt_MatSau_2.text().strip()
                        is_reversed = True
                        self.dialog_them.txt_MatTruoc_2.clear()
                        self.dialog_them.txt_MatSau_2.clear()
                        self.dialog_them.txt_MatTruoc_2.setFocus()

                    if not truoc or not sau:
                        QtWidgets.QMessageBox.warning(self.dialog_them, "Lỗi", "Vui lòng nhập đủ Mặt trước và Mặt sau!")
                        return

                    thanh_cong = self.note_dao.add_note_and_cards(
                        deck_name=bo_the_chon,
                        front=truoc,
                        back=sau,
                        tags=nhan,
                        is_reversed=is_reversed
                    )

                    if thanh_cong:
                        print(f"✅ Đã thêm '{truoc}' thành công!")
                        self.tai_du_lieu_len_man_hinh_chinh()
                    else:
                        QtWidgets.QMessageBox.critical(self.dialog_them, "Lỗi", "Không thể lưu dữ liệu!")

                except Exception as e:
                    error_msg = traceback.format_exc()
                    QtWidgets.QMessageBox.critical(self.dialog_them, "Máy dò lỗi",
                                                   f"App vừa suýt văng vì lỗi này:\n\n{error_msg}")

            self.dialog_them.btn_Them.clicked.connect(xu_ly_them)

            def mo_tu_dien():
                self.tu_dien_window = CuaSoTuDien()  # Khởi tạo cửa sổ
                self.tu_dien_window.show()  # Bật nó lên

            self.dialog_them.btn_TimKiemTuVung.clicked.connect(mo_tu_dien)

            self.dialog_them.show()

        except Exception as e:
            error_msg = traceback.format_exc()
            QtWidgets.QMessageBox.critical(self, "Máy dò lỗi", f"Không mở được Cửa sổ Thêm:\n\n{error_msg}")

    def mo_cua_so_duyet_the(self):
        try:
            self.window_duyet = CuaSoDuyetThe()
            self.window_duyet.show()
        except Exception as e:
            error_msg = traceback.format_exc()
            QtWidgets.QMessageBox.critical(self, "Lỗi", f"Không mở được Duyệt Thẻ:\n{error_msg}")


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = AnkiApp()
    window.show()
    sys.exit(app.exec_())
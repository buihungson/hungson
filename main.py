from PyQt5 import QtWidgets, uic, QtCore
import sys, requests, time

from dao_hacap import DeckDAO, NoteDAO, CardDAO


# =========================================================
# 1. CỬA SỔ DUYỆT THẺ
# =========================================================
class CuaSoDuyetThe(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi('duyet_the.ui', self)
        self.setWindowTitle("Duyệt toàn bộ Thẻ")

        self.deck_dao = DeckDAO()
        self.note_dao = NoteDAO()
        self.current_edit_note_id = None # người dùng click vào đâu

        self.table_The.setColumnCount(2)
        self.table_The.setHorizontalHeaderLabels(["Mặt trước", "Bộ thẻ"])
        self.table_The.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.table_The.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table_The.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)

        self.tai_danh_sach_bo_the()
        self.tai_danh_sach_the(None)

        self.list_BoThe.itemClicked.connect(self.chon_bo_the)
        self.table_The.itemSelectionChanged.connect(self.chon_the)
        self.btn_LuuThayDoi.clicked.connect(self.luu_thay_doi)
        self.btn_XoaThe.clicked.connect(self.xu_ly_xoa_the)
        self.txt_TimBoThe.textChanged.connect(self.loc_bo_the)
        self.txt_TimThe.textChanged.connect(self.loc_the)

    def tai_danh_sach_bo_the(self):
        self.list_BoThe.clear()
        item_all = QtWidgets.QListWidgetItem("Tất cả các bộ thẻ")
        item_all.setData(int(QtCore.Qt.ItemDataRole.UserRole), None)
        self.list_BoThe.addItem(item_all)
        danh_sach = self.deck_dao.get_all_decks()
        for bo in danh_sach:
            item = QtWidgets.QListWidgetItem(bo['name'])
            item.setData(int(QtCore.Qt.ItemDataRole.UserRole), bo['id'])
            self.list_BoThe.addItem(item)

    def tai_danh_sach_the(self, deck_id):
        self.table_The.setRowCount(0)
        danh_sach_the = self.note_dao.get_all_notes_with_deck(deck_id)
        for row, the in enumerate(danh_sach_the):
            self.table_The.insertRow(row)
            item_truoc = QtWidgets.QTableWidgetItem(the['front'])
            item_truoc.setData(int(QtCore.Qt.ItemDataRole.UserRole), the['id'])
            item_truoc.setData(int(int(QtCore.Qt.ItemDataRole.UserRole)) + 1, the['back'])
            item_truoc.setData(int(int(QtCore.Qt.ItemDataRole.UserRole)) + 2, the.get('loai_the', 'Cơ bản'))
            item_bo = QtWidgets.QTableWidgetItem(the['deck_name'])
            self.table_The.setItem(row, 0, item_truoc)
            self.table_The.setItem(row, 1, item_bo)

    def chon_bo_the(self, item):
        deck_id = item.data(int(int(QtCore.Qt.ItemDataRole.UserRole)))
        self.tai_danh_sach_the(deck_id)
        self.txt_EditTruoc.clear()
        self.txt_EditSau.clear()
        self.current_edit_note_id = None

    def chon_the(self):
        dong_chon = self.table_The.currentRow()
        if dong_chon < 0: return
        item_truoc = self.table_The.item(dong_chon, 0)
        self.current_edit_note_id = item_truoc.data(int(int(QtCore.Qt.ItemDataRole.UserRole)))
        self.txt_EditTruoc.setText(item_truoc.text())
        self.txt_EditSau.setText(item_truoc.data(int(int(QtCore.Qt.ItemDataRole.UserRole)) + 1))
        loai_the = item_truoc.data(int(int(QtCore.Qt.ItemDataRole.UserRole)) + 2)
        self.lbl_LoaiThe.setText(f"Loại thẻ: {loai_the}")

    def luu_thay_doi(self):
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
            dong_chon = self.table_The.currentRow()
            item_truoc = self.table_The.item(dong_chon, 0)
            item_truoc.setText(truoc_moi)
            item_truoc.setData(int(int(QtCore.Qt.ItemDataRole.UserRole)) + 1, sau_moi)
            QtWidgets.QMessageBox.information(self, "Thành công", "Đã lưu bản sửa mới nhất!")
        else:
            QtWidgets.QMessageBox.critical(self, "Lỗi", "Lưu thất bại!")

    def xu_ly_xoa_the(self):
        if not self.current_edit_note_id:
            QtWidgets.QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn 1 thẻ để xóa!")
            return
        cau_hoi = QtWidgets.QMessageBox.question(self, "Xác nhận xóa",
                                                 "Bạn có chắc chắn muốn xóa thẻ này vĩnh viễn không?",
                                                 QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if cau_hoi == QtWidgets.QMessageBox.Yes:
            thanh_cong = self.note_dao.delete_note(self.current_edit_note_id)
            if thanh_cong:
                self.table_The.removeRow(self.table_The.currentRow())
                self.txt_EditTruoc.clear()
                self.txt_EditSau.clear()
                self.current_edit_note_id = None
                QtWidgets.QMessageBox.information(self, "Thành công", "Đã xóa thẻ!")

    def loc_bo_the(self, text):
        for i in range(self.list_BoThe.count()):
            item = self.list_BoThe.item(i)
            item.setHidden(text.lower() not in item.text().lower())

    def loc_the(self, text):
        for i in range(self.table_The.rowCount()):
            item_truoc = self.table_The.item(i, 0)
            item_bo = self.table_The.item(i, 1)
            match = text.lower() in item_truoc.text().lower() or text.lower() in item_bo.text().lower()
            self.table_The.setRowHidden(i, not match)


# =========================================================
# 2. CỬA SỔ TỪ ĐIỂN
# =========================================================
class CuaSoTuDien(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi('tu_dien.ui', self)
        self.setWindowTitle("Tra cứu từ vựng Jdict")
        self.chi_tiet.viewport().setCursor(QtCore.Qt.ArrowCursor)

        self.goi_y.hide()

        self.timer_tim_kiem = QtCore.QTimer()
        self.timer_tim_kiem.setSingleShot(True)
        self.timer_tim_kiem.timeout.connect(self.tim_kiem_tu_api)

        self.input_tim_kiem.textChanged.connect(self.xu_ly_go_phim)
        self.goi_y.itemClicked.connect(self.xem_chi_tiet_tu)

    def xu_ly_go_phim(self):
        tu_khoa = self.input_tim_kiem.text().strip()
        if not tu_khoa:
            self.goi_y.clear()
            self.goi_y.hide()
            self.chi_tiet.clear()
            return
        self.timer_tim_kiem.start(500)

    def tim_kiem_tu_api(self):
        tu_khoa = self.input_tim_kiem.text().strip()
        if not tu_khoa: return

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
                chuoi = f"{item.get('word', '')} ({item.get('kana', '')}) - {item.get('suggest_mean', '')}"
                list_item = QtWidgets.QListWidgetItem(chuoi)
                list_item.setData(int(int(QtCore.Qt.ItemDataRole.UserRole)), item.get('slug', ''))
                self.goi_y.addItem(list_item)
            self.goi_y.show()
            self.chi_tiet.setText(f"Tìm thấy {len(danh_sach_tu)} kết quả.")
        except Exception as e:
            self.chi_tiet.setText(f"Lỗi kết nối mạng: {e}")

    def xem_chi_tiet_tu(self, item):
        slug = item.data(int(int(QtCore.Qt.ItemDataRole.UserRole)))
        if not slug: return
        self.goi_y.hide()
        self.chi_tiet.setText("Đang tải chi tiết...")
        url_chi_tiet = f"https://api.jdict.net/api/v1/words/{slug}?get_relate=1"
        try:
            response = requests.get(url_chi_tiet).json()
            word = response.get('word', '')
            kana = response.get('kana', '')
            nghia_tv = response.get('suggest_mean', '')
            kanjis = response.get('kanjis', [])
            chuoi_han_viet = " ".join([k.get('hanviet', '') for k in kanjis])
            html = f"<h1>{word}</h1><h3>Cách đọc: {kana}</h3><h3>Hán Việt: {chuoi_han_viet}</h3><hr><p>{nghia_tv}</p>"
            self.chi_tiet.setHtml(html)
        except Exception as e:
            self.chi_tiet.setText(f"Lỗi kết nối mạng: {e}")


# =========================================================================
# 3. CỬA SỔ THÊM THẺ (Đã gỡ bỏ máy dò lỗi traceback)
# =========================================================================
class CuaSoThemThe(QtWidgets.QWidget):
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app

        self.deck_dao = DeckDAO()
        self.note_dao = NoteDAO()

        uic.loadUi('man_hinh_them.ui', self)
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)

        self.combo_BoThe.clear()
        danh_sach = self.deck_dao.get_all_decks()
        if danh_sach:
            for bo_the in danh_sach:
                self.combo_BoThe.addItem(bo_the['name'])
        else:
            self.combo_BoThe.addItem("Mặc định")

        self.combo_BoThe.addItem("➕ Tạo bộ thẻ mới...")

        def xu_ly_chon_bo_the(index):
            ten_muc_duoc_chon = self.combo_BoThe.itemText(index)

            if ten_muc_duoc_chon == "➕ Tạo bộ thẻ mới...":
                dialog_nhap = QtWidgets.QInputDialog(self)
                dialog_nhap.setWindowTitle("Thêm bộ thẻ")
                dialog_nhap.setLabelText("Nhập tên bộ thẻ mới:")
                dialog_nhap.setWindowFlags(dialog_nhap.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)

                ok = dialog_nhap.exec_()
                ten_moi = dialog_nhap.textValue().strip()

                if ok and ten_moi:
                    deck_id_moi = self.deck_dao.add_deck(ten_moi)
                    if deck_id_moi:
                        vi_tri_cuoi = self.combo_BoThe.count() - 1
                        self.combo_BoThe.insertItem(vi_tri_cuoi, ten_moi)
                        self.combo_BoThe.setCurrentIndex(vi_tri_cuoi)
                        self.main_app.tai_du_lieu_len_man_hinh_chinh()
                    else:
                        QtWidgets.QMessageBox.warning(self, "Lỗi", "Tên bộ thẻ đã tồn tại!")
                        self.combo_BoThe.setCurrentIndex(0)
                else:
                    self.combo_BoThe.setCurrentIndex(0)

        self.combo_BoThe.activated.connect(xu_ly_chon_bo_the)

        def chuyen_form_nhap_lieu(index):
            self.stackedWidget_Kieu.setCurrentIndex(index)

        self.combo_Kieu.currentIndexChanged.connect(chuyen_form_nhap_lieu)
        self.stackedWidget_Kieu.setCurrentIndex(0)

        self.btn_Dong.clicked.connect(self.close)

        def xu_ly_them():
            che_do = self.combo_Kieu.currentIndex()
            bo_the_chon = self.combo_BoThe.currentText()
            nhan = self.txt_Nhan.text()

            truoc = ""
            sau = ""
            is_reversed = False

            if che_do == 0:
                truoc = self.txt_MatTruoc_1.text().strip()
                sau = self.txt_MatSau_1.text().strip()
                self.txt_MatTruoc_1.clear()
                self.txt_MatSau_1.clear()
                self.txt_MatTruoc_1.setFocus()

            elif che_do == 1:
                truoc = self.txt_MatTruoc_2.text().strip()
                sau = self.txt_MatSau_2.text().strip()
                is_reversed = True
                self.txt_MatTruoc_2.clear()
                self.txt_MatSau_2.clear()
                self.txt_MatTruoc_2.setFocus()

            if not truoc or not sau:
                QtWidgets.QMessageBox.warning(self, "Lỗi", "Vui lòng nhập đủ Mặt trước và Mặt sau!")
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
                self.main_app.tai_du_lieu_len_man_hinh_chinh()
            else:
                QtWidgets.QMessageBox.critical(self, "Lỗi", "Không thể lưu dữ liệu!")

        self.btn_Them.clicked.connect(xu_ly_them)

        def mo_tu_dien():
            self.tu_dien_window = CuaSoTuDien()
            self.tu_dien_window.show()

        self.btn_TimKiemTuVung.clicked.connect(mo_tu_dien)


# =========================================================
# 4. APP CHÍNH (Đã gỡ bỏ máy dò lỗi traceback)
# =========================================================
class AnkiApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi('item_bo_the.ui', self)



        self.deck_dao = DeckDAO()
        self.note_dao = NoteDAO()
        self.card_dao = CardDAO()

        self.pushButton_5.clicked.connect(self.mo_man_hinh_chinh)
        self.pushButton_6.clicked.connect(self.mo_cua_so_them_the)
        self.btn_Duyet.clicked.connect(self.mo_cua_so_duyet_the)

        self.tai_du_lieu_len_man_hinh_chinh()

        self.current_deck_id = None
        self.current_card = None

        self.settings = QtCore.QSettings("AppCuaSon", "AnkiClone")
        hom_nay = time.strftime("%Y-%m-%d")
        ngay_luu_cu = self.settings.value("ngay_hoc", "")

        if ngay_luu_cu == hom_nay:
            self.so_the_da_hoc = int(self.settings.value("so_the", 0))
        else:
            self.so_the_da_hoc = 0
            self.settings.setValue("ngay_hoc", hom_nay)
            self.settings.setValue("so_the", 0)

        self.lbl_ThongKeHomNay.setText(f"Đã học {self.so_the_da_hoc} thẻ trong hôm nay")

        self.btn_HocBayGio.clicked.connect(self.bat_dau_hoc)
        self.btn_HienDapAn.clicked.connect(self.hien_thi_dap_an)

        self.btn_Lai.clicked.connect(lambda: self.danh_gia_the(1))
        self.btn_Kho.clicked.connect(lambda: self.danh_gia_the(2))
        self.btn_Tot.clicked.connect(lambda: self.danh_gia_the(3))
        self.btn_De.clicked.connect(lambda: self.danh_gia_the(4))

    def tai_du_lieu_len_man_hinh_chinh(self):
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
            row_widget.setMinimumHeight(60)
            row_widget.btn_TenBoThe.setText(deck_name)

            thong_ke = self.card_dao.count_cards_by_state(deck_id)

            row_widget.lbl_SoMoi.setText(str(thong_ke['new']))
            row_widget.lbl_SoHoc.setText(str(thong_ke['learn']))
            row_widget.lbl_SoDenHan.setText(str(thong_ke['due']))

            row_widget.lbl_SoMoi.setStyleSheet("color: #0000ff; font-weight: bold;")
            row_widget.lbl_SoHoc.setStyleSheet("color: #d80000; font-weight: bold;")
            row_widget.lbl_SoDenHan.setStyleSheet("color: #00aa00; font-weight: bold;")

            row_widget.btn_TenBoThe.clicked.connect(
                lambda checked, d_id=deck_id, d_name=deck_name: self.mo_man_hinh_tong_quan(d_id, d_name))

            menu = QtWidgets.QMenu(self)
            action_doi_ten = QtWidgets.QAction("Đổi tên", self)
            action_xoa = QtWidgets.QAction("Xóa", self)
            menu.addAction(action_doi_ten)
            menu.addAction(action_xoa)

            row_widget.btn_Settings.setMenu(menu)
            row_widget.btn_Settings.setPopupMode(QtWidgets.QToolButton.InstantPopup)

            action_doi_ten.triggered.connect(
                lambda checked, d_id=deck_id, old_name=deck_name: self.xu_ly_doi_ten(d_id, old_name))
            action_xoa.triggered.connect(lambda checked, d_id=deck_id: self.xu_ly_xoa_bo_the(d_id))

            layout.addWidget(row_widget)
            row_widget.show()

        spacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        layout.addItem(spacer)

    def mo_man_hinh_tong_quan(self, deck_id, deck_name):
        self.current_deck_id = deck_id
        self.lbl_TongQuan_TenBoThe.setText(deck_name)

        thong_ke = self.card_dao.count_cards_by_state(deck_id)
        self.lbl_TongQuan_SoMoi.setText(str(thong_ke['new']))
        self.lbl_TongQuan_SoHoc.setText(str(thong_ke['learn']))
        self.lbl_TongQuan_SoDenHan.setText(str(thong_ke['due']))

        self.lbl_ThongKeHomNay.setText(f"Đã học {self.so_the_da_hoc} thẻ trong hôm nay")

        self.stackedWidget.setCurrentIndex(1)

    def bat_dau_hoc(self):
        self.stackedWidget.setCurrentIndex(2)
        self.tai_the_tiep_theo()

    def tai_the_tiep_theo(self):
        today = int(time.time() / 86400)
        self.current_card = self.card_dao.get_next_card_to_study(self.current_deck_id, today)

        if self.current_card:
            html_truoc = f"<div style='text-align: center; font-size: 32px; margin-top: 50px;'>{self.current_card['front']}</div>"
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

    def hien_thi_dap_an(self):
        if self.current_card:
            html_day_du = f"""
            <div style='text-align: center; font-size: 32px; margin-top: 20px;'>
                {self.current_card['front']}
                <hr style='width: 80%; border: 1px solid #ccc; margin: 20px auto;'>
                <span style='color: #0055ff;'>{self.current_card['back']}</span>
            </div>
            """
            self.txt_NoiDungThe.setText(html_day_du)

            self.btn_HienDapAn.hide()
            self.frame_DanhGia.show()

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

    def mo_man_hinh_chinh(self):
        self.tai_du_lieu_len_man_hinh_chinh()
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
        self.window_them = CuaSoThemThe(self)
        self.window_them.show()

    def mo_cua_so_duyet_the(self):
        self.window_duyet = CuaSoDuyetThe()
        self.window_duyet.show()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = AnkiApp()
    window.show()
    sys.exit(app.exec_())
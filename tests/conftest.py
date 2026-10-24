"""
conftest.py - PySide6 Modal ve Bloklayan Diyalog Sahteleme (Autouse Fixture)
QMessageBox, QDialog, QFileDialog ve QInputDialog çağrılarını otomatik olarak
yakalar, modal kilitlenmeleri (test takılmalarını) engeller ve testlerin yanıtları
ve çağrı argümanlarını denetlemesini sağlar.
"""

from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import pytest
from PySide6.QtWidgets import QApplication, QDialog, QFileDialog, QInputDialog, QMessageBox


class QtDialogRecord:
    def __init__(
        self,
        kind: str,
        title: str,
        message: str,
        parent: Any = None,
        extra: Optional[Dict[str, Any]] = None,
    ):
        self.kind = kind
        self.title = title
        self.message = message
        self.parent = parent
        self.extra = extra or {}

    def __repr__(self):
        return f"<QtDialogRecord kind={self.kind} title={self.title!r} message={self.message[:30]!r}>"


class QtDialogManager:
    """Testler sırasında diyalog yanıtlarını yöneten ve çağrıları kaydeden kontrolcü."""

    def __init__(self):
        self.records: List[QtDialogRecord] = []
        self._question_response: QMessageBox.StandardButton = QMessageBox.StandardButton.Yes
        self._warning_response: Optional[QMessageBox.StandardButton] = None
        self._critical_response: QMessageBox.StandardButton = QMessageBox.StandardButton.Ok
        self._information_response: QMessageBox.StandardButton = QMessageBox.StandardButton.Ok
        self._dialog_response: QDialog.DialogCode = QDialog.DialogCode.Accepted
        self._file_open_response: Tuple[str, str] = ("", "")
        self._file_save_response: Tuple[str, str] = ("", "")
        self._dir_response: str = ""
        self._input_text_response: Tuple[str, bool] = ("", True)
        self._input_int_response: Tuple[int, bool] = (0, True)
        self._input_item_response: Tuple[str, bool] = ("", True)

    def clear(self):
        self.records.clear()

    # Yanıt değiştirici yardımcı metodlar
    def set_question_response(self, response: QMessageBox.StandardButton):
        self._question_response = response

    def set_warning_response(self, response: Optional[QMessageBox.StandardButton]):
        self._warning_response = response

    def set_dialog_response(self, response: QDialog.DialogCode):
        self._dialog_response = response

    def set_file_open_response(self, path: str, filter_str: str = ""):
        self._file_open_response = (path, filter_str)

    def set_file_save_response(self, path: str, filter_str: str = ""):
        self._file_save_response = (path, filter_str)

    def set_existing_dir_response(self, path: str):
        self._dir_response = path

    def set_input_text_response(self, text: str, ok: bool = True):
        self._input_text_response = (text, ok)

    def set_input_int_response(self, val: int, ok: bool = True):
        self._input_int_response = (val, ok)

    def set_input_item_response(self, item: str, ok: bool = True):
        self._input_item_response = (item, ok)

    # Sorgulama yardımcıları
    def has_message(self, substring: str, kind: Optional[str] = None) -> bool:
        for r in self.records:
            if kind and r.kind != kind:
                continue
            if substring.lower() in r.message.lower() or substring.lower() in r.title.lower():
                return True
        return False

    def last_record(self) -> Optional[QtDialogRecord]:
        return self.records[-1] if self.records else None


@pytest.fixture(scope="session", autouse=True)
def qapp():
    """Tüm oturum için tekil QApplication sağlar."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture(autouse=True)
def mock_qt_dialogs(monkeypatch) -> QtDialogManager:
    """
    Autouse fixture: Test boyunca hiçbir QMessageBox, QDialog.exec,
    QFileDialog veya QInputDialog çağrısının bloklamasına izin vermez.
    """
    manager = QtDialogManager()

    # 1. QMessageBox.information
    def fake_information(parent=None, title="", text="", *args, **kwargs):
        manager.records.append(QtDialogRecord("information", str(title), str(text), parent))
        return manager._information_response

    # 2. QMessageBox.warning (bazı yerlerde onay için Yes|No ile çağrılır)
    def fake_warning(parent=None, title="", text="", buttons=None, defaultButton=None, *args, **kwargs):
        manager.records.append(QtDialogRecord("warning", str(title), str(text), parent, {"buttons": buttons}))
        if manager._warning_response is not None:
            return manager._warning_response
        # Eğer Yes/No butonları varsa varsayılan Yes dön, yoksa Ok dön
        if buttons is not None and (int(buttons) & int(QMessageBox.StandardButton.Yes)):
            return QMessageBox.StandardButton.Yes
        return QMessageBox.StandardButton.Ok

    # 3. QMessageBox.critical
    def fake_critical(parent=None, title="", text="", *args, **kwargs):
        manager.records.append(QtDialogRecord("critical", str(title), str(text), parent))
        return manager._critical_response

    # 4. QMessageBox.question (varsayılan Yes)
    def fake_question(parent=None, title="", text="", buttons=None, defaultButton=None, *args, **kwargs):
        manager.records.append(QtDialogRecord("question", str(title), str(text), parent, {"buttons": buttons}))
        return manager._question_response

    # 5. QMessageBox.about
    def fake_about(parent=None, title="", text="", *args, **kwargs):
        manager.records.append(QtDialogRecord("about", str(title), str(text), parent))
        return None

    monkeypatch.setattr(QMessageBox, "information", fake_information)
    monkeypatch.setattr(QMessageBox, "warning", fake_warning)
    monkeypatch.setattr(QMessageBox, "critical", fake_critical)
    monkeypatch.setattr(QMessageBox, "question", fake_question)
    monkeypatch.setattr(QMessageBox, "about", fake_about)

    # 6. QDialog.exec ve exec_
    def fake_exec(self):
        manager.records.append(QtDialogRecord("dialog_exec", self.__class__.__name__, "", self))
        return manager._dialog_response

    monkeypatch.setattr(QDialog, "exec", fake_exec)
    monkeypatch.setattr(QDialog, "exec_", fake_exec)

    # 7. QFileDialog çağrıları
    def fake_get_open_file_name(parent=None, caption="", dir="", filter="", *args, **kwargs):
        manager.records.append(QtDialogRecord("file_open", str(caption), str(dir), parent, {"filter": filter}))
        return manager._file_open_response

    def fake_get_open_file_names(parent=None, caption="", dir="", filter="", *args, **kwargs):
        manager.records.append(QtDialogRecord("file_open_multiple", str(caption), str(dir), parent, {"filter": filter}))
        return ([manager._file_open_response[0]] if manager._file_open_response[0] else [], manager._file_open_response[1])

    def fake_get_save_file_name(parent=None, caption="", dir="", filter="", *args, **kwargs):
        manager.records.append(QtDialogRecord("file_save", str(caption), str(dir), parent, {"filter": filter}))
        return manager._file_save_response

    def fake_get_existing_directory(parent=None, caption="", dir="", *args, **kwargs):
        manager.records.append(QtDialogRecord("dir_open", str(caption), str(dir), parent))
        return manager._dir_response

    monkeypatch.setattr(QFileDialog, "getOpenFileName", fake_get_open_file_name)
    monkeypatch.setattr(QFileDialog, "getOpenFileNames", fake_get_open_file_names)
    monkeypatch.setattr(QFileDialog, "getSaveFileName", fake_get_save_file_name)
    monkeypatch.setattr(QFileDialog, "getExistingDirectory", fake_get_existing_directory)

    # 8. QInputDialog çağrıları
    def fake_get_text(parent=None, title="", label="", *args, **kwargs):
        manager.records.append(QtDialogRecord("input_text", str(title), str(label), parent))
        return manager._input_text_response

    def fake_get_int(parent=None, title="", label="", *args, **kwargs):
        manager.records.append(QtDialogRecord("input_int", str(title), str(label), parent))
        return manager._input_int_response

    def fake_get_item(parent=None, title="", label="", items=None, *args, **kwargs):
        manager.records.append(QtDialogRecord("input_item", str(title), str(label), parent, {"items": items}))
        return manager._input_item_response

    monkeypatch.setattr(QInputDialog, "getText", fake_get_text)
    monkeypatch.setattr(QInputDialog, "getInt", fake_get_int)
    monkeypatch.setattr(QInputDialog, "getItem", fake_get_item)

    return manager


@pytest.fixture
def dialog_manager(mock_qt_dialogs) -> QtDialogManager:
    """Test fonksiyonlarının manager'a erişebilmesi için doğrudan fixture."""
    return mock_qt_dialogs

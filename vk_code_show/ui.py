from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QEvent, QObject, QTimer, Qt
from PySide6.QtGui import QIcon, QKeyEvent, QKeySequence, QScreen
from PySide6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QComboBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .config import (
    APP_NAME,
    DEFAULT_WINDOW_HEIGHT,
    DEFAULT_WINDOW_WIDTH,
    MAX_HISTORY_ROWS,
    MIN_WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
)
from .key_codes import key_name_for_vk, visible_text
from .models import KeyCapture
from .settings import SettingsStore
from .theme import apply_global_styles
from .ui_scale_overrides import apply_scaled_metrics
from .ui_scale_runtime import resolve_ui_scale_from_screen
from .ui_scale_service import (
    UIScaleState,
    UI_SCALE_DELTA_VALUES,
    normalize_ui_scale_delta_percent,
    scale_px,
)


class KeyEventFilter(QObject):
    def __init__(self, window: "MainWindow") -> None:
        super().__init__(window)
        self._window = window

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.KeyPress and isinstance(event, QKeyEvent):
            active_window = QApplication.activeWindow()
            if active_window is not None and (
                active_window is self._window or self._window.isAncestorOf(active_window)
            ):
                self._window.record_key_event(event)
                return False
        return super().eventFilter(watched, event)


class MainWindow(QMainWindow):
    def __init__(
        self,
        window_icon: QIcon | None = None,
        settings_store: SettingsStore | None = None,
        initial_scale_state: UIScaleState | None = None,
    ) -> None:
        super().__init__()
        self.settings_store = settings_store or SettingsStore()
        self._ui_scale_state = initial_scale_state or resolve_ui_scale_from_screen(
            QApplication.primaryScreen(),
            self.settings_store.get_int("ui_scale_delta_percent", 0),
        )
        self._ui_scale_factor = self._ui_scale_state.scale_factor
        self._ui_scale_screen: QScreen | None = None
        self._ui_scale_app_hooks_installed = False
        self._ui_scale_window_hook_installed = False
        self._key_filter_installed = False

        self.setWindowTitle(APP_NAME)
        if window_icon is not None and not window_icon.isNull():
            self.setWindowIcon(window_icon)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self._last_capture: KeyCapture | None = None
        self._key_filter = KeyEventFilter(self)

        central = QWidget(self)
        central.setObjectName("central")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        header = QLabel(APP_NAME)
        header.setObjectName("header")
        root.addWidget(header)

        self.status_label = QLabel("Окно активно. Нажмите любую клавишу.")
        self.status_label.setObjectName("status")
        root.addWidget(self.status_label)

        root.addWidget(self._build_summary())
        root.addWidget(self._build_scale_group())
        root.addLayout(self._build_controls())
        root.addWidget(self._build_table(), 1)

        self._sync_ui_scale_combo()
        self._apply_window_metrics()
        self._persist_ui_scale_state(save=True)
        self._update_ui_scale_info()
        self._restore_window_settings()

    def show_from_settings(self) -> None:
        if self.settings_store.get("maximized", False):
            self.showMaximized()
        else:
            self.show()

    def showEvent(self, event: QEvent) -> None:
        app = QApplication.instance()
        if app is not None and not self._key_filter_installed:
            app.installEventFilter(self._key_filter)
            self._key_filter_installed = True
        super().showEvent(event)

    def closeEvent(self, event: QEvent) -> None:
        self._save_window_settings()
        app = QApplication.instance()
        if app is not None and self._key_filter_installed:
            app.removeEventFilter(self._key_filter)
            self._key_filter_installed = False
        super().closeEvent(event)

    def changeEvent(self, event: QEvent) -> None:
        if event.type() == QEvent.Type.ActivationChange:
            if self.isActiveWindow():
                self.status_label.setText("Окно активно. Нажмите любую клавишу.")
            else:
                self.status_label.setText(
                    "Окно неактивно. Активируйте его для захвата клавиш."
                )
        super().changeEvent(event)

    def record_key_event(self, event: QKeyEvent) -> None:
        vk_code = int(event.nativeVirtualKey())
        if vk_code <= 0:
            return

        capture = KeyCapture(
            vk_code=vk_code,
            qt_key=int(event.key()),
            scan_code=int(event.nativeScanCode()),
            key_name=key_name_for_vk(vk_code, self._qt_key_text(event)),
            text=visible_text(event.text()),
            modifiers=self._modifier_text(event),
            is_auto_repeat=event.isAutoRepeat(),
        )
        self._last_capture = capture
        self._update_summary(capture)
        self._add_history_row(capture)
        self.status_label.setText("Клавиша захвачена. Выберите строку для копирования VK.")

    def copy_selected_vk(self) -> None:
        self._copy_selected_column(1, "VK скопирован")

    def copy_selected_hex(self) -> None:
        self._copy_selected_column(2, "Hex VK скопирован")

    def copy_latest_vkc_token(self) -> None:
        if self._last_capture is None:
            return
        QApplication.clipboard().setText(self._last_capture.vkc_token)
        self.status_label.setText(f"VKC token скопирован: {self._last_capture.vkc_token}")

    def copy_latest_scan_code(self) -> None:
        if self._last_capture is None:
            return
        QApplication.clipboard().setText(self._last_capture.scan_decimal)
        self.status_label.setText(
            f"Scan code скопирован: {self._last_capture.scan_decimal}"
        )

    def clear_history(self) -> None:
        self.table.setRowCount(0)
        self._last_capture = None
        self.vk_label.setText("-")
        self.hex_label.setText("-")
        self.name_label.setText("-")
        self.text_label.setText("-")
        self.scan_label.setText("-")
        self.vkc_code_label.setText("-")
        self.status_label.setText("История очищена. Нажмите любую клавишу.")
        self.update_copy_buttons()

    def update_copy_buttons(self) -> None:
        has_selection = self.table.currentRow() >= 0
        self.copy_button.setEnabled(has_selection)
        self.copy_hex_button.setEnabled(has_selection)
        has_capture = self._last_capture is not None
        self.copy_latest_vkc_button.setEnabled(has_capture)
        self.copy_latest_scan_button.setEnabled(has_capture)

    def install_ui_scale_hooks(self) -> None:
        app = QApplication.instance()
        if app is not None and not self._ui_scale_app_hooks_installed:
            app.primaryScreenChanged.connect(self.on_ui_scale_topology_changed)
            app.screenAdded.connect(self.on_ui_scale_topology_changed)
            app.screenRemoved.connect(self.on_ui_scale_topology_changed)
            self._ui_scale_app_hooks_installed = True

        window_handle = self.windowHandle()
        if window_handle is not None and not self._ui_scale_window_hook_installed:
            window_handle.screenChanged.connect(self.on_ui_scale_window_screen_changed)
            self._ui_scale_window_hook_installed = True

        self._connect_active_screen_hooks()

    def on_ui_scale_window_screen_changed(self, _screen: QScreen) -> None:
        self._connect_active_screen_hooks()
        self.apply_ui_scale(allow_window_resize=False, reason="screen-changed")

    def on_ui_scale_screen_metrics_changed(self, *_args: object) -> None:
        self.apply_ui_scale(allow_window_resize=False, reason="screen-metrics")

    def on_ui_scale_topology_changed(self, *_args: object) -> None:
        QTimer.singleShot(
            0,
            lambda: self.apply_ui_scale(
                allow_window_resize=False,
                reason="screen-topology",
            ),
        )

    def on_ui_scale_delta_changed(self) -> None:
        delta_percent = normalize_ui_scale_delta_percent(self.ui_scale_combo.currentData())
        self.settings_store.update(
            {"ui_scale_delta_percent": delta_percent},
            save=True,
        )
        self.apply_ui_scale(allow_window_resize=True, reason="manual-delta")

    def apply_ui_scale(self, *, allow_window_resize: bool, reason: str) -> None:
        self._ui_scale_state = resolve_ui_scale_from_screen(
            self._active_screen(),
            self.settings_store.get_int("ui_scale_delta_percent", 0),
        )
        self._ui_scale_factor = self._ui_scale_state.scale_factor
        self._persist_ui_scale_state(save=True)

        app = QApplication.instance()
        if isinstance(app, QApplication):
            apply_global_styles(app, self._ui_scale_factor)

        self._apply_window_metrics()
        self._sync_ui_scale_combo()
        self._update_ui_scale_info()

        if allow_window_resize and not self.isMaximized():
            self._fit_window_to_scaled_minimum()
            self._save_window_settings()

    def get_ui_scale_factor(self) -> float:
        return self._ui_scale_factor

    def _build_summary(self) -> QFrame:
        summary = QFrame()
        summary.setObjectName("summary")
        summary_layout = QHBoxLayout(summary)
        summary_layout.setContentsMargins(0, 0, 0, 0)
        summary_layout.setSpacing(12)

        vk_card = QFrame()
        vk_card.setObjectName("vkCard")
        vk_layout = QVBoxLayout(vk_card)
        vk_layout.setContentsMargins(18, 16, 18, 16)
        vk_layout.setSpacing(8)

        vk_title = QLabel("VK CODE")
        vk_title.setObjectName("vkCardTitle")
        self.vk_label = QLabel("-")
        self.vk_label.setObjectName("vkValue")
        vk_layout.addWidget(vk_title)
        vk_layout.addWidget(self.vk_label)

        vk_details = QGridLayout()
        vk_details.setHorizontalSpacing(18)
        vk_details.setVerticalSpacing(3)
        self.hex_label = QLabel("-")
        self.name_label = QLabel("-")
        self.text_label = QLabel("-")
        vk_details.addWidget(self._caption("Hex"), 0, 0)
        vk_details.addWidget(self._caption("Клавиша"), 0, 1)
        vk_details.addWidget(self._caption("Текст"), 0, 2)
        vk_details.addWidget(self.hex_label, 1, 0)
        vk_details.addWidget(self.name_label, 1, 1)
        vk_details.addWidget(self.text_label, 1, 2)
        vk_details.setColumnStretch(1, 1)
        vk_layout.addLayout(vk_details)
        vk_layout.addStretch(1)

        vk_copy_row = QHBoxLayout()
        vk_copy_row.setSpacing(8)
        self.vkc_code_label = QLabel("-")
        self.vkc_code_label.setObjectName("vkcCode")
        self.copy_latest_vkc_button = QPushButton("Копировать")
        self.copy_latest_vkc_button.setObjectName("copyVkcButton")
        self.copy_latest_vkc_button.setToolTip("Скопировать последний VKC token")
        self.copy_latest_vkc_button.clicked.connect(self.copy_latest_vkc_token)
        self.copy_latest_vkc_button.setEnabled(False)
        vk_copy_row.addWidget(self.vkc_code_label, 1)
        vk_copy_row.addWidget(self.copy_latest_vkc_button)
        vk_layout.addLayout(vk_copy_row)

        scan_card = QFrame()
        scan_card.setObjectName("scanCard")
        scan_layout = QVBoxLayout(scan_card)
        scan_layout.setContentsMargins(18, 16, 18, 16)
        scan_layout.setSpacing(8)

        scan_title = QLabel("SCAN CODE")
        scan_title.setObjectName("scanCardTitle")
        self.scan_label = QLabel("-")
        self.scan_label.setObjectName("scanValue")
        scan_description = QLabel("Физическое положение клавиши на клавиатуре")
        scan_description.setObjectName("scanDescription")
        scan_description.setWordWrap(True)
        scan_layout.addWidget(scan_title)
        scan_layout.addWidget(self.scan_label)
        scan_layout.addWidget(scan_description)
        scan_layout.addStretch(1)

        self.copy_latest_scan_button = QPushButton("Копировать scan code")
        self.copy_latest_scan_button.setObjectName("copyScanButton")
        self.copy_latest_scan_button.setToolTip("Скопировать scan code в десятичном виде")
        self.copy_latest_scan_button.clicked.connect(self.copy_latest_scan_code)
        self.copy_latest_scan_button.setEnabled(False)
        scan_layout.addWidget(self.copy_latest_scan_button)

        summary_layout.addWidget(vk_card, 1)
        summary_layout.addWidget(scan_card, 1)
        return summary

    def _build_scale_group(self) -> QGroupBox:
        group = QGroupBox("Масштаб интерфейса")
        layout = QHBoxLayout(group)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        layout.addWidget(QLabel("Масштаб:"))
        self.ui_scale_combo = QComboBox()
        self.ui_scale_combo.setToolTip("Ручная поправка к автоматическому масштабу")
        for delta_percent in UI_SCALE_DELTA_VALUES:
            self.ui_scale_combo.addItem(f"{100 + delta_percent}%", delta_percent)
        self.ui_scale_combo.currentIndexChanged.connect(self.on_ui_scale_delta_changed)
        layout.addWidget(self.ui_scale_combo)

        self.ui_scale_info_label = QLabel("")
        self.ui_scale_info_label.setObjectName("status")
        layout.addWidget(self.ui_scale_info_label, 1)
        return group

    def _build_controls(self) -> QHBoxLayout:
        controls = QHBoxLayout()
        controls.setSpacing(8)
        self.copy_button = QPushButton("Копировать VK")
        self.copy_button.setToolTip("Скопировать выбранный virtual-key code")
        self.copy_button.clicked.connect(self.copy_selected_vk)
        self.copy_button.setEnabled(False)

        self.copy_hex_button = QPushButton("Копировать Hex")
        self.copy_hex_button.setToolTip("Скопировать выбранный VK в hex-формате")
        self.copy_hex_button.clicked.connect(self.copy_selected_hex)
        self.copy_hex_button.setEnabled(False)

        clear_button = QPushButton("Очистить")
        clear_button.setToolTip("Очистить историю захваченных клавиш")
        clear_button.clicked.connect(self.clear_history)

        controls.addWidget(self.copy_button)
        controls.addWidget(self.copy_hex_button)
        controls.addStretch(1)
        controls.addWidget(clear_button)
        return controls

    def _build_table(self) -> QTableWidget:
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(
            ["Время", "VK", "Hex", "Клавиша", "Текст", "Scan", "Qt key", "Модификаторы"]
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.itemSelectionChanged.connect(self.update_copy_buttons)
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setMinimumSectionSize(72)
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        return self.table

    def _update_summary(self, capture: KeyCapture) -> None:
        self.vk_label.setText(capture.vk_decimal)
        self.hex_label.setText(capture.vk_hex)
        self.name_label.setText(capture.key_name)
        self.text_label.setText(capture.text or "-")
        self.scan_label.setText(capture.scan_display)
        self.vkc_code_label.setText(capture.vkc_token)
        self.copy_latest_scan_button.setEnabled(True)
        self.copy_latest_vkc_button.setEnabled(True)

    def _add_history_row(self, capture: KeyCapture) -> None:
        row = 0
        self.table.insertRow(row)
        values = [
            datetime.now().strftime("%H:%M:%S"),
            capture.vk_decimal,
            capture.vk_hex,
            capture.key_name,
            capture.text,
            capture.scan_display,
            capture.qt_hex,
            self._history_modifier_text(capture),
        ]
        for column, value in enumerate(values):
            item = QTableWidgetItem(value)
            if column in {1, 2, 5, 6}:
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, column, item)

        self.table.selectRow(row)

        if self.table.rowCount() > MAX_HISTORY_ROWS:
            self.table.removeRow(self.table.rowCount() - 1)

    def _copy_selected_column(self, column: int, message: str) -> None:
        row = self.table.currentRow()
        if row < 0:
            return
        item = self.table.item(row, column)
        if item is None:
            return
        QApplication.clipboard().setText(item.text())
        self.status_label.setText(f"{message}: {item.text()}")

    def _modifier_text(self, event: QKeyEvent) -> str:
        modifiers = event.modifiers()
        names: list[str] = []
        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            names.append("Shift")
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            names.append("Ctrl")
        if modifiers & Qt.KeyboardModifier.AltModifier:
            names.append("Alt")
        if modifiers & Qt.KeyboardModifier.MetaModifier:
            names.append("Win")
        return "+".join(names)

    def _qt_key_text(self, event: QKeyEvent) -> str:
        sequence = QKeySequence(event.keyCombination())
        return sequence.toString(QKeySequence.SequenceFormat.NativeText)

    def _history_modifier_text(self, capture: KeyCapture) -> str:
        parts = []
        if capture.modifiers:
            parts.append(capture.modifiers)
        if capture.is_auto_repeat:
            parts.append("повтор")
        return ", ".join(parts)

    def _caption(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setProperty("role", "caption")
        return label

    def _active_screen(self) -> QScreen | None:
        window_handle = self.windowHandle()
        if window_handle is not None and window_handle.screen() is not None:
            return window_handle.screen()
        if self.screen() is not None:
            return self.screen()
        app = QApplication.instance()
        if isinstance(app, QApplication):
            return app.primaryScreen()
        return None

    def _connect_active_screen_hooks(self) -> None:
        screen = self._active_screen()
        if screen is self._ui_scale_screen:
            return

        if self._ui_scale_screen is not None:
            self._disconnect_screen_hooks(self._ui_scale_screen)

        self._ui_scale_screen = screen
        if screen is not None:
            screen.logicalDotsPerInchChanged.connect(self.on_ui_scale_screen_metrics_changed)
            screen.geometryChanged.connect(self.on_ui_scale_screen_metrics_changed)
            screen.availableGeometryChanged.connect(self.on_ui_scale_screen_metrics_changed)

    def _disconnect_screen_hooks(self, screen: QScreen) -> None:
        for signal in (
            screen.logicalDotsPerInchChanged,
            screen.geometryChanged,
            screen.availableGeometryChanged,
        ):
            try:
                signal.disconnect(self.on_ui_scale_screen_metrics_changed)
            except (RuntimeError, TypeError):
                pass

    def _persist_ui_scale_state(self, *, save: bool) -> None:
        self.settings_store.update(
            {
                "ui_scale_mode": "auto",
                "ui_scale_delta_percent": self._ui_scale_state.delta_percent,
                "ui_scale_percent": self._ui_scale_state.final_percent,
            },
            save=save,
        )

    def _sync_ui_scale_combo(self) -> None:
        previous_state = self.ui_scale_combo.blockSignals(True)
        index = self.ui_scale_combo.findData(self._ui_scale_state.delta_percent)
        self.ui_scale_combo.setCurrentIndex(max(0, index))
        self.ui_scale_combo.blockSignals(previous_state)

    def _update_ui_scale_info(self) -> None:
        manual_percent = 100 + self._ui_scale_state.delta_percent
        self.ui_scale_info_label.setText(
            "Авто: "
            f"{self._ui_scale_state.auto_percent}% | "
            f"Поправка: {manual_percent}% | "
            f"Итог: {self._ui_scale_state.final_percent}%"
        )

    def _apply_window_metrics(self) -> None:
        factor = self._ui_scale_factor
        self.table.horizontalHeader().setMinimumSectionSize(scale_px(72, factor))
        self.table.verticalHeader().setDefaultSectionSize(scale_px(38, factor))
        central_widget = self.centralWidget()
        if central_widget is not None:
            apply_scaled_metrics(central_widget, factor)
        self.setMinimumSize(
            scale_px(MIN_WINDOW_WIDTH, factor),
            scale_px(MIN_WINDOW_HEIGHT, factor),
        )

    def _restore_window_settings(self) -> None:
        width = self.settings_store.get_int("window_width", DEFAULT_WINDOW_WIDTH)
        height = self.settings_store.get_int("window_height", DEFAULT_WINDOW_HEIGHT)
        self.resize(width, height)

        pos_x = self.settings_store.get("window_pos_x")
        pos_y = self.settings_store.get("window_pos_y")
        if pos_x is not None and pos_y is not None:
            self.move(int(pos_x), int(pos_y))

    def _fit_window_to_scaled_minimum(self) -> None:
        self.resize(
            max(self.width(), self.minimumWidth()),
            max(self.height(), self.minimumHeight()),
        )

    def _save_window_settings(self) -> None:
        if self.isMaximized():
            self.settings_store.update({"maximized": True}, save=True)
            return

        self.settings_store.update(
            {
                "window_pos_x": self.x(),
                "window_pos_y": self.y(),
                "window_width": self.width(),
                "window_height": self.height(),
                "maximized": False,
            },
            save=True,
        )

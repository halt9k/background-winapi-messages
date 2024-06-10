import win32con
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QWidget, QGroupBox, QTextEdit, QSizePolicy, QGridLayout, QListWidget, \
    QPushButton, QVBoxLayout, QLabel, QLineEdit, QCheckBox, QAbstractItemView, QComboBox, QHBoxLayout, QFrame

# TODO not optimal place to declare
mod_keys = {'LSHIFT': win32con.VK_LSHIFT,
            'LCONTROL': win32con.VK_LCONTROL,
            'LALT': win32con.VK_LMENU,
            'VK_RETURN': win32con.VK_RETURN,
            'VK_TAB': win32con.VK_TAB,}


class CommandWidget(QWidget):
    def __init__(self, parent, name, enabled=True, int_param=None, enum_param=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)

        self.enabled_check = QCheckBox(name, self)
        self.enabled_check.setChecked(enabled)
        self.layout.addWidget(self.enabled_check)

        if int_param:
            self.int_param_edit = QLineEdit(self)
            self.int_param_edit.setMask('\\0\\xHh')
            self.int_param_edit.setText(str(int_param))
            self.layout.addWidget(self.int_param_edit)

        if enum_param:
            self.enum_param_dropdown = QComboBox(self)
            for key, value in enum_param.items():
                self.enum_param_dropdown.addItem(key, value)
            self.layout.addWidget(self.enum_param_dropdown)


class MainWindow(QMainWindow):
    def __init__(self, on_peek_window_under_cursor, on_refresh, on_start_sending, on_window_select, on_guess_char):
        super().__init__()
        self.setWindowTitle("WinApi message test")
        if not self.objectName():
            self.setObjectName(u"QMainWindow")
        self.resize(800, 600)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.window_group = QGroupBox("Select window", self.central_widget)
        self.command_group = QGroupBox("Select messages", self.central_widget)
        self.log_text = QTextEdit(self.central_widget)
        self.log_text.setReadOnly(True)
        self.log_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.main_grid = QGridLayout(self.central_widget)
        self.main_grid.addWidget(self.window_group, 0, 0)
        self.main_grid.addWidget(self.command_group, 0, 1)
        self.main_grid.addWidget(self.log_text, 1, 0, 1, 2, Qt.AlignmentFlag.AlignVCenter)

        # self.window_group.setFrameStyle(QFrame.StyledPanel)
        self.window_listbox = QListWidget(self.window_group)
        self.window_listbox.itemSelectionChanged.connect(on_window_select)
        self.window_listbox.setSelectionMode( QAbstractItemView.SelectionMode.SingleSelection)
        self.pick_windows_button = QPushButton("Pick under cursor", self.window_group)
        self.pick_windows_button.clicked.connect(on_peek_window_under_cursor)
        self.refresh_windows_button = QPushButton("Refresh", self.window_group)
        self.refresh_windows_button.clicked.connect(on_refresh)

        self.window_layout = QVBoxLayout(self.window_group)
        self.window_layout.addWidget(self.window_listbox)
        self.window_layout.addWidget(self.pick_windows_button)
        self.window_layout.addWidget(self.refresh_windows_button)

        # self.command_group.setFrameShape(QFrame.StyledPanel)
        self.command_info = QFrame(self.command_group)
        self.key_label = QLabel("Guess char to keycode:", self.command_info)
        self.key_entry = QLineEdit('', self.command_info)
        self.key_entry.setMaximumWidth(50)
        self.key_entry.setInputMask('x')
        self.key_entry.textChanged.connect(on_guess_char)
        self.code_label = QLabel("", self.command_info)

        self.info_layout = QHBoxLayout(self.command_info)
        self.info_layout.addWidget(self.key_label)
        self.info_layout.addWidget(self.key_entry)
        self.info_layout.addWidget(self.code_label)

        self.send_down_command = CommandWidget(self.command_group, name='SendMessage WM_KEYDOWN', enum_param=mod_keys)
        self.py_keybd_command = CommandWidget(self.command_group, name='keybd_event (down?)', enum_param=mod_keys)
        self.post_down_command = CommandWidget(self.command_group, name='PostMessage WM_KEYDOWN', int_param=65)
        self.post_char_command = CommandWidget(self.command_group, name='PostMessage WM_CHAR', int_param=66)
        self.send_char_command = CommandWidget(self.command_group, name='SendMessage WM_CHAR', int_param=67)
        self.post_up_command = CommandWidget(self.command_group, name='PostMessage WM_KEYUP', int_param=68)
        self.py_keybd_up_command = CommandWidget(self.command_group, name='keybd_event KEYEVENTF_KEYUP', enum_param=mod_keys)
        self.send_up_command = CommandWidget(self.command_group, name='SendMessage WM_KEYUP', enum_param=mod_keys)

        self.send_messages_button = QPushButton("Start Sending", self.command_group)
        self.send_messages_button.clicked.connect(on_start_sending)

        self.command_layout = QVBoxLayout(self.command_group)
        self.command_layout.addWidget(self.command_info)

        self.command_layout.addWidget(self.send_down_command)
        self.command_layout.addWidget(self.py_keybd_command)
        self.command_layout.addWidget(self.post_down_command)
        self.command_layout.addWidget(self.post_char_command)
        self.command_layout.addWidget(self.send_char_command)
        self.command_layout.addWidget(self.post_up_command)
        self.command_layout.addWidget(self.py_keybd_up_command)
        self.command_layout.addWidget(self.send_up_command)

        self.command_layout.addWidget(self.send_messages_button)

        # QMetaObject.connectSlotsByName(self)

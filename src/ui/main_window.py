from PySide6.QtWidgets import QMainWindow, QWidget, QGroupBox, QTextEdit, QSizePolicy, QGridLayout, QListWidget, \
    QPushButton, QVBoxLayout, QLineEdit, QCheckBox, QAbstractItemView, QComboBox, QHBoxLayout

# TODO use patterns Luke
from src.helpers.qt import QComboBoxEx
from src.helpers.qt_async_button import QAsyncButton
from src.messages import EnumArg, message_presets


class CommandWidget(QWidget):
    """ UI entry with checkbox is created for each command like SendMessage """
    def __init__(self, parent, name, cmd, enabled=True, str_param=None, enum_param: EnumArg = None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.enabled_check = QCheckBox(name, self)
        self.enabled_check.setChecked(enabled)

        self.layout.addWidget(self.enabled_check)

        self.cmd = cmd
        # TODO attach model instead?
        self.str_param = str_param
        self.enum_param = enum_param

        if str_param:
            self.str_param_edit = QLineEdit(self)
            self.str_param_edit.setText(str_param)
            self.str_param_edit.setMaximumSize(self.str_param_edit.minimumSizeHint())
            self.layout.addWidget(self.str_param_edit)

        if enum_param:
            self.enum_param_dropdown = QComboBoxEx(self, values=enum_param.named_values,
                                                   default_value=enum_param.value)

            self.enum_param_dropdown.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
            self.layout.addWidget(self.enum_param_dropdown)
            self.layout.setStretchFactor(self.enum_param_dropdown, 2)


class CommandGroup(QGroupBox):
    def __init__(self, text, parent):
        super().__init__(text, parent)
        self.send_messages_button = QAsyncButton(text="Start Sending...", parent=self)

        cmd_widgets = []
        for msg in message_presets:
            name = msg.cmd.__name__
            cmd_widgets += [CommandWidget(self, name=name, cmd=msg.cmd,
                                          str_param=msg.str_arg1, enum_param=msg.enum_arg1)]

        self.command_layout = QVBoxLayout(self)
        for w in cmd_widgets:
            self.command_layout.addWidget(w)

        self.command_layout.addWidget(self.send_messages_button)


class WindowGroup(QGroupBox):
    def __init__(self, text, parent):
        super().__init__(text, parent)

        # self.window_group.setFrameStyle(QFrame.StyledPanel)
        self.window_listbox = QListWidget(self)

        self.window_listbox.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.pick_windows_button = QAsyncButton(text="Pick under cursor...", parent=self)
        self.refresh_windows_button = QPushButton("Refresh", self)

        self.window_layout = QVBoxLayout(self)
        self.window_layout.addWidget(self.window_listbox)
        self.window_layout.addWidget(self.pick_windows_button)
        self.window_layout.addWidget(self.refresh_windows_button)


class CentralWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.window_group = WindowGroup("Select window", self)
        self.command_group = CommandGroup("Select messages", self)

        self.log_text = QTextEdit(self)
        self.log_text.setReadOnly(True)
        # self.log_text.setMinimumHeight(200)

        self.main_grid = QGridLayout(self)
        self.main_grid.addWidget(self.window_group, 0, 0)
        self.main_grid.addWidget(self.command_group, 0, 1)
        self.main_grid.addWidget(self.log_text, 1, 0, 1, 2, )

        self.main_grid.setRowStretch(0, 2)
        self.main_grid.setRowStretch(1, 1)
        self.main_grid.setColumnStretch(0, 3)
        self.main_grid.setColumnStretch(1, 2)

        # self.command_group.setFrameShape(QFrame.StyledPanel)
        '''
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
        # self.command_layout.addWidget(self.command_info)
        '''


class MainWindowFrame(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("WinApi message test")
        if not self.objectName():
            self.setObjectName(u"QMainWindow")
        self.resize(800, 600)

        self.central_widget = CentralWidget(self)
        self.setCentralWidget(self.central_widget)

        # QMetaObject.connectSlotsByName(self)

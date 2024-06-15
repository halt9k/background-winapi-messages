from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QWidget, QGroupBox, QTextEdit, QSizePolicy, QGridLayout, QListWidget, \
    QPushButton, QVBoxLayout, QLabel, QLineEdit, QCheckBox, QAbstractItemView, QComboBox, QHBoxLayout, QFrame, \
    QAbstractScrollArea

# TODO use patterns Luke
from src.messages import EnumArg


class CommandWidget(QWidget):
    def __init__(self, parent, name, cmd, enabled=True, str_param=None, enum_param: EnumArg = None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.enabled_check = QCheckBox(name, self)
        self.enabled_check.setChecked(enabled)

        self.layout.addWidget(self.enabled_check)

        self.cmd = cmd
        self.str_param = str_param
        self.enum_param = enum_param

        if str_param:
            self.str_param_edit = QLineEdit(self)
            self.str_param_edit.setText(str_param)
            self.str_param_edit.setMaximumSize(self.str_param_edit.minimumSizeHint())
            self.layout.addWidget(self.str_param_edit)

        if enum_param:
            self.enum_param_dropdown = QComboBox(self)

            cur_index = None
            for i, (key, value) in enumerate(enum_param.named_values):
                self.enum_param_dropdown.addItem(key, value)
                if value == enum_param.value:
                    cur_index = i
            if cur_index:
                self.enum_param_dropdown.setCurrentIndex(cur_index)

            self.enum_param_dropdown.setMinimumContentsLength(5)
            self.enum_param_dropdown.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
            self.enum_param_dropdown.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
            self.layout.addWidget(self.enum_param_dropdown)
            self.layout.setStretchFactor(self.enum_param_dropdown, 2)


class CommandGroup(QGroupBox):
    def __init__(self, text, parent, custom_messages, on_start_sending):
        super().__init__(text, parent)
        self.send_messages_button = QPushButton("Start Sending...", self)
        self.send_messages_button.clicked.connect(on_start_sending)

        cmd_widgets = []
        for msg in custom_messages:
            name = msg[0].__name__
            enum_param = None
            str_param = None
            for arg in msg[1: len(msg)]:
                if type(arg) is str:
                    str_param = arg
                if type(arg) is EnumArg:
                    enum_param = arg
            cmd_widgets += [CommandWidget(self, name=name, cmd=msg[0], str_param=str_param, enum_param=enum_param)]

        self.command_layout = QVBoxLayout(self)
        for w in cmd_widgets:

            self.command_layout.addWidget(w)

        self.command_layout.addWidget(self.send_messages_button)


class WindowGroup(QGroupBox):
    def __init__(self, text, parent, on_window_select, on_peek_window_under_cursor, on_refresh):
        super().__init__(text, parent)

        # self.window_group.setFrameStyle(QFrame.StyledPanel)
        self.window_listbox = QListWidget(self)
        self.window_listbox.itemSelectionChanged.connect(on_window_select)
        self.window_listbox.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.pick_windows_button = QPushButton("Pick under cursor...", self)
        self.pick_windows_button.clicked.connect(on_peek_window_under_cursor)
        self.refresh_windows_button = QPushButton("Refresh", self)
        self.refresh_windows_button.clicked.connect(on_refresh)

        self.window_layout = QVBoxLayout(self)
        self.window_layout.addWidget(self.window_listbox)
        self.window_layout.addWidget(self.pick_windows_button)
        self.window_layout.addWidget(self.refresh_windows_button)


class CentralWidget(QWidget):
    def __init__(self, parent, on_peek_window_under_cursor, on_refresh, on_start_sending, on_window_select,
                 on_guess_char, custom_messages):
        super().__init__(parent)
        self.window_group = WindowGroup("Select window", self,
                                        on_window_select, on_peek_window_under_cursor, on_refresh)
        self.command_group = CommandGroup("Select messages", self, custom_messages, on_start_sending)

        self.log_text = QTextEdit(self)
        self.log_text.setReadOnly(True)
        # self.log_text.setMinimumHeight(200)

        self.main_grid = QGridLayout(self)
        self.main_grid.addWidget(self.window_group, 0, 0)
        self.main_grid.addWidget(self.command_group, 0, 1)
        self.main_grid.addWidget(self.log_text, 1, 0, 1, 2, )

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


class MainWindow(QMainWindow):
    def __init__(self, *args):
        super().__init__()

        self.setWindowTitle("WinApi message test")
        if not self.objectName():
            self.setObjectName(u"QMainWindow")
        self.resize(800, 600)

        self.central_widget = CentralWidget(self, *args)
        self.setCentralWidget(self.central_widget)

        # QMetaObject.connectSlotsByName(self)

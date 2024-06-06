from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QWidget, QGroupBox, QTextEdit, QSizePolicy, QGridLayout, QListWidget, \
    QPushButton, QVBoxLayout, QLabel, QLineEdit, QCheckBox, QAbstractItemView


class MainWindow(QMainWindow):
    def __init__(self, peek_window_under_cursor, on_refresh, start_sending, on_window_select):
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
        self.peek_window_button = QPushButton("Peek under cursor", self.window_group)
        self.peek_window_button.clicked.connect(peek_window_under_cursor)
        self.refresh_windows_button = QPushButton("Refresh", self.window_group)
        self.refresh_windows_button.clicked.connect(on_refresh)

        self.window_layout = QVBoxLayout(self.window_group)
        self.window_layout.addWidget(self.window_listbox)
        self.window_layout.addWidget(self.peek_window_button)
        self.window_layout.addWidget(self.refresh_windows_button)

        # self.command_group.setFrameShape(QFrame.StyledPanel)
        self.key_label = QLabel("Enter Key (Hex):", self.command_group)
        self.key_entry = QLineEdit(self.command_group)
        self.keydown_check = QCheckBox("Key Down", self.command_group)
        self.keydown_check.setChecked(True)
        self.keyup_check = QCheckBox("Key Up", self.command_group)
        self.start_sending_button = QPushButton("Start Sending", self.command_group)
        self.start_sending_button.clicked.connect(start_sending)

        self.command_layout = QVBoxLayout(self.command_group)
        self.command_layout.addWidget(self.key_label)
        self.command_layout.addWidget(self.key_entry)
        self.command_layout.addWidget(self.keydown_check)
        self.command_layout.addWidget(self.keyup_check)
        self.command_layout.addWidget(self.start_sending_button)

        # QMetaObject.connectSlotsByName(self)
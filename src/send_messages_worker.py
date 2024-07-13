from dataclasses import dataclass
from typing import List

from PySide6.QtCore import Slot, QThread, Signal

from lib.qt.qt import q_info
from lib.qt.qt_async_button import QWorker
from lib.qt.qt_n_timer import QNTimer
from src.helpers.virtual_methods import override
from src.messages import run_test_message, WinMsg


@dataclass(init=True)
class SendData:
    hwnds: List[int]
    messages: List[WinMsg]


# TODO something locks
class SendMessagesWorker(QWorker):
    # non threaded QTimer is better option for this specific task,
    # but thread template may be handy for future extensions,
    # since this is also sandbox for Qt hwnd experiments

    request_send_data = Signal()

    def __init__(self):
        super(SendMessagesWorker, self).__init__()
        self.request_timer = QNTimer(self)
        # continue_loops() can be attached to request or to send, affects who ensures QWorker.finished()
        # TODO signal mismatch - source of crash?
        self.request_timer.timeout_n.connect(self.request_send_data)
        self.request_timer.finished.connect(self.finished)

    @staticmethod
    def send_messages(data: SendData):
        if len(data.hwnds) < 1:
            q_info(f'\nNo hwnds selected, send canceled.\n')
            return
        else:
            q_info(f'\nTrying to send to hwnds: {data.hwnds}')

        # key_override_str = self.ui.key_entry.text()
        # key_hex = int(key_override_str, 16) if key_override_str else None
        for hwnd in data.hwnds:
            for msg in data.messages:
                run_test_message(hwnd, msg)
                q_info(f"{msg}")
                QThread.msleep(20)

    @Slot()
    def on_recieve_data(self, data: SendData):
        """
        This worker requires UI data to start WinApi messages,
        UI data better to be recieved on Slot to avoid interthreaded UI ascess,
        this function recieves UI data
        """
        with self.request_timer.qntimer_timeout_guard():
            self.send_messages(data)

    @Slot()
    @override
    def on_run(self):
        q_info(f"Next 10s sending messages to background selected window or \n"
               f"try to switch window to test foreground send")
        self.request_timer.start(loop_n=2, interval_msec=100)

    @Slot()
    @override
    def on_finished(self):
        q_info(f"Send over")

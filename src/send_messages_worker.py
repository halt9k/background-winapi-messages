from dataclasses import dataclass
from typing import List

from PySide6.QtCore import Slot, QThread, Signal, qWarning

from lib.qt.qt import q_info
from lib.qt.qt_async_button import QWorker
from lib.qt.qt_n_timer import QNTimer
from src.helpers.virtual_methods import override
from src.messages import run_test_message, WinMsg


@dataclass(init=True)
class SendData:
    hwnds: List[int]
    messages: List[WinMsg]


class SendMessagesWorker(QWorker):
    # non threaded QTimer is better option for this specific task,
    # but thread template may be handy for future extensions,
    # since this is also sandbox for Qt hwnd experiments

    request_send_data = Signal(int)

    def __init__(self):
        super(SendMessagesWorker, self).__init__()
        self.request_timer = QNTimer(self)

        # qntimer_timeout_guard() can be attached to request_send_data or to on_recieve_data,
        # affects who ensures QWorker.finished()
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
                QThread.msleep(150)

    @Slot()
    def on_recieve_data(self, data: SendData):
        """
        This worker requires UI data to start WinApi messages,
        UI data better to be recieved on Slot to avoid interthreaded UI ascess,
        this function recieves UI data
        """
        try:
            with self.request_timer.qntimer_timeout_guard():
                self.send_messages(data)
        except (RuntimeWarning) as e:
            qWarning(str(e))

    @Slot()
    @override
    def on_run(self):
        q_info(f"Next 10s sending messages to background selected window or \n"
               f"try to switch window to test foreground send")
        self.request_timer.start(loop_n=20, interval_msec=1000)

    @Slot()
    @override
    def on_finished(self):
        q_info(f"Send over")

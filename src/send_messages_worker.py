from dataclasses import dataclass
from typing import List, Optional

from PySide6.QtCore import Slot, QThread, Signal, QTimer

from src.helpers.python_extensions import catch_exceptions, context_switch
from src.helpers.qt import Logger, QNTimer, qntimer_timeout_slot
from src.helpers.qt_async_button import QWorker
from src.helpers.virtual_methods import override
from src.messages import run_test_message, WinMsg, EnumArg


@dataclass(init=True)
class SendData:
    hwnds: List[int]
    messages: List[WinMsg]


class SendMessagesWorker(QWorker):
    # non threaded QTimer is better option for this specific task,
    # but thread template may be handy for future extensions,
    # since this is also sandbox for Qt hwnd experiments

    request_send_data = Signal()

    def __init__(self):
        super(SendMessagesWorker, self).__init__()
        self.request_timer = QNTimer(parent=self)
        # continue_loops() can be attached to request or to send, affects who ensures QWorker.finished()
        self.request_timer.timeout_n.connect(self.request_send_data)
        self.request_timer.finished.connect(self.finished)

    def send_messages(self, data: SendData):
        if len(data.hwnds) < 1:
            Logger.log(f'\nNo hwnds selected, send canceled.\n')
            return
        else:
            Logger.log(f'\nTrying to send to hwnds: {data.hwnds}')

        # key_override_str = self.ui.key_entry.text()
        # key_hex = int(key_override_str, 16) if key_override_str else None
        for hwnd in data.hwnds:
            for msg in data.messages:
                run_test_message(hwnd, msg)
                Logger.log(f"{msg}")
                QThread.msleep(200)

    @Slot()
    def on_recieve_data(self, data: SendData):
        """
        This worker requires UI data to start WinApi messages,
        UI data better to be recieved on Slot to avoid interthreaded UI ascess,
        this function recieves UI data
        """
        try:
            self.send_messages(data)
        except:
            self.request_timer.stop()
            self.finished.emit()
            raise

        self.request_timer.continue_loop()

    @Slot()
    @override
    def on_run(self):
        Logger.log(f"Next 10s sending messages to background selected window or \n"
                   f"try to switch window to test foreground send")
        self.request_timer.start(repeats=10, interval_msec=1000)

    @Slot()
    @override
    def on_finished(self):
        Logger.log(f"Send over")

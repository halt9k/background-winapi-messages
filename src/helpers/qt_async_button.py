from abc import abstractmethod
from typing import Callable

import pydevd
from PySide6.QtCore import QThread, Slot, QObject, Signal, QDeadlineTimer
from PySide6.QtWidgets import QPushButton


class QWorker(QObject):
    finished = Signal()

    @abstractmethod
    def on_run(self):
        raise NotImplementedError

    @Slot()
    def run(self):
        pydevd.settrace(suspend=False)
        try:
            self.on_run()
        finally:
            self.finished.emit()


class QAsyncButton(QPushButton):
    """
    This was intended as a button which spawns separate thread for experiments.
    Remember not to interact directly with UI in spawned threads.
    Even win32gui.GetWindowText(main_hwnd) can deadlock if called while thread termination is waited.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.contexts = []
        self.on_get_sync_contexts = None

        self.on_before_worker = None
        self.on_after_worker = None

        self.thread = QThread()
        close_event = self.window().close_event
        if close_event:
            self.window().close_event.connect(self.on_close)
        else:
            print("QAsyncButton needs to know when MainWindow is closed to terminate thread if it works.\n"
                  "Propagate a signal from QMainWindow.closeEvent() for this.")

        self.clicked.connect(self.on_clicked)
        self.worker = None

    @Slot()
    def on_close(self):
        if self.thread.isRunning():
            self.thread.quit()
            deadline = QDeadlineTimer(500)
            self.thread.wait(deadline)
            if deadline.hasExpired():
                print("Warning: thread did not quit fluently and will be terminated.\n"
                      "This is expected if WinApi calls on QMainWindow are used, which may deadlock wait().\n"
                      "Proper and easier way is QTimer, but this example deliberately experimented with QAsyncButton.\n"
                      "Another option is to use QApplication.aboutToExit() instead of QMainWindow.closeEvent(),\n"
                      "but closeEvent() better couples lifetime of thread and button.")
                self.thread.terminate()

    def on_before_thread(self):
        self.setEnabled(False)

        self.enter_contexts()
        if self.on_before_worker:
            self.on_before_worker()

    @Slot()
    def on_after_thread(self):
        self.setEnabled(True)

        if self.on_after_worker:
            self.on_after_worker()
        self.exit_contexts()

    @Slot()
    def on_clicked(self) -> None:
        assert self.worker

        self.on_before_thread()
        self.thread.finished.connect(self.on_after_thread)

        self.thread.start()

    def attach_worker(self, worker: QWorker, on_get_sync_contexts=None,
                      on_before_worker: Callable = None,
                      on_after_worker: Callable = None):
        """
        sync_contexts: will wrap worker.run() and are called in caller thread, not in the worker
        on_before_worker, on_after_worker: similar to contexts if only one is required
        """
        self.worker = worker
        self.worker.moveToThread(self.thread)

        self.on_get_sync_contexts = on_get_sync_contexts
        self.on_before_worker = on_before_worker
        self.on_after_worker = on_after_worker

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)

    def exit_contexts(self):
        for c in reversed(self.contexts):
            # propagate errors?
            c.__exit__(None, None, None)
        self.contexts = []

    def enter_contexts(self):
        self.contexts = self.on_get_sync_contexts() if self.on_get_sync_contexts else []
        for c in self.contexts:
            c.__enter__()

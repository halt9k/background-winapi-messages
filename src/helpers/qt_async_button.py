from abc import abstractmethod
from typing import Callable

import pydevd
from PySide6.QtCore import QThread, Slot, QObject, Signal, QDeadlineTimer, QEvent
from PySide6.QtWidgets import QPushButton
from typing_extensions import override
from src.helpers.qt import Logger, QTracedThread
from src.helpers.virtual_methods import virutalmethod


class QWorker(QObject):
    finished = Signal()

    def __init__(self):
        super(QWorker, self).__init__()
        self.finished.connect(self.on_finished)

    @abstractmethod
    def on_run(self):
        raise NotImplementedError

    @Slot()
    def run(self):
        pydevd.settrace(suspend=False)

        try:
            self.on_run()
        except:
            self.finished.emit()
            raise

    @virutalmethod
    def on_finished(self):
        pass


'''
class QReusableWorker(QObject):
    """ 
    A draft of reusable which is expected to have same lifetime with button, 
    and moved into new thread before QReusableWorker.run() 
    and back on QReusableWorker.finished()
    no destructions, but extra thread spam. Unfinished draft. 
    """
     
    finished = Signal()

    def __init__(self):
        super().__init__()
        self.original_thread = QTracedThread.currentThread()

    @abstractmethod
    def on_run(self):
        raise NotImplementedError

    @Slot()
    def run(self):
        pydevd.settrace(suspend=False)
        

        # Worker is not expected to branch own thread, but can ensure
        assert self.original_thread != QThread.currentThread()

        try:
            self.on_run()
        except:
            self.finished.emit()
            
    def on_finished(self):
        self.moveToThread(self.original_thread)
'''

THREAD_QUIT_DEADLINE_MS = 500
THREAD_TERMINATION_DEADLINE_MS = 5000


def quit_or_terminate_qthread(thread: QThread):
    assert thread != QThread.currentThread()

    if not thread.isRunning():
        return

    thread.quit()
    deadline = QDeadlineTimer(THREAD_QUIT_DEADLINE_MS)
    thread.wait(deadline)
    if not thread.isRunning():
        return

    print("Warning: thread did not quit fluently, termination attempt scheduled.\n"
          "This is expected, for example, if: \n"
          " -sleep is used"
          " -WinApi calls on QMainWindow may deadlock wait() during closeEvent().\n"
          "Proper way is QTimer instead of sleep(), but it may overcomlicate some cases.\n"
          "Another option is to use QApplication.aboutToExit() instead of QMainWindow.closeEvent(),\n"
          "but closeEvent() better couples lifetime of thread and button.")
    thread.terminate()
    deadline = QDeadlineTimer(THREAD_TERMINATION_DEADLINE_MS)
    thread.wait(deadline)

    if thread.isRunning():
        print(f"Thread termination in {THREAD_TERMINATION_DEADLINE_MS}ms failed. Python crash expected.")


class QAsyncButton(QPushButton):
    """
    This was intended as a button which spawns separate thread for experiments.
    Remember not to interact directly with UI in spawned threads.
    Even win32gui.GetWindowText(main_hwnd) can deadlock if called while thread termination is waited.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.contexts = []
        self.create_sync_contexts = None
        self.create_worker = None

        self.on_before_worker = None
        self.on_after_worker = None

        self.ui_thread = QThread.currentThread()
        self.thread = QTracedThread()

        close_event = self.window().close_event
        if close_event:
            self.window().close_event.connect(self.on_close)
        else:
            print("QAsyncButton needs to know when MainWindow is closed to terminate thread if it works.\n"
                  "Propagate a signal from QMainWindow.closeEvent() for this.")

        self.clicked.connect(self.on_start_worker)
        self.thread.finished.connect(self.on_after_thread)
        self.worker = None

    @Slot()
    def on_close(self):
        if self.worker:
            self.on_worker_finished()
        quit_or_terminate_qthread(self.thread)

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
    def on_start_worker(self):
        assert self.ui_thread == QThread.currentThread()
        assert self.worker is None

        self.worker = self.create_worker()
        self.worker.moveToThread(self.thread)

        # worker quits as expected
        self.worker.finished.connect(self.on_worker_finished)
        # thread terminated externally, for example, when main window closed
        self.thread.finished.connect(self.on_worker_finished)

        self.thread.started.connect(self.worker.run)

        self.on_before_thread()
        self.thread.start()

    @Slot()
    def on_worker_finished(self):
        if self.worker:
            self.worker.moveToThread(self.ui_thread)
            self.worker = None
        quit_or_terminate_qthread(self.thread)

    def attach_worker(self, create_worker: Callable[[], QWorker], create_sync_contexts=None,
                      on_before_worker: Callable = None,
                      on_after_worker: Callable = None):
        """
        create_worker: factory function because on each button press a new worker must be created
        sync_contexts, on_before_worker, on_after_worker: optionals, will wrap worker.run() in UI thread
        """
        self.create_worker = create_worker
        self.create_sync_contexts = create_sync_contexts
        self.on_before_worker = on_before_worker
        self.on_after_worker = on_after_worker

    def exit_contexts(self):
        for c in reversed(self.contexts):
            # propagate errors?
            c.__exit__(None, None, None)
        self.contexts = []

    def enter_contexts(self):
        self.contexts = self.create_sync_contexts() if self.create_sync_contexts else []
        for c in self.contexts:
            c.__enter__()

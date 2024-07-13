import sys
import threading
from abc import abstractmethod

import pydevd
from PySide6.QtCore import QThread, QObject, Signal, Slot, QDeadlineTimer, qWarning, QMutex, QMutexLocker, \
    qInstallMessageHandler, qDebug, qCritical
from typing_extensions import override

from src.helpers.virtual_methods import virutalmethod


class QTracedThread(QThread):
    QUIT_DEADLINE_MS = 500
    TERMINATION_DEADLINE_MS = 5000

    @override
    def run(self):
        # controls timer events tracing even when worker is used
        pydevd.settrace(suspend=False)

        qDebug('QTracedThread.run')
        super().run()

    @staticmethod
    def quit_or_terminate_qthread(thread: QThread):
        assert thread != QThread.currentThread()

        if not thread.isRunning():
            return
        thread.quit()

        deadline = QDeadlineTimer(QTracedThread.QUIT_DEADLINE_MS)
        if thread.wait(deadline):
            return
        qWarning(f"Warning: thread quit takes more than {QTracedThread.QUIT_DEADLINE_MS}ms.\n")

        deadline = QDeadlineTimer(QTracedThread.TERMINATION_DEADLINE_MS)
        if thread.wait(deadline):
            return

        # Also consider QApplication.aboutToExit() instead of QMainWindow.closeEvent(),
        # but closeEvent() better couples lifetime of thread and button.
        # Also consider QTimer instead of sleep(), but it may overcomlicate some cases.
        qCritical(f"Error: thread quit took more than {QTracedThread.TERMINATION_DEADLINE_MS}, "
               "crash on termination attempt is expected. Possible reasons: \n"
               " - sleep() is used in the thread"
               " - WinApi calls on QMainWindow may deadlock wait() during closeEvent()\n")
        thread.terminate()

        if thread.isRunning():
            raise TimeoutError(f"Thread termination has failed.")


class QWorker(QObject):
    finished = Signal()
    started = Signal()

    def __init__(self, *args, **kwargs):
        super(QWorker, self).__init__(*args, **kwargs)
        # self.on_finished better before other connections, therefore in __init__, not on_run
        self.finished.connect(self.on_finished)

    @abstractmethod
    def on_run(self):
        raise NotImplementedError

    @Slot()
    def run(self):
        # was nessesary for QTimer events traced and possibly for others
        pydevd.settrace(suspend=False)
        qDebug('QWorker.run')

        try:
            self.started.emit()
            self.on_run()
        except:
            self.finished.emit()
            raise

    @Slot()
    @virutalmethod
    def on_finished(self):
        pass


'''
class QReusableWorker(QObject):
    """ 
    A draft of reusable which is expected to have same lifetime with button, 
    and moved into new thread before QReusableWorker.run() 
    and back on QReusableWorker.finished().
    No destructions, but extra thread spammed during button lifetime. 
    Unfinished draft. 
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


class QSafeThreadedPrint:
    """ Redirects qDebug, qWarning, etc to output """
    mutex = QMutex()

    @staticmethod
    def log_handler(mode, context, msg):
        deb_at = sys.gettrace() is not None
        with QMutexLocker(QSafeThreadedPrint.mutex):
            print(f"{threading.current_thread().name:>10}    Debug: {deb_at}     {msg}")

    @staticmethod
    def print_qt_in_ouput():
        qInstallMessageHandler(QSafeThreadedPrint.log_handler)

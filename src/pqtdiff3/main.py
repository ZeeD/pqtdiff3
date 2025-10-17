from sys import argv
from typing import override

from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import QEvent
from PySide6.QtCore import QObject
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QApplication

from pqtdiff3.ui import PQtDiff3
from pqtdiff3.ui import pqtdiff3
from pqtdiff3.ui import reload


class F5EventFilter(QObject):
    widget: PQtDiff3 | None = None

    @override
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if (
            isinstance(event, QKeyEvent)
            and event.type() == QEvent.Type.KeyPress
            and event == QKeySequence.StandardKey.Refresh
            and self.widget is not None
        ):
            reload(self.widget)
            return True
        return super().eventFilter(watched, event)


def main() -> None:
    QCoreApplication.setAttribute(
        Qt.ApplicationAttribute.AA_ShareOpenGLContexts
    )
    app = QApplication(argv)

    f5_event_filter = F5EventFilter()
    app.installEventFilter(f5_event_filter)
    widget = pqtdiff3(app)
    f5_event_filter.widget = widget
    widget.show()

    raise SystemExit(app.exec())

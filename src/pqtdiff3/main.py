from sys import argv

from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from pqtdiff3.ui import pqtdiff3


def main() -> None:
    QCoreApplication.setAttribute(
        Qt.ApplicationAttribute.AA_ShareOpenGLContexts
    )
    app = QApplication(argv)

    widget = pqtdiff3(app)
    widget.show()

    raise SystemExit(app.exec())

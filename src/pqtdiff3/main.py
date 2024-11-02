from enum import Enum
from enum import auto
from pathlib import Path
from sys import argv
from typing import TYPE_CHECKING
from typing import cast

from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import Qt
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication
from PySide6.QtWidgets import QLineEdit
from PySide6.QtWidgets import QTextBrowser
from PySide6.QtWidgets import QWidget

if TYPE_CHECKING:
    from collections.abc import Iterator


def _resource(filename: str) -> Path:
    return Path(__file__).with_name(filename)


class PQtDiff3(QWidget):
    line_edit_old: QLineEdit
    text_browser_old: QTextBrowser
    line_edit_add: QLineEdit
    text_browser_add: QTextBrowser
    line_edit_acc: QLineEdit
    text_browser_acc: QTextBrowser


class Common(Enum):
    all = auto()
    old_add = auto()
    old_acc = auto()
    add_acc = auto()
    none = auto()


def diff3(
    old_lines: list[str], add_lines: list[str], acc_lines: list[str]
) -> list[Common]:
    old_itor = iter(old_lines)
    add_itor = iter(add_lines)
    acc_itor = iter(acc_lines)

    def gen() -> 'Iterator[Common]':
        old = next(old_itor, None)
        add = next(add_itor, None)
        acc = next(acc_itor, None)
        while old or add or acc:
            if old == add:
                if old == acc:
                    yield Common.all
                    old = next(old_itor, None)
                    add = next(add_itor, None)
                    acc = next(acc_itor, None)
                else:
                    yield Common.old_add
                    old = next(old_itor, None)
                    add = next(add_itor, None)
            elif old == acc:
                yield Common.old_acc
                old = next(old_itor, None)
                acc = next(acc_itor, None)
            elif add == acc:
                yield Common.add_acc
                add = next(add_itor, None)
                acc = next(acc_itor, None)
            else:
                yield Common.none
                old = next(old_itor, None)
                add = next(add_itor, None)
                acc = next(acc_itor, None)

    return list(gen())


def html(lines: list[str], commons: list[Common], selected: set[Common]) -> str:
    colors: dict[Common, str] = {
        Common.all: 'lightgreen',
        Common.old_add: 'lightred',
        Common.old_acc: 'lightblue',
        Common.add_acc: 'lightcyan',
        Common.none: 'black',
    }

    def gen() -> 'Iterator[str]':
        for line, color in zip(
            lines, (colors[c] for c in commons if c in selected), strict=True
        ):
            yield f'<pre style="background-color: {color}">{line}</pre>'

    return (
        """<html><head><style>* { margin: 0 }</style></head><body>"""
        + ''.join(gen())
        + '</body></html>'
    )


def get_p_qt_diff3(old: Path, add: Path, acc: Path) -> PQtDiff3:
    p_qt_diff3 = cast(PQtDiff3, QUiLoader().load(_resource('pqtdiff3.ui')))
    p_qt_diff3.line_edit_old.setText(str(old))
    p_qt_diff3.line_edit_add.setText(str(add))
    p_qt_diff3.line_edit_acc.setText(str(acc))

    old_lines = old.read_text().splitlines(keepends=True)
    add_lines = add.read_text().splitlines(keepends=True)
    acc_lines = acc.read_text().splitlines(keepends=True)

    common_lines = diff3(old_lines, add_lines, acc_lines)

    p_qt_diff3.text_browser_old.setHtml(
        html(
            old_lines,
            common_lines,
            {Common.all, Common.old_add, Common.old_acc},
        )
    )
    p_qt_diff3.text_browser_add.setHtml(
        html(
            add_lines,
            common_lines,
            {Common.all, Common.old_add, Common.add_acc},
        )
    )
    p_qt_diff3.text_browser_acc.setHtml(
        html(
            acc_lines,
            common_lines,
            {Common.all, Common.old_acc, Common.add_acc},
        )
    )

    return p_qt_diff3


def main() -> None:
    QCoreApplication.setAttribute(
        Qt.ApplicationAttribute.AA_ShareOpenGLContexts
    )
    app = QApplication(argv)

    orig, new, merged = (Path(arg) for arg in app.arguments()[1:])

    p_qt_diff3 = get_p_qt_diff3(orig, new, merged)
    p_qt_diff3.show()

    raise SystemExit(app.exec())

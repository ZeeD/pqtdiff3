from difflib import SequenceMatcher
from enum import Enum
from enum import auto
from itertools import permutations
from pathlib import Path
from sys import argv
from typing import TYPE_CHECKING
from typing import Protocol
from typing import cast

from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import Qt
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication
from PySide6.QtWidgets import QLineEdit
from PySide6.QtWidgets import QScrollBar
from PySide6.QtWidgets import QTextBrowser

if TYPE_CHECKING:
    from collections.abc import Iterable
    from collections.abc import Iterator


def _resource(filename: str) -> Path:
    return Path(__file__).with_name(filename)


class PQtDiff3(Protocol):
    line_edit_old: QLineEdit
    text_browser_old: QTextBrowser
    line_edit_add: QLineEdit
    text_browser_add: QTextBrowser
    line_edit_acc: QLineEdit
    text_browser_acc: QTextBrowser

    def show(self) -> None: ...


class Common(Enum):
    all = auto()
    old_add = auto()
    old_acc = auto()
    add_acc = auto()
    none = auto()


def html(lines: list[str], commons: list[Common]) -> str:
    colors: dict[Common, str] = {
        Common.all: 'lightgreen',
        Common.old_add: 'lightyellow',
        Common.old_acc: 'lightcoral',
        Common.add_acc: 'lightsteelblue',
        Common.none: 'lightgray',
    }

    def gen() -> 'Iterator[str]':
        for line, color in zip(
            lines, (colors[c] for c in commons), strict=True
        ):
            yield f'<pre style="background-color: {color}">{line}</pre>'

    return (
        """<html><head><style>* { margin: 0 }</style></head><body>"""
        + ''.join(gen())
        + '</body></html>'
    )


def get_commons(
    a: list[str], bs: list[list[str]], cfps: list[Common]
) -> list[Common]:
    matching_blockss = [
        SequenceMatcher(a=a, b=b, autojunk=False).get_matching_blocks()
        for b in bs
    ]

    commons = [Common.none for _ in a]
    for matching_blocks, cfp in zip(matching_blockss, cfps, strict=True):
        for i, _, n in matching_blocks:
            for j in range(i, i + n):
                if commons[j] is Common.none:
                    commons[j] = cfp
                else:  # old_acc
                    commons[j] = Common.all
    return commons


def bind_scroll_bars(scroll_bars: 'Iterable[QScrollBar]') -> None:
    for sb1, sb2 in permutations(scroll_bars, 2):
        sb1.valueChanged.connect(sb2.setValue)


def get_p_qt_diff3(old: Path, add: Path, acc: Path) -> PQtDiff3:
    p_qt_diff3 = cast(PQtDiff3, QUiLoader().load(_resource('pqtdiff3.ui')))

    bind_scroll_bars(
        tb.verticalScrollBar()
        for tb in [
            p_qt_diff3.text_browser_old,
            p_qt_diff3.text_browser_add,
            p_qt_diff3.text_browser_acc,
        ]
    )
    bind_scroll_bars(
        tb.horizontalScrollBar()
        for tb in [
            p_qt_diff3.text_browser_old,
            p_qt_diff3.text_browser_add,
            p_qt_diff3.text_browser_acc,
        ]
    )

    p_qt_diff3.line_edit_old.setText(str(old))
    p_qt_diff3.line_edit_add.setText(str(add))
    p_qt_diff3.line_edit_acc.setText(str(acc))

    old_lines = old.read_text().splitlines()
    add_lines = add.read_text().splitlines()
    acc_lines = acc.read_text().splitlines()

    p_qt_diff3.text_browser_old.setHtml(
        html(
            old_lines,
            get_commons(
                old_lines,
                [add_lines, acc_lines],
                [Common.old_add, Common.old_acc],
            ),
        )
    )
    p_qt_diff3.text_browser_add.setHtml(
        html(
            add_lines,
            get_commons(
                add_lines,
                [old_lines, acc_lines],
                [Common.old_add, Common.add_acc],
            ),
        )
    )
    p_qt_diff3.text_browser_acc.setHtml(
        html(
            acc_lines,
            get_commons(
                acc_lines,
                [old_lines, add_lines],
                [Common.old_acc, Common.add_acc],
            ),
        )
    )

    return p_qt_diff3

def pqtdiff3(app: QApplication) -> PQtDiff3:
    orig, new, merged = (Path(arg) for arg in app.arguments()[1:])

    return get_p_qt_diff3(orig, new, merged)


def main() -> None:
    QCoreApplication.setAttribute(
        Qt.ApplicationAttribute.AA_ShareOpenGLContexts
    )
    app = QApplication(argv)

    widget = pqtdiff3(app)
    widget.show()

    raise SystemExit(app.exec())

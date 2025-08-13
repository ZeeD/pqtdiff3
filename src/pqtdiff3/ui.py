from itertools import permutations
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Protocol
from typing import cast

from PySide6.QtUiTools import QUiLoader

from pqtdiff3.diff3 import Common
from pqtdiff3.diff3 import fillblanks
from pqtdiff3.diff3 import get_commons

if TYPE_CHECKING:
    from collections.abc import Iterable
    from collections.abc import Iterator

    from PySide6.QtWidgets import QApplication
    from PySide6.QtWidgets import QLineEdit
    from PySide6.QtWidgets import QScrollBar
    from PySide6.QtWidgets import QTextBrowser


def _resource(filename: str) -> Path:
    return Path(__file__).with_name(filename)


class PQtDiff3(Protocol):
    line_edit_old: 'QLineEdit'
    text_browser_old: 'QTextBrowser'
    line_edit_add: 'QLineEdit'
    text_browser_add: 'QTextBrowser'
    line_edit_acc: 'QLineEdit'
    text_browser_acc: 'QTextBrowser'

    def show(self) -> None: ...


def html(
    lines: list[str], commons: list[Common], others_commons: list[list[Common]]
) -> str:
    colors: dict[Common, str] = {
        Common.all: 'lightgreen',
        Common.old_add: 'lightyellow',
        Common.old_acc: 'lightcoral',
        Common.add_acc: 'lightsteelblue',
        Common.none: 'lightgray',
        Common.empty: 'white',
    }

    def gen() -> 'Iterator[str]':
        for line, common in fillblanks(lines, commons, others_commons):
            color = colors[common]
            yield f'<pre style="background-color: {color}">{line}</pre>'

    return (
        """<html><head><style>* { margin: 0 }</style></head><body>"""
        + ''.join(gen())
        + '</body></html>'
    )


def bind_scroll_bars(scroll_bars: 'Iterable[QScrollBar]') -> None:
    for sb1, sb2 in permutations(scroll_bars, 2):
        sb1.valueChanged.connect(sb2.setValue)


def get_lines(path: str) -> list[str]:
    return [s.strip() for s in Path(path).read_text().splitlines()]

def reload(ui: PQtDiff3) -> None:
    orig = ui.line_edit_old.text()
    new = ui.line_edit_add.text()
    merged = ui.line_edit_acc.text()

    old_lines = get_lines(orig)
    add_lines = get_lines(new)
    acc_lines = get_lines(merged)

    old_commons = get_commons(
        old_lines, [add_lines, acc_lines], [Common.old_add, Common.old_acc]
    )
    add_commons = get_commons(
        add_lines, [old_lines, acc_lines], [Common.old_add, Common.add_acc]
    )
    acc_commons = get_commons(
        acc_lines, [old_lines, add_lines], [Common.old_acc, Common.add_acc]
    )

    ui.text_browser_old.setHtml(
        html(old_lines, old_commons, [add_commons, acc_commons])
    )
    ui.text_browser_add.setHtml(
        html(add_lines, add_commons, [old_commons, acc_commons])
    )
    ui.text_browser_acc.setHtml(
        html(acc_lines, acc_commons, [add_commons, old_commons])
    )


def pqtdiff3(app: 'QApplication') -> 'PQtDiff3':
    orig, new, merged = app.arguments()[1:]

    ui = cast('PQtDiff3', QUiLoader().load(_resource('pqtdiff3.ui')))

    bind_scroll_bars(
        tb.verticalScrollBar()
        for tb in [
            ui.text_browser_old,
            ui.text_browser_add,
            ui.text_browser_acc,
        ]
    )
    bind_scroll_bars(
        tb.horizontalScrollBar()
        for tb in [
            ui.text_browser_old,
            ui.text_browser_add,
            ui.text_browser_acc,
        ]
    )

    ui.line_edit_old.setText(orig)
    ui.line_edit_add.setText(new)
    ui.line_edit_acc.setText(merged)

    reload(ui)

    return ui

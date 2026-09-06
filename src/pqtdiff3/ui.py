from itertools import permutations
from pathlib import Path
from typing import TYPE_CHECKING
from typing import ClassVar
from typing import Protocol
from typing import cast
from typing import override

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtGui import QColorConstants
from PySide6.QtGui import QPainter
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QProxyStyle
from PySide6.QtWidgets import QStyle
from PySide6.QtWidgets import QStyleOptionComplex
from PySide6.QtWidgets import QStyleOptionSlider
from PySide6.QtWidgets import QTextBrowser
from PySide6.QtWidgets import QWidget

from pqtdiff3.diff3 import Common
from pqtdiff3.diff3 import fillblanks
from pqtdiff3.diff3 import get_commons

if TYPE_CHECKING:
    from collections.abc import Iterable
    from collections.abc import Iterator

    from PySide6.QtWidgets import QApplication
    from PySide6.QtWidgets import QLineEdit
    from PySide6.QtWidgets import QScrollBar
    from PySide6.QtWidgets import QSplitter


def _resource(filename: str) -> Path:
    return Path(__file__).with_name(filename)


class PQtDiff3(Protocol):
    line_edit_old: 'QLineEdit'
    text_browser_old: 'QTextBrowser'
    line_edit_add: 'QLineEdit'
    text_browser_add: 'QTextBrowser'
    line_edit_acc: 'QLineEdit'
    text_browser_acc: 'QTextBrowser'
    splitter_acc: 'QSplitter'

    def show(self) -> None: ...


def html(blanks_filled: list[tuple[str, Common]]) -> str:
    colors: dict[Common, str] = {
        Common.all: 'lightgreen',
        Common.old_add: 'lightyellow',
        Common.old_acc: 'lightcoral',
        Common.add_acc: 'lightsteelblue',
        Common.none: 'lightgray',
        Common.empty: 'white',
    }

    def gen() -> 'Iterator[str]':
        for line_, common in blanks_filled:
            color = colors[common]
            line = (
                line_
                if line_ == ' '
                else line_.replace(' ', '·').replace('\t', '⇥')
            )
            yield f'<pre style="background-color: {color}">{line}</pre>'

    return (
        """<html><head><style>* { margin: 0 }</style></head><body>"""
        + ''.join(gen())
        + '</body></html>'
    )


def bind_scroll_bars(scroll_bars: 'Iterable[QScrollBar]') -> None:
    for sb1, sb2 in permutations(scroll_bars, 2):
        sb1.valueChanged.connect(sb2.setValue)


def get_lines(path: str | None) -> list[str]:
    if path is None:
        return []

    try:
        text = Path(path).read_text()
    except OSError:
        return []

    return [s.strip() for s in text.splitlines()]


def set_html_and_ticks(
    tb: QTextBrowser,
    lines: list[str],
    commons: list[Common],
    others_commons: list[list[Common]],
) -> None:
    blanks_filled = fillblanks(lines, commons, others_commons)
    tb.setHtml(html(blanks_filled))

    style = tb.verticalScrollBar().style()
    if not isinstance(style, TickStyle):
        raise TypeError
    style.lines = [common for (_, common) in blanks_filled]


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

    set_html_and_ticks(
        ui.text_browser_old, old_lines, old_commons, [add_commons, acc_commons]
    )
    set_html_and_ticks(
        ui.text_browser_add, add_lines, add_commons, [old_commons, acc_commons]
    )
    set_html_and_ticks(
        ui.text_browser_acc, acc_lines, acc_commons, [add_commons, old_commons]
    )


class TickStyle(QProxyStyle):
    lines: list[Common]
    colors: ClassVar[dict[Common, QColor]] = {
        Common.all: QColorConstants.Green,
        Common.old_add: QColorConstants.Yellow,
        Common.old_acc: QColorConstants.Red,
        Common.add_acc: QColorConstants.Blue,
        Common.none: QColorConstants.Gray,
        Common.empty: QColorConstants.White,
    }

    @override
    def drawComplexControl(
        self,
        control: QStyle.ComplexControl,
        option: QStyleOptionComplex,
        painter: QPainter,
        widget: QWidget | None = None,
    ) -> None:
        super().drawComplexControl(control, option, painter, widget=widget)
        if widget is None:
            return

        # check if control type and orientation match
        if control != QStyle.ComplexControl.CC_ScrollBar:
            return
        if not isinstance(option, QStyleOptionSlider):
            raise TypeError
        if option.orientation != Qt.Orientation.Vertical:
            return

        if not self.lines:
            return

        zero = self.subControlRect(
            control, option, QStyle.SubControl.SC_ScrollBarAddLine, widget
        ).height()
        rect = self.subControlRect(
            control, option, QStyle.SubControl.SC_ScrollBarGroove, widget
        )
        width = rect.width()
        height = rect.height()
        n = len(self.lines)

        for i, line in enumerate(self.lines):
            y = zero + (height * i / n)
            color = type(self).colors[line]
            painter.fillRect(width - 5, int(y), 5, 1, color)


def pqtdiff3(app: 'QApplication') -> 'PQtDiff3':
    args = app.arguments()[1:]
    two: bool
    try:
        orig, new, merged = args
        two = False
    except ValueError:
        try:
            orig, new = args
            merged = None
            two = True
        except ValueError:
            msg = f'uso: {app.arguments()[0]} orig new [merged]'
            raise SystemExit(msg) from None

    ui = cast('PQtDiff3', QUiLoader().load(_resource('pqtdiff3.ui')))

    if two:
        ui.splitter_acc.setVisible(False)

    tbs = [ui.text_browser_old, ui.text_browser_add, ui.text_browser_acc]

    for get_scrollbar in (
        QTextBrowser.verticalScrollBar,
        QTextBrowser.horizontalScrollBar,
    ):
        bind_scroll_bars(get_scrollbar(tb) for tb in tbs)

    for tb in tbs:
        scrollbar = tb.verticalScrollBar()
        scrollbar.setStyle(TickStyle())

    ui.line_edit_old.setText(orig)
    ui.line_edit_add.setText(new)
    ui.line_edit_acc.setText(merged)

    reload(ui)

    return ui

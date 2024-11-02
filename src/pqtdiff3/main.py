from collections.abc import Iterator
from difflib import SequenceMatcher
from enum import Enum
from enum import auto
from pathlib import Path
from sys import argv
from typing import cast

from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import Qt
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication
from PySide6.QtWidgets import QLineEdit
from PySide6.QtWidgets import QTextBrowser
from PySide6.QtWidgets import QWidget


def _resource(filename: str) -> Path:
    return Path(__file__).with_name(filename)


class PQtDiff3(QWidget):
    lineEdit: QLineEdit
    textBrowser: QTextBrowser
    lineEdit_2: QLineEdit
    textBrowser_2: QTextBrowser
    lineEdit_3: QLineEdit
    textBrowser_3: QTextBrowser


class Common(Enum):
    all = auto()
    old_add = auto()
    old_acc = auto()
    add_acc = auto()
    none = auto()


def diff3_old(
    old_lines: list[str], add_lines: list[str], acc_lines: list[str]
) -> list[Common]:
    """old_lines -> ~; add_lines -> ListaMovi; acc_lines -> acc."""
    old_add = SequenceMatcher(
        a=old_lines, b=add_lines, autojunk=False
    ).get_opcodes()
    old_acc = SequenceMatcher(
        a=old_lines, b=acc_lines, autojunk=False
    ).get_opcodes()

    #    old_add:
    #    insert 0 0 0 1
    #    equal 0 2 1 3
    #    delete 2 4 3 3
    #    old_acc:
    #    insert 0 0 0 1
    #    equal 0 4 1 5
    def gen() -> Iterator[Common]:
        old_add_itor = iter(old_add)
        old_acc_itor = iter(old_acc)
        while True:
            try:
                add_tag, add_i1, add_i2, add_j1, add_j2 = next(old_add_itor)
            except StopIteration:
                break

            if add_tag == 'equal':  # old == add
                n = add_i2 - add_i1
                assert add_j2 - add_j1 == n, f'{add_j2 - add_j1=}, {n=}'

                try:
                    acc_tag, acc_i1, acc_i2, acc_j1, acc_j2 = next(old_acc_itor)
                except StopIteration:
                    break

                if acc_tag == 'equal':  # all equal
                    m = acc_i2 - acc_i1
                    assert acc_j2 - acc_j1 == m, f'{acc_j2 - acc_j1=}, {m=}'
                    if n == m:
                        for _ in range(n):
                            yield Common.all
                    elif n < m:
                        for _ in range(n):
                            yield Common.all
                        for _ in range(m - n):
                            yield Common.old_acc
                    else:
                        for _ in range(n):
                            yield Common.all
                        for _ in range(m - n):
                            yield Common.add_acc
                    continue
            elif add_tag == 'insert':  # no old, in add
                ...

    return list(gen())


def diff3(
    old_lines: list[str], add_lines: list[str], acc_lines: list[str]
) -> list[Common]:
    old_itor = iter(old_lines)
    add_itor = iter(add_lines)
    acc_itor = iter(acc_lines)

    def gen() -> Iterator[Common]:
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
    }

    def gen() -> Iterator[str]:
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
    p_qt_diff3.lineEdit.setText(str(old))
    p_qt_diff3.lineEdit_2.setText(str(add))
    p_qt_diff3.lineEdit_3.setText(str(acc))

    old_lines = old.read_text().splitlines(keepends=True)
    add_lines = add.read_text().splitlines(keepends=True)
    acc_lines = acc.read_text().splitlines(keepends=True)

    common_lines = diff3(old_lines, add_lines, acc_lines)
    for common_line in common_lines:
        print(common_line)

    p_qt_diff3.textBrowser.setHtml(
        html(
            old_lines,
            common_lines,
            {Common.all, Common.old_add, Common.old_acc},
        )
    )
    p_qt_diff3.textBrowser_2.setHtml(
        html(
            add_lines,
            common_lines,
            {Common.all, Common.old_add, Common.add_acc},
        )
    )
    p_qt_diff3.textBrowser_3.setHtml(
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

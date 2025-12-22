from tempfile import NamedTemporaryFile
from unittest.case import TestCase
from unittest.mock import MagicMock

from pqtdiff3.ui import reload

prefix = '<html><head><style>* { margin: 0 }</style></head><body>'
suffix = '</body></html>'


def pre(background_color: str, msg: str) -> str:
    return f'<pre style="background-color: {background_color}">{msg}</pre>'


def g(msg: str) -> str:
    return pre('lightgreen', msg)


def w() -> str:
    return pre('white', ' ')


def gr(msg: str) -> str:
    return pre('lightgray', msg)


class TestImpostaDiBollo(TestCase):
    def test_imposta_di_bollo(self) -> None:
        with (
            NamedTemporaryFile('w+', delete_on_close=False) as old,
            NamedTemporaryFile('w+', delete_on_close=False) as add,
            NamedTemporaryFile('w+', delete_on_close=False) as acc,
        ):
            old.write('xxx')
            add.write('xxx \nxxx')
            acc.write('xxx ')
            old.close()
            add.close()
            acc.close()

            ui = MagicMock()
            ui.line_edit_old.text = MagicMock(return_value=old.name)
            ui.line_edit_add.text = MagicMock(return_value=add.name)
            ui.line_edit_acc.text = MagicMock(return_value=acc.name)

            reload(ui)

            ui.text_browser_old.setHtml.assert_called_with(
                f'{prefix}{g("xxx")}{w()}{suffix}'
            )
            ui.text_browser_add.setHtml.assert_called_with(
                f'{prefix}{g("xxx")}{gr("xxx")}{suffix}'
            )
            ui.text_browser_acc.setHtml.assert_called_with(
                f'{prefix}{g("xxx")}{w()}{suffix}'
            )

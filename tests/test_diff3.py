from unittest.case import TestCase

from pqtdiff3.diff3 import Common
from pqtdiff3.diff3 import get_commons


class TestGetCommons(TestCase):
    maxDiff = None

    def test_updaterow(self) -> None:
        a = ['common1', 'common2', 'changed', 'common3']
        b1 = ['common1', 'common2', 'onlybs', 'changedbs', 'common3']
        b2 = ['common1', 'common2', 'onlybs', 'changedbs', 'common3']

        expected = [Common.all, Common.all, Common.none, Common.all]
        actual = get_commons(a, [b1, b2], [Common.old_add, Common.old_acc])
        self.assertListEqual(expected, actual)

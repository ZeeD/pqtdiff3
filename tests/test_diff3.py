from unittest.case import TestCase

from pqtdiff3.diff3 import Common
from pqtdiff3.diff3 import fillblanks
from pqtdiff3.diff3 import get_commons


class TestGetCommons(TestCase):
    maxDiff = None

    def test_get_commons(self) -> None:
        a = ['common1', 'common2', 'changed', 'common3']
        b1 = ['common1', 'common2', 'onlybs', 'changedbs', 'common3']
        b2 = ['common1', 'common2', 'onlybs', 'changedbs', 'common3']

        expected = [Common.all, Common.all, Common.none, Common.all]
        actual = get_commons(a, [b1, b2], [Common.old_add, Common.old_acc])
        self.assertListEqual(expected, actual)

    def test_fillblanks(self) -> None:
        lines = ['1com', '2cha', '3com', '8com']
        commons = [Common.all, Common.none, Common.all, Common.all]
        others_commons = [
            [
                Common.all,
                Common.old_acc,
                Common.all,
                Common.old_acc,
                Common.old_acc,
                Common.old_acc,
                Common.old_acc,
                Common.all,
                Common.old_acc,
                Common.old_acc,
            ],
            [
                Common.all,
                Common.old_acc,
                Common.all,
                Common.old_acc,
                Common.old_acc,
                Common.old_acc,
                Common.old_acc,
                Common.all,
                Common.old_acc,
                Common.old_acc,
            ],
        ]

        expected = [
            ('1com', Common.all),
            ('2cha', Common.none),
            ('3com', Common.all),
            ('', Common.empty),
            ('', Common.empty),
            ('', Common.empty),
            ('', Common.empty),
            ('8com', Common.all),
            ('', Common.empty),
            ('', Common.empty),
        ]
        actual = fillblanks(lines, commons, others_commons)
        self.assertListEqual(expected, actual)

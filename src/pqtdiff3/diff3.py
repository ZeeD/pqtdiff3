from difflib import SequenceMatcher
from enum import Enum
from enum import auto


class Common(Enum):
    all = auto()
    old_add = auto()
    old_acc = auto()
    add_acc = auto()
    none = auto()
    empty = auto()


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

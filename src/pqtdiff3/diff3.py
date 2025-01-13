from difflib import SequenceMatcher
from enum import Enum
from enum import auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator


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


def _fillblanks(
    lines: list[str], commons: list[Common], others_commons: list[list[Common]]
) -> 'Iterator[tuple[str, Common]]':
    lines_it = iter(lines)
    commons_it = iter(commons)
    others_commons_its = [
        iter(other_commons) for other_commons in others_commons
    ]

    while True:
        line = next(lines_it, None)
        if line is None:
            break
        common = next(commons_it)
        if common is Common.all:
            # search for holes
            while True:
                others = [
                    next(other_commons_it, None)
                    for other_commons_it in others_commons_its
                ]
                if any(other is None for other in others):
                    yield line, common
                    break
                if any(other is Common.all for other in others):
                    yield line, common
                    break
                # hole
                yield ' ', Common.empty
        else:
            # consume others
            for other_commons_it in others_commons_its:
                next(other_commons_it, None)
            yield line, common

    # add an empty line at the end to match others lenghts
    while True:
        others_commons_dones = [
            next(other_commons_it, None) is None
            for other_commons_it in others_commons_its
        ]
        if all(others_commons_dones):
            break
        yield ' ', Common.empty


def fillblanks(
    lines: list[str], commons: list[Common], others_commons: list[list[Common]]
) -> list[tuple[str, Common]]:
    return list(_fillblanks(lines, commons, others_commons))

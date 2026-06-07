from itertools import zip_longest
from logging import INFO
from logging import basicConfig
from logging import getLogger
from pathlib import Path
from subprocess import PIPE
from subprocess import run
from sys import argv
from typing import NewType

from conflict_parser import ConflictSegment
from conflict_parser import ContextSegment
from conflict_parser import MergeMetadata
from conflict_parser.parser.stateful_parsing import parse_content

from pqtdiff3.diff3 import Common

logger = getLogger(__name__)


def get_segments(
    my_fn: str, old_fn: str, your_fn: str
) -> list[ContextSegment | ConflictSegment]:
    return parse_content(
        run(  # noqa: S603
            [
                '/usr/bin/diff3',
                '--show-all',
                '--merge',
                '--text',
                '--strip-trailing-cr',
                my_fn,
                old_fn,
                your_fn,
            ],
            stdout=PIPE,
            check=False,
            text=True,
        ).stdout,
        MergeMetadata(conflict_style='diff3'),
    )


AnnotatedRow = NewType('AnnotatedRow', tuple[Common, int, str])
AnnotatedRows = NewType('AnnotatedRows', list[AnnotatedRow])


def _annotate_context_segment(
    i: int, seg: ContextSegment, rows: list[str]
) -> tuple[int, AnnotatedRows]:
    ret = AnnotatedRows([])
    while i < seg.start_line_no:
        ret.append(AnnotatedRow((Common.all, i, rows[i - 1])))
        i += 1
    for line in seg.lines:
        ret.append(AnnotatedRow((Common.all, i, line.rstrip())))
        i += 1
    return i, ret


def _annotate_conflict_segment(
    i: int, seg: ConflictSegment, rows: list[str]
) -> tuple[int, AnnotatedRows]:
    ret = AnnotatedRows([])
    while i < seg.start_line_no:
        ret.append(AnnotatedRow((Common.all, i, rows[i - 1])))
        i += 1

    for ours_line, theirs_line, base_line in zip_longest(
        seg.ours_lines, seg.theirs_lines, seg.base_label or []
    ):
        if ours_line is not None and ours_line == theirs_line:
            ret.append(AnnotatedRow((Common.old_acc, i, ours_line.rstrip())))
        elif ours_line is not None and ours_line == base_line:
            ret.append(AnnotatedRow((Common.old_add, i, ours_line.rstrip())))
        elif theirs_line is not None and  theirs_line == base_line:
            ret.append(AnnotatedRow((Common.add_acc, i, theirs_line.rstrip())))
        else:
            if ours_line is not None:
                ret.append(AnnotatedRow((Common.none, i, ours_line.rstrip())))
            if theirs_line is not None:
                ret.append(AnnotatedRow((Common.none, i, theirs_line.rstrip())))
            if base_line is not None:
                ret.append(AnnotatedRow((Common.none, i, base_line.rstrip())))
        i += 1
    return i, ret


def annotate(
    fn: str, segments: list[ContextSegment | ConflictSegment]
) -> AnnotatedRows:
    rows = Path(fn).read_text().split('\n')
    ret = AnnotatedRows([])
    i = 1

    for seg in segments:
        if isinstance(seg, ContextSegment):
            i, annotated_rows = _annotate_context_segment(i, seg, rows)
            ret.extend(annotated_rows)
        elif isinstance(seg, ConflictSegment):
            i, annotated_rows = _annotate_conflict_segment(i, seg, rows)
            ret.extend(annotated_rows)
        else:
            raise TypeError
    ret.extend(AnnotatedRow((Common.all, i, row)) for row in rows[i + 1 :])

    return ret


def demo_parser(my_fn: str, old_fn: str, your_fn: str) -> None:
    segments = get_segments(my_fn, old_fn, your_fn)

    logger.info('---%s', my_fn)
    for mark, i, row in annotate(my_fn, segments):
        logger.info('%s[%04d] %s', mark, i, row)
    logger.info('---%s', old_fn)
    for mark, i, row in annotate(old_fn, segments):
        logger.info('%s[%04d] %s', mark, i, row)
    logger.info('---%s', your_fn)
    for mark, i, row in annotate(your_fn, segments):
        logger.info('%s[%04d] %s', mark, i, row)


def main() -> None:
    basicConfig(format='%(message)s', level=INFO)

    errmsg = f'Usage: {argv[0]} MYFILE OLDFILE YOURFILE'

    args = argv[1:]
    if not args:
        raise SystemExit(errmsg)
    try:
        my_fn, old_fn, your_fn = args
    except ValueError:
        raise SystemExit(errmsg) from None
    demo_parser(my_fn, old_fn, your_fn)


if __name__ == '__main__':
    main()

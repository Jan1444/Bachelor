# -*- coding: utf-8 -*-

import inspect
from pprint import pprint

debug_on: bool = True


def printer(*text: object) -> None:
    if debug_on:
        frame = inspect.currentframe()
        caller = frame.f_back
        info = inspect.getframeinfo(caller)
        file_name = info.filename
        line_number = info.lineno

        print(f"\nline: {line_number}: ", end="")
        pprint(text, sort_dicts=False)
        print(f"{file_name}", end="\n\n")

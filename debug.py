# -*- coding: utf-8 -*-

from pprint import pprint
import inspect

debug_on: bool = True


def printer(text: str) -> None:
    if debug_on:
        frame = inspect.currentframe()
        caller = frame.f_back
        info = inspect.getframeinfo(caller)
        file_name = info.filename
        line_number = info.lineno

        print(f"\nline: {line_number}: ", end="")
        pprint(text, sort_dicts=False)
        print(f"{file_name}", end="\n\n")

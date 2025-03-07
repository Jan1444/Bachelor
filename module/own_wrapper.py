#  -*- coding: utf-8 -*-
from functools import wraps

from numpy import float32, uint16, round as np_round

from frozendict import frozendict


def freeze_all(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        def freeze(obj):
            if isinstance(obj, dict):
                return frozendict({k: freeze(v) for k, v in obj.items()})
            elif isinstance(obj, list):
                return tuple(freeze(v) for v in obj)
            return obj

        frozen_args = tuple(freeze(arg) for arg in args)
        frozen_kwargs = {k: freeze(v) for k, v in kwargs.items()}
        return func(*frozen_args, **frozen_kwargs)
    return wrapped


def precision(precision_: int = 5):
    def _precision(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            precision_args = (np_round(arg, precision_) if isinstance(arg, (float, float32))
                              else arg for arg in args)
            precision_kwargs = {k: (np_round(v, precision_) if isinstance(v, (float, float32)) else v)
                                for k, v in kwargs.items()}
            return func(*precision_args, **precision_kwargs)
        return wrapped
    return _precision


def formatter(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        np_args = (float32(arg) if isinstance(arg, float)
                   else (uint16(arg) if isinstance(arg, int)
                         else ([float32(x) for x in arg] if isinstance(arg, list)
                               else arg)
                         )
                   for arg in args)
        return func(*np_args, **kwargs)
    return wrapped

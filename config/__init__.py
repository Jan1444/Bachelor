# -*- coding: utf-8 -*-

import pathlib
import tomli
import tomli_w

path: pathlib.Path = pathlib.Path(__file__).parent / "config_test.toml"

with path.open(mode="rb") as fp:
    config_data: dict = tomli.load(fp)


def write_config_data(data: dict):
    with path.open(mode="wb") as f:
        tomli_w.dump(data, f)

# -*- coding: utf-8 -*-

import pathlib
import tomli

path: pathlib.Path = pathlib.Path(__file__).parent / "config_test.toml"

with path.open(mode="rb") as fp:
    config_data: dict = tomli.load(fp)

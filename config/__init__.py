# -*- coding: utf-8 -*-

import pathlib
import tomli

path = pathlib.Path(__file__).parent / "config.toml"

with path.open(mode="rb") as fp:
    config_data = tomli.load(fp)

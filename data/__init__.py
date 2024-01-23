# -*- coding: utf-8 -*-

import pathlib
import tomli
import tomli_w

path: pathlib.Path = pathlib.Path(__file__).parent / "data.toml"

with path.open(mode="rb") as fp:
    energy_data: dict = tomli.load(fp)


def write_energy_data(data: dict):
    with path.open(mode="wb") as f:
        tomli_w.dump(data, f)

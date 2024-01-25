# -*- coding: utf-8 -*-

import pathlib
import tomli
import tomli_w

path_data: pathlib.Path = pathlib.Path(__file__).parent / "data.toml"

path_ev: pathlib.Path = pathlib.Path(__file__).parent / "ev_data.toml"
path_mor: pathlib.Path = pathlib.Path(__file__).parent / "mor_data.toml"

with path_data.open(mode="rb") as fp:
    energy_data: dict = tomli.load(fp)

with path_ev.open(mode="rb") as fp:
    evening_data: dict = tomli.load(fp)

with path_mor.open(mode="rb") as fp:
    morning_data: dict = tomli.load(fp)


def write_energy_data(data: dict):
    with path_data.open(mode="wb") as f:
        tomli_w.dump(data, f)


def write_evening_data(data: dict):
    with path_ev.open(mode="wb") as f:
        tomli_w.dump(data, f)


def write_morning_data(data: dict):
    with path_mor.open(mode="wb") as f:
        tomli_w.dump(data, f)

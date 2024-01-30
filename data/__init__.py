# -*- coding: utf-8 -*-

import pathlib
import toml

path_data: pathlib.Path = pathlib.Path(__file__).parent / "data.toml"

path_ev: pathlib.Path = pathlib.Path(__file__).parent / "ev_data.toml"
path_mor: pathlib.Path = pathlib.Path(__file__).parent / "mor_data.toml"

with path_data.open(mode="r") as fp:
    energy_data: dict = toml.load(fp)

with path_ev.open(mode="r") as fp:
    evening_data: dict = toml.load(fp)

with path_mor.open(mode="r") as fp:
    morning_data: dict = toml.load(fp)


def write_energy_data(data: dict):
    with path_data.open(mode="w") as f:
        toml.dump(data, f)


def write_evening_data(data: dict):
    with path_ev.open(mode="w") as f:
        toml.dump(data, f)


def write_morning_data(data: dict):
    with path_mor.open(mode="w") as f:
        toml.dump(data, f)


class EnergyManager:
    def __init__(self, config_path):
        self.energy_path = pathlib.Path(config_path)
        self.energy_path = pathlib.Path(__file__).parent / config_path
        self._energy_data = None

    @property
    def energy_data(self):
        if self._energy_data is None:
            self.reload_data()
        return self._energy_data

    def reload_data(self):
        with self.energy_path.open(mode="r") as f:
            self._energy_data = toml.load(f)

    def write_energy_data(self, data):
        with self.energy_path.open(mode="w") as f:
            toml.dump(data, f)
            self._energy_data = data  # Update the in-memory data


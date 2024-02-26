# -*- coding: utf-8 -*-

import pathlib
import toml
import datetime

path_data: pathlib.Path = pathlib.Path(__file__).parent / "data.toml"

path_ev: pathlib.Path = pathlib.Path(__file__).parent / "ev_data.toml"
path_mor: pathlib.Path = pathlib.Path(__file__).parent / "mor_data.toml"


class EnergyManager:
    def __init__(self, config_path):
        self.energy_path = pathlib.Path(config_path)
        self.energy_path = pathlib.Path(__file__).parent / config_path
        self._energy_data = None

    @property
    def energy_data(self):
        self._reload_data()
        if self._energy_data is None:
            self.reload_data()
        return self._energy_data

    def _reload_data(self):
        with self.energy_path.open(mode="r", encoding='UTF-8') as f:
            self._energy_data = toml.load(f)

    def write_energy_data(self, data):
        time_format: str = "%d-%m-%Y %H:%M:%S"
        time_write = datetime.datetime.now().strftime(time_format)
        data.update(
            {
                'write_time': {
                    'time': time_write,
                    'format': time_format
                }
            }
        )
        with self.energy_path.open(mode="w", encoding='UTF-8') as f:
            toml.dump(data, f)
            self._energy_data = data

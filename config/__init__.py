# -*- coding: utf-8 -*-
import pathlib
import toml
import datetime


class ConfigManager:
    def __init__(self, config_path):
        self.config_path = pathlib.Path(config_path)
        self.config_path = pathlib.Path(__file__).parent / config_path
        self._config_data = None

    @property
    def config_data(self):
        self._reload_config()
        if self._config_data is None:
            self._reload_config()
        return self._config_data

    def _reload_config(self):
        with self.config_path.open(mode="r", encoding='UTF-8') as fp:
            self._config_data = toml.load(fp)

    def write_config_data(self, data):
        time_format: str = "%d-%m-%Y %H:%M:%S"
        time_write = datetime.datetime.now().strftime(time_format)
        data['write_time']['time'] = time_write
        data['write_time']['format'] = time_format
        data['reload'] = True
        with self.config_path.open(mode="w") as f:
            toml.dump(data, f)
            self._config_data = data

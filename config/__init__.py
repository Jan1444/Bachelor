# -*- coding: utf-8 -*-
import pathlib
import toml


class ConfigManager:
    def __init__(self, config_path):
        self.config_path = pathlib.Path(config_path)
        self.config_path = pathlib.Path(__file__).parent / config_path
        self._config_data = None

    @property
    def config_data(self):
        if self._config_data is None:
            self.reload_config()
        return self._config_data

    def reload_config(self):
        with self.config_path.open(mode="r") as fp:
            self._config_data = toml.load(fp)

    def write_config_data(self, data):
        with self.config_path.open(mode="w") as f:
            toml.dump(data, f)
            self._config_data = data

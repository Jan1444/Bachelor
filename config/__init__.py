# -*- coding: utf-8 -*-
import pathlib
import tomli
import tomli_w


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
        with self.config_path.open(mode="rb") as fp:
            self._config_data = tomli.load(fp)

    def write_config_data(self, data):
        with self.config_path.open(mode="wb") as f:
            tomli_w.dump(data, f)
            self._config_data = data  # Update the in-memory data

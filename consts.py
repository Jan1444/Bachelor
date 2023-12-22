from typing import Final

config_file_Path: Final[str] = r'config/config_test.toml'
data_file_Path: Final[str] = r'data/data.toml'
uploads_file_Path: Final[str] = r'uploads/'
plot_path: Final[str] = r'static/plots/'

config_data: Final[dict] = {
    "coordinates": {
        "latitude": "",
        "longitude": ""
    },
    "pv": {
        "tilt_angle": "",
        "area": "",
        "module_efficiency": "",
        "converter_power": "",
        "exposure_angle": ""
    },

    "converter": {
        "max_power": ""
    },

    "market": {
        "consumer_price": ""
    },

    "shelly": {
        "ip_address": ""
    },

    "ir_remote": {

    }
}



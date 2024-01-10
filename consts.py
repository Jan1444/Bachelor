from typing import Final

config_file_Path: Final[str] = r'config/config_test.toml'
data_file_Path: Final[str] = r'data/data.toml'
downloads_file_Path: Final[str] = r'downloads/'
uploads_file_Path: Final[str] = r'uploads/'
plot_path: Final[str] = r'static/plots/'

config_data: Final[dict] = {
    "write_time": {
        "time": "",
        "format": "%d-%m-%Y %H:%M:%S"
    },
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

    },

    "air_conditioner": {
        'air_conditioner': '',
        'air_conditioner_steering': '',
        'ip_address_cloud': '',
        'ir_remote': '',
    },
    "heating": {
        "heating_power": "",
        "heating_area": ""
    },
    "house": {
        'house_year': '',
        'window1_frame': '',
        'window1_glazing': '',
        'window1_year': '',
        'window1_width': '',
        'window1_height': '',
        'wall1': '',
        'construction_wall1': '',
        'wall1_width': '',
        'wall1_height': '',
        'door_wall1': '',
        'door_wall1_width': '',
        'door_wall1_height': '',
        'window4_frame': '',
        'window4_glazing': '',
        'window4_year': '',
        'window4_width': '',
        'window4_height': '',
        'ceiling': '',
        'construction_ceiling': '',
        'window2_frame': '',
        'window2_glazing': '',
        'window2_year': '',
        'window2_width': '',
        'window2_height': '',
        'wall4': '',
        'construction_wall4': '',
        'wall2': '',
        'construction_wall2': '',
        'wall2_width': '',
        'door_wall4': '',
        'door_wall4_width': '',
        'door_wall4_height': '',
        'floor': '',
        'construction_floor': '',
        'door_wall2': '',
        'door_wall2_width': '',
        'door_wall2_height': '',
        'window3_frame': '',
        'window3_glazing': '',
        'window3_year': '',
        'window3_width': '',
        'window3_height': '',
        'wall3': '',
        'construction_wall3': '',
        'door_wall3': '',
        'door_wall3_width': '',
        'door_wall3_height': ''
    }
}

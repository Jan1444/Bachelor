from typing import Final

CONFIG_FILE_PATH: Final[str] = r'../config/config_test.toml'
DATA_FILE_PATH: Final[str] = r'./data/data.toml'
DOWNLOADS_FILE_PATH: Final[str] = r'./downloads/'
UPLOADS_FILE_PATH: Final[str] = r'uploads/'
PLOT_PATH: Final[str] = r'./static/plots/'
LOAD_PROFILE_FOLDER: Final[str] = r'./static/load_datas'

WINDOW_DATA: Final[dict] = {
    'Holzrahmen': ['Einfachverglasung', 'Doppelverglasung', 'Isolierverglasung'],
    'Kunststoffrahmen': ['Isolierverglasung'],
    'Metallrahmen': ['Isolierverglasung'],
    'ENEV': ['2009', '2014', '2016'],
    'u_value': ['']
}

WALL_DATA: Final[dict] = {
    'Außenwand': ['Massivbauweise', 'Holzkonstruktion'],
    'Innenwand': ['Massivbauweise', 'Holzkonstruktion'],
    'gegen Erdreich': ['Massivbauweise', 'Holzkonstruktion'],
    'ENEV Außenwand': ['2009', '2014', '2016'],
    'ENEV Innenwand': ['2009', '2014', '2016'],
    'u_value': ['']
}

DOOR_DATA: Final[dict] = {
    'ENEV': ['2009', '2014', '2016'],
    'u_value': ['']
}

CEILING_DATA: Final[dict] = {
    'Decke über Außenbereich': ['Massiv', 'Holzbalkendecke'],
    'unbeheiztes Geschoss': ['Massiv', 'Holzbalkendecke'],
    'ENEV unbeheiztes Geschoss': ['2009', '2014', '2016'],
    'ENEV beheiztes Geschoss': ['2009', '2014', '2016'],
    'ENEV Dach': ['2009', '2014', '2016'],
    'u_value': ['']
}

FLOOR_DATA: Final[dict] = {
    'gegen Erdreich': ['Massivbauweise', 'Holzkonstruktion'],
    'unbeheiztes Geschoss': ['Massivbauweise', 'Holzkonstruktion'],
    'beheiztes Geschoss': ['Massivbauweise', 'Holzkonstruktion'],
    'ENEV unbeheiztes Geschoss': ['2009', '2014', '2016'],
    'ENEV beheiztes Geschoss': ['2009', '2014', '2016'],
    'u_value': ['']
}

CONFIG_DATA: Final[dict] = {
    "write_time": {
        "time": "",
        "format": "%d-%m-%Y %H:%M:%S"
    },
    "analytics": {
        "reload": ""
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
    "house": {
        'house_year': '',
        'window1_frame': '',
        'window1_glazing': '',
        'window1_year': '',
        'window1_width': '',
        'window1_height': '',
        'window1_u_value': '',
        'wall1': '',
        'construction_wall1': '',
        'wall1_width': '',
        'wall1_height': '',
        'wall1_u_value': '',
        'wall1_diff_temp': '',
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

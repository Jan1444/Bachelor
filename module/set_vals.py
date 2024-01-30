# -*- coding: utf-8 -*-

import datetime

from module import debug
from module import functions


def write_data_to_config(config_data: dict, data: dict) -> dict | int:
    try:
        debug.printer(data)

        for data_key in data.keys():
            data[data_key] = str(data.get(data_key)).replace(",", ".")

        if data.get('latitude') != "" or data.get('longitude') != "":
            config_data['coordinates']['latitude'] = float(data.get('latitude', 0))
            config_data['coordinates']['longitude'] = float(data.get('longitude', 0))
        else:
            lat, lon = functions.get_coord(str(data.get('Straße', "")), str(data.get('Nr', '')),
                                           str(data.get('Stadt', '')),
                                           int(data.get('PLZ', 0)), str(data.get('Land', '')))
            config_data['coordinates']['latitude'] = lat
            config_data['coordinates']['longitude'] = lon

        tme = config_data.get('write_time')
        pv = config_data.get('pv')
        market = config_data.get('market')
        converter = config_data.get('converter')
        shelly = config_data.get('shelly')
        air_conditioner = config_data.get('air_conditioner')

        house = config_data.get('house')

        time_format: str = "%d-%m-%Y %H:%M:%S"
        tme['time'] = datetime.datetime.now().strftime(time_format)
        tme['format'] = time_format

        config_data['reload'] = True

        pv['tilt_angle'] = float(data.get('tilt_angle', 0))
        pv['area'] = float(data.get('area', 0))
        pv['module_efficiency'] = float(data.get('module_efficiency', 0))
        pv['exposure_angle'] = float(data.get('exposure_angle', 0))
        pv['temperature_coefficient'] = float(data.get('temperature_coefficient', 0))
        pv['nominal_temperature'] = float(data.get('nominal_temperature', 0))
        pv['mounting_type'] = int(data.get('mounting_type', 0))

        converter['max_power'] = float(data.get('converter_power', 0))

        market['consumer_price'] = float(data.get('consumer_price', 0))

        shelly['ip_address'] = str(data.get('ip_address', ''))

        air_conditioner["air_conditioner"] = str(data.get('air_conditioner', ''))
        air_conditioner["air_conditioner_cop"] = float(data.get('air_conditioner_cop', ''))
        air_conditioner["air_conditioner_steering"] = str(data.get('air_conditioner_steering', ''))
        air_conditioner["ip_address_cloud"] = str(data.get('ip_address_cloud', ''))
        air_conditioner["ir_remote"] = str(data.get('ir_remote', ''))

        house['house_year'] = int(data.get('house_year', 0))

        for i in range(1, 5):
            house[f'window{i}_frame'] = str(data.get(f'window{i}_frame', ''))
            house[f'window{i}_glazing'] = str(data.get(f'window{i}_glazing', ''))
            house[f'window{i}_year'] = int(data.get(f'window{i}_year', 0))
            house[f'window{i}_width'] = float(data.get(f'window{i}_width', 0))
            house[f'window{i}_height'] = float(data.get(f'window{i}_height', 0))
            house[f'window{i}_u_value'] = float(data.get(f'window{i}_u_value', 0))

            house[f'wall{i}'] = str(data.get(f'wall{i}', ''))
            house[f'wall{i}_width'] = float(data.get(f'wall{i}_width', 0))
            house[f'wall{i}_height'] = float(data.get(f'wall{i}_height', 0))
            house[f'construction_wall{i}'] = str(data.get(f'construction_wall{i}', ''))
            house[f'wall{i}_type'] = int(data.get(f'wall{i}_type', 0))
            house[f'wall{i}_u_value'] = float(data.get(f'wall{i}_u_value', 0))
            house[f'wall{i}_diff_temp'] = float(data.get(f'wall{i}_diff_temp', 0))

            house[f'door_wall{i}'] = int(data.get(f'door_wall{i}', 0))
            house[f'door_wall{i}_enev'] = str(data.get(f'door_wall{i}_enev', 0))
            house[f'door_wall{i}_width'] = float(data.get(f'door_wall{i}_width', 0))
            house[f'door_wall{i}_height'] = float(data.get(f'door_wall{i}_height', 0))

        house['ceiling'] = str(data.get('ceiling', ''))
        house['construction_ceiling'] = str(data.get('construction_ceiling', ''))

        house['floor'] = str(data.get('floor', ''))
        house['construction_floor'] = str(data.get('construction_floor', ''))

        return config_data

    except KeyError as error:
        print("Missing key: ", error)
        return -1

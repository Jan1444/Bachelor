# -*- coding: utf-8 -*-
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

        pv = config_data.get('pv')
        market = config_data.get('market')
        load_profile = config_data.get('load_profile')
        converter = config_data.get('converter')
        battery = config_data.get('battery')
        shelly = config_data.get('shelly')
        air_conditioner = config_data.get('air_conditioner')
        heater = config_data.get('heater')

        house = config_data.get('house')

        for key in pv:
            alignment = int(data.get('alignment'))
            pv['alignment'] = alignment
            pv['pv_lifetime'] = float(data.get('pv_lifetime', 0))
            pv['pv_peak_power'] = float(data.get('pv_peak_power', 0))
            pv['pv_cost'] = float(data.get('pv_cost', 0))

            if '1' in key:
                if alignment >= 1:
                    pv[key] = float(data.get(key, 0))
                else:
                    pv[key] = 0.0

            if '2' in key:
                if alignment >= 2:
                    pv[key] = float(data.get(key, 0))
                else:
                    pv[key] = 0.0

            if '3' in key:
                if alignment >= 3:
                    pv[key] = float(data.get(key, 0))
                else:
                    pv[key] = 0.0

            if '4' in key:
                if alignment == 4:
                    pv[key] = float(data.get(key, 0))
                else:
                    pv[key] = 0.0

        for key in converter:
            converter[key] = float(data.get(f'converter_{key}', 0))

        for key in battery:
            battery[key] = float(data.get(f'battery_{key}', 0))

        heater['heater_type'] = str(data.get('heater_type', ''))
        heater['heater_efficiency'] = float(data.get('heater_efficiency', 0))
        heater['heater_price'] = float(data.get('heater_price', 0))

        market['consumer_price'] = float(data.get('consumer_price', 0))

        load_profile['name'] = str(data.get('load_profile_name'))

        shelly['ip_address'] = str(data.get('ip_address', ''))

        for key in air_conditioner:
            air_conditioner[key] = str(data.get(f'air_conditioner_{key}', ''))
        air_conditioner["air_conditioner_cop"] = float(data.get('air_conditioner_cop', ''))

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

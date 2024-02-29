#  -*- coding: utf-8 -*-

import datetime
from functools import lru_cache

import toml
from numpy import float64, float32, float16, uint16, array, absolute

from module import functions, analytics

from module import classes, consts, own_wrapper as wrap


def prepare_data_to_write(time, power: list[float], market_price: list[float], energy: float,
                          radiation: None | list[float] = None, radiation_dni: None | list[float] = None) -> dict | int:
    data: dict = {
        "write_time": {
            "time": datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
            "format": "%d-%m-%Y %H:%M:%S"
        },
        "energy": {
            "energy": energy
        }
    }
    # write radiation
    try:
        if radiation is not None:
            h = -1
            for i, k in enumerate(time):
                data.update({
                    k: {
                        "direct_radiation": radiation[i],
                        "power": round(power[i], 3),
                        "market_price": market_price[h]
                    }
                })

                if (i - 4) % 4 == 0:
                    h += 1

            return data

    except KeyError as error:
        print(f"Key {error} is not a valid")
        return -1

    except IndexError as error:
        print(f"List is to short or long, need same length as time\n"
              f"len(time) -> {len(time)}\n"
              f"len(radiation) -> {len(radiation)}, {'✅' if len(radiation) == len(time) else '❌'}\n"
              f"len(power) -> {len(power)}, {'✅' if len(power) == len(time) else '❌'}\n"
              f"len(market_price) -> {len(market_price)}, {'✅' if len(market_price) * 4 + 1 == len(time) else '❌'}\n"
              f"{error}")
        return -1

    # write radiation_dni
    try:
        if radiation_dni:
            h = -1
            for i, k in enumerate(time):
                data.update({
                    k: {"dni_radiation": radiation_dni[i],
                        "power": round(power[i], 3),
                        "market_price": market_price[h]
                        }
                })

                if (i - 4) % 4 == 0:
                    h += 1

            return data

    except KeyError as error:
        print(f"Key {error} is not a valid")
        return -1

    except IndexError as error:
        print(f"List is to short or long, need same length as time\n"
              f"len(time) -> {len(time)}\n"
              f"len(radiation_dni) -> {len(radiation_dni)}, {'✅' if len(radiation_dni) == len(time) else '❌'}\n"
              f"len(power) -> {len(power)}, {'✅' if len(power) == len(time) else '❌'}\n"
              f"len(market_price) -> {len(market_price)}, {'✅' if len(market_price) == len(time) else '❌'}\n"
              f"{error}")
        return -1


def heating_power(config_data: dict, weather: dict) -> (list, list, list):
    def _calc_area(data_house: dict, prefix: str, prefix2: str | None = None) -> float16:
        try:
            if prefix2 is None:
                prefix2 = prefix
            area = float16(data_house.get(f"{prefix}_width", 0) * data_house.get(f"{prefix2}_height", 0))
            return area

        except AttributeError as err:
            print(prefix, prefix2)
            print(f"Attribute Missing: {err}")
            return float16(0)

    def _get_u_value(data_house: dict, u_value: dict, prefix: str) -> float16:
        try:
            if "wall" in prefix:

                wall_: str = data_house.get(prefix, "")
                wall_type: str = data_house.get(f"construction_{prefix}", "")
                year: uint16 = uint16(data_house.get(f"house_year", 0)
                                      if data_house.get(f"house_year") < 1995 else 1995)

                if wall_ == "ENEV Außenwand" or wall_ == "ENEV Innenwand":
                    return float16(u_value.get("Wand").get(wall_).get(uint16(wall_type)))
                elif wall_ == "u_value":
                    return float16(data_house.get(f"{prefix}_u_value", 0))
                else:
                    return float16(u_value.get("Wand").get(wall_).get(wall_type).get(year))

            elif "window" in prefix:
                window_: str = data_house.get(f"{prefix}_frame", "")
                glazing: str = data_house.get(f"{prefix}_glazing", "")
                window_year: uint16 = uint16(data_house.get(f"{prefix}_year", 0) if data_house.get(
                    f"{prefix}_year") < 1995 else 1995)

                if window_ == "ENEV":
                    return float16(u_value.get("Fenster").get(window_).get(uint16(glazing)))
                elif window_ == "u_value":
                    return float16(data_house.get(f"{prefix}_u_value", 0))
                else:
                    return u_value.get("Fenster").get(window_).get(glazing).get(window_year)

            elif "door" in prefix:
                year: uint16 = uint16(data_house.get(f"house_year", 0)
                                      if data_house.get(f"house_year") < 1995 else 1995)
                return float16(u_value.get("Türen").get("alle").get(year, 0))

            elif "floor" in prefix:
                floor_: str = data_house.get(f"floor", "")
                floor_type: str = data_house.get(f"construction_floor", "")
                year: uint16 = uint16(data_house.get(f"house_year", 0)
                                      if data_house.get(f"house_year") < 1995 else 1995)
                if floor_ == "ENEV unbeheiztes Geschoss" or floor_ == "ENEV beheiztes Geschoss":
                    u: float16 = float16(u_value.get("Boden").get(floor_).get(uint16(floor_type)))
                    return u
                elif floor_ == "u_value":
                    return float16(data_house.get(f"{prefix}_u_value", 0))
                else:
                    return float16(u_value.get("Boden").get(floor_).get(floor_type).get(year))

            elif "ceiling" in prefix:
                ceiling_: str = data_house.get(f"ceiling", "")
                ceiling_type: str = data_house.get(f"construction_ceiling", "")
                year: uint16 = uint16(data_house.get(f"house_year", 0)
                                      if data_house.get(f"house_year") < 1995 else 1995)
                if (ceiling_ == "ENEV unbeheiztes Geschoss" or ceiling_ == "ENEV beheiztes Geschoss" or
                        ceiling_ == "ENEV Dach"):
                    return float16(u_value.get("Decke").get(ceiling_).get(uint16(ceiling_type)))
                elif ceiling_ == "u_value":
                    return float16(data_house.get(f"{prefix}_u_value", 0))
                else:
                    return float16(u_value.get("Decke").get(ceiling_).get(ceiling_type).get(year))
        except AttributeError as err:
            print(prefix)
            print(f"Attribute Missing: {err}")
            return float16(0.0)

    def _interior_wall(data_house: dict, prefix: str):
        try:
            if data_house.get(f"{prefix}", "") == "ENEV Innenwand":
                temp = data_house.get(f"{prefix}_diff_temp", "")
                return temp
            else:
                return 0

        except AttributeError as err:
            print(prefix)
            print(f"Attribute Missing: {err}")
            return 0

    data: dict = config_data["house"]
    shelly_data = config_data["shelly"]

    hp: classes.RequiredHeatingPower = classes.RequiredHeatingPower()
    trv: classes.ShellyTRVControl = classes.ShellyTRVControl(shelly_data["ip_address"])

    room = hp.Room

    floor = room.Floor
    ceiling = room.Ceiling

    floor.area = _calc_area(data, f"wall1", f"wall2")
    ceiling.area = _calc_area(data, f"wall1", f"wall2")

    floor.u_wert = _get_u_value(data, hp.u_value, "floor")
    ceiling.u_wert = _get_u_value(data, hp.u_value, "ceiling")

    room.volume = data.get("wall1_width", 0) * data.get("wall1_height", 0) * data.get("wall2_width", 0)

    for wall_number in range(1, 5):
        window_number: uint16 = uint16(1)
        wall = getattr(room, f"Wall{wall_number}")
        window = getattr(wall, f"Window{window_number}")
        door = getattr(wall, "Door")

        wall.area = _calc_area(data, f"wall{wall_number}")
        wall.interior_wall_temp = _interior_wall(data, f"wall{wall_number}")

        window.area = _calc_area(data, f"window{window_number}")
        door.area = _calc_area(data, f"door_wall{wall_number}")

        wall.u_wert = _get_u_value(data, hp.u_value, f"wall{wall_number}")
        window.u_wert = _get_u_value(data, hp.u_value, f"window{window_number}")
        door.u_wert = _get_u_value(data, hp.u_value, f"door")

    # trv_data: dict = trv.get_thermostat()
    # if trv_data is None:
    #    trv_data: dict = trv.get_thermostat(timeout=10)

    # indoor_temp: float16 = float16((trv_data.get("tmp").get("value")) if trv_data is not None else 22)

    indoor_temp: float16 = float16(22)

    hp_data: list = []
    diff_data: list = []
    tme_data: list = []
    cop_temp: list = []

    old_temp: float16 = float16(16)
    for date, weather_today in weather.items():
        for tme, data in weather_today.items():

            outdoor_temp: float16 = float16(data.get("temp", old_temp))
            old_temp = outdoor_temp
            diff_temp: float16 = indoor_temp - outdoor_temp

            room.Floor.temp_diff = diff_temp
            room.Ceiling.temp_diff = diff_temp

            room.Wall1.temp_diff = diff_temp
            if room.Wall1.interior_wall_temp:
                room.Wall1.temp_diff = float16(absolute(room.Wall1.interior_wall_temp - indoor_temp))

            room.Wall2.temp_diff = diff_temp
            if room.Wall2.interior_wall_temp:
                room.Wall2.temp_diff = float16(absolute(room.Wall2.interior_wall_temp - indoor_temp))

            room.Wall3.temp_diff = diff_temp
            if room.Wall3.interior_wall_temp:
                room.Wall3.temp_diff = float16(absolute(room.Wall3.interior_wall_temp - indoor_temp))

            room.Wall4.temp_diff = diff_temp
            if room.Wall4.interior_wall_temp:
                room.Wall4.temp_diff = float16(absolute(room.Wall4.interior_wall_temp - indoor_temp))

            d = hp.calc_heating_power(room)

            cop: float16 = float16(((1 / 14) * outdoor_temp + 2.5) if outdoor_temp > -20 else 1)

            cop_temp.append(cop)
            diff_data.append(diff_temp)
            hp_data.append(d)
            tme_data.append(f"{date} {tme}")

    # debug.printer(diff_data, hp_data)
    return tme_data, hp_data, cop_temp


@wrap.freeze_all
def analyze_data(config_data: dict, weather_data: dict, consumption_data: bool = True, init_battery_charge: float = 0):
    return _analyze_data(config_data, weather_data, consumption_data, init_battery_charge)


@lru_cache(maxsize=1)
def _analyze_data(config_data: dict, weather_data: dict, consumption_data: bool = True, init_battery_charge: float = 0):
    converter = config_data["converter"]
    load_profile = config_data["load_profile"]
    battery = config_data.get('battery')

    pv_data_data: list = []
    weather_time: list = []

    diff_power: list = []

    battery_load: list = []
    min_capacity: float32 = float32(
        battery.get('capacity', 0) * 1_000 * (1 - battery.get('max_deload', 100) / 100))
    charging_power: float32 = float32(battery.get('charging_power', 0) * 0.25)
    battery_capacity: float32 = float32(battery.get('capacity', 0) * 1_000)
    state_of_charge: float32 = float32(init_battery_charge)
    min_state_of_charge: float32 = float32(min_capacity / battery_capacity * 100)
    load_efficiency: float32 = float32(battery.get('load_efficiency', 0) / 100)

    sun_class = functions.init_sun(config_data)

    pv_class = functions.init_pv(config_data, number=1)
    pv_class2 = functions.init_pv(config_data, number=2)
    pv_class3 = functions.init_pv(config_data, number=3)
    pv_class4 = functions.init_pv(config_data, number=4)

    market_class = functions.init_market(config_data)

    load_profile_data: dict = functions.load_load_profile(f'{consts.LOAD_PROFILE_FOLDER}/{load_profile.get("name")}')

    hp = analytics.heating_power(config_data, weather_data)

    indx: uint16 = uint16(0)

    state_of_charge_old = -1

    for date, weather_today in weather_data.items():
        date_load: str = date.rsplit('-', 1)[0]
        curr_load: dict = load_profile_data.get(date_load, "")

        for (tme_pv, data), (tme_load, load_data) in zip(weather_today.items(), curr_load.items()):
            time_float: float16 = functions.string_time_to_float(tme_pv)
            temp: float16 = float16(data.get("temp", 0))
            radiation_ghi: float16 = float16(data.get("ghi_radiation", 0))

            azimuth, elevation = functions.get_sun_data(sun_class, time_float)

            power_ghi: float32 = functions.get_pv_data(pv_class, temp, radiation_ghi, azimuth, elevation)

            if config_data['pv']['alignment'] >= 2:
                power_ghi += functions.get_pv_data(pv_class2, temp, radiation_ghi, azimuth, elevation)
            if config_data['pv']['alignment'] >= 3:
                power_ghi += functions.get_pv_data(pv_class3, temp, radiation_ghi, azimuth, elevation)
            if config_data['pv']['alignment'] >= 4:
                power_ghi += functions.get_pv_data(pv_class4, temp, radiation_ghi, azimuth, elevation)

            if power_ghi > converter.get("max_power", 0):
                power_ghi = converter.get("max_power", 0)

            weather_time.append(f'{date} {tme_pv}')
            pv_data_data.append(power_ghi)

            if tme_pv != tme_load:
                continue

            heating_power: float16 = hp[1][indx]
            cop: float16 = hp[2][indx]

            if not consumption_data:
                load_data = float16(0)

            load_diff: float16 = power_ghi - load_data  # Strom überschuss

            diff_energy: float16 = load_diff - (heating_power / cop)

            energy: float16 = diff_energy * 0.25

            if energy < 0:
                netto_energy = energy / (converter.get('efficiency') / 100)
            else:
                energy = min((energy, charging_power))
                netto_energy = energy * load_efficiency

            state_of_charge += netto_energy / battery_capacity * 100
            state_of_charge = max((min_state_of_charge, min((state_of_charge, 100))))
            battery_load.append(state_of_charge)

            discharge = 0
            if state_of_charge_old > state_of_charge:
                discharge = abs(diff_energy)

            state_of_charge_old = state_of_charge

            diff_power.append(diff_energy + discharge)

            if indx == 96:
                toml.dump({'analytics': {
                    'datum': date_old,
                    'state_of_charge': float(state_of_charge)
                }
                }, open('./data/data.toml', mode='w'))
            date_old = date
            indx += 1

    market_time = [time.get('start_timestamp') for time in market_class.data]
    market_price = [price.get('consumerprice') for price in market_class.data]

    energy_today = functions.calc_energy(pv_data_data[:95], kwh=False, round_=2)

    pv_power_data = [[time, value] for time, value in zip(weather_time, array(pv_data_data, dtype=float64))]

    market_data = [[time, value] for time, value in zip(market_time, array(market_price, dtype=float64))]

    heating_power_data = [[time, value] for time, value in zip(hp[0], array(hp[1], dtype=float64))]

    difference_power = [[time, value] for time, value in zip(hp[0], array(diff_power, dtype=float64))]

    battery_power = [[time, value] for time, value in zip(hp[0], array(battery_load, dtype=float64))]

    return energy_today, pv_power_data, market_data, heating_power_data, difference_power, battery_power

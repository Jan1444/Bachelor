#  -*- coding: utf-8 -*-

import datetime
from functools import lru_cache

import toml
from numpy import float64, float32, float16, uint16, array, absolute

from module import functions

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
                print(wall_type)
                year: uint16 = uint16(data_house.get(f"house_year", 0)
                                      if data_house.get(f"house_year") < 1995 else 1995)
                #TODO: fix wall_type Enev
                if wall_ == "ENEV Außenwand" or wall_ == "ENEV Innenwand":
                    wall_type = 2016
                    print("a,",u_value.get("Wand"))
                    print("b,",u_value.get("Wand").get(wall_))
                    print("c,",u_value.get("Wand").get(wall_).get(uint16(wall_type)))
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

    return tme_data, hp_data, cop_temp


@wrap.freeze_all
def analyze_data(config_data: dict, weather_data: dict, consumption_data: bool = True, init_battery_charge: float = 0,
                 calc_cost: bool = True, index_data: bool = False):
    return _analyze_data(config_data, weather_data, consumption_data, init_battery_charge, calc_cost, index_data)


@lru_cache(maxsize=1)
def _analyze_data(config_data: dict, weather_data: dict, consumption_data: bool = True, init_battery_charge: float = 0,
                  calc_cost: bool = False, index_data: bool = False):
    converter = config_data.get("converter")
    load_profile = config_data.get("load_profile")
    battery = config_data.get('battery')

    pv_data_data: list = []
    weather_time: list = []

    max_converter_power: float16 = float16(converter.get("max_power", 0))
    converter_efficiency: float16 = float16(converter.get('efficiency'))

    diff_energy_data: list = []
    diff_power: list = []

    battery_load: list = []
    overload_energy: float32 = float32(0)
    min_capacity: float32 = float32(
        battery.get('capacity', 0) * 1_000 * (1 - battery.get('max_deload', 100) / 100))
    charging_power: float32 = float32(battery.get('charging_power', 0) * 0.25)
    battery_capacity: float32 = float32(battery.get('capacity', 0) * 1_000)
    state_of_charge: float32 = float32(init_battery_charge)
    min_state_of_charge: float32 = float32(min_capacity / battery_capacity * 100)
    load_efficiency: float32 = float32(battery.get('load_efficiency', 0) / 100)

    battery_max_charging_power: float16 = float16(battery.get('charging_power'))

    sun_class = functions.init_sun(config_data)

    pv_class = functions.init_pv(config_data, number=1)
    pv_class2 = functions.init_pv(config_data, number=2)
    pv_class3 = functions.init_pv(config_data, number=3)
    pv_class4 = functions.init_pv(config_data, number=4)

    market_class = functions.init_market(config_data)

    market_time = [time.get('start_timestamp') for time in market_class.data]
    market_price = [price.get('consumerprice') for price in market_class.data]

    load_profile_data: dict = functions.load_load_profile(f'{consts.LOAD_PROFILE_FOLDER}/{load_profile.get("name")}')

    hp = heating_power(config_data, weather_data)

    indx: uint16 = uint16(0)
    day_indx: uint16 = uint16(0)

    state_of_charge_old: float32 = float32(-1)
    state_of_charge_end_old: float32 = float32(-1)
    indx_charge: uint16 = uint16(0)
    ret: uint16 = uint16(0)
    ret_old: uint16 = uint16(0)
    indx_state_of_charge_end: int = 0

    path_soc: str = r'./data/data.toml'

    vals: dict = {}
    price: dict = {}
    option: list = []

    for date, weather_today in weather_data.items():
        day_indx += 1
        date_load: str = date.rsplit('-', 1)[0]
        curr_load: dict = load_profile_data.get(date_load, "")
        state_of_charge_end = 0
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

            if power_ghi > max_converter_power:
                overload_energy = power_ghi - max_converter_power
                power_ghi = max_converter_power

            weather_time.append(f'{date} {tme_pv}')
            pv_data_data.append(power_ghi)

            if tme_pv != tme_load:
                continue

            heating_pwr: float16 = hp[1][indx]
            cop: float16 = hp[2][indx]

            if not consumption_data:
                load_data = float16(0)

            load_diff: float16 = power_ghi - load_data  # Strom überschuss

            diff_energy: float16 = load_diff - (heating_pwr / cop)

            if diff_energy > battery_max_charging_power:
                diff_energy = battery_max_charging_power

            energy: float16 = diff_energy * 0.25

            if energy < 0:
                netto_energy = energy / (converter_efficiency / 100)
            else:
                energy = min((energy, charging_power))
                netto_energy = energy * load_efficiency

            netto_energy += overload_energy * 0.25

            state_of_charge += netto_energy / battery_capacity * 100
            state_of_charge = max((min_state_of_charge, min((state_of_charge, 100))))
            battery_load.append(state_of_charge)

            discharge: float16 = float16(0)
            if state_of_charge_old > state_of_charge:
                discharge = abs(diff_energy)

            elif state_of_charge >= state_of_charge_end:
                state_of_charge_end = state_of_charge
                indx_state_of_charge_end = indx

            if state_of_charge_old == min_state_of_charge and state_of_charge_old < state_of_charge:
                indx_charge = indx

            state_of_charge_old = state_of_charge

            diff_power.append(diff_energy + discharge)
            diff_energy_data.append(abs(diff_energy))

            if indx == 96:
                file = open(path_soc, 'r')
                data = toml.load(file)
                file.close()

                data.update({date_old: {
                    'state_of_charge': float(state_of_charge)
                }
                })
                file = open(path_soc, mode='w')
                toml.dump(data, file)
                file.close()
            date_old = date
            indx += 1

        if calc_cost:
            slicer: slice = slice(indx - 96, indx - 1)

            if indx > 96:
                market_price_calc: list = []
                max_market_price = max(market_price) * 1.1
                for _ in market_price:
                    market_price_calc.append(max_market_price)
            else:
                market_price_calc = market_price

            heating_cost_sum, heating_cost_other_sum = calc_heating_cost(config_data, diff_power[slicer], hp[1][slicer],
                                                                         market_price_calc, diff_energy_data)

            if heating_cost_other_sum < heating_cost_sum:
                ret = uint16(1)

                state_of_charge = state_of_charge_end

                for i in range(indx_state_of_charge_end, 96 * day_indx):
                    battery_load[i] = state_of_charge_end

                if ret_old == 1:
                    for i in range((day_indx - 1) * 96, day_indx * 96):

                        if i < indx_charge:
                            battery_load[i] = state_of_charge_end_old

                        elif indx_charge <= i < (96 * day_indx):
                            battery_load[i] = min(battery_load[i] + state_of_charge_end_old - min_state_of_charge, 100)
            else:
                ret = uint16(2)

            en = functions.calc_energy(pv_data_data[slicer], kwh=False, round_=2)

            option.append(int(ret))
            price[int(day_indx)] = {
                'heater': round(float(heating_cost_other_sum), 2),
                'strom': round(float(heating_cost_sum), 2)
            }
            vals[int(day_indx)] = {
                'battery': round(float(max(battery_load[slicer])), 2),
                'pv': round(float(max(pv_data_data[slicer])), 2),
                'energy': float(en)
            }

            ret_old = ret
            state_of_charge_end_old = state_of_charge_end

    if index_data:
        return {'vals': vals, 'price': price, 'option': option}

    energy_today = functions.calc_energy(pv_data_data[:95], kwh=False, round_=2)

    pv_power_data = [[time, value] for time, value in zip(weather_time, array(pv_data_data, dtype=float64))]

    market_data = [[time, value] for time, value in zip(market_time, array(market_price, dtype=float64))]

    heating_power_data = [[time, value] for time, value in zip(hp[0], array(hp[1], dtype=float64))]

    difference_power = [[time, value] for time, value in zip(hp[0], array(diff_power, dtype=float64))]

    battery_power = [[time, value] for time, value in zip(hp[0], array(battery_load, dtype=float64))]

    return (energy_today, pv_power_data, market_data, heating_power_data, difference_power, battery_power,
            diff_energy_data)


def calc_heating_cost(config_data: dict, difference_power: list, heating_power_data: list, market_data: list,
                      diff_energy_battery: list):
    heater: dict = config_data.get('heater')
    pv: dict = config_data.get('pv')
    battery: dict = config_data.get('battery')

    heater_efficiency: float32 = float32(heater.get('heater_efficiency'))
    heater_type: str = heater.get('heater_type')
    fuel_price: float32 = float32(heater.get('heater_price', 0) * 100 * 0.25)

    battery_energy_price: float32 = float32(battery.get('price', 0) /
                                            (battery.get('capacity', 0.0001) * battery.get('load_cycle', 0.0001)))
    pv_energy_price: float32 = float32(pv.get('pv_cost', 0) /
                                       (pv.get('pv_peak_power', 0.0001) * pv.get('pv_lifetime') * 1100))

    heating_cost_pv: list = []
    heating_cost_other: list = []

    for dp, hp, md, bat_en in zip(difference_power, heating_power_data, market_data, diff_energy_battery):
        electricity_costs: float = md * 0.25
        dp_kw: float32 = float32(abs(dp / 1_000))
        hp_kw: float32 = float32(abs(hp / 1_000))

        if dp < 0:
            heating_cost_pv.append(dp_kw * electricity_costs)
        elif dp > 0:
            heating_cost_pv.append(dp_kw * electricity_costs * pv_energy_price * 0.25)
        elif dp == 0:
            heating_cost_pv.append((bat_en / 1_000) * electricity_costs * battery_energy_price * 0.25)

        fuel_gas_price: float32 = (functions.calc_fuel_gas_consumption(hp_kw, heater_efficiency, heater_type) *
                                   fuel_price)
        heating_cost_other.append(fuel_gas_price)

    heating_cost_other_sum: float32 = sum(heating_cost_other)
    heating_cost_sum: float32 = sum(heating_cost_pv)

    return heating_cost_sum, heating_cost_other_sum

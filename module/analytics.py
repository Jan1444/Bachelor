#  -*- coding: utf-8 -*-

import datetime
from functools import lru_cache, wraps
from frozendict import frozendict

from module import functions
from module import consts

from numpy import float64, float32, float16, uint16, array


def freeze_all(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        def freeze(obj):
            if isinstance(obj, dict):
                return frozendict({k: freeze(v) for k, v in obj.items()})
            elif isinstance(obj, list):
                return tuple(freeze(v) for v in obj)
            return obj

        frozen_args = tuple(freeze(arg) for arg in args)
        frozen_kwargs = {k: freeze(v) for k, v in kwargs.items()}

        return func(*frozen_args, **frozen_kwargs)

    return wrapped


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


@freeze_all
def analyze_data(config_data: dict, weather_data: dict):
    return _analyze_data(config_data, weather_data)


@lru_cache(maxsize=1)
def _analyze_data(config_data: dict, weather_data: dict):
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
    state_of_charge: float32 = float32(min_capacity / battery_capacity * 100)
    min_state_of_charge: float32 = float32(min_capacity / battery_capacity * 100)
    load_efficiency: float32 = float32(battery.get('load_efficiency', 0) / 100)

    sun_class = functions.init_sun(config_data)
    pv_class = functions.init_pv(config_data, number=1)
    pv_class2 = functions.init_pv(config_data, number=2)
    pv_class3 = functions.init_pv(config_data, number=3)
    pv_class4 = functions.init_pv(config_data, number=4)

    # weather_data = functions.get_weather_data(config_data, days=14)

    market_class = functions.init_market(config_data)

    load_profile_data: dict = functions.load_load_profile(f'{consts.LOAD_PROFILE_FOLDER}/{load_profile.get("name")}')

    hp = functions.heating_power(config_data, weather_data)
    indx: uint16 = uint16(0)

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

            load_diff: float16 = power_ghi - load_data  # Strom überschuss

            diff_energy: float16 = load_diff - (heating_power / cop)

            energy: float16 = diff_energy * 0.25

            if energy < 0:
                netto_energy = energy * converter.get('efficiency')
            else:
                energy = min((energy, charging_power))
                netto_energy = energy * load_efficiency

            state_of_charge += netto_energy / battery_capacity * 100
            state_of_charge = max((min_state_of_charge, min((state_of_charge, 100))))
            battery_load.append(state_of_charge)

            diff_power.append(diff_energy)

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

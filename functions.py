#  -*- coding: utf-8 -*-

import datetime
import os
from functools import lru_cache, wraps

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import tomli
import tomli_w
from frozendict import frozendict

import classes
import consts
import debug


def init_classes(latitude: float, longitude: float, module_efficiency: float, module_area: int, tilt_angle: float,
                 exposure_angle: float, mounting_type: int, costs: float) -> (
        classes.Weather, classes.MarketData, classes.CalcSunPos, classes.PVProfit):
    """

    :rtype: classes.Weather, classes.MarketData, classes.CalcSunPos, classes.PVProfit
    :param mounting_type:
    :param costs:
    :param latitude:
    :param longitude:
    :param module_efficiency:
    :param module_area:
    :param tilt_angle:
    :param exposure_angle:
    :return:
    """
    weather: classes.Weather = classes.Weather(latitude, longitude)
    market: classes.MarketData = classes.MarketData(costs)
    sun: classes.CalcSunPos = classes.CalcSunPos(latitude, longitude)
    pv: classes.PVProfit = classes.PVProfit(module_efficiency, module_area, tilt_angle, exposure_angle, -0.35, 25,
                                            mounting_type)
    return weather, market, sun, pv


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


def write_data_to_config(data: dict, path: str = None) -> int:
    """

    :param path:
    :param data:
    :return:
    """
    if path is None:
        path = consts.config_file_Path

    try:
        config_data = tomli.load(open(path, 'rb'))
    except FileNotFoundError:
        tomli_w.dump(consts.config_data, open(path, 'xb'))
        config_data = tomli.load(open(path, 'rb'))

    try:
        if data['latitude'] != "" or data['longitude'] != "":
            config_data['coordinates']['latitude'] = float(data['latitude'])
            config_data['coordinates']['longitude'] = float(data['longitude'])
        else:
            lat, lon = get_coord(data['Straße'], data['Nr'], data['Stadt'], data['PLZ'], data['Land'])
            config_data['coordinates']['latitude'] = lat
            config_data['coordinates']['longitude'] = lon

        pv = config_data['pv']
        market = config_data['market']
        converter = config_data['converter']
        shelly = config_data['shelly']
        ir_remote = config_data['ir_remote']

        pv['tilt_angle'] = float(data['tilt_angle'])
        pv['area'] = float(data['area'])
        pv['module_efficiency'] = float(data['module_efficiency'])
        pv['exposure_angle'] = float(data['exposure_angle'])
        pv['temperature_coefficient'] = float(data['temperature_coefficient'])
        pv['nominal_temperature'] = float(data['nominal_temperature'])
        pv['mounting_type'] = int(data['mounting_type'])

        converter['max_power'] = float(data['converter_power'])

        market['consumer_price'] = float(data['consumer_price'])

        shelly['ip_address'] = str(data['ip_address'])

        tomli_w.dump(config_data, open(path, 'wb'))

        return 1

    except KeyError as error:
        print("Missing key: ", error)
        return -1


def write_data_to_file(weather_data: None | dict = None, sun: None | classes.CalcSunPos = None,
                       pv: None | classes.PVProfit = None, market: None | classes.MarketData = None,
                       time: None | list[str] = None, radiation: None | list[float] = None,
                       radiation_dni: None | list[float] = None, power: None | list[float] = None,
                       market_price: None | list[float] = None, path: None | str = None) -> int:
    """

    :param path:
    :param radiation_dni:
    :param weather_data:
    :param sun:
    :param pv:
    :param market:
    :param time:
    :param radiation:
    :param power:
    :param market_price:
    :return:
    """
    if path is None:
        data_file_path = r"data/data.toml"
    else:
        data_file_path = path

    data: dict = {
        "write_time": {
            "time": datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
            "format": "%d-%m-%Y %H:%M:%S"
        }
    }
    try:
        if time is not None and radiation is not None and power is not None and market_price is not None:
            h = -1
            for i, k in enumerate(time):
                if k != "daily":
                    data.update({
                        k: {
                            "direct_radiation": radiation[i],
                            "power": round(power[i], 3),
                            "market_price": market_price[h]
                        }
                    })

                if (i - 4) % 4 == 0:
                    h += 1

            with open(data_file_path, 'wb') as f:
                tomli_w.dump(data, f)
            return 1

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

    try:
        if time is not None and radiation_dni is not None and power is not None and market_price is not None:
            h = -1
            for i, k in enumerate(time):
                if k != "daily":
                    data.update({
                        k: {"dni_radiation": radiation_dni[i],
                            "power": round(power[i], 3),
                            "market_price": market_price[h]
                            }
                    })

                if (i - 4) % 4 == 0:
                    h += 1

            with open(data_file_path, 'wb') as f:
                tomli_w.dump(data, f)
            return 1

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

    try:
        zeit: int = -1
        for z, t in enumerate(weather_data.keys()):
            if t != "daily":
                radiation = float(weather_data[t]["direct_radiation"])
                radiation_dni = float(weather_data[t]["dni_radiation"])
                time_float = float(t[:2]) + float(t[3:]) / 100
                sun_height = sun.calc_solar_elevation(time_float)
                sun_azimuth = sun.calc_azimuth(time_float)
                incidence = pv.calc_incidence_angle(sun_height, sun_azimuth)
                curr_eff = pv.calc_temp_dependency(weather_data[t]["temp"], radiation)
                power = pv.calc_power(radiation, incidence, sun_height, curr_eff)

                data.update({
                    t: {
                        "direct_radiation": radiation,
                        "dni_radiation": radiation_dni,
                        "power": round(power, 3),
                        "market_price": market.data[zeit]["consumerprice"]
                    }
                })

            if (z - 4) % 4 == 0:
                zeit += 1

        with open(data_file_path, 'wb') as f:
            tomli_w.dump(data, f)
        return 1

    except KeyError as error:
        print(f"Key {error} is not a valid")
        return -1


def read_data_from_file(file_path: str) -> dict | None:
    """

    :param file_path:
    :return:
    """
    try:
        with open(file_path, 'rb') as f:
            data = tomli.load(f)
        return data
    except FileNotFoundError:
        print("No File at " + file_path)
        return None


def get_coord(street: str, nr: str, city: str, postalcode: int, country: str) -> (str, str):
    # https://nominatim.org/release-docs/develop/api/Search/
    """

    :param street:
    :param nr:
    :param city:
    :param postalcode:
    :param country:
    :return:
    """
    street_rep = street.replace(" ", "&20")
    city_rep = city.replace(" ", "&20")
    url = (f"https://nominatim.openstreetmap.org/search?q={street_rep}%20{nr}%20{city_rep}%20{postalcode}%20{country}"
           f"&format=json&addressdetails=1")
    debug.printer(url)
    req = requests.request("GET", url).json()
    if len(req) > 1:
        for result in req:
            if "address" in result.keys():
                if street in result["address"].values():
                    if city in result["address"].values():
                        if nr in result["address"].values():
                            if postalcode in result["address"].values():
                                lat = float(req[0]["lat"])
                                lon = float(req[0]["lon"])
                                return lat, lon

    lat = float(req[0]["lat"])
    lon = float(req[0]["lon"])
    return lat, lon


def calc_energy(energy: list, interval: float = 0.25, kwh: bool = True) -> float:
    """

    :param energy:
    :param interval:
    :param kwh:
    :return:
    """
    multiplier = 1
    if kwh:
        multiplier = 1000
    power_values = list(map(lambda x: x / multiplier, energy))
    total_energy = sum((power_values[i] + power_values[i + 1]) / 2 * interval for i in range(len(power_values) - 1))
    debug.printer(total_energy)
    return total_energy


def date_time_download() -> dict:
    """

    :return:
    """
    date_today = datetime.datetime.now().strftime("%Y-%m-%d")
    date_and_time = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M")
    data: dict = {
        "date": date_today,
        "datetime": date_and_time
    }
    return data


@freeze_all
@lru_cache(maxsize=None)
def generate_weather_data(data: dict, config_data: dict) -> str:
    """

    :param data:
    :param config_data:
    :return:
    """
    if not os.path.exists(consts.uploads_file_Path):
        os.mkdir(consts.uploads_file_Path)

    start_date = datetime.datetime.strptime(data['start_date_weather'], "%Y-%m-%d")
    end_date = datetime.datetime.strptime(data['end_date_weather'], "%Y-%m-%d")

    weather_date = classes.Weather(
        config_data['coordinates']['latitude'], config_data['coordinates']['longitude'],
        datetime.datetime.strftime(start_date, "%d-%m-%Y"),
        datetime.datetime.strftime(end_date, "%d-%m-%Y")).data

    pv = classes.PVProfit(config_data["pv"]["module_efficiency"], config_data["pv"]["area"],
                          config_data["pv"]["tilt_angle"], config_data["pv"]["exposure_angle"],
                          config_data["pv"]["temperature_coefficient"],
                          config_data["pv"]["nominal_temperature"], config_data["pv"]["mounting_type"])

    power_data: dict = {}
    energy_data: dict = {}
    msg: str = ""
    for date in weather_date.keys():
        sun = classes.CalcSunPos(config_data['coordinates']['latitude'],
                                 config_data['coordinates']['longitude'],
                                 date)

        power_data[date] = {}
        energy_data_list: list = []
        for t in weather_date[date].keys():
            if t != "daily":
                time_float: float = int(t[:2]) + int(t[3:]) / 100
                azimuth: float = sun.calc_azimuth(time_float)
                elevation: float = sun.calc_solar_elevation(time_float)
                incidence = pv.calc_incidence_angle(elevation, azimuth)
                eff = pv.calc_temp_dependency(weather_date[date][t]["temp"], weather_date[date][t]["direct_radiation"])
                power_data[date][t] = pv.calc_power(weather_date[date][t]["direct_radiation"], incidence, elevation,
                                                    eff)
                energy_data_list.append(power_data[date][t])
        energy_data[date] = calc_energy(energy_data_list)

    if "excel_weather" in data.keys():
        if os.path.exists(rf"{consts.uploads_file_Path}data.xlsx"):
            os.remove(rf"{consts.uploads_file_Path}data.xlsx")
        if data["excel_weather"] == "on":
            df = pd.DataFrame.from_dict(energy_data, orient='index', columns=['energy [kWh]'])
            df.to_excel('{consts.uploads_file_Path}data.xlsx')
            msg = "excel"

    if "plot_png_weather" in data.keys():
        if data["plot_png_weather"] == "on":
            if os.path.exists(rf"{consts.uploads_file_Path}plot.png"):
                os.remove(rf"{consts.uploads_file_Path}plot.png")
            if len(energy_data.keys()) > 50:
                x = len(energy_data.keys()) * 0.25
                y = x * 0.4
            else:
                x = 10
                y = 5

            plt.figure(figsize=(x, y))
            plt.grid()
            plt.plot(list(energy_data.keys()), list(energy_data.values()), label="Energy[kWh]")
            plt.xticks(rotation=90, ha="right", fontsize=18)
            x = len(energy_data.keys())
            z = max(energy_data.values())
            z = (z + (100 if z > 100 else 5))
            ticks = np.arange(0, z, step=(x // 100 * 10 if z > 100 else 1))
            plt.yticks(ticks=ticks, ha="right", fontsize=20)
            plt.legend(loc="upper left", fontsize=20)
            plt.tight_layout()
            plt.savefig(rf"{consts.uploads_file_Path}plot.png")
            msg = f"{msg}, plot"

    return msg


@freeze_all
@lru_cache(maxsize=None)
def unpack_data(data: dict) -> (list[str], list[float], list[float], list[float]):
    """

    :param data:
    :return:
    """
    weather_time: list[str] = []
    radiation_data: list[float] = []
    power_data: list[float] = []

    market_time: list[float] = []
    market_price: list[float] = []

    error_key: int = 0

    try:
        if "dni_radiation" in data["00:00"].keys():
            radiation_key = "dni_radiation"
        elif "radiation" in data["00:00"].keys():
            radiation_key = "radiation"
        else:
            raise KeyError("No key: dni_radiation or radiation")
    except KeyError as error:
        print(error)
        return -1, -1, -1, -1

    try:

        for t in data.keys():
            if t != "write_time":
                weather_time.append(t)
                radiation_data.append(data[t][radiation_key])
                power_data.append(data[t]["power"])
                if t[3:] == "00":
                    market_time.append(t)
                    market_price.append(data[t]["market_price"])
                error_key += 1
        return weather_time, radiation_data, power_data, market_time, market_price
    except KeyError as error:
        print(f"No key: {error}")
        print(f"In line: {error_key * 5 + 7}")


if __name__ == "__main__":
    print("Run test, functions.py")
    print("Test write_data_to_config")
    test_data: dict = {
        "latitude": 1,
        "longitude": 2,
        "tilt_angle": 3,
        "area": 4,
        "module_efficiency": 5,
        "exposure_angle": 6,
        "temperature_coefficient": 7,
        "nominal_temperature": 8,
        "mounting_type": 9,
        "converter_power": 10,
        "consumer_price": 11,
        "ip_address": "IP"
    }

    ret = write_data_to_config(test_data, "config/function_tes.toml")
    if ret == 1:
        print('✅', "PASS")
    elif ret == -1:
        print('❌', "FAIL")

    print("Test write_data_to_file")
    weather_test_data: dict = {
        'daily': {'temp_max': 8.5, 'temp_min': 1.8, 'sunrise': '08:10', 'sunset': '16:20'},
        '00:00': {'temp': 5.6, 'cloudcover': 93, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '00:15': {'temp': 5.6, 'cloudcover': 93, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '00:30': {'temp': 5.6, 'cloudcover': 93, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '00:45': {'temp': 5.6, 'cloudcover': 93, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '01:00': {'temp': 5.6, 'cloudcover': 92, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '01:15': {'temp': 5.6, 'cloudcover': 92, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '01:30': {'temp': 5.6, 'cloudcover': 92, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '01:45': {'temp': 5.6, 'cloudcover': 92, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '02:00': {'temp': 5.1, 'cloudcover': 89, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '02:15': {'temp': 5.1, 'cloudcover': 89, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '02:30': {'temp': 5.1, 'cloudcover': 89, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '02:45': {'temp': 5.1, 'cloudcover': 89, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '03:00': {'temp': 4.8, 'cloudcover': 90, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '03:15': {'temp': 4.8, 'cloudcover': 90, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '03:30': {'temp': 4.8, 'cloudcover': 90, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '03:45': {'temp': 4.8, 'cloudcover': 90, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '04:00': {'temp': 4.4, 'cloudcover': 95, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '04:15': {'temp': 4.4, 'cloudcover': 95, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '04:30': {'temp': 4.4, 'cloudcover': 95, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '04:45': {'temp': 4.4, 'cloudcover': 95, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '05:00': {'temp': 4.4, 'cloudcover': 100, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '05:15': {'temp': 4.4, 'cloudcover': 100, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '05:30': {'temp': 4.4, 'cloudcover': 100, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '05:45': {'temp': 4.4, 'cloudcover': 100, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '06:00': {'temp': 4.6, 'cloudcover': 99, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '06:15': {'temp': 4.6, 'cloudcover': 99, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '06:30': {'temp': 4.6, 'cloudcover': 99, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '06:45': {'temp': 4.6, 'cloudcover': 99, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '07:00': {'temp': 4.4, 'cloudcover': 98, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '07:15': {'temp': 4.4, 'cloudcover': 98, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '07:30': {'temp': 4.4, 'cloudcover': 98, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '07:45': {'temp': 4.4, 'cloudcover': 98, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '08:00': {'temp': 4.5, 'cloudcover': 97, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '08:15': {'temp': 4.5, 'cloudcover': 97, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '08:30': {'temp': 4.5, 'cloudcover': 97, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '08:45': {'temp': 4.5, 'cloudcover': 97, 'direct_radiation': 1.0, 'dni_radiation': 15.0},
        '09:00': {'temp': 4.5, 'cloudcover': 97, 'direct_radiation': 1.0, 'dni_radiation': 12.2},
        '09:15': {'temp': 4.5, 'cloudcover': 97, 'direct_radiation': 1.0, 'dni_radiation': 9.5},
        '09:30': {'temp': 4.5, 'cloudcover': 97, 'direct_radiation': 2.0, 'dni_radiation': 15.1},
        '09:45': {'temp': 4.5, 'cloudcover': 97, 'direct_radiation': 5.0, 'dni_radiation': 31.5},
        '10:00': {'temp': 5.6, 'cloudcover': 98, 'direct_radiation': 5.0, 'dni_radiation': 27.4},
        '10:15': {'temp': 5.6, 'cloudcover': 98, 'direct_radiation': 7.0, 'dni_radiation': 34.3},
        '10:30': {'temp': 5.6, 'cloudcover': 98, 'direct_radiation': 9.0, 'dni_radiation': 40.2},
        '10:45': {'temp': 5.6, 'cloudcover': 98, 'direct_radiation': 10.0, 'dni_radiation': 41.5},
        '11:00': {'temp': 6.9, 'cloudcover': 98, 'direct_radiation': 21.0, 'dni_radiation': 82.0},
        '11:15': {'temp': 6.9, 'cloudcover': 98, 'direct_radiation': 20.0, 'dni_radiation': 74.4},
        '11:30': {'temp': 6.9, 'cloudcover': 98, 'direct_radiation': 7.0, 'dni_radiation': 25.1},
        '11:45': {'temp': 6.9, 'cloudcover': 98, 'direct_radiation': 7.0, 'dni_radiation': 24.4},
        '12:00': {'temp': 7.6, 'cloudcover': 99, 'direct_radiation': 13.0, 'dni_radiation': 44.5},
        '12:15': {'temp': 7.6, 'cloudcover': 99, 'direct_radiation': 20.0, 'dni_radiation': 67.9},
        '12:30': {'temp': 7.6, 'cloudcover': 99, 'direct_radiation': 8.0, 'dni_radiation': 27.2},
        '12:45': {'temp': 7.6, 'cloudcover': 99, 'direct_radiation': 31.0, 'dni_radiation': 106.1},
        '13:00': {'temp': 8.1, 'cloudcover': 74, 'direct_radiation': 17.0, 'dni_radiation': 59.2},
        '13:15': {'temp': 8.1, 'cloudcover': 74, 'direct_radiation': 28.0, 'dni_radiation': 100.1},
        '13:30': {'temp': 8.1, 'cloudcover': 74, 'direct_radiation': 33.0, 'dni_radiation': 122.4},
        '13:45': {'temp': 8.1, 'cloudcover': 74, 'direct_radiation': 96.0, 'dni_radiation': 373.1},
        '14:00': {'temp': 8.5, 'cloudcover': 100, 'direct_radiation': 20.0, 'dni_radiation': 82.5},
        '14:15': {'temp': 8.5, 'cloudcover': 100, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '14:30': {'temp': 8.5, 'cloudcover': 100, 'direct_radiation': 1.0, 'dni_radiation': 4.9},
        '14:45': {'temp': 8.5, 'cloudcover': 100, 'direct_radiation': 1.0, 'dni_radiation': 5.4},
        '15:00': {'temp': 8.0, 'cloudcover': 100, 'direct_radiation': 1.0, 'dni_radiation': 6.2},
        '15:15': {'temp': 8.0, 'cloudcover': 100, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '15:30': {'temp': 8.0, 'cloudcover': 100, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '15:45': {'temp': 8.0, 'cloudcover': 100, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '16:00': {'temp': 7.0, 'cloudcover': 100, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '16:15': {'temp': 7.0, 'cloudcover': 100, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '16:30': {'temp': 7.0, 'cloudcover': 100, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '16:45': {'temp': 7.0, 'cloudcover': 100, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '17:00': {'temp': 6.2, 'cloudcover': 100, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '17:15': {'temp': 6.2, 'cloudcover': 100, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '17:30': {'temp': 6.2, 'cloudcover': 100, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '17:45': {'temp': 6.2, 'cloudcover': 100, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '18:00': {'temp': 5.5, 'cloudcover': 100, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '18:15': {'temp': 5.5, 'cloudcover': 100, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '18:30': {'temp': 5.5, 'cloudcover': 100, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '18:45': {'temp': 5.5, 'cloudcover': 100, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '19:00': {'temp': 4.6, 'cloudcover': 100, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '19:15': {'temp': 4.6, 'cloudcover': 100, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '19:30': {'temp': 4.6, 'cloudcover': 100, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '19:45': {'temp': 4.6, 'cloudcover': 100, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '20:00': {'temp': 3.7, 'cloudcover': 100, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '20:15': {'temp': 3.7, 'cloudcover': 100, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '20:30': {'temp': 3.7, 'cloudcover': 100, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '20:45': {'temp': 3.7, 'cloudcover': 100, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '21:00': {'temp': 2.8, 'cloudcover': 63, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '21:15': {'temp': 2.8, 'cloudcover': 63, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '21:30': {'temp': 2.8, 'cloudcover': 63, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '21:45': {'temp': 2.8, 'cloudcover': 63, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '22:00': {'temp': 2.2, 'cloudcover': 76, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '22:15': {'temp': 2.2, 'cloudcover': 76, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '22:30': {'temp': 2.2, 'cloudcover': 76, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '22:45': {'temp': 2.2, 'cloudcover': 76, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '23:00': {'temp': 1.8, 'cloudcover': 48, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '23:15': {'temp': 1.8, 'cloudcover': 48, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '23:30': {'temp': 1.8, 'cloudcover': 48, 'direct_radiation': 0.0, 'dni_radiation': 0.0},
        '23:45': {'temp': 1.8, 'cloudcover': 48, 'direct_radiation': 0.0, 'dni_radiation': 0.0}}
    time_test_data: list = ['00:00', '00:15', '00:30', '00:45', '01:00', '01:15', '01:30', '01:45', '02:00', '02:15',
                            '02:30', '02:45', '03:00']
    power_test_data: list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
    market_price_test_data: list = [0.1, 0.2, 0.3]
    radiation_dni_test_data: list = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100, 1200, 1300]
    radiation_test_data: list = [10_000, 10_100, 10_200, 10_300, 10_400, 10_500, 10_600, 10_700, 10_800, 10_900, 11_000,
                                 11_100, 11_200]

    ret = write_data_to_file(weather_test_data, classes.CalcSunPos(49.5198371, 11.2948653),
                             classes.PVProfit(20, 10, 0, 30, -0.1, 25, 1),
                             classes.MarketData(13), path=r'data/test_data_classes.toml')
    if ret == 1:
        print('✅', "PASS, classes")
    elif ret == -1:
        print('❌', "FAIL, classes")

    ret = write_data_to_file(time=time_test_data, radiation=radiation_test_data, power=power_test_data,
                             market_price=market_price_test_data, path=r'data/test_data_direct.toml')

    if ret == 1:
        print('✅', "PASS, direct radiation")
    elif ret == -1:
        print('❌', "FAIL, direct radiation")

    ret = write_data_to_file(time=time_test_data, radiation_dni=radiation_dni_test_data, power=power_test_data,
                             market_price=market_price_test_data, path=r'data/test_data_dni.toml')

    if ret == 1:
        print('✅', "PASS, dni radiation")
    elif ret == -1:
        print('❌', "FAIL, dni radiation")

    print("Test read_data_from_file")
    ret = read_data_from_file(r"data/test_data_dni.toml")
    if ret is not None:
        print('✅', "PASS")
    else:
        print('❌', "FAIL")

    print("Test get_coord")
    ret = get_coord("Hirschenau", "2", "Rückersdorf", 90607, 'Deutschland')
    print(ret)
    if ret[0] == 49.4989187 and ret[1] == 11.249947:
        print('✅', "PASS")
    else:
        print('❌', "FAIL")

    print("Test calc_energy")
    energy_test: list[float] = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    ret = calc_energy(energy_test, 1, False)
    if ret == 50:
        print('✅', "PASS")
    else:
        print('❌', "FAIL")

    print("Test generate_weather_data")




    print("Test unpack_data")
    data_test: dict = tomli.load(open(r"data/data.toml", "rb"))
    ret = unpack_data(data_test)
    if ret != (-1, -1, -1, -1):
        print('✅', "PASS")
    else:
        print('❌', "FAIL")

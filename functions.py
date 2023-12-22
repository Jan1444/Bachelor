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
import consts
import classes


def init_classes(latitude: float, longitude: float, module_efficiency: float, module_area: int, tilt_angle: float,
                 exposure_angle: float, mounting_type: int, costs: float) -> (
        classes.Weather, classes.MarketData, classes.CalcSunPos, classes.PVProfit):
    """

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


def write_data_to_config(data: dict) -> None:
    """

    :param data:
    :return:
    """
    with open(consts.config_file_Path, 'rb') as f:
        config_data = tomli.load(f)
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

    with open(consts.config_file_Path, 'wb') as f:
        tomli_w.dump(config_data, f)


def write_data_to_file(weather_data: None | dict, sun: None | classes.CalcSunPos, pv: None | classes.PVProfit,
                       market: None | classes.MarketData, time: None | list = None, radiation: None | list = None,
                       radiation_dni: None | list = None, power: None | list = None, market_price: None | list = None) \
        -> None:
    """

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
    data_file_path = r"data/data.toml"
    data: dict = {
        "write_time": {
            "time": datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
            "format": "%d-%m-%Y %H:%M:%S"
        }
    }

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

    elif time is not None and radiation_dni is not None and power is not None and market_price is not None:
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
    else:
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


def read_data_from_file(file_path: str) -> dict:
    """

    :param file_path:
    :return:
    """
    with open(file_path, 'rb') as f:
        data = tomli.load(f)
    return data


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


def unpack_data(data: dict) -> (list, list, list, list):
    """

    :param data:
    :return:
    """
    weather_time: list = []
    radiation_data: list = []
    power_data: list = []

    market_time: list = []
    market_price: list = []

    radiation_key: str = ""

    if "dni_radiation" in data["00:00"].keys():
        radiation_key = "dni_radiation"
    elif "radiation" in data["00:00"].keys():
        radiation_key = "radiation"

    for t in data.keys():

        if t != "write_time":
            weather_time.append(t)
            radiation_data.append(data[t][radiation_key])
            power_data.append(data[t]["power"])
            if t[3:] == "00":
                market_time.append(t)
                market_price.append(data[t]["market_price"])

    return weather_time, radiation_data, power_data, market_time, market_price

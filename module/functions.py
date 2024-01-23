#  -*- coding: utf-8 -*-

import datetime
import json
import os
from functools import lru_cache, wraps
from typing import Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import tomli
import tomli_w
from frozendict import frozendict

from module import classes, consts, debug


def init_classes(latitude: float, longitude: float, module_efficiency: float, module_area: int, tilt_angle: float,
                 exposure_angle: float, mounting_type: int, costs: float, ip_address: str) -> (classes.Weather,
                                                                                               classes.MarketData,
                                                                                               classes.CalcSunPos,
                                                                                               classes.PVProfit,
                                                                                               classes.RequiredHeatingPower):
    """

    :param ip_address:
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
    hp: classes.RequiredHeatingPower = classes.RequiredHeatingPower()
    s_trv: classes.ShellyTRVControl = classes.ShellyTRVControl(ip_address)
    return weather, market, sun, pv, hp, s_trv


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

    config_data = read_data_from_file(path)
    if config_data is None:
        folder: str = consts.config_file_Path[:1 + consts.config_file_Path.rfind("/")]
        if os.path.exists(folder):
            os.mkdir(folder)
        tomli_w.dump(consts.config_data, open(path, 'xb'))
        config_data = read_data_from_file(path)

    try:
        debug.printer(data)

        for data_key in data.keys():
            data[data_key] = str(data[data_key]).replace(",", ".")

        if data['latitude'] != "" or data['longitude'] != "":
            config_data['coordinates']['latitude'] = float(data.get('latitude', 0))
            config_data['coordinates']['longitude'] = float(data.get('longitude', 0))
        else:
            lat, lon = get_coord(str(data.get('Straße', "")), str(data.get('Nr', '')), str(data.get('Stadt', '')),
                                 int(data.get('PLZ', 0)), str(data.get('Land', '')))
            config_data['coordinates']['latitude'] = lat
            config_data['coordinates']['longitude'] = lon

        tme = config_data.get('write_time')
        analytics = config_data.get('analytics')
        pv = config_data.get('pv')
        market = config_data.get('market')
        converter = config_data.get('converter')
        shelly = config_data.get('shelly')
        air_conditioner = config_data.get('air_conditioner')

        house = config_data.get('house')

        time_format: str = "%d-%m-%Y %H:%M:%S"
        tme['time'] = datetime.datetime.now().strftime(time_format)
        tme['format'] = time_format

        analytics['reload'] = True

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
        air_conditioner["air_conditioner_steering"] = str(data.get('air_conditioner_steering', ''))
        air_conditioner["ip_address_cloud"] = str(data.get('ip_address_cloud', ''))
        air_conditioner["ir_remote"] = str(data.get('ir_remote', ''))

        house['house_year'] = int(data.get('house_year', 0))

        house['window1_frame'] = str(data.get('window1_frame', ''))
        house['window1_glazing'] = str(data.get('window1_glazing', ''))
        house['window1_year'] = int(data.get('window1_year', 0))
        house['window1_width'] = float(data.get('window1_width', 0))
        house['window1_height'] = float(data.get('window1_height', 0))
        house['window1_u_value'] = float(data.get('window1_u_value', 0))

        house['wall1'] = str(data.get('wall1', ''))
        house['wall1_width'] = float(data.get('wall1_width', 0))
        house['wall1_height'] = float(data.get('wall1_height', 0))
        house['construction_wall1'] = str(data.get('construction_wall1', ''))
        house['wall1_type'] = int(data.get('wall1_type', 0))
        house['wall1_u_value'] = float(data.get('wall1_u_value', 0))
        house['wall1_diff_temp'] = float(data.get('wall1_diff_temp', 0))

        house['door_wall1'] = int(data.get('door_wall1', 0))
        house['door_wall1_width'] = float(data.get('door_wall1_width', 0))
        house['door_wall1_height'] = float(data.get('door_wall1_height', 0))

        house['window2_frame'] = str(data.get('window2_frame', ''))
        house['window2_glazing'] = str(data.get('window2_glazing', ''))
        house['window2_year'] = int(data.get('window2_year', 0))
        house['window2_width'] = float(data.get('window2_width', 0))
        house['window2_height'] = float(data.get('window2_height', 0))

        house['wall2'] = str(data.get('wall2', ''))
        house['wall2_width'] = float(data.get('wall2_width', 0))
        house['construction_wall2'] = str(data.get('construction_wall2', ''))

        house['door_wall2'] = int(data.get('door_wall2', 0))
        house['door_wall2_width'] = float(data.get('door_wall2_width', 0))
        house['door_wall2_height'] = float(data.get('door_wall2_height', 0))

        house['window3_frame'] = str(data.get('window3_frame', ''))
        house['window3_glazing'] = str(data.get('window3_glazing', ''))
        house['window3_year'] = int(data.get('window3_year', 0))
        house['window3_width'] = float(data.get('window3_width', 0))
        house['window3_height'] = float(data.get('window3_height', 0))

        house['wall3'] = str(data.get('wall3', ''))
        house['construction_wall3'] = str(data.get('construction_wall3', ''))

        house['door_wall3'] = int(data.get('door_wall3', 0))
        house['door_wall3_width'] = float(data.get('door_wall3_width', 0))
        house['door_wall3_height'] = float(data.get('door_wall3_height', 0))

        house['window4_frame'] = str(data.get('window4_frame', ''))
        house['window4_glazing'] = str(data.get('window4_glazing', ''))
        house['window4_year'] = int(data.get('window4_year', 0))
        house['window4_width'] = float(data.get('window4_width', 0))
        house['window4_height'] = float(data.get('window4_height', 0))

        house['ceiling'] = str(data.get('ceiling', ''))
        house['construction_ceiling'] = str(data.get('construction_ceiling', ''))

        house['floor'] = str(data.get('floor', ''))
        house['construction_floor'] = str(data.get('construction_floor', ''))

        house['wall4'] = str(data.get('wall4', ''))
        house['construction_wall4'] = str(data.get('construction_wall4', ''))

        house['door_wall4'] = int(data.get('door_wall4', 0))
        house['door_wall4_width'] = float(data.get('door_wall4_width', 0))
        house['door_wall4_height'] = float(data.get('door_wall4_height', 0))

        write_data_to_file(config_data, path)

        return 1

    except KeyError as error:
        print("Missing key: ", error)
        return -1


def write_data_to_data_file(weather_data: None | dict = None, sun: None | classes.CalcSunPos = None,
                            pv: None | classes.PVProfit = None, market: None | classes.MarketData = None,
                            time: None | list[str] = None, radiation: None | list[float] = None,
                            radiation_dni: None | list[float] = None, power: None | list[float] = None,
                            market_price: None | list[float] = None, path: None | str = None, energy: float = 0
                            ) -> int:
    """

    :param energy:
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
        data_file_path = consts.data_file_Path
    else:
        data_file_path = path

    data: dict = {
        "write_time": {
            "time": datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
            "format": "%d-%m-%Y %H:%M:%S"
        },
        "energy": {
            "energy": energy
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

            write_data_to_file(data, data_file_path)

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

            write_data_to_file(data, data_file_path)

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

        write_data_to_file(data, data_file_path)

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
        print("Try again")
        file_path = file_path[1:]
        print("Try again with: " + file_path)
        try:
            with open(file_path, 'rb') as f:
                data = tomli.load(f)
            return data
        except FileNotFoundError:
            return None


def write_data_to_file(data: dict, file_path: str) -> None:
    """

    :param data:
    :param file_path:
    :return:
    """
    try:
        with open(file_path, 'wb') as f:
            tomli_w.dump(data, f)
        return data
    except FileNotFoundError:
        print("No File at " + file_path)
        print("Try again")
        file_path = file_path[1:]
        print("Try again with: " + file_path)
        try:
            with open(file_path, 'wb') as f:
                tomli_w.dump(data, f)
        except FileNotFoundError:
            print("No File at " + file_path)


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


@freeze_all
@lru_cache(maxsize=None)
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
def generate_weather_data(data: dict, config_data: dict) -> list[str]:
    """

    :param data:
    :param config_data:
    :return:
    """
    if not os.path.exists(consts.downloads_file_Path):
        os.mkdir(consts.downloads_file_Path)

    config_coordinates = config_data["coordinates"]
    config_pv = config_data["pv"]

    start_date = datetime.datetime.strptime(data['start_date_weather'], "%Y-%m-%d")
    end_date = datetime.datetime.strptime(data['end_date_weather'], "%Y-%m-%d")

    weather_date = classes.Weather(
        config_coordinates['latitude'], config_coordinates['longitude'],
        datetime.datetime.strftime(start_date, "%d-%m-%Y"),
        datetime.datetime.strftime(end_date, "%d-%m-%Y")).data

    pv = classes.PVProfit(config_pv["module_efficiency"], config_pv["area"],
                          config_pv["tilt_angle"], config_pv["exposure_angle"],
                          config_pv["temperature_coefficient"],
                          config_pv["nominal_temperature"], config_pv["mounting_type"])

    power_data: dict = {}
    energy_data: dict = {}
    msg: list[str] = []

    for date in weather_date.keys():
        sun = classes.CalcSunPos(config_coordinates['latitude'],
                                 config_coordinates['longitude'],
                                 date)

        power_data[date]: dict = {}
        energy_data_list: list[float] = []
        for t in weather_date[date].keys():
            if t != "daily":
                time_float: float = int(t[:2]) + int(t[3:]) / 100
                azimuth: float = sun.calc_azimuth(time_float)
                elevation: float = sun.calc_solar_elevation(time_float)
                incidence: float = pv.calc_incidence_angle(elevation, azimuth)
                eff: float = pv.calc_temp_dependency(weather_date[date][t]["temp"],
                                                     weather_date[date][t]["direct_radiation"])
                power_data[date][t] = pv.calc_power(weather_date[date][t]["direct_radiation"], incidence, elevation,
                                                    eff)
                energy_data_list.append(power_data[date][t])
        energy_data[date] = calc_energy(energy_data_list)

    if "excel_weather" in data.keys():
        if os.path.exists(rf"{consts.downloads_file_Path}weather_data.xlsx"):
            os.remove(rf"{consts.downloads_file_Path}weather_data.xlsx")
        if data["excel_weather"] == "on":
            df = pd.DataFrame.from_dict(energy_data, orient='index', columns=['energy [kWh]'])
            df.to_excel(f'{consts.downloads_file_Path}weather_data.xlsx')
            msg.append("excel_weather")

    if "plot_png_weather" in data.keys():
        if data["plot_png_weather"] == "on":
            if os.path.exists(rf"{consts.downloads_file_Path}weather_plot.png"):
                os.remove(rf"{consts.downloads_file_Path}weather_plot.png")
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
            plt.savefig(rf"{consts.downloads_file_Path}weather_plot.png")
            msg.append("plot_weather")

    if "excel_market" in data.keys():
        if os.path.exists(rf"{consts.downloads_file_Path}market_data.xlsx"):
            os.remove(rf"{consts.downloads_file_Path}market_data.xlsx")
        if data["excel_market"] == "on":
            df = pd.DataFrame.from_dict(energy_data, orient='index', columns=['price [ct]'])
            df.to_excel(f'{consts.downloads_file_Path}market_data.xlsx')
            msg.append("excel_market")

    return msg


@freeze_all
@lru_cache(maxsize=None)
def generate_market_data(data: dict, config_data: dict) -> list[str]:
    """

    :param data:
    :param config_data:
    :return:
    """
    if not os.path.exists(consts.downloads_file_Path):
        os.mkdir(consts.downloads_file_Path)

    market_datas = classes.MarketData(config_data["market"]["consumer_price"], data['start_date_market'],
                                      data['end_date_market']).data

    msg: list[str] = []
    price_data: list[float] = []
    time_data: list[float] = []
    data_dict: dict = {}

    for i, market_data in enumerate(market_datas):
        time_data.append(f"{market_data['date']} {market_data['start_timestamp']}")
        price_data.append(market_data['consumerprice'])
        data_dict.update({f"{market_data['date']} {market_data['start_timestamp']}": market_data['consumerprice']})

    if "excel_market" in data.keys():
        if os.path.exists(rf"{consts.downloads_file_Path}market_data.xlsx"):
            os.remove(rf"{consts.downloads_file_Path}market_data.xlsx")
        if data["excel_market"] == "on":
            df = pd.DataFrame.from_dict(data_dict, orient='index', columns=['price [ct]'])
            df.to_excel(f'{consts.downloads_file_Path}market_data.xlsx')
            msg.append("excel_market")

    if "plot_png_market" in data.keys():
        if data["plot_png_market"] == "on":
            if os.path.exists(rf"{consts.downloads_file_Path}plot_market.png"):
                os.remove(rf"{consts.downloads_file_Path}plot_market.png")
            if len(price_data) > 50:
                x = len(price_data) * 0.25
                y = x * 0.4
            else:
                x = 10
                y = 5

            plt.figure(figsize=(x, y))
            plt.grid()
            plt.plot(time_data, price_data, label="price [ct]")
            plt.xticks(rotation=90, ha="right", fontsize=18)
            x = len(price_data)
            z = max(price_data)
            z = (z + (100 if z > 100 else 5))
            ticks = np.arange(0, z, step=(x // 100 * 10 if z > 100 else 1))
            plt.yticks(ticks=ticks, ha="right", fontsize=20)
            plt.legend(loc="upper left", fontsize=20)
            plt.tight_layout()
            plt.savefig(rf"{consts.downloads_file_Path}market_plot.png")
            msg.append("plot_market")

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


@lru_cache(maxsize=None)
def data_analyzer(path: None | str = None) -> int | tuple[float, float, float, str, str, str, str, list, list, float,
str, float]:
    config_data: dict = read_data_from_file(consts.config_file_Path)

    config_pv: dict = config_data["pv"]
    if path is None:
        path = rf"../uploads/{os.listdir("../uploads")[0]}"

    data = json.load(open(path, "rb+"))

    location: dict = data["inputs"]["location"]
    meteo_data: dict = data["inputs"]["meteo_data"]
    pv_alignment: dict = data["inputs"]["mounting_system"]["fixed"]
    datas: dict = data["outputs"]["hourly"]

    lat: float = location["latitude"]
    lon: float = location["longitude"]
    ele: float = location["elevation"]

    slope: float = pv_alignment["slope"]["value"]
    azimuth: float = pv_alignment["azimuth"]["value"]

    rad_database: str = meteo_data["radiation_db"]
    meteo_database: str = meteo_data["meteo_db"]
    year_min: str = meteo_data["year_min"]
    year_max: str = meteo_data["year_max"]

    power_data: list = []
    date_time_data: list = []

    pv: classes.PVProfit = classes.PVProfit(config_pv["module_efficiency"], config_pv["area"],
                                            config_pv["tilt_angle"], config_pv["exposure_angle"],
                                            config_pv["temperature_coefficient"],
                                            config_pv["nominal_temperature"],
                                            config_pv["mounting_type"])

    if "Gb(i)" not in datas[0]:
        print(datas[0])
        return -1

    if slope == 0 and azimuth == 0:
        for data in datas:
            date: str = datetime.datetime.strptime(data["time"], "%Y%m%d:%H%M").strftime("%d-%m-%Y")
            time: float = float(datetime.datetime.strptime(data["time"], "%Y%m%d:%H%M").strftime("%H.%M"))

            sun: classes.CalcSunPos = classes.CalcSunPos(lat, lon, date)
            azimuth: float = sun.calc_azimuth(time)
            elevation: float = sun.calc_solar_elevation(time)

            incidence: float = pv.calc_incidence_angle(elevation, azimuth)
            eff: float = pv.calc_temp_dependency(20, data["Gb(i)"])
            power: float = pv.calc_power(data["Gb(i)"], incidence, elevation, eff)

            date_time: str = datetime.datetime.strptime(data["time"], "%Y%m%d:%H%M").strftime("%d-%m-%Y - %H:%M")

            power_data.append(round(power, 2))
            date_time_data.append(date_time)

    elif slope == config_pv["tilt_angle"] and azimuth == config_pv["exposure_angle"]:
        for data in datas:
            date: str = datetime.datetime.strptime(data["time"], "%Y%m%d:%H%M").strftime("%d-%m-%Y")
            time: float = float(datetime.datetime.strptime(data["time"], "%Y%m%d:%H%M").strftime("%H.%M"))

            sun: classes.CalcSunPos = classes.CalcSunPos(lat, lon, date)

            adj_data: float = sun.adjust_for_new_angle(data["Gb(i)"], slope, azimuth, config_pv["tilt_angle"],
                                                       config_pv["exposure_angle"], time)

            azimuth: float = sun.calc_azimuth(time)
            elevation: float = sun.calc_solar_elevation(time)

            incidence: float = pv.calc_incidence_angle(elevation, azimuth)
            eff: float = pv.calc_temp_dependency(20, abs(adj_data))
            power: float = pv.calc_power(abs(adj_data), incidence, elevation, eff)

            date_time: str = datetime.datetime.strptime(data["time"], "%Y%m%d:%H%M").strftime("%d-%m-%Y - %H:%M")

            power_data.append(round(power, 2))
            date_time_data.append(date_time)

    else:
        for data in datas:
            date: str = datetime.datetime.strptime(data["time"], "%Y%m%d:%H%M").strftime("%d-%m-%Y")
            time: float = float(datetime.datetime.strptime(data["time"], "%Y%m%d:%H%M").strftime("%H.%M"))

            sun: classes.CalcSunPos = classes.CalcSunPos(lat, lon, date)
            adj_data: float = sun.adjust_for_new_angle(data["Gb(i)"], slope, azimuth, config_pv["tilt_angle"],
                                                       config_pv["exposure_angle"], time)
            azimuth: float = sun.calc_azimuth(time)
            elevation: float = sun.calc_solar_elevation(time)

            incidence: float = pv.calc_incidence_angle(elevation, azimuth)
            eff: float = pv.calc_temp_dependency(20, abs(adj_data))

            power: float = pv.calc_power(abs(adj_data), incidence, elevation, eff)

            date_time: str = datetime.datetime.strptime(data["time"], "%Y%m%d:%H%M").strftime("%d-%m-%Y - %H:%M")

            power_data.append(round(power, 2))
            date_time_data.append(date_time)

    max_energy: float = max(power_data)
    time_max_energy: str = date_time_data[power_data.index(max_energy)]
    average_energy: float = round(calc_energy(power_data, 1, True) / (year_max + 1 - year_min), 2)

    plt.clf()
    plt.figure(figsize=(20, 6))
    plt.grid(True)
    plt.plot(date_time_data, power_data, '-', linewidth=0.5, alpha=0.5)
    plt.xticks(np.linspace(0, len(date_time_data), 100), rotation=90, ha='right', fontsize=8)
    plt.tight_layout()
    plt.margins(0.01)
    plt.savefig(f".{consts.downloads_file_Path}plot_uploaded_data.png", dpi=300)

    return (lat, lon, ele, rad_database, meteo_database, year_min, year_max, power_data, date_time_data,
            max_energy, time_max_energy, average_energy)


def heating_power():
    data = read_data_from_file(consts.config_file_Path)

    house_data: dict = data["house"]
    weather_data = data["coordinates"]
    shelly_data = data["shelly"]

    hp: classes.RequiredHeatingPower = classes.RequiredHeatingPower()
    weather: classes.Weather = classes.Weather(weather_data["latitude"], weather_data["longitude"])
    trv: classes.ShellyTRVControl = classes.ShellyTRVControl(shelly_data["ip_address"])

    room = hp.Room

    floor = room.Floor
    ceiling = room.Ceiling

    wall1 = room.Wall1
    wall2 = room.Wall2
    wall3 = room.Wall3
    wall4 = room.Wall4

    window1 = wall1.Window1
    window2 = wall2.Window1
    window3 = wall3.Window1
    window4 = wall4.Window1

    door1 = wall1.Door
    door2 = wall2.Door
    door3 = wall3.Door
    door4 = wall4.Door

    floor.area = house_data.get("wall1_width", 0) * house_data.get("wall2_width", 0)

    floor.u_wert = hp.u_value[house_data.get("floor", 0)][house_data.get("construction_floor", 0)][
        house_data.get("house_year" if house_data["house_year"] < 1995 else 1995, 0)]

    room.Ceiling.area = house_data.get("wall1_width", 0) * house_data.get("wall2_width", 0)

    ceiling.u_wert = hp.u_value.get(house_data["ceiling"], 0).get(house_data["construction_ceiling"], 0).get(
        house_data["house_year"] if house_data["house_year"] < 1995 else 1995, 0)

    wall1.area = house_data.get("wall1_width", 0) * house_data.get("wall1_height", 0)

    if house_data.get("wall1") == "ENEV Außenwand" or house_data.get("wall") == "ENEV Innenwand":
        wall1.u_wert = hp.u_value.get(house_data["wall1"], 0).get(house_data["construction_wall1"], 0)

    else:
        wall1.u_wert = hp.u_value.get(house_data["wall1"], 0).get(house_data["construction_wall1"], 0).get(
            house_data["house_year"] if house_data["house_year"] < 1995 else 1995, 0)

    window1.area = house_data.get("window1_width", 0) * house_data.get("window1_height", 0)

    if house_data.get("window1_frame") == "ENEV":
        window1.u_wert = hp.u_value.get("Fenster", {}).get(house_data["window1_frame"], {}).get(
            house_data["window1_glazing"], 0)
    else:
        window1.u_wert = hp.u_value.get("Fenster", {}).get(house_data["window1_frame"], {}).get(
            house_data["window1_glazing"], {}).get(
            house_data["window1_year"] if house_data["window1_year"] < 1995 else 1995, 0)

    door1.area = house_data.get("door_wall1_width", 0) * house_data.get("door_wall1_height", 0)
    door1.u_wert = hp.u_value.get("Türen", 0).get("alle", 0).get(
        house_data["house_year"] if house_data["house_year"] < 1995 else 1995, 0)

    wall2.area = house_data.get("wall2_width", 0) * house_data.get("wall1_height", 0)

    wall2.u_wert = hp.u_value.get(house_data["wall2"], 0).get(house_data["construction_wall2"], 0).get(
        house_data["house_year"] if house_data["house_year"] < 1995 else 1995, 0)
    window2.area = house_data.get("window2_width", 0) * house_data.get("window2_height", 0)
    window2.u_wert = hp.u_value.get("Fenster").get(house_data["window2_frame"], {}).get(
        house_data["window2_glazing"], {}).get(
        house_data["window2_year"] if house_data["window2_year"] < 1995 else 1995, 0)
    door2.area = house_data.get("door_wall2_width", 0) * house_data.get("door_wall2_height", 0)
    door2.u_wert = hp.u_value.get("Türen", 0).get("alle", 0).get(
        house_data["house_year"] if house_data["house_year"] < 1995 else 1995, 0)

    wall3.area = house_data.get("wall1_width", 0) * house_data.get("wall1_height", 0)

    wall3.u_wert = hp.u_value.get(house_data["wall3"], 0).get(house_data["construction_wall3"], 0).get(
        house_data["house_year"] if house_data["house_year"] < 1995 else 1995, 0)
    window3.area = house_data.get("window3_width", 0) * house_data.get("window3_height", 0)
    window3.u_wert = hp.u_value.get("Fenster", {}).get(house_data["window3_frame"], {}).get(
        house_data["window3_glazing"], {}).get(
        house_data["window3_year"] if house_data["window3_year"] < 1995 else 1995, 0)
    door3.area = house_data.get("door_wall3_width", 0) * house_data.get("door_wall3_height", 0)
    door3.u_wert = hp.u_value.get("Türen", 0).get("alle", 0).get(
        house_data["house_year"] if house_data["house_year"] < 1995 else 1995, 0)

    wall4.area = house_data.get("wall2_width", 0) * house_data.get("wall1_height", 0)

    wall4.u_wert = hp.u_value.get(house_data["wall4"], 0).get(house_data["construction_wall4"]).get(
        house_data["house_year"] if house_data["house_year"] < 1995 else 1995, 0)
    window4.area = house_data["window4_width"] * house_data["window4_height"]
    window4.u_wert = hp.u_value.get("Fenster", {}).get(house_data["window4_frame"], {}).get(
        house_data["window4_glazing"], {}).get(
        house_data["window4_year"] if house_data["window4_year"] < 1995 else 1995, 0)
    door4.area = house_data.get("door_wall4_width", 0) * house_data.get("door_wall4_height", 0)
    door4.u_wert = hp.u_value.get("Türen", 0).get("alle", 0).get(
        house_data["house_year"] if house_data["house_year"] < 1995 else 1995, 0)

    room.volume = house_data.get("wall1_width", 0) * house_data.get("wall1_height", 0) * house_data.get("wall2_width",
                                                                                                        0)

    trv_data: dict = trv.get_thermostat()
    if trv_data is None:
        trv_data: dict = trv.get_thermostat(timeout=10)

    indoor_temp: float = (trv_data.get("tmp").get("value")) if trv_data is not None else 18

    ret_dat: list = []
    diff_data: list = []

    today = weather.data[list(weather.data.keys())[0]]
    i = 0

    for t in today.keys():
        print(t)
        if t != "daily":
            print(today[t])
            outdoor_temp: float = today[t]["temp"]
            diff_temp: float = (indoor_temp + i) - outdoor_temp

            i += 1

            room.Floor.temp_diff = diff_temp
            room.Ceiling.temp_diff = diff_temp
            room.Wall1.temp_diff = diff_temp
            room.Wall2.temp_diff = diff_temp
            room.Wall3.temp_diff = diff_temp
            room.Wall4.temp_diff = diff_temp
            d = hp.calc_heating_power(room)

            diff_data.append(diff_temp)
            ret_dat.append(d)

    debug.printer(diff_data, ret_dat)
    # print((room.volume * 1.225 * 1000 * diff_temp) / (3000 - ret_dat))


def heating_power2():
    def _calc_area(data_house: dict, prefix: str, prefix2: str | None = None):
        try:
            if prefix2 is None:
                prefix2 = prefix
            area = data_house.get(f"{prefix}_width", 0) * data_house.get(f"{prefix2}_width", 0)
            return area

        except AttributeError as err:
            print(prefix, prefix2)
            print(f"Attribute Missing: {err}")
            return 0

    def _get_u_value(data_house: dict, u_value: dict, prefix: str):
        try:
            if "wall" in prefix:

                wall_: str = data_house.get(prefix, "")
                wall_type: str = data_house.get(f"construction_{prefix}", "")
                year: int = data_house.get(f"house_year", 0) if data_house.get(f"house_year") < 1995 else 1995

                if wall_ == "ENEV Außenwand" or wall_ == "ENEV Innenwand":
                    return u_value.get("Wand").get(wall).get(int(wall_type))
                elif wall_ == "u_value":
                    return data_house.get(f"{prefix}_u_value", 0)
                else:
                    return u_value.get("Wand").get(wall_).get(wall_type).get(year)

            elif "window" in prefix:
                window_: str = data_house.get(f"{prefix}_frame", "")
                glazing: str = data_house.get(f"{prefix}_glazing", "")
                window_year: int = data_house.get(f"{prefix}_year", 0) if data_house.get(
                    f"{prefix}_year") < 1995 else 1995

                if window_ == "ENEV":
                    return u_value.get("Fenster").get(window_).get(int(glazing))
                elif window_ == "u_value":
                    return data_house.get(f"{prefix}_u_value", 0)
                else:
                    return u_value.get("Fenster").get(window_).get(glazing).get(window_year)

            elif "door" in prefix:
                year: int = data_house.get(f"house_year", 0) if data_house.get(f"house_year") < 1995 else 1995
                return u_value.get("Türen").get("alle").get(year)

            elif "floor" in prefix:
                floor_: str = data_house.get(f"floor", "")
                floor_type: str = data_house.get(f"construction_floor", "")
                year: int = data_house.get(f"house_year", 0) if data_house.get(f"house_year") < 1995 else 1995
                if floor_ == "ENEV unbeheiztes Geschoss" or floor_ == "ENEV beheiztes Geschoss":
                    u = u_value.get("Boden").get(floor_).get(int(floor_type))
                    return u
                elif floor_ == "u_value":
                    return data_house.get(f"{prefix}_u_value", 0)
                else:
                    return u_value.get("Boden").get(floor_).get(floor_type).get(year)

            elif "ceiling" in prefix:
                ceiling_: str = data_house.get(f"ceiling", "")
                ceiling_type: str = data_house.get(f"construction_ceiling", "")
                year: int = data_house.get(f"house_year", 0) if data_house.get(f"house_year") < 1995 else 1995
                if ceiling_ == "ENEV unbeheiztes Geschoss" or ceiling_ == "ENEV beheiztes Geschoss" or ceiling_ == "ENEV Dach":
                    return u_value.get("Decke").get(ceiling_).get(int(ceiling_type))
                elif ceiling_ == "u_value":
                    return data_house.get(f"{prefix}_u_value", 0)
                else:
                    return u_value.get("Decke").get(ceiling_).get(ceiling_type).get(year)
        except AttributeError as err:
            print(prefix)
            print(f"Attribute Missing: {err}")
            return 0

    file_data: dict = read_data_from_file(consts.config_file_Path)

    data: dict = file_data["house"]
    weather_data = file_data["coordinates"]
    shelly_data = file_data["shelly"]

    hp: classes.RequiredHeatingPower = classes.RequiredHeatingPower()
    weather: classes.Weather = classes.Weather(weather_data["latitude"], weather_data["longitude"])
    trv: classes.ShellyTRVControl = classes.ShellyTRVControl(shelly_data["ip_address"])

    room: classes.RequiredHeatingPower.Room = hp.Room

    floor = room.Floor
    ceiling = room.Ceiling

    floor.area = _calc_area(data, f"wall1", f"wall2")
    ceiling.area = _calc_area(data, f"wall1", f"wall2")

    floor.u_wert = _get_u_value(data, hp.u_value, "floor")
    ceiling.u_wert = _get_u_value(data, hp.u_value, "ceiling")

    room.volume = data.get("wall1_width", 0) * data.get("wall1_height", 0) * data.get("wall2_width", 0)

    for wall_number in range(1, 5):
        window_number: int = 1
        wall = getattr(room, f"Wall{wall_number}")
        window = getattr(wall, f"Window{window_number}")
        door = getattr(wall, "Door")

        wall.area = _calc_area(data, f"wall{wall_number}")
        window.area = _calc_area(data, f"window{window_number}")
        door.area = _calc_area(data, f"door_wall{wall_number}")

        wall.u_wert = _get_u_value(data, hp.u_value, f"wall{wall_number}")
        window.u_wert = _get_u_value(data, hp.u_value, f"window{window_number}")
        door.u_wert = _get_u_value(data, hp.u_value, f"door")

    trv_data: dict = trv.get_thermostat()
    if trv_data is None:
        trv_data: dict = trv.get_thermostat(timeout=10)

    indoor_temp: float = (trv_data.get("tmp").get("value")) if trv_data is not None else 18

    ret_dat: list = []
    diff_data: list = []

    today = weather.data[list(weather.data.keys())[0]]
    i = 0

    for t in today.keys():
        print(t)
        if t != "daily":
            print(today[t])
            outdoor_temp: float = today[t]["temp"]
            diff_temp: float = (indoor_temp + i) - outdoor_temp

            i += 1

            room.Floor.temp_diff = diff_temp
            room.Ceiling.temp_diff = diff_temp
            room.Wall1.temp_diff = diff_temp
            room.Wall2.temp_diff = diff_temp
            room.Wall3.temp_diff = diff_temp
            room.Wall4.temp_diff = diff_temp
            d = hp.calc_heating_power(room)

            diff_data.append(diff_temp)
            ret_dat.append(d)

    debug.printer(diff_data, ret_dat)

    return 1


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

    ret = write_data_to_config(test_data, "../config/function_tes.toml")
    if ret == 1:
        print('✅', "PASS")
    elif ret == -1:
        print('❌', "FAIL")
    ret = 0

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

    ret = write_data_to_data_file(weather_test_data, classes.CalcSunPos(49.5198371, 11.2948653),
                                  classes.PVProfit(20, 10, 0, 30, -0.1, 25, 1), classes.MarketData(13),
                                  path=r'../data/test_data_classes.toml')
    if ret == 1:
        print('✅', "PASS, classes")
    elif ret == -1:
        print('❌', "FAIL, classes")
    ret = 0

    ret = write_data_to_data_file(time=time_test_data, radiation=radiation_test_data, power=power_test_data,
                                  market_price=market_price_test_data, path=r'../data/test_data_direct.toml')

    if ret == 1:
        print('✅', "PASS, direct radiation")
    elif ret == -1:
        print('❌', "FAIL, direct radiation")
    ret = 0

    ret = write_data_to_data_file(time=time_test_data, radiation_dni=radiation_dni_test_data, power=power_test_data,
                                  market_price=market_price_test_data, path=r'../data/test_data_dni.toml')

    if ret == 1:
        print('✅', "PASS, dni radiation")
    elif ret == -1:
        print('❌', "FAIL, dni radiation")
    ret = 0

    print("Test read_data_from_file")
    ret = read_data_from_file(r"../data/test_data_dni.toml")
    if ret is not None:
        print('✅', "PASS")
    else:
        print('❌', "FAIL")
    ret = 0

    print("Test get_coord")
    ret = get_coord("Hirschenau", "2", "Rückersdorf", 90607, 'Deutschland')
    print(ret)
    if ret[0] == 49.4989187 and ret[1] == 11.249947:
        print('✅', "PASS")
    else:
        print('❌', "FAIL")
    ret = 0

    print("Test calc_energy")
    energy_test: list[float] = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    ret = calc_energy(energy_test, 1, False)
    if ret == 50:
        print('✅', "PASS")
    else:
        print('❌', "FAIL")
    ret = 0

    print("Test generate_weather_data")

    print("Test data_analyzer")

    data_analyzer()

    print("Test unpack_data")
    data_test: dict = tomli.load(open(r"../data/data.toml", "rb"))
    ret = unpack_data(data_test)
    if ret != (-1, -1, -1, -1):
        print('✅', "PASS")
    else:
        print('❌', "FAIL")
    ret = 0

    print("Test heating_power")
    # heating_power()
    ret = heating_power2()

    if ret == 1:
        print('✅', "PASS")
    else:
        print('❌', "FAIL")
    ret = 0

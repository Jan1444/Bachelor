#  -*- coding: utf-8 -*-

import datetime
import json
import os
from functools import lru_cache, wraps

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import tomli
import tomli_w
from frozendict import frozendict

# from config import config_data, write_config_data
from config import ConfigManager as ConfigManager_config
from module import classes, consts, debug
from data import energy_data, write_energy_data
from data import EnergyManager as ConfigManager_data

config_manager_config = ConfigManager_config("config_test.toml")
config_manager_data = ConfigManager_data("data.toml")


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
    config_manager_config.reload_config()
    config_data = config_manager_config.config_data

    if path is None:
        path = consts.config_file_Path

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
        config_manager_config.write_config_data(config_data)
        # write_config_data(config_data)

        return 1

    except KeyError as error:
        print("Missing key: ", error)
        return -1


def write_data_to_data_file(time, power: list[float], market_price: list[float], energy: float,
                            radiation: None | list[float] = None, radiation_dni: None | list[float] = None,
                            path: None | str = None) -> int:
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
    # write radiation
    try:
        if radiation is not None:
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

            if path is None:
                write_energy_data(data)
            else:
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

    # write radiation_dni
    try:
        if radiation_dni:
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

            if path is None:
                write_energy_data(data)
            else:
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
def calc_energy(energy: list, interval: float = 0.25, kwh: bool = True, round_: None | int = None) -> float:
    """

    :param energy:
    :param interval:
    :param kwh:
    :param round_:
    :return:
    """
    multiplier = 1
    if kwh:
        multiplier = 1000
    power_values = list(map(lambda x: x / multiplier, energy))
    total_energy = sum((power_values[i] + power_values[i + 1]) / 2 * interval for i in range(len(power_values) - 1))
    total_energy = sum(power_values[i] * interval for i in range(len(power_values) - 1))

    if round_ is not None:
        total_energy = round(total_energy, round_)
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


def get_weather_data(config_data_: dict):
    coord = config_data_["coordinates"]
    w = classes.Weather(coord["latitude"], coord["longitude"])
    return w.data


def get_sun_data(config_data_: dict, tme: float) -> (float, float):
    coord = config_data_["coordinates"]
    s = classes.CalcSunPos(coord["latitude"], coord["longitude"])
    az = s.calc_azimuth(tme)
    el = s.calc_solar_elevation(tme)
    return az, el


def get_pv_data(config_data_: dict, temp: float, rad: float, azimuth: float, elevation: float, dni: bool = False) -> (
        float, float):
    pv = config_data_["pv"]
    p = classes.PVProfit(pv["module_efficiency"], pv["area"], pv["tilt_angle"], pv["exposure_angle"],
                         pv["temperature_coefficient"], pv["nominal_temperature"], pv["mounting_type"])
    incidence_angle = p.calc_incidence_angle(elevation, azimuth)
    if dni:
        power: float = p.calc_power_with_dni(rad, incidence_angle, temp)
        return power
    eff: float = p.calc_temp_dependency(temp, rad)
    power: float = p.calc_power(rad, incidence_angle, elevation, eff)
    return power


def string_time_to_float(tme: str) -> float:
    tme_list: list = tme.split(":")
    return int(tme_list[0]) + float(tme_list[1]) / 100


def save_mor_ev_data(config_data: dict) -> dict:
    power_list: list = []
    write_dict: dict = {
        "write_time": {
            "time": datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
            "format": "%d-%m-%Y %H:%M:%S"
        }
    }

    weather_data: dict = get_weather_data(config_data)
    today_data = list(weather_data.keys())[0]
    weather_data_today = weather_data[today_data]
    weather_data_today.pop("daily")

    for tme in weather_data_today:
        data: dict = weather_data_today[tme]
        tme_float: float = string_time_to_float(tme)
        azimuth, elevation = get_sun_data(config_data, tme_float)
        temp: float = float(data.get("temp", 0))
        radiation: float = float(data.get("dni_radiation", 0))
        power: float = get_pv_data(config_data, temp, radiation, azimuth, elevation, True)

        write_dict.update(
            {
                tme: {
                    "dni_radiation": radiation,
                    "cloudcover": data.get("cloudcover", 0),
                    "temp": temp,
                    "power": power
                }
            }
        )

        power_list.append(power)

    energy: float = calc_energy(power_list, round_=3)

    write_dict.update(
        {
            "energy": energy
        }
    )

    return write_dict


@freeze_all
@lru_cache(maxsize=None)
def generate_weather_data(data: dict, config_data_: dict) -> list[str]:
    """

    :param data:
    :param config_data_:
    :return:
    """
    if not os.path.exists(consts.downloads_file_Path):
        os.mkdir(consts.downloads_file_Path)

    config_coordinates = config_data_["coordinates"]
    config_pv = config_data_["pv"]

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
                time_float = string_time_to_float(t)
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
            plt.step(list(energy_data.keys()), list(energy_data.values()), label="Energy[kWh]")
            plt.xticks(rotation=90, ha="right", fontsize=18)

            _max = (max(energy_data.values()) + (100 if max(energy_data.values()) > 100 else 5))
            ticks = np.arange(0, _max, step=(len(energy_data.keys()) // 100 * 10 if _max > 100 else 1))

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
def generate_market_data(data: dict, config_data_: dict) -> list[str]:
    """

    :param data:
    :param config_data_:
    :return:
    """

    if not os.path.exists(consts.downloads_file_Path):
        os.mkdir(consts.downloads_file_Path)

    market_datas = classes.MarketData(config_data_["market"]["consumer_price"], data['start_date_market'],
                                      data['end_date_market']).data

    msg: list[str] = []
    price_data: list[float] = []
    time_data: list[str] = []
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
            plt.step(time_data, price_data, label="price [ct]")
            plt.xticks(rotation=90, ha="right", fontsize=18)

            _max = (max(price_data) + (100 if max(price_data) > 100 else 5))
            ticks = np.arange(0, _max, step=(len(price_data) // 100 * 10 if _max > 100 else 1))

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
    config_manager_config.reload_config()
    config_data = config_manager_config.config_data
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

    config_manager_config.reload_config()
    config_data = config_manager_config.config_data

    data: dict = config_data["house"]
    weather_data = config_data["coordinates"]
    shelly_data = config_data["shelly"]

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


def comp_mor_ev_data(error: float = 1):
    from data import evening_data, morning_data

    debug.printer(evening_data, description="evening_data: ")
    debug.printer(morning_data, description="morning_data: ")

    tme_ev = evening_data.get("write_time", {"time": "0", "format": "0"})
    time_evening = datetime.datetime.strptime(tme_ev.get("time"), tme_ev.get("format"))

    tme_mor = morning_data.get("write_time", {"time": "0", "format": "0"})
    time_morning = datetime.datetime.strptime(tme_mor.get("time"), tme_mor.get("format"))

    if time_evening <= time_morning:
        print("No comparison available, no right time!")
        return -1

    total_dni_difference = 0
    count = 0

    for time_point, evening_values in evening_data.items():
        if time_point in ["energy", "write_time"]:
            continue

        morning_values = morning_data.get(time_point)
        if morning_values:
            total_dni_difference += abs(evening_values.get('dni_radiation', 0) - morning_values.get('dni_radiation', 0))
            count += 1

    energy_difference = abs(evening_data.get("energy", 0) - morning_data.get("energy", 0))

    if count > 0:
        average_dni_difference = total_dni_difference / count
    else:
        average_dni_difference = None

    return {
        "average_dni_difference": average_dni_difference,
        "energy_difference": energy_difference
    }


if __name__ == "__main__":
    z = comp_mor_ev_data()
    print(z)

if __name__ == "__main_":
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

    time_test_data: list = ['00:00', '00:15', '00:30', '00:45', '01:00', '01:15', '01:30', '01:45', '02:00', '02:15',
                            '02:30', '02:45', '03:00']
    power_test_data: list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
    market_price_test_data: list = [0.1, 0.2, 0.3]
    radiation_dni_test_data: list = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100, 1200, 1300]
    radiation_test_data: list = [10_000, 10_100, 10_200, 10_300, 10_400, 10_500, 10_600, 10_700, 10_800, 10_900, 11_000,
                                 11_100, 11_200]

    '''    ret = write_data_to_data_file(time=time_test_data, radiation=radiation_test_data, power=power_test_data,
                                  market_price=market_price_test_data, path=r'../data/test_data_direct.toml')'''

    if ret == 1:
        print('✅', "PASS, direct radiation")
    elif ret == -1:
        print('❌', "FAIL, direct radiation")
    ret = 0

    '''    ret = write_data_to_data_file(time=time_test_data, radiation_dni=radiation_dni_test_data, power=power_test_data,
                                  market_price=market_price_test_data, path=r'../data/test_data_dni.toml')'''

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
    ret = heating_power()

    if ret == 1:
        print('✅', "PASS")
    else:
        print('❌', "FAIL")
    ret = 0

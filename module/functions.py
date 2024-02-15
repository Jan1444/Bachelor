#  -*- coding: utf-8 -*-

import datetime
import json
import os
from functools import lru_cache, wraps

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import requests
import toml
from frozendict import frozendict

from module import classes, consts, debug


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


def precision(func, precision_: int = 5):
    @wraps(func)
    def wrapped(*args, **kwargs):
        precision_args = (round(arg, precision_) if isinstance(arg, (float, np.float32)) else arg for arg in args)

        precision_kwargs = {k: (round(v, precision_) if isinstance(v, (float, np.float32)) else v) for k, v in kwargs.items()}

        return func(*precision_args, **precision_kwargs)
    return wrapped


def read_data_from_file(file_path: str) -> dict | None:
    """

    :param file_path:
    :return:
    """
    try:
        with open(file_path, 'r') as f:
            data = toml.load(f)
        return data
    except FileNotFoundError:
        print("No File at " + file_path)
        print("Try again")
        file_path = file_path[1:]
        print("Try again with: " + file_path)
        try:
            with open(file_path, 'r') as f:
                data = toml.load(f)
            return data
        except FileNotFoundError:
            return None


def write_data_to_file(data: dict, file_path: str) -> dict:
    """

    :param data:
    :param file_path:
    :return:
    """
    try:
        with open(file_path, 'w') as f:
            toml.dump(data, f)
        return data
    except FileNotFoundError:
        print("No File at " + file_path)
        print("Try again")
        file_path = file_path[1:]
        print("Try again with: " + file_path)
        try:
            with open(file_path, 'w') as f:
                toml.dump(data, f)
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


@precision
@freeze_all
@lru_cache(maxsize=1_000)
def calc_energy(power: list, interval: float = 0.25, kwh: bool = True, round_: None | int = None) -> float:
    """

    :param power:
    :param interval:
    :param kwh:
    :param round_:
    :return:
    """
    multiplier = 1
    if kwh:
        multiplier = 1000
    power_values = list(map(lambda x: x / multiplier, power))
    total_energy = sum(power * interval for power in power_values)

    if round_ is not None:
        total_energy = round(total_energy, round_)
    debug.printer(total_energy)

    return float(total_energy)


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


def get_weather_data(config_data: dict, start: str | None = None, end: str | None = None):
    coord = config_data["coordinates"]
    w = classes.Weather(coord["latitude"], coord["longitude"], start, end)
    return w.data


def init_sun(config_data: dict, date: str | None = None) -> classes.CalcSunPos:
    coord = config_data["coordinates"]
    s = classes.CalcSunPos(coord["latitude"], coord["longitude"], date)
    return s


def get_sun_data(sun_class: classes.CalcSunPos, tme: float) -> (float, float):
    az = sun_class.calc_azimuth(tme)
    print(sun_class._calc_azimuth.cache_info())
    el = sun_class.calc_solar_elevation(tme)
    #print(sun_class.calc_solar_elevation.cache_info())
    return az, el


def init_pv(config_data: dict, number: int = 1) -> classes.PVProfit:
    pv = config_data["pv"]
    p = classes.PVProfit(pv[f"module_efficiency{number}"], pv[f"area{number}"], pv[f"tilt_angle{number}"],
                         pv[f"exposure_angle{number}"], pv[f"temperature_coefficient{number}"],
                         pv[f"nominal_temperature{number}"], pv[f"mounting_type{number}"])
    return p


def get_pv_data(pv_class: classes.PVProfit, temp: float, radiation: float, azimuth: float, elevation: float,
                dni: bool = False) -> (
        float, float):
    incidence_angle = pv_class.calc_incidence_angle(elevation, azimuth)
    if dni:
        power: float = pv_class.calc_power_with_dni(radiation, incidence_angle, temp)
        return power
    eff: float = pv_class.calc_temp_dependency(temp, radiation)
    power: float = pv_class.calc_power(radiation, incidence_angle, elevation, eff)
    return power


def init_market(config_data: dict, start_time: int | None = None, end_time: int | None = None) -> classes.MarketData:
    cc: float = config_data["market"].get("consumer_price", 0)
    m = classes.MarketData(cc, start_time, end_time)
    return m


def string_time_to_float(tme: str) -> float:
    tme_list: list = tme.split(":")
    return int(tme_list[0]) + float(tme_list[1]) / 100


def save_mor_ev_data(config_data: dict) -> dict:
    power_list: list = []
    write_dict: dict = {}

    weather_data: dict = get_weather_data(config_data)
    today_data = list(weather_data.keys())[0]
    weather_data_today = weather_data[today_data]
    weather_data_today.pop("daily")

    sun_class = init_sun(config_data)
    pv_class = init_pv(config_data)

    for tme, data in weather_data_today.items():
        tme_float: float = string_time_to_float(tme)
        azimuth, elevation = get_sun_data(sun_class, tme_float)
        temp: float = float(data.get("temp", 0))
        radiation: float = float(data.get("dni_radiation", 0))
        radiation_ghi: float = float(data.get("ghi_radiation", 0))
        # power: float = get_pv_data(pv_class, temp, radiation, azimuth, elevation, True)
        power: float = get_pv_data(pv_class, temp, radiation_ghi, azimuth, elevation, False)

        write_dict.update(
            {
                tme: {
                    "dni_radiation": radiation,
                    "ghi_radiation": radiation_ghi,
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


@precision
@freeze_all
@lru_cache(maxsize=1_000)
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


def data_analyzer(config_data: dict, path: None | str = None):
    if path is None:
        path = rf"./uploads/{os.listdir("./uploads")[0]}"

    data = json.load(open(path, "rb+"))

    config_pv: dict = config_data["pv"]

    location: dict = data["inputs"]["location"]
    meteo_data: dict = data["inputs"]["meteo_data"]
    pv_alignment: dict = data["inputs"]["mounting_system"]["fixed"]
    datas: dict = data["outputs"]["hourly"]

    lat: float = location["latitude"]
    lon: float = location["longitude"]
    ele: float = location["elevation"]

    slope: float = pv_alignment["slope"]["value"]
    azimuth: float = pv_alignment["azimuth"]["value"]

    rad_database: str = meteo_data.get("radiation_db", "0")
    meteo_database: str = meteo_data.get("meteo_db", "0")
    year_min: str = meteo_data.get("year_min", "0")
    year_max: str = meteo_data.get("year_max", "0")

    power_data: list = []
    date_time_data: list = []

    pv_class = init_pv(config_data)

    if "Gb(i)" not in datas[0]:
        print(datas[0])
        return -1

    if slope == 0 and azimuth == 0:
        for data in datas:
            date: str = datetime.datetime.strptime(data["time"], "%Y%m%d:%H%M").strftime("%d-%m-%Y")
            tme: float = float(datetime.datetime.strptime(data["time"], "%Y%m%d:%H%M").strftime("%H.%M"))

            sun_class = init_sun(config_data, date)
            azimuth, elevation = get_sun_data(sun_class, tme)

            temp: float = 17
            radiation: float = data.get("Gb(i)", 0)

            power: float = get_pv_data(pv_class, temp, radiation, azimuth, elevation)

            date_time: str = datetime.datetime.strptime(data["time"], "%Y%m%d:%H%M").strftime("%d-%m-%Y - %H:%M")

            power_data.append(round(power, 2))
            date_time_data.append(date_time)

    elif slope == config_pv["tilt_angle"] and azimuth == config_pv["exposure_angle"]:
        for data in datas:
            date: str = datetime.datetime.strptime(data["time"], "%Y%m%d:%H%M").strftime("%d-%m-%Y")
            tme: float = float(datetime.datetime.strptime(data["time"], "%Y%m%d:%H%M").strftime("%H.%M"))

            sun_class = init_sun(config_data, date)

            temp: float = 17
            radiation: float = data.get("Gb(i)", 0)

            adj_data: float = sun_class.adjust_for_new_angle(radiation, slope, azimuth, config_pv["tilt_angle"],
                                                             config_pv["exposure_angle"], tme)

            azimuth, elevation = get_sun_data(sun_class, tme)

            power: float = get_pv_data(pv_class, temp, abs(adj_data), azimuth, elevation)

            """incidence: float = pv.calc_incidence_angle(elevation, azimuth)
            eff: float = pv.calc_temp_dependency(20, abs(adj_data))
            power: float = pv.calc_power(abs(adj_data), incidence, elevation, eff)"""

            date_time: str = datetime.datetime.strptime(data["time"], "%Y%m%d:%H%M").strftime("%d-%m-%Y - %H:%M")

            power_data.append(round(power, 2))
            date_time_data.append(date_time)

    else:
        for data in datas:
            date: str = datetime.datetime.strptime(data["time"], "%Y%m%d:%H%M").strftime("%d-%m-%Y")
            tme: float = float(datetime.datetime.strptime(data["time"], "%Y%m%d:%H%M").strftime("%H.%M"))

            temp: float = 17
            radiation: float = data.get("Gb(i)", 0)

            sun_class = init_sun(config_data, date)

            adj_data: float = sun_class.adjust_for_new_angle(radiation, slope, azimuth, config_pv["tilt_angle"],
                                                             config_pv["exposure_angle"], tme)

            azimuth, elevation = get_sun_data(sun_class, tme)

            """incidence: float = pv.calc_incidence_angle(elevation, azimuth)
            eff: float = pv.calc_temp_dependency(20, abs(adj_data))

            power: float = pv.calc_power(abs(adj_data), incidence, elevation, eff)"""

            power: float = get_pv_data(pv_class, temp, abs(adj_data), azimuth, elevation)

            date_time: str = datetime.datetime.strptime(data["time"], "%Y%m%d:%H%M").strftime("%d-%m-%Y - %H:%M")

            power_data.append(round(power, 2))
            date_time_data.append(date_time)

    max_energy: float = max(power_data)
    time_max_energy: str = date_time_data[power_data.index(max_energy)]
    average_energy: float = round(calc_energy(power_data, 1, True) / (float(year_max) + 1 - float(year_min)), 2)

    plt.clf()
    plt.figure(figsize=(20, 6))
    plt.grid(True)
    plt.step(date_time_data, power_data, '-', linewidth=0.5, alpha=0.5)
    plt.xticks(np.linspace(0, len(date_time_data), 100), rotation=90, ha='right', fontsize=8)
    plt.tight_layout()
    plt.margins(0.01)
    plt.savefig(f"{consts.DOWNLOADS_FILE_PATH}plot_uploaded_data.png", dpi=300)

    return (lat, lon, ele, rad_database, meteo_database, year_min, year_max, power_data, date_time_data,
            max_energy, time_max_energy, average_energy)


def heating_power(config_data: dict, weather: dict):
    def _calc_area(data_house: dict, prefix: str, prefix2: str | None = None):
        try:
            if prefix2 is None:
                prefix2 = prefix
            area = data_house.get(f"{prefix}_width", 0) * data_house.get(f"{prefix2}_height", 0)
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
                    return u_value.get("Wand").get(wall_).get(int(wall_type))
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
                if (ceiling_ == "ENEV unbeheiztes Geschoss" or ceiling_ == "ENEV beheiztes Geschoss" or
                        ceiling_ == "ENEV Dach"):
                    return u_value.get("Decke").get(ceiling_).get(int(ceiling_type))
                elif ceiling_ == "u_value":
                    return data_house.get(f"{prefix}_u_value", 0)
                else:
                    return u_value.get("Decke").get(ceiling_).get(ceiling_type).get(year)
        except AttributeError as err:
            print(prefix)
            print(f"Attribute Missing: {err}")
            return 0

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
    weather_data = config_data["coordinates"]
    shelly_data = config_data["shelly"]

    hp: classes.RequiredHeatingPower = classes.RequiredHeatingPower()
    # weather: classes.Weather = classes.Weather(weather_data["latitude"], weather_data["longitude"])
    # trv: classes.ShellyTRVControl = classes.ShellyTRVControl(shelly_data["ip_address"])

    room = hp.Room

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
        wall.interior_wall_temp = _interior_wall(data, f"wall{wall_number}")

        window.area = _calc_area(data, f"window{window_number}")
        door.area = _calc_area(data, f"door_wall{wall_number}")

        wall.u_wert = _get_u_value(data, hp.u_value, f"wall{wall_number}")
        window.u_wert = _get_u_value(data, hp.u_value, f"window{window_number}")
        door.u_wert = _get_u_value(data, hp.u_value, f"door")

    """
    trv_data: dict = trv.get_thermostat()
    if trv_data is None:
        trv_data: dict = trv.get_thermostat(timeout=10)

    indoor_temp: float = (trv_data.get("tmp").get("value")) if trv_data is not None else 22
    """
    indoor_temp: float = 22
    cop: float = config_data.get("air_conditioner", {"air_conditioner_cop": 0}).get("air_conditioner_cop")

    hp_data: list = []
    diff_data: list = []
    tme_data: list = []
    cop_temp: list = []

    # today = weather.data[list(weather.data.keys())[0]]

    old_temp: int = 16
    for date, weather_today in weather.items():
        for tme, data in weather_today.items():
            if tme == 'daily':
                continue

            outdoor_temp: float = data.get("temp", old_temp)
            old_temp = outdoor_temp
            diff_temp: float = indoor_temp - outdoor_temp

            room.Floor.temp_diff = diff_temp
            room.Ceiling.temp_diff = diff_temp

            room.Wall1.temp_diff = diff_temp
            if room.Wall1.interior_wall_temp:
                room.Wall1.temp_diff = abs(room.Wall1.interior_wall_temp - indoor_temp)

            room.Wall2.temp_diff = diff_temp
            if room.Wall2.interior_wall_temp:
                room.Wall2.temp_diff = abs(room.Wall2.interior_wall_temp - indoor_temp)

            room.Wall3.temp_diff = diff_temp
            if room.Wall3.interior_wall_temp:
                room.Wall3.temp_diff = abs(room.Wall3.interior_wall_temp - indoor_temp)

            room.Wall4.temp_diff = diff_temp
            if room.Wall4.interior_wall_temp:
                room.Wall4.temp_diff = abs(room.Wall4.interior_wall_temp - indoor_temp)

            d = hp.calc_heating_power(room)

            cop = ((1/14) * outdoor_temp + 2.5) if outdoor_temp > -20 else 1

            cop_temp.append(cop)
            diff_data.append(diff_temp)
            hp_data.append(d)
            tme_data.append(f"{date} {tme}")

    # debug.printer(diff_data, hp_data)

    return tme_data, hp_data, cop_temp


def comp_mor_ev_data(morning_data, evening_data):
    debug.printer(evening_data, description="evening_data: ")
    debug.printer(morning_data, description="morning_data: ")

    tme_ev = evening_data.get("write_time", {"time": "0", "format": "0"})
    time_evening = datetime.datetime.strptime(tme_ev.get("time"), tme_ev.get("format"))

    tme_mor = morning_data.get("write_time", {"time": "0", "format": "0"})
    time_morning = datetime.datetime.strptime(tme_mor.get("time"), tme_mor.get("format"))

    if time_evening <= time_morning:
        print("No comparison available, no right time!")
        return {}

    total_dni_difference = 0
    count = 0

    for time_point, evening_values in evening_data.items():
        if time_point in ["energy", "write_time"]:
            continue

        morning_values = morning_data.get(time_point)
        if morning_values:
            total_dni_difference += abs(evening_values.get('dni_radiation', 0) - morning_values.get('dni_radiation', 0))
            total_dni_difference += abs(evening_values.get('ghi_radiation', 0) - morning_values.get('ghi_radiation', 0))
            count += 1

    energy_difference = abs(evening_data.get("energy", 0) - morning_data.get("energy", 0))
    energy_difference = abs(evening_data.get("energy", 0) / morning_data.get("energy", 0)) * 100

    if count > 0:
        average_dni_difference = total_dni_difference / count
    else:
        average_dni_difference = None

    return {
        "average_dni_difference": average_dni_difference,
        "energy_difference": energy_difference
    }


def calc_diff_hp_energy(hp: list, cop: list, power: list) -> list:

    heating_energy: list = list(map(lambda p, c: (p * c) if p is not None else None, power, cop))
    diff: list = list(map(lambda e, p: e - p, heating_energy, hp))

    return diff


def load_load_profile(path: str | None) -> dict:

    def _create_null_profile() -> dict:
        empty_dict: dict = {}
        start = datetime.date(2024, 1, 1)
        end = datetime.date(2024, 12, 31)

        delta = (end - start).days

        for i in range(0, delta + 1):
            day = start + datetime.timedelta(days=i)
            date_ = day.strftime("%d-%m")
            empty_dict[date_] = {}
            for hour in range(0, 24):
                for minute in range(0, 60, 15):
                    tme = f'{str(hour).zfill(2)}:{str(minute).zfill(2)}'
                    empty_dict[date_][tme] = 0
        return empty_dict

    if path is None or 'None' in path:
        return _create_null_profile()

    data_extension = path[path.rfind('.'):]

    if '.json' in data_extension:
        return _create_null_profile()
        # sheet = json.load(open(path, "rb+"))

    elif '.xlsx' in data_extension or '.xls' in data_extension:
        try:
            xl = pd.ExcelFile(path)
        except FileNotFoundError:
            return _create_null_profile()

        df = xl.parse(xl.sheet_names[0])
        data_dict = {}

        for row in df.values:
            try:
                date_str, load = row[0], row[1]

                if 'timestamp' in str(type(date_str)):
                    date_time = date_str

                else:
                    date_time = datetime.datetime.strptime(date_str, "%d.%m.%Y %H:%M:%S")

                date = date_time.date().strftime("%d-%m")
                time = date_time.time().strftime("%H:%M")

                if date not in data_dict:
                    data_dict[date] = {}
                data_dict[date][time] = float(str(load).replace(",", '.'))  # * 1000
            except Exception as e:
                print(f'Following error is occurred by loading load_profile: {e}')
                return _create_null_profile()

        return data_dict

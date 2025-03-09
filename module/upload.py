#  -*- coding: utf-8 -*-

import datetime
import json
import os

import matplotlib.pyplot as plt
from numpy import linspace

from module import consts, functions


def data_analyzer(config_data: dict, path: None | str = None):
    if path is None:
        path = rf"./uploads/{os.listdir('./uploads')[0]}"

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

    pv_class = functions.init_pv(config_data)

    if "Gb(i)" not in datas[0]:
        print(datas[0])
        return -1

    if slope == 0 and azimuth == 0:
        for data in datas:
            date: str = datetime.datetime.strptime(data["time"], "%Y%m%d:%H%M").strftime("%d-%m-%Y")
            tme: float = float(datetime.datetime.strptime(data["time"], "%Y%m%d:%H%M").strftime("%H.%M"))

            sun_class = functions.init_sun(config_data, date)
            azimuth, elevation = functions.get_sun_data(sun_class, tme)

            temp: float = 17
            radiation: float = data.get("Gb(i)", 0)

            power: float = functions.get_pv_data(pv_class, temp, radiation, azimuth, elevation)

            date_time: str = datetime.datetime.strptime(data["time"], "%Y%m%d:%H%M").strftime("%d-%m-%Y - %H:%M")

            power_data.append(round(power, 2))
            date_time_data.append(date_time)

    elif slope == config_pv["tilt_angle1"] and azimuth == config_pv["exposure_angle1"]:
        for data in datas:
            date: str = datetime.datetime.strptime(data["time"], "%Y%m%d:%H%M").strftime("%d-%m-%Y")
            tme: float = float(datetime.datetime.strptime(data["time"], "%Y%m%d:%H%M").strftime("%H.%M"))

            sun_class = functions.init_sun(config_data, date)

            temp: float = 17
            radiation: float = data.get("Gb(i)", 0)

            adj_data: float = sun_class.adjust_for_new_angle(radiation, slope, azimuth, config_pv["tilt_angle"],
                                                             config_pv["exposure_angle"], tme)

            azimuth, elevation = functions.get_sun_data(sun_class, tme)

            power: float = functions.get_pv_data(pv_class, temp, abs(adj_data), azimuth, elevation)

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

            sun_class = functions.init_sun(config_data, date)

            adj_data: float = sun_class.adjust_for_new_angle(radiation, slope, azimuth, config_pv["tilt_angle1"],
                                                             config_pv["exposure_angle1"], tme)

            azimuth, elevation = functions.get_sun_data(sun_class, tme)

            """incidence: float = pv.calc_incidence_angle(elevation, azimuth)
            eff: float = pv.calc_temp_dependency(20, abs(adj_data))

            power: float = pv.calc_power(abs(adj_data), incidence, elevation, eff)"""

            power: float = functions.get_pv_data(pv_class, temp, abs(adj_data), azimuth, elevation)

            date_time: str = datetime.datetime.strptime(data["time"], "%Y%m%d:%H%M").strftime("%d-%m-%Y - %H:%M")

            power_data.append(round(power, 2))
            date_time_data.append(date_time)

    max_energy: float = max(power_data)
    time_max_energy: str = date_time_data[power_data.index(max_energy)]
    average_energy: float = round(functions.calc_energy(power_data, 1, True) / (float(year_max) + 1 - float(year_min)), 2)
    plt.clf()
    plt.figure(figsize=(20, 6))
    plt.grid(True)
    plt.step(date_time_data, power_data, '-', linewidth=0.5, alpha=0.5)
    plt.xticks(linspace(0, len(date_time_data), 100), rotation=90, ha='right', fontsize=8)
    plt.tight_layout()
    plt.margins(0.01)
    plt.savefig(f"{consts.DOWNLOADS_FILE_PATH}plot_uploaded_data.png", dpi=300)

    return (lat, lon, ele, rad_database, meteo_database, year_min, year_max, power_data, date_time_data,
            max_energy, time_max_energy, average_energy)

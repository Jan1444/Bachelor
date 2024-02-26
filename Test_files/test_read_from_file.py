# -*- coding: utf-8 -*-

import tomli
import tomli_w
import json
import datetime
from module import classes, debug
import matplotlib.pyplot as plt
import numpy as np


def load_write_config(data: dict | None = None, path: str | None = None) -> dict | None:
    if path is None:
        path = '../config/config_test.toml'
    if data:
        tomli_w.dump(config, open(path, "wb"))
    else:
        debug.printer("opened config file")
        return tomli.load(open(path, "rb"))


if __name__ == '__main__':
    # 'https://re.jrc.ec.europa.eu/pvg_tools/de/#api_5.2'
    path = r"uploads/Timeseries_49.520_11.295_SA2_0deg_0deg_2020_2020.json"
    data = json.load(open(path, "rb+"))
    print(data["inputs"]["location"].keys())

    power_list: list = []
    time_date: list = []

    for element in (data["outputs"]["hourly"]):

        date = datetime.datetime.strptime(element["time"], "%Y%m%d:%H%M").strftime("%d-%m-%Y")
        time = float(datetime.datetime.strptime(element["time"], "%Y%m%d:%H%M").strftime("%H.%M"))

        sun = classes.CalcSunPos(49.51981, 11.29489, date)
        azimuth = sun.calc_azimuth(time)
        elevation = sun.calc_solar_elevation(time)

        pv = classes.PVProfit(20, 20, 30, 0, -0.385, 25, 0)

        incidence = pv.calc_incidence_angle(elevation, azimuth)
        eff = pv.calc_temp_dependency(16, element["Gb(i)"])
        power = pv.calc_power(element["Gb(i)"], incidence, elevation, eff)

        date_time = datetime.datetime.strptime(element["time"], "%Y%m%d:%H%M").strftime("%H:%M - %d-%m-%Y")
        print(date_time)
        print("radiation: ", element["Gb(i)"])
        print(power)
        time_date.append(date_time)
        power_list.append(power)

    print("plot")

    plt.figure(figsize=(20, 6))  # Angepasste Höhe für das Plot-Seitenverhältnis
    plt.grid(True)
    plt.plot(time_date, power_list, '-', linewidth=0.5, alpha=0.1)  # Leichtere Linien und geringe Transparenz
    plt.xticks(np.linspace(0, len(time_date), 20), rotation=45, ha='right',
               fontsize=8)  # Weniger x-Ticks mit Rotation und kleinerer Schriftgröße
    plt.tight_layout()
    plt.margins(0.01)
    plt.savefig("plot.png", dpi=300)
    '''
    plt.figure(figsize=(350, 50))
    plt.grid()
    plt.plot(time_date, power_list, "-", markersize=1, alpha=0.02)
    # plt.xticks(rotation=90, ha="right", fontsize=30)
    # plt.tight_layout()
    plt.margins(0.01)
    plt.savefig("plot.png")
    # plt.show()
    '''


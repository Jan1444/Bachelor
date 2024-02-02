#  -*- coding: utf-8 -*-

import datetime
import os
from functools import lru_cache, wraps

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from frozendict import frozendict

from module import consts
from module import debug
from module import functions


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


@freeze_all
@lru_cache(maxsize=None)
def generate_weather_data(request_data: dict, config_data: dict) -> list[str]:
    if not os.path.exists(consts.DOWNLOADS_FILE_PATH):
        os.mkdir(consts.DOWNLOADS_FILE_PATH)

    start_date = datetime.datetime.strptime(request_data['start_date_weather'], "%Y-%m-%d").strftime("%d-%m-%Y")
    end_date = datetime.datetime.strptime(request_data['end_date_weather'], "%Y-%m-%d").strftime("%d-%m-%Y")

    weather_date = functions.get_weather_data(config_data, start_date, end_date)

    pv_class = functions.init_pv(config_data)

    power_data: dict = {}
    energy_data: dict = {}
    msg: list[str] = []

    for date, day in weather_date.items():
        sun_class = functions.init_sun(config_data, date)

        day.pop("daily")

        power_data[date]: dict = {}
        energy_data_list: list[float] = []

        for tme, data in day.items():
            time_float = functions.string_time_to_float(tme)
            temp = data.get("temp", 0)
            radiation = data.get("dni_radiation", 0)
            azimuth, elevation = functions.get_sun_data(sun_class, time_float)

            power_data[date][tme] = functions.get_pv_data(pv_class, temp, radiation, azimuth, elevation, True)

            energy_data_list.append(power_data[date][tme])

        energy_data[date] = functions.calc_energy(energy_data_list)

    if os.path.exists(rf"{consts.DOWNLOADS_FILE_PATH}weather_data.xlsx"):
        os.remove(rf"{consts.DOWNLOADS_FILE_PATH}weather_data.xlsx")

    if os.path.exists(rf"{consts.DOWNLOADS_FILE_PATH}weather_plot.png"):
        os.remove(rf"{consts.DOWNLOADS_FILE_PATH}weather_plot.png")

    if request_data.get("excel_weather", "") == "on":
        df = pd.DataFrame.from_dict(energy_data, orient='index', columns=['energy [kWh]'])
        df.to_excel(f'{consts.DOWNLOADS_FILE_PATH}weather_data.xlsx')
        msg.append("excel_weather")

    if request_data.get("plot_png_weather", "") == "on":
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
        plt.savefig(rf"{consts.DOWNLOADS_FILE_PATH}weather_plot.png")

        msg.append("plot_weather")

    return msg


@freeze_all
@lru_cache(maxsize=None)
def generate_market_data(request_data: dict, config_data: dict) -> list[str]:
    if not os.path.exists(consts.DOWNLOADS_FILE_PATH):
        os.mkdir(consts.DOWNLOADS_FILE_PATH)

    market_class = functions.init_market(config_data, request_data.get('start_date_market'),
                                         request_data.get('end_date_market'))
    market_datas: list[dict] = market_class.data

    debug.printer(market_datas)

    msg: list[str] = []
    price_data: list[float] = []
    time_data: list[str] = []
    data_dict: dict = {}

    for market_data in market_datas:
        time_data.append(
            f"{market_data.get('date', "")} {market_data.get('start_timestamp', ":")}"
        )
        price_data.append(market_data.get('consumerprice', 0))
        data_dict.update(
            {
                f"{market_data.get('date', "")} {market_data.get('start_timestamp', ":")}": market_data.get(
                    'consumerprice', "0")
            }
        )

    if os.path.exists(rf"{consts.DOWNLOADS_FILE_PATH}market_data.xlsx"):
        os.remove(rf"{consts.DOWNLOADS_FILE_PATH}market_data.xlsx")
    if os.path.exists(rf"{consts.DOWNLOADS_FILE_PATH}plot_market.png"):
        os.remove(rf"{consts.DOWNLOADS_FILE_PATH}plot_market.png")

    if request_data.get("excel_market", "") == "on":
        df = pd.DataFrame.from_dict(data_dict, orient='index', columns=['price [ct]'])
        df.to_excel(f'{consts.DOWNLOADS_FILE_PATH}market_data.xlsx')
        msg.append("excel_market")

    if request_data.get("plot_png_market", "") == "on":
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
        plt.savefig(rf"{consts.DOWNLOADS_FILE_PATH}market_plot.png")
        msg.append("plot_market")

    return msg

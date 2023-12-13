import datetime
import os
from functools import lru_cache, wraps

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import tomli
import tomli_w
from flask import Flask, render_template, request, send_from_directory
from frozendict import frozendict

import classes

app = Flask(__name__)


def init_classes(latitude: float, longitude: float, module_efficiency: float, module_area: int, tilt_angle: float,
                 exposure_angle: float, mounting_type: int, costs: float) -> \
        (classmethod, classmethod, classmethod, classmethod):
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
    weather = classes.Weather(latitude, longitude)
    market = classes.MarketData(costs)
    sun = classes.CalcSunPos(latitude, longitude)
    pv = classes.PVProfit(module_efficiency, module_area, tilt_angle, exposure_angle, -0.35, 25, mounting_type)
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


def write_data_to_config(data: dict, toml_file_path: str) -> None:
    with open(toml_file_path, 'rb') as f:
        config_data = tomli.load(f)
    if data['latitude'] != "" or data['longitude'] != "":
        config_data['coordinates']['latitude'] = float(data['latitude'])
        config_data['coordinates']['longitude'] = float(data['longitude'])
    else:
        lat, lon = get_coord(data['Straße'], data['Nr'], data['Stadt'], data['PLZ'], data['Land'])
        config_data['coordinates']['latitude'] = lat
        config_data['coordinates']['longitude'] = lon
    config_data['pv']['tilt_angle'] = float(data['tilt_angle'])
    config_data['pv']['area'] = float(data['area'])
    config_data['pv']['module_efficiency'] = float(data['module_efficiency'])
    config_data['pv']['exposure_angle'] = float(data['exposure_angle'])
    config_data['pv']['temperature_coefficient'] = float(data['temperature_coefficient'])
    config_data['pv']['nominal_temperature'] = float(data['nominal_temperature'])
    config_data['pv']['mounting_type'] = int(data['mounting_type'])
    config_data['market']['consumer_price'] = float(data['consumer_price'])

    with open(toml_file_path, 'wb') as f:
        tomli_w.dump(config_data, f)


def write_data_to_file(weather_data: None | dict, sun: None | object, pv: None | object, market: None | object,
                       time: None | dict = None, radiation: None | dict = None, power: None | dict = None,
                       market_price: None | dict = None) -> None:
    data_file_path = r"data/data.toml"
    data: dict = {"write_time": {"time": datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                                 "format": "%d-%m-%Y %H:%M:%S"}}

    if time is not None and radiation is not None and power is not None and market_price is not None:
        h = -1
        for i, k in enumerate(time):
            if k != "daily":
                data.update(
                    {k: {"radiation": radiation[i], "power": round(power[i], 3), "market_price": market_price[h]}})
            if (i - 4) % 4 == 0:
                h += 1

    else:
        zeit: int = -1
        for z, t in enumerate(weather_data.keys()):
            if t != "daily":
                radiation = float(weather_data[t]["radiation"])
                time_float = float(t[:2]) + float(t[3:]) / 100
                sun_height = sun.calc_solar_elevation(time_float)
                sun_azimuth = sun.calc_azimuth(time_float)
                incidence = pv.calc_incidence_angle(sun_height, sun_azimuth)
                curr_eff = pv.calc_temp_dependency(weather_data[t]["temp"], radiation)
                power = pv.calc_energy(radiation, incidence, sun_height, curr_eff)

                data.update({t: {"radiation": radiation, "power": round(power, 3),
                                 "market_price": market.data[zeit]["consumerprice"]}})
            if (z - 4) % 4 == 0:
                zeit += 1

    with open(data_file_path, 'wb') as f:
        tomli_w.dump(data, f)


def read_data_from_file(file_path: str) -> dict:
    with open(file_path, 'rb') as f:
        data = tomli.load(f)
    return data


def get_coord(street: str, nr: str, city: str, postalcode: int, country: str) -> (str, str):
    # https://nominatim.org/release-docs/develop/api/Search/
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


def calc_energy(energy: list, interval: float = 0.25, kwh: bool = True) -> list:
    multiplier = 1
    if kwh:
        multiplier = 1000
    power_values = list(map(lambda x: x / multiplier, energy))
    total_energy = sum((power_values[i] + power_values[i + 1]) / 2 * interval for i in range(len(power_values) - 1))
    return total_energy


def date_time_download() -> dict:
    date_today = datetime.datetime.now().strftime("%Y-%m-%d")
    date_and_time = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M")
    data: dict = {"date": date_today, "datetime": date_and_time}
    return data


@freeze_all
@lru_cache(maxsize=None)
def generate_weather_data(data: dict, config_data: dict) -> str:
    if not os.path.exists(r"uploads"):
        os.mkdir(r"uploads")

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
                eff = pv.calc_temp_dependency(weather_date[date][t]["temp"], weather_date[date][t]["radiation"])
                power_data[date][t] = pv.calc_power(weather_date[date][t]["radiation"], incidence, elevation,
                                                    eff)
                energy_data_list.append(power_data[date][t])
        energy_data[date] = calc_energy(energy_data_list)

    if "excel_weather" in data.keys():
        if os.path.exists(r"uploads/data.xlsx"):
            os.remove(r"uploads/data.xlsx")
        if data["excel_weather"] == "on":
            df = pd.DataFrame.from_dict(energy_data, orient='index', columns=['energy [kWh]'])
            df.to_excel('uploads/data.xlsx')
            msg = "excel"

    if "plot_png_weather" in data.keys():
        if data["plot_png_weather"] == "on":
            if os.path.exists(r"uploads/plot.png"):
                os.remove(r"uploads/plot.png")
            if len(energy_data.keys()) > 50:
                x = len(energy_data.keys()) * 0.25
                y = x * 0.4
            else:
                x = 10
                y = 5

            plt.figure(figsize=(x, y))
            plt.grid()
            plt.plot(energy_data.keys(), energy_data.values(), label="Energy[kWh]")
            plt.xticks(rotation=90, ha="right", fontsize=18)
            x = len(energy_data.keys())
            z = max(energy_data.values())
            z = (z) + (100 if z > 100 else 5)
            ticks = np.arange(0, z, step=(x // 100 * 10 if z > 100 else 1))
            plt.yticks(ticks=ticks, ha="right", fontsize=20)
            plt.legend(loc="upper left", fontsize=20)
            plt.tight_layout()
            plt.savefig(r"uploads/plot.png")
            msg = f"{msg}, plot"

    return msg


def unpack_data(data: dict) -> (list, list, list, list):
    weather_time: list = []
    power_data: list = []

    market_time: list = []
    market_price: list = []

    for t in data.keys():
        if t != "write_time":
            weather_time.append(t)
            power_data.append(data[t]["power"])

            if t[3:] == "00":
                market_time.append(t)
                market_price.append(data[t]["market_price"])

    return weather_time, power_data, market_time, market_price


def test():
    from config import settings as consts
    coordinates = consts["coordinates"]
    pv_consts = consts["pv"]
    market_consts = consts["market"]

    w, m, sun, pv = init_classes(coordinates["latitude"], coordinates["longitude"],
                                 pv_consts["module_efficiency"], pv_consts["area"],
                                 pv_consts["tilt_angle"], pv_consts["exposure_angle"],
                                 pv_consts["mounting_type"], market_consts["consumer_price"])

    w = w.data[list(w.data.keys())[0]]

    return w, m, sun, pv


@app.route('/', methods=['GET', 'POST'])
def index():
    toml_file_path = r'config/config_test.toml'
    with open(toml_file_path, 'rb') as f:
        config_data = tomli.load(f)

    return render_template('index.html', config=config_data)


@app.route('/dashboard')
def dashboard():
    toml_file_path = 'config/config_test.toml'

    # TOML-Datei lesen
    with open(toml_file_path, 'rb') as f:
        config_data = tomli.load(f)

    return render_template('dashboard.html', config=config_data)


@app.route('/analytics')
def analytics():
    power_data: list = []
    weather_time: list = []

    energy: float = 0.0
    energy_data: list = []

    market_time: list = []
    market_price: list = []

    old_data: bool = True

    if os.path.exists(r"data/data.toml"):
        data = read_data_from_file(r"data/data.toml")

        time_write = datetime.datetime.strptime(data["write_time"]["time"], data["write_time"]["format"])
        time_now = datetime.datetime.now()

        if (time_now - time_write).seconds < (60 * 60) and (time_now - time_write).days <= 0:
            old_data = False

            weather_time, power_data, market_time, market_price = unpack_data(data)

            energy = calc_energy(power_data, kwh=False)

    if old_data:
        toml_file_path = 'config/config_test.toml'

        with open(toml_file_path, 'rb') as f:
            config_data = tomli.load(f)

        coordinates = config_data["coordinates"]
        pv_consts = config_data["pv"]
        market_consts = config_data["market"]

        weather, market, sun, pv = init_classes(coordinates["latitude"], coordinates["longitude"],
                                                pv_consts["module_efficiency"], pv_consts["area"],
                                                pv_consts["tilt_angle"], pv_consts["exposure_angle"],
                                                pv_consts["mounting_type"], market_consts["consumer_price"])
        today = list(weather.data.keys())[0]
        weather_date = weather.data[today]

        radiation_data: list = []

        for t in weather_date.keys():
            if t != "daily":
                weather_time.append(t)
                time_float: float = int(t[:2]) + int(t[3:]) / 100
                azimuth: float = sun.calc_azimuth(time_float)
                elevation: float = sun.calc_solar_elevation(time_float)
                incidence = pv.calc_incidence_angle(elevation, azimuth)
                radiation = weather_date[t]["radiation"]
                radiation_data.append(radiation)
                eff = pv.calc_temp_dependency(weather_date[t]["temp"], radiation)
                power_data.append(pv.calc_power(weather_date[t]["radiation"], incidence, elevation, eff))

        energy = calc_energy(power_data, kwh=False)

        for t in market.data:
            market_time.append(t["start_timestamp"])
            market_price.append(t["consumerprice"])

        write_data_to_file(None, None, None, None, weather_time, radiation_data, power_data, market_price)

    for p in power_data:
        energy_data.append(energy)

    plt.clf()
    plt.figure(figsize=(60, 25))
    plt.grid()
    plt.plot(weather_time, power_data, label="Power [W]")
    plt.plot(weather_time, energy_data, label="Energy [Wh]")
    plt.xticks(rotation=90, ha="right", fontsize=30)
    plt.yticks(ticks=np.arange(0, max(max(power_data), max(energy_data)) + 100, step=100), ha="right", fontsize=30)
    plt.tight_layout()
    plt.legend(loc="center left", fontsize=30)
    plt.savefig('static/plots/output_weather.png')

    plt.clf()
    plt.figure(figsize=(60, 25))
    plt.grid()
    plt.plot(market_time, market_price, label="Preis [ct/kWh]")
    plt.xticks(rotation=90, ha="right", fontsize=30)
    plt.yticks(ticks=np.arange(0, max(market_price) + 5, step=1), ha="right", fontsize=30)
    plt.tight_layout()
    plt.legend(loc="center left", fontsize=30)
    plt.savefig('static/plots/output_market.png')

    return render_template('analytics.html', name="new_plot", url_weather="/static/plots/output_weather.png",
                           url_market="/static/plots/output_market.png")


@app.route('/generate_download', methods=['POST'])
def download():
    toml_file_path: str = r'config/config_test.toml'
    msg: str = ""
    err_msg_weather: str = ""
    err_msg_market: str = ""
    date_now: dict = {}

    with open(toml_file_path, 'rb') as f:
        config_data = tomli.load(f)

    if request.method == 'POST':
        date_now = date_time_download()
        data = request.form.to_dict()
        print(data)
        if "excel_weather" in data.keys() or "plot_png_weather" in data.keys():
            if data['start_date_weather'] == "":
                err_msg_weather = "Bitte Start Datum ausfüllen"

            elif data['start_date_weather'] != "":
                t = datetime.datetime.now() - datetime.datetime.strptime(data['start_date_weather'], "%Y-%m-%d")
                if t.total_seconds() < 0:
                    err_msg_weather = "Das Startdatum muss kleiner sein als das Enddatum"
            print(err_msg_weather)
            if err_msg_weather != "":
                return render_template('file_download.html', config=date_now, ret=msg,
                                       error_weather=err_msg_weather, error_market=err_msg_market)

        if "excel_market" in data.keys() or "plot_png_market" in data.keys():
            if data['start_date_market'] == "":
                err_msg_market = "Bitte Start Datum ausfüllen"

            elif data['start_date_market'] != "":
                t = datetime.datetime.now() - datetime.datetime.strptime(data['start_date_market'],
                                                                         "%Y-%m-%dT%H:%M")
                if t.total_seconds() < 0:
                    err_msg_market = "Das Startdatum muss kleiner sein als das Enddatum"
            if err_msg_market != "":
                return render_template('file_download.html', config=date_now, ret=msg,
                                       error_weather=err_msg_weather, error_market=err_msg_market)

        if "excel_weather" in data.keys() or "plot_png_weather" in data.keys():
            msg = generate_weather_data(data, config_data)

    return render_template('file_download.html', config=date_now, ret=msg,
                           error_weather=err_msg_weather, error_market=err_msg_market)


@app.route('/uploads/<name>')
def download_file(name):
    return send_from_directory("uploads", name)


@app.route('/settings')
def settings():
    toml_file_path = r'config/config_test.toml'

    try:
        with open(toml_file_path, 'rb') as f:
            config_data = tomli.load(f)

    except FileNotFoundError:
        open(toml_file_path, "x")
        config_data = {
            "coordinates": {
                "latitude": "",
                "longitude": ""
            },
            "pv": {
                "tilt_angle": "",
                "area": "",
                "module_efficiency": "",
                "exposure_angle": ""
            },
            "market": {
                "consumer_price": "",
            }
        }
    finally:
        return render_template('set_vals.html', config=config_data)


@app.route('/save_settings', methods=['POST'])
def safe_settings():
    if request.method == 'POST':
        toml_file_path = r'config/config_test.toml'
        with open(toml_file_path, 'rb') as f:
            config_data = tomli.load(f)

        data = request.form.to_dict()

        if ((data['latitude'] != "" and data['longitude'] != "") or (data['Straße'] != "" and data['Nr'] != "" and
                                                                     data['Stadt'] != "" and data['PLZ'] != "" and
                                                                     data['Land'])):
            write_data_to_config(data, toml_file_path)
            return render_template('index.html', config=config_data)
        else:
            return render_template('set_vals.html',
                                   error='Bitte füllen Sie mindestens Latitude und Longitude aus oder die Adresse',
                                   config=config_data)


@app.route('/file_download')
def file_download():
    data = date_time_download()
    return render_template('file_download.html', config=data)


if __name__ == '__main__':
    app.run(debug=True)

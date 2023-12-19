# -*- coding: utf-8 -*-

import datetime
import os

import matplotlib.pyplot as plt
import numpy as np

import tomli

from flask import Flask, render_template, request, send_from_directory

import functions as fc

app = Flask(__name__)


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
        data = fc.read_data_from_file(r"data/data.toml")

        time_write = datetime.datetime.strptime(data["write_time"]["time"], data["write_time"]["format"])
        time_now = datetime.datetime.now()

        if (time_now - time_write).seconds < (60 * 60) and (time_now - time_write).days <= 0:
            old_data = False

            weather_time, radiation_data, power_data, market_time, market_price = fc.unpack_data(data)
            energy = fc.calc_energy(power_data, kwh=False)

    if old_data:
        toml_file_path = 'config/config_test.toml'
        with open(toml_file_path, 'rb') as f:
            config_data = tomli.load(f)

        coordinates = config_data["coordinates"]
        pv_consts = config_data["pv"]
        market_consts = config_data["market"]

        weather, market, sun, pv = fc.init_classes(coordinates["latitude"], coordinates["longitude"],
                                                   pv_consts["module_efficiency"], pv_consts["area"],
                                                   pv_consts["tilt_angle"], pv_consts["exposure_angle"],
                                                   pv_consts["mounting_type"], market_consts["consumer_price"])
        today = list(weather.data.keys())[0]
        weather_date = weather.data[today]

        radiation_data: list = []
        radiation_data_dni: list = []

        for t in weather_date.keys():
            if t != "daily":
                weather_time.append(t)
                time_float = float(t[:2]) + float(t[3:]) / 100
                azimuth: float = sun.calc_azimuth(time_float)
                elevation: float = sun.calc_solar_elevation(time_float)
                incidence = pv.calc_incidence_angle(elevation, azimuth)
                radiation = weather_date[t]["direct_radiation"]
                radiation_dni = weather_date[t]["dni_radiation"]
                radiation_data.append(radiation)
                radiation_data_dni.append(radiation_dni)
                energy_dni = pv.calc_power_with_dni(radiation_dni, incidence, weather_date[t]["temp"])

                power_data.append(energy_dni)

        energy = fc.calc_energy(power_data, kwh=False)

        for t in market.data:
            market_time.append(t["start_timestamp"])
            market_price.append(t["consumerprice"])

        fc.write_data_to_file(None, None, None, None, time=weather_time, radiation_dni=radiation_data_dni,
                              power=power_data, market_price=market_price)

    for _ in power_data:
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
        date_now = fc.date_time_download()
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
            msg = fc.generate_weather_data(data, config_data)

    return render_template('file_download.html', config=date_now, ret=msg,
                           error_weather=err_msg_weather, error_market=err_msg_market)


@app.route('/uploads/<name>')
def download_file(name):
    return send_from_directory("uploads", name)


@app.route('/settings')
def settings():
    toml_file_path = r'config/config_test.toml'
    config_data: dict = {}
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
            fc.write_data_to_config(data, toml_file_path)
            return render_template('index.html', config=config_data)
        else:
            return render_template('set_vals.html',
                                   error='Bitte füllen Sie mindestens Latitude, Longitude aus oder die Adresse',
                                   config=config_data)


@app.route('/file_download')
def file_download():
    data = fc.date_time_download()
    return render_template('file_download.html', config=data)


if __name__ == '__main__':
    app.run(debug=False)

# -*- coding: utf-8 -*-

import datetime
import os

import matplotlib.pyplot as plt
import numpy as np

from flask import Flask, render_template, request, send_from_directory, flash, redirect, jsonify
from werkzeug.utils import secure_filename
from flask_apscheduler import APScheduler

from config import ConfigManager
from data import EnergyManager

from module import consts, debug
from module import functions as fc
from module import set_vals
from module import analytics as analytics_module
from module import download as download_module

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS: set[str] = {'json'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = os.urandom(24)

scheduler = APScheduler()
scheduler.api_enabled = True
scheduler.init_app(app)
scheduler.start()

config_manager = ConfigManager("config_test.toml")
energy_manager_data = EnergyManager("data.toml")
energy_manager_morning_data = EnergyManager("mor_data.toml")
energy_manager_evening_data = EnergyManager("ev_data.toml")


@app.route('/', methods=['GET', 'POST'])
def index():
    config_manager.reload_config()
    config_data = config_manager.config_data
    return render_template('index.html', config=config_data)


@app.route('/dashboard')
def dashboard():
    config_manager.reload_config()
    config_data = config_manager.config_data
    return render_template('dashboard.html', config=config_data)


@app.route('/analytics')
def analytics():
    config_manager.reload_config()
    config_data = config_manager.config_data

    energy_manager_data.reload_data()
    energy_data = energy_manager_data.energy_data

    converter_consts = config_data["converter"]

    power_data: list = []
    weather_time: list = []

    market_time: list = []
    market_price: list = []

    time_write_data = datetime.datetime.strptime(energy_data.get("write_time", {"time": "0"}).get("time"),
                                                 energy_data.get("write_time", {"format": "0"}).get("format"))
    time_now = datetime.datetime.now()

    if (time_now - time_write_data).seconds < (60 * 60) and (time_now - time_write_data).days <= 0:
        if not config_data['reload']:
            return render_template('analytics.html', name="new_plot",
                                   url_weather=f"{consts.plot_path}output_weather.png",
                                   url_market=f"{consts.plot_path}output_market.png",
                                   energy_data=energy_data.get("energy", {"energy": 0}).get("energy"))

        config_data['reload'] = False
        config_manager.write_config_data(config_data)

    sun_class: classes.CalcSunPos = fc.init_sun(config_data)
    pv_class: classes.PVProfit = fc.init_pv(config_data)
    market_class: classes.MarketData = fc.init_market(config_data)

    weather = fc.get_weather_data(config_data)

    today = list(weather.keys())[0]
    weather_today = weather[today]
    weather_today.pop("daily")

    radiation_data_dni: list = []

    for tme, data in weather_today.items():
        time_float = fc.string_time_to_float(tme)
        temp: float = data.get("temp", 0)
        radiation_dni = data.get("dni_radiation", 0)
        azimuth, elevation = fc.get_sun_data(sun_class, time_float)

        power_dni: float = fc.get_pv_data(pv_class, temp, radiation_dni, azimuth, elevation, dni=True)

        if power_dni > converter_consts.get("max_power", 0):
            power_dni = converter_consts.get("max_power", 0)

        power_data.append(power_dni)
        weather_time.append(tme)
        radiation_data_dni.append(radiation_dni)

    energy = fc.calc_energy(power_data, kwh=False, round_=2)

    for t in market_class.data:
        market_time.append(t["start_timestamp"])
        market_price.append(t["consumerprice"])

    write_data = analytics_module.prepare_data_to_write(weather_time, power_data, market_price, energy, None,
                                                        radiation_data_dni)
    energy_manager_data.write_energy_data(write_data)

    plt.clf()
    plt.figure(figsize=(60, 25))
    plt.grid()
    plt.step(weather_time, power_data, label="Power [W]")
    plt.xticks(rotation=90, ha="right", fontsize=30)
    _size = converter_consts["max_power"]
    _step = 25 if _size <= 1000 else (_size / 50) if (_size / 50) % 5 == 0 else _size / 50 - (_size / 50) % 5
    _ticks = np.arange(0, _size + _step, step=_step)
    plt.yticks(ticks=_ticks, ha="right", fontsize=30)
    plt.tight_layout()
    plt.legend(loc="center left", fontsize=30)
    plt.savefig(f'{consts.plot_path}output_weather.png')

    plt.clf()
    plt.figure(figsize=(60, 25))
    plt.grid()
    plt.step(market_time, market_price, label="Preis [ct/kWh]")
    plt.xticks(rotation=90, ha="right", fontsize=30)
    plt.yticks(ticks=np.arange(0, max(market_price) + 5, step=1), ha="right", fontsize=30)
    plt.tight_layout()
    plt.legend(loc="center left", fontsize=30)
    plt.savefig(f'{consts.plot_path}output_market.png')

    return render_template('analytics.html', name="new_plot", url_weather=f"{consts.plot_path}output_weather.png",
                           url_market=f"{consts.plot_path}output_market.png", energy_data=energy)


@app.route('/generate_download', methods=['POST'])
def download():
    config_manager.reload_config()
    config_data = config_manager.config_data

    msg: str = ""
    msg_market: list[str] = []
    msg_weather: list[str] = []
    err_msg_weather: str = ""
    err_msg_market: str = ""
    date_now: dict = {}

    if request.method == 'POST':
        date_now = fc.date_time_download()
        data: dict = request.form.to_dict()

        if "excel_weather" in data.keys() or "plot_png_weather" in data.keys():
            if data['start_date_weather'] == "":
                err_msg_weather = "Bitte Start Datum ausfüllen"

            elif data['start_date_weather'] != "":
                t = datetime.datetime.now() - datetime.datetime.strptime(data['start_date_weather'], "%Y-%m-%d")
                if t.total_seconds() < 0:
                    err_msg_weather = "Das Startdatum muss kleiner sein als das Enddatum"

        if "excel_market" in data.keys() or "plot_png_market" in data.keys():
            if data['start_date_market'] == "":
                err_msg_market = "Bitte Start Datum ausfüllen"

            elif data['start_date_market'] != "":
                t = datetime.datetime.now() - datetime.datetime.strptime(data['start_date_market'],
                                                                         "%Y-%m-%dT%H:%M")
                if t.total_seconds() < 0:
                    err_msg_market = "Das Startdatum muss kleiner sein als das Enddatum"

        if err_msg_market != "" or err_msg_weather != "":
            return render_template('file_download.html', config=date_now, ret=msg,
                                   error_weather=err_msg_weather, error_market=err_msg_market)

        if "excel_weather" in data.keys() or "plot_png_weather" in data.keys():
            msg_weather = download_module.generate_weather_data(data, config_data)

        if "excel_market" in data.keys() or "plot_png_market" in data.keys():
            msg_market = download_module.generate_market_data(data, config_data)

    return render_template('file_download.html', config=date_now, ret_weather=msg_weather,
                           ret_market=msg_market, error_weather=err_msg_weather, error_market=err_msg_market)


@app.route('/downloads/<name>')
def download_file(name):
    return send_from_directory("downloads", name)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/settings')
def settings():
    config_manager.reload_config()
    config_data = config_manager.config_data
    return render_template('set_vals.html', config=config_data, window_data=consts.window_data,
                           wall_data=consts.wall_data, door_data=consts.door_data, ceiling_data=consts.ceiling_data)


@app.route('/save_settings', methods=['POST'])
def safe_settings():
    config_manager.reload_config()
    config_data = config_manager.config_data

    if request.method == 'POST':

        data = request.form.to_dict()

        debug.printer(data)

        if data["mounting_type"] == "-1":
            return render_template('set_vals.html',
                                   error_mounting_type='Bitte wählen Sie einen Montagetypen aus',
                                   config=config_data, window_data=consts.window_data,
                                   wall_data=consts.wall_data, door_data=consts.door_data,
                                   ceiling_data=consts.ceiling_data)

        if ((data.get('latitude', "") != "" and data.get('longitude', "") != "") or (
                data.get('Straße', "") != "" and data.get('Nr', "") != "" and
                data.get('Stadt', "") != "" and data.get('PLZ', "") != "" and
                data.get('Land', ""))):

            write_data = set_vals.write_data_to_config(config_data, data)
            config_manager.write_config_data(write_data)

            return render_template('index.html', config=config_data)
        else:
            return render_template('set_vals.html',
                                   error='Bitte füllen Sie mindestens Latitude, Longitude aus oder die Adresse',
                                   config=config_data, window_data=consts.window_data,
                                   wall_data=consts.wall_data, door_data=consts.door_data,
                                   ceiling_data=consts.ceiling_data)


@app.route('/file_download')
def file_download():
    data = fc.date_time_download()
    return render_template('file_download.html', config=data)


@app.route('/file_upload')
def file_upload():
    return render_template('file_upload.html')


@app.route('/upload_file', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'upload_file_json' not in request.files:
            flash('No file part')
            return redirect(request.url)

        file = request.files['upload_file_json']

        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            for filename in os.listdir("uploads"):
                os.remove(f"uploads/{filename}")

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return render_template('file_upload.html', name=filename)

        elif not allowed_file(file.filename):
            filename = secure_filename(file.filename)
            ending = filename.rsplit('.', 1)[1].lower()
            err = f".{ending} ist nicht erlaubt. Nur {ALLOWED_EXTENSIONS} ist zulässig"
            return render_template('file_upload.html', err_ending=err)

    return render_template('file_upload.html', data=None)


@app.route('/analyze_file', methods=['GET', 'POST'])
def analyze_file():
    ret = fc.data_analyzer()
    if ret == -1:
        return render_template('file_upload.html', error="Bitte wählen Sie 'Einstrahlungskomponenten' aus")

    return_data: dict = {}
    name_list: list = ["lat", "lon", "ele", "rad_database", "meteo_database", "year_min", "year_max", "power_data",
                       "date_time_data", "max_energy", "time_max_energy", "average_energy"]

    for i, element in enumerate(ret):
        return_data.update(
            {
                name_list[i]: element
            }
        )

    zipped_data = zip(ret[7], ret[8])

    return render_template('analyzed_data.html', data=return_data, power_time_data=zipped_data)


@app.route('/get_window/<frame>')
def get_window(frame):
    return jsonify(consts.window_data.get(frame, []))


@app.route('/get_wall/<wall>')
def get_wall(wall):
    return jsonify(consts.wall_data.get(wall, []))


@app.route('/get_floor/<floor>')
def get_floor(floor):
    return jsonify(consts.floor_data.get(floor, []))


@app.route('/get_ceiling/<ceiling>')
def get_ceiling(ceiling):
    return jsonify(consts.ceiling_data.get(ceiling, []))


@app.route('/get_ceiling/<door>')
def get_door(door):
    return jsonify(consts.door_data.get(door, []))


@scheduler.task("cron", id="morning_saver", hour=5)
def save_morning():
    print("save_data morning")
    print(datetime.datetime.now())

    config_manager.reload_config()
    config_data: dict = config_manager.config_data

    write_dict: dict = fc.save_mor_ev_data(config_data)

    energy_manager_morning_data.write_energy_data(write_dict)


@scheduler.task("cron", id="evening_saver", hour=21)
def save_evening():
    print("save_data evening")
    print(datetime.datetime.now())

    config_manager.reload_config()
    config_data: dict = config_manager.config_data

    write_dict: dict = fc.save_mor_ev_data(config_data)

    energy_manager_evening_data.write_energy_data(write_dict)


@scheduler.task("cron", id="evening_saver", hour=23)
def compare_data():
    print("compare data")
    print(datetime.datetime.now())

    energy_manager_evening_data.reload_data()
    energy_manager_morning_data.reload_data()

    energy_data_morning = energy_manager_morning_data.energy_data
    energy_data_evening = energy_manager_evening_data.energy_data

    err = fc.comp_mor_ev_data(energy_data_morning, energy_data_evening)
    print(err)

    if err.get("average_dni_difference", 3) > 2 or err.get("energy_difference", 3) > (2 / 100):
        print("Big error")


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8888)

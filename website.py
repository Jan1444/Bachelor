# -*- coding: utf-8 -*-

import datetime
import os

import matplotlib.pyplot as plt
import numpy as np

import tomli
import tomli_w

from flask import Flask, render_template, request, send_from_directory, flash, redirect, jsonify
from werkzeug.utils import secure_filename

from module import consts, debug
from module import functions as fc

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS: set[str] = {'json'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = os.urandom(24)


@app.route('/', methods=['GET', 'POST'])
def index():
    toml_file_path = consts.config_file_Path
    with open(toml_file_path, 'rb') as f:
        config_data = tomli.load(f)

    return render_template('index.html', config=config_data)


@app.route('/dashboard')
def dashboard():
    toml_file_path = consts.config_file_Path

    # TOML-Datei lesen
    with open(toml_file_path, 'rb') as f:
        config_data = tomli.load(f)

    return render_template('dashboard.html', config=config_data)


@app.route('/analytics')
def analytics():
    with open(consts.config_file_Path, 'rb') as f:
        config_data = tomli.load(f)

    analy = config_data['analytics']
    coordinates = config_data["coordinates"]
    pv_consts = config_data["pv"]
    market_consts = config_data["market"]
    converter_consts = config_data["converter"]

    power_data: list = []
    weather_time: list = []

    market_time: list = []
    market_price: list = []

    if os.path.exists(consts.data_file_Path):
        data = fc.read_data_from_file(consts.data_file_Path)

        time_write_data = datetime.datetime.strptime(data["write_time"]["time"], data["write_time"]["format"])
        time_now = datetime.datetime.now()

        if (time_now - time_write_data).seconds < (60 * 60) and (time_now - time_write_data).days <= 0:
            if not analy['reload']:
                return render_template('analytics.html', name="new_plot",
                                       url_weather=f"{consts.plot_path}output_weather.png",
                                       url_market=f"{consts.plot_path}output_market.png",
                                       energy_data=data["energy"]["energy"])

            analy['reload'] = False
            tomli_w.dump(config_data, open(consts.config_file_Path, 'wb'))

    weather, market, sun, pv, hp, trv = fc.init_classes(coordinates["latitude"], coordinates["longitude"],
                                                        pv_consts["module_efficiency"], pv_consts["area"],
                                                        pv_consts["tilt_angle"], pv_consts["exposure_angle"],
                                                        pv_consts["mounting_type"], market_consts["consumer_price"],
                                                        "192.168.178.000")
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
            power_dni = pv.calc_power_with_dni(radiation_dni, incidence, weather_date[t]["temp"])

            if power_dni > converter_consts["max_power"]:
                power_dni = converter_consts["max_power"]

            power_data.append(power_dni)

    energy = round(fc.calc_energy(power_data, kwh=False), 2)

    for t in market.data:
        market_time.append(t["start_timestamp"])
        market_price.append(t["consumerprice"])

    fc.write_data_to_file(None, None, None, None, time=weather_time, radiation_dni=radiation_data_dni,
                          power=power_data, market_price=market_price, energy=energy)

    plt.clf()
    plt.figure(figsize=(60, 25))
    plt.grid()
    plt.plot(weather_time, power_data, label="Power [W]")
    # plt.plot(weather_time, energy_data, label="Energy [Wh]")
    plt.xticks(rotation=90, ha="right", fontsize=30)
    _size = converter_consts["max_power"]
    debug.printer(_size)
    _step = 25 if _size <= 1000 else (_size / 50) if (_size / 50) % 5 == 0 else _size / 50 - (_size / 50) % 5
    _ticks = np.arange(0, _size + _step, step=_step)
    debug.printer(_ticks)
    plt.yticks(ticks=_ticks, ha="right", fontsize=30)
    plt.tight_layout()
    plt.legend(loc="center left", fontsize=30)
    plt.savefig(f'{consts.plot_path}output_weather.png')

    plt.clf()
    plt.figure(figsize=(60, 25))
    plt.grid()
    plt.plot(market_time, market_price, label="Preis [ct/kWh]")
    plt.xticks(rotation=90, ha="right", fontsize=30)
    plt.yticks(ticks=np.arange(0, max(market_price) + 5, step=1), ha="right", fontsize=30)
    plt.tight_layout()
    plt.legend(loc="center left", fontsize=30)
    plt.savefig(f'{consts.plot_path}output_market.png')

    return render_template('analytics.html', name="new_plot", url_weather=f"{consts.plot_path}output_weather.png",
                           url_market=f"{consts.plot_path}output_market.png", energy_data=energy)


@app.route('/generate_download', methods=['POST'])
def download():
    toml_file_path: str = consts.config_file_Path
    msg: str = ""
    msg_market: list[str] = []
    msg_weather: list[str] = []
    err_msg_weather: str = ""
    err_msg_market: str = ""
    date_now: dict = {}

    with open(toml_file_path, 'rb') as f:
        config_data = tomli.load(f)

    if request.method == 'POST':
        date_now = fc.date_time_download()
        data = request.form.to_dict()

        if "excel_weather" in data.keys() or "plot_png_weather" in data.keys():
            if data['start_date_weather'] == "":
                err_msg_weather = "Bitte Start Datum ausfüllen"

            elif data['start_date_weather'] != "":
                t = datetime.datetime.now() - datetime.datetime.strptime(data['start_date_weather'], "%Y-%m-%d")
                if t.total_seconds() < 0:
                    err_msg_weather = "Das Startdatum muss kleiner sein als das Enddatum"

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
            msg_weather = fc.generate_weather_data(data, config_data)

        if "excel_market" in data.keys() or "plot_png_market" in data.keys():
            msg_market = fc.generate_market_data(data, config_data)

    return render_template('file_download.html', config=date_now, ret_weather=msg_weather,
                           ret_market=msg_market, error_weather=err_msg_weather, error_market=err_msg_market)


@app.route('/downloads/<name>')
def download_file(name):
    return send_from_directory("downloads", name)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/settings')
def settings():
    toml_file_path = consts.config_file_Path
    config_data: dict = {}
    try:
        with open(toml_file_path, 'rb') as f:
            config_data = tomli.load(f)

    except FileNotFoundError:
        open(toml_file_path, "x")
        config_data = consts.config_data
    finally:
        return render_template('set_vals.html', config=config_data)


@app.route('/save_settings', methods=['POST'])
def safe_settings():
    if request.method == 'POST':
        config_data = tomli.load(open(consts.config_file_Path, 'rb'))

        data = request.form.to_dict()

        debug.printer(data)

        if data["mounting_type"] == "-1":
            return render_template('set_vals.html',
                                   error_mounting_type='Bitte wählen Sie einen Montagetypen aus',
                                   config=config_data)

        if ((data['latitude'] != "" and data['longitude'] != "") or (data['Straße'] != "" and data['Nr'] != "" and
                                                                     data['Stadt'] != "" and data['PLZ'] != "" and
                                                                     data['Land'])):
            fc.write_data_to_config(data)
            return render_template('index.html', config=config_data)
        else:
            return render_template('set_vals.html',
                                   error='Bitte füllen Sie mindestens Latitude, Longitude aus oder die Adresse',
                                   config=config_data)


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
        return_data.update({name_list[i]: element})

    zipped_data = zip(ret[7], ret[8])

    return render_template('analyzed_data.html', data=return_data, power_time_data=zipped_data)


@app.route('/get_window/<frame>')
def get_window(frame):
    door_data = {
        'Holzrahmen': ['Einfachverglasung', 'Doppelverglasung', 'Isolierverglasung'],
        'Kunststoffrahmen': ['Isolierverglasung'],
        'Metallrahmen': ['Isolierverglasung']
    }
    return jsonify(door_data.get(frame, []))


@app.route('/get_wall/<wall>')
def get_wall(wall):
    wall_data = {
        'Außenwand': ['Massivbauweise', 'Holzkonstruktion'],
        'Wand gegen Erdreich': ['Massivbauweise', 'Holzkonstruktion'],
        'Innenwand gegen unbeheizte Kellergeschosse': ['Massivbauweise', 'Holzkonstruktion']
    }
    return jsonify(wall_data.get(wall, []))


@app.route('/get_floor/<floor>')
def get_floor(floor):
    floor_data = {
        'Außenwand': ['Massivbauweise', 'Holzkonstruktion'],
        'Wand gegen Erdreich': ['Massivbauweise', 'Holzkonstruktion'],
        'Innenwand gegen unbeheizte Kellergeschosse': ['Massivbauweise', 'Holzkonstruktion']
    }
    return jsonify(floor_data.get(floor, []))


@app.route('/get_ceiling/<ceiling>')
def get_ceiling(ceiling):
    ceiling_data = {
        'Decke gegen das Erdreich': ['Massivbauweise', 'Holzkonstruktion'],
        'Dach zwischen beheizten und unbeheizten Dachgeschoss': ['Massivbauweise', 'Holzkonstruktion'],
        'Decke im obersten Geschoss': ['Massiv', 'Holzbalkendecke'],
        'Decke über Außenbereich': ['Massiv', 'Holzbalkendecke']
    }
    return jsonify(ceiling_data.get(ceiling, []))


if __name__ == '__main__':
    app.run(debug=True)

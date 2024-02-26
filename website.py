# -*- coding: utf-8 -*-

import datetime
import os

from flask import Flask, render_template, request, send_from_directory, redirect, flash, jsonify
from flask_apscheduler import APScheduler
from werkzeug.utils import secure_filename

from config import ConfigManager
from data import EnergyManager
from module import analytics as analytics_module
from module import consts, debug
from module import download as download_module
from module import functions as fc
from module import set_vals
from module import upload as upload_module

app = Flask(__name__)
app.secret_key = os.urandom(24)

scheduler = APScheduler()
scheduler.api_enabled = True

config_manager = ConfigManager("config_test.toml")
energy_manager_data = EnergyManager("data.toml")
energy_manager_morning_data = EnergyManager("mor_data.toml")
energy_manager_evening_data = EnergyManager("ev_data.toml")


@app.route('/', methods=['GET', 'POST'])
def index():
    config_data = config_manager.config_data
    return render_template('index.html', config=config_data)


@app.route('/dashboard')
def dashboard():
    config_data = config_manager.config_data
    return render_template('dashboard.html', config=config_data)


@app.route('/analytics')
def analytics():
    config_data = config_manager.config_data
    weather_data = fc.get_weather_data(config_data, days=14)

    energy_today, pv_power_data, market_data, heating_power_data, difference_power, battery_power = (
        analytics_module.analyze_data(config_data, weather_data))

    return render_template('analytics.html', energy_data=energy_today,
                           pv_power_data=pv_power_data, market_data=market_data,
                           heating_power_data=heating_power_data, differnce_power=difference_power,
                           battery_power=battery_power)


@app.route('/generate_download', methods=['POST'])
def download():
    config_data = config_manager.config_data

    msg: str = ""
    msg_market: list[str] = []
    msg_weather: list[str] = []
    err_msg_weather: str = ""
    err_msg_market: str = ""
    date_now: dict = {}

    if request.method == 'POST':
        date_now = download_module.date_time_download()
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


def allowed_file(filename, extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in extensions


@app.route('/settings')
def settings():
    config_files: list = os.listdir(consts.LOAD_PROFILE_FOLDER)
    valid_files: list = []
    for file in config_files:
        if allowed_file(file, {'json', 'xlsx', 'xls'}):
            valid_files.append(file)

    config_data = config_manager.config_data
    return render_template('set_vals.html', config=config_data, window_data=consts.WINDOW_DATA,
                           wall_data=consts.WALL_DATA, door_data=consts.DOOR_DATA, ceiling_data=consts.CEILING_DATA,
                           load_files=valid_files)


@app.route('/save_settings', methods=['POST'])
def safe_settings():
    config_data = config_manager.config_data

    if request.method == 'POST':

        data = request.form.to_dict()

        debug.printer(data)

        if data["mounting_type1"] == "-1":
            return render_template('set_vals.html',
                                   error_mounting_type='Bitte wählen Sie einen Montagetypen aus',
                                   config=config_data, window_data=consts.WINDOW_DATA,
                                   wall_data=consts.WALL_DATA, door_data=consts.DOOR_DATA,
                                   ceiling_data=consts.CEILING_DATA)

        if ((data.get('latitude', "") != "" and data.get('longitude', "") != "") or (
                data.get('Straße', "") != "" and data.get('Nr', "") != "" and
                data.get('Stadt', "") != "" and data.get('PLZ', "") != "" and
                data.get('Land', ""))):

            write_data = set_vals.write_data_to_config(config_data, data)
            config_manager.write_config_data(write_data)

            return redirect('/')
        else:
            return render_template('set_vals.html',
                                   error='Bitte füllen Sie mindestens Latitude, Longitude aus oder die Adresse',
                                   config=config_data, window_data=consts.WINDOW_DATA,
                                   wall_data=consts.WALL_DATA, door_data=consts.DOOR_DATA,
                                   ceiling_data=consts.CEILING_DATA)


@app.route('/file_download')
def file_download():
    data = download_module.date_time_download()
    return render_template('file_download.html', config=data)


@app.route('/file_upload')
def file_upload():
    return render_template('file_upload.html')


@app.route('/upload_file_solar_data', methods=['GET', 'POST'])
def upload_file_solar_data():
    ex: set = {'json'}
    err, filename, data = upload_file(ex, 'uploads', False)

    return render_template('file_upload.html', err_ending_solar=err, name_solar=filename, data=data)


@app.route('/upload_load_profile', methods=['GET', 'POST'])
def upload_load_profile():
    ex: set = {'json', 'xls', 'xlsx'}
    if not os.path.exists(consts.LOAD_PROFILE_FOLDER):
        os.makedirs(consts.LOAD_PROFILE_FOLDER)
    err, filename, data = upload_file(ex, consts.LOAD_PROFILE_FOLDER, False)

    return render_template('file_upload.html', err_ending_load=err, name_load=filename, data=data)


def upload_file(extensions: set, folder: str, delete_file=True):
    if request.method == 'POST':
        err = ''
        filename = ''

        if 'upload_file_json' not in request.files:
            flash('No file part')
            return err, filename, None

        file = request.files['upload_file_json']

        if file.filename == '':
            flash('No selected file')
            return err, filename, None

        if file and allowed_file(file.filename, extensions):
            if not os.path.exists(folder):
                os.mkdir(folder)
            if delete_file:
                for filename in os.listdir(folder):
                    os.remove(f"{folder}/{filename}")

            filename = secure_filename(file.filename)
            file.save(os.path.join(folder, filename))
            return err, filename, None

        elif not allowed_file(file.filename, extensions):
            filename = secure_filename(file.filename)
            ending = filename.rsplit('.', 1)[1].lower()
            err = f".{ending} ist nicht erlaubt. Nur {extensions} ist zulässig"
            return err, filename, None


@app.route('/analyze_file', methods=['GET', 'POST'])
def analyze_file():
    config_data = config_manager.config_data

    ret = upload_module.data_analyzer(config_data)
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
    return jsonify(consts.WINDOW_DATA.get(frame, []))


@app.route('/get_wall/<wall>')
def get_wall(wall):
    return jsonify(consts.WALL_DATA.get(wall, []))


@app.route('/get_floor/<floor>')
def get_floor(floor):
    return jsonify(consts.FLOOR_DATA.get(floor, []))


@app.route('/get_ceiling/<ceiling>')
def get_ceiling(ceiling):
    return jsonify(consts.CEILING_DATA.get(ceiling, []))


@app.route('/get_ceiling/<door>')
def get_door(door):
    return jsonify(consts.DOOR_DATA.get(door, []))


@scheduler.task("cron", id="morning_saver", hour=6)
def save_morning():
    print("save_data morning")
    print(datetime.datetime.now())

    config_data: dict = config_manager.config_data

    write_dict: dict = fc.save_mor_ev_data(config_data)

    energy_manager_morning_data.write_energy_data(write_dict)


@scheduler.task("cron", id="evening_saver", hour=20)
def save_evening():
    print("save_data evening")
    print(datetime.datetime.now())

    config_data: dict = config_manager.config_data

    write_dict: dict = fc.save_mor_ev_data(config_data)

    energy_manager_evening_data.write_energy_data(write_dict)


@scheduler.task("cron", id="data_compare", hour=21)
def compare_data():
    print("compare data")
    print(datetime.datetime.now())

    energy_data_morning = energy_manager_morning_data.energy_data
    energy_data_evening = energy_manager_evening_data.energy_data

    err = fc.comp_mor_ev_data(energy_data_morning, energy_data_evening)
    print(err)

    if err.get("average_dni_difference", 21) > 20 or err.get("energy_difference", 1) > (20 / 100):
        print("Big error")


@scheduler.task("interval", id="steering", seconds=3601)
def steering():
    config_data: dict = config_manager.config_data
    heater = config_data.get('heater')

    weather_data = fc.get_weather_data(config_data, days=1)

    energy_today, pv_power_data, market_data, heating_power_data, difference_power, battery_power = (
        analytics_module.analyze_data(config_data, weather_data, False)
    )

    heating_cost: list = []
    heating_cost_other: list = []
    idx = 0

    for (_, dp), (_, hp) in zip(difference_power, heating_power_data):
        electricity_costs: float = market_data[idx][1] * 0.25
        dp_kw: float = abs(dp / 1_000)
        hp_kw = abs(hp / 1_000)
        heater_efficiency: float = heater.get('heater_efficiency')
        heater_type: str = heater.get('heater_type')
        fuel_price: float = heater.get('heater_price', 0) * 100 * 0.25

        heating_cost.append((dp_kw * electricity_costs) if dp < 0 else dp_kw * 0.08 * 0.25)

        fuel_gas_price = fc.calc_fuel_gas_consumption(hp_kw, heater_efficiency, heater_type) * fuel_price

        heating_cost_other.append(fuel_gas_price)

        if idx % 4 == 0 and idx != 0:
            idx += 1

    z = []
    for _, hp in heating_power_data:
        z.append(hp)

    print(fc.calc_energy(z))

    daily_cost = sum(heating_cost)
    daily_cost_other = sum(heating_cost_other)

    print(daily_cost, 'ct')
    print(daily_cost_other, 'ct')


if __name__ == '__main__':
    scheduler.init_app(app)
    scheduler.start()

    app.run(debug=debug.debug_on, host='0.0.0.0', port=8888)

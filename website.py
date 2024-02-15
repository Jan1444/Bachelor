# -*- coding: utf-8 -*-

import datetime
import os

from flask import Flask, render_template, request, send_from_directory, redirect, flash, jsonify
from werkzeug.utils import secure_filename
from flask_apscheduler import APScheduler

from config import ConfigManager
from data import EnergyManager

from module import consts, debug
from module import functions as fc
from module import set_vals
from module import download as download_module

from numpy import array

UPLOAD_FOLDER = 'uploads'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
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

    converter = config_data["converter"]
    load_profile = config_data["load_profile"]
    battery = config_data.get('battery')

    pv_data_data: list = []
    weather_time: list = []

    diff_power: list = []

    battery_load: list = []
    min_capacity = battery.get('capacity', 0) * 1_000 * (1 - battery.get('max_deload', 100) / 100)
    charging_power = battery.get('charging_power', 0) * 0.25
    battery_capacity = battery.get('capacity', 0) * 1_000
    state_of_charge: float = min_capacity / battery_capacity * 100
    min_state_of_charge = min_capacity / battery_capacity * 100
    load_efficiency: float = battery.get('load_efficiency', 0) / 100

    time_now = datetime.datetime.now()

    sun_class = fc.init_sun(config_data)
    pv_class = fc.init_pv(config_data, number=1)
    pv_class2 = fc.init_pv(config_data, number=2)
    pv_class3 = fc.init_pv(config_data, number=3)
    pv_class4 = fc.init_pv(config_data, number=4)

    start_date = time_now.date().strftime('%d-%m-%Y')
    end_date = (time_now + datetime.timedelta(days=14)).date().strftime('%d-%m-%Y')

    weather = fc.get_weather_data(config_data, start_date, end_date)

    market_class = fc.init_market(config_data)

    load_profile_data: dict = fc.load_load_profile(f'{consts.LOAD_PROFILE_FOLDER}/{load_profile.get("name")}')

    hp = fc.heating_power(config_data, weather)
    indx = 0

    for date, weather_today in weather.items():
        weather_today.pop("daily")
        date_load: str = date.rsplit('-', 1)[0]
        curr_load: dict = load_profile_data.get(date_load, "")

        for (tme_pv, data), (tme_load, load_data) in zip(weather_today.items(), curr_load.items()):
            time_float = fc.string_time_to_float(tme_pv)
            temp: float = data.get("temp", 0)
            radiation_ghi = data.get("ghi_radiation", 0)

            azimuth, elevation = fc.get_sun_data(sun_class, time_float)

            power_ghi: float = fc.get_pv_data(pv_class, temp, radiation_ghi, azimuth, elevation)

            if config_data['pv']['alignment'] >= 2:
                power_ghi += fc.get_pv_data(pv_class2, temp, radiation_ghi, azimuth, elevation)
            if config_data['pv']['alignment'] >= 3:
                power_ghi += fc.get_pv_data(pv_class3, temp, radiation_ghi, azimuth, elevation)
            if config_data['pv']['alignment'] >= 4:
                power_ghi += fc.get_pv_data(pv_class4, temp, radiation_ghi, azimuth, elevation)

            if power_ghi > converter.get("max_power", 0):
                power_ghi = converter.get("max_power", 0)

            weather_time.append(f'{date} {tme_pv}')
            pv_data_data.append(power_ghi)

            if tme_pv != tme_load:
                continue

            heating_power: float = hp[1][indx]
            cop: float = hp[2][indx]

            load_diff: float = power_ghi - load_data  # Strom überschuss

            diff_energy: float = load_diff - (heating_power / cop)

            energy = diff_energy * 0.25

            if energy < 0:
                netto_energy = energy * converter.get('efficiency')
            else:
                energy = min(energy, charging_power)
                netto_energy = energy * load_efficiency

            state_of_charge += netto_energy / battery_capacity * 100
            state_of_charge = max(min_state_of_charge, min(state_of_charge, 100))
            battery_load.append(state_of_charge)

            diff_power.append(diff_energy)

            indx += 1

    energy_today = fc.calc_energy(pv_data_data[:95], kwh=False, round_=2)

    market_time = [time.get('start_timestamp') for time in market_class.data]
    market_price = [price.get('consumerprice') for price in market_class.data]

    pv_power_data = [[time, value] for time, value in zip(weather_time, array(pv_data_data, dtype=float))]

    market_data = [[time, value] for time, value in zip(market_time, market_price)]

    heating_power_data = [[time, value] for time, value in zip(hp[0], hp[1])]

    difference_power = [[time, value] for time, value in zip(hp[0], diff_power)]

    battery_power = [[time, value] for time, value in zip(hp[0], battery_load)]

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
    data = fc.date_time_download()
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

    ret = fc.data_analyzer(config_data)
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

    if err.get("average_dni_difference", 21) > 20 or err.get("energy_difference", 1) > (200 / 1_000):
        print("Big error")


'''@scheduler.task("interval", id="steering", seconds=900)
def steering():
    print(datetime.datetime.now())
    print("steering")

'''

if __name__ == '__main__':
    scheduler.init_app(app)
    scheduler.start()

    app.run(debug=debug.debug_on, host='0.0.0.0', port=8888)

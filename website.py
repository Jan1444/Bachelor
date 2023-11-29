import datetime
import random

import matplotlib.pyplot as plt
import requests
import tomli
import tomli_w
from flask import Flask, render_template, request

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


def write_data_to_file(weather_data: dict, sun: object, pv: object, market: object) -> None:
    data_file_path = "data/data.toml"
    data: dict = {"write_time": {"time": datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                                 "format": "%d-%m-%Y %H:%M:%S"}}
    zeit: int = -1
    for z, t in enumerate(weather_data.keys()):
        if t != "daily":
            radiation = float(weather_data[t]["radiation"])
            time_float = float(t[:2]) + float(t[3:]) / 100
            sun_height = sun.calc_solar_elevation(time_float)
            sun_azimuth = sun.calc_azimuth(time_float)
            incidence = pv.calc_incidence_angle(sun_height, sun_azimuth)
            curr_eff = pv.calc_temp_dependency(weather_data[t]["temp"], radiation)
            energy = pv.calc_energy(radiation, incidence, sun_height, curr_eff)

            data.update({t: {"radiation": radiation, "energy": round(energy, 3),
                             "market_price": market.data[zeit]["consumerprice"]}})
        if (z - 4) % 4 == 0:
            zeit += 1

    with open(data_file_path, 'wb') as f:
        tomli_w.dump(data, f)


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


def calc_energy(energy: list, interval: float = 0.25) -> list:
    power_values = list(map(lambda x: x / 1000, energy))
    total_energy = sum((power_values[i] + power_values[i + 1]) / 2 * interval for i in range(len(power_values) - 1))
    return total_energy


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
    toml_file_path = 'config/config_test.toml'
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
    plt.clf()
    xs = range(100)
    ys = [random.randint(1, 50) for x in xs]
    plt.plot(xs, ys)
    plt.savefig('static/plots/output.png')
    return render_template('analytics.html', name="new_plot", url="/static/plots/output.png")


@app.route('/download', methods=['POST'])
def download():
    toml_file_path = 'config/config_test.toml'
    with open(toml_file_path, 'rb') as f:
        config_data = tomli.load(f)
    if request.method == 'POST':
        data = request.form.to_dict()
        start_date = datetime.datetime.strptime(data['start_date'], "%Y-%m-%d")
        end_date = datetime.datetime.strptime(data['end_date'], "%Y-%m-%d")

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
        for date in weather_date.keys():
            sun = classes.CalcSunPos(config_data['coordinates']['latitude'], config_data['coordinates']['longitude'],
                                     date)
            power_data[date] = {}
            energy_data_list: list = []
            for t in weather_date[date].keys():
                if t != "daily":
                    time_float: float = int(t[:2]) + int(t[3:]) / 100
                    azimuth: float = sun.calc_azimuth(time_float)
                    elevation: floatt = sun.calc_solar_elevation(time_float)
                    incidence = pv.calc_incidence_angle(elevation, azimuth)
                    eff = pv.calc_temp_dependency(weather_date[date][t]["temp"], weather_date[date][t]["radiation"])
                    power_data[date][t] = pv.calc_power(weather_date[date][t]["radiation"], incidence, elevation, eff)
                    energy_data_list.append(power_data[date][t])
            energy_data[date] = calc_energy(energy_data_list)
        print(power_data)
        print(energy_data)
        plt.figure(figsize=(60, 15))
        plt.grid()
        plt.xticks(rotation=90)
        plt.plot(energy_data.keys(), energy_data.values())
        plt.savefig("plot.png")
    return render_template('index.html', config=config_data)


@app.route('/settings')
def settings():
    toml_file_path = 'config/config_test.toml'

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
        toml_file_path = 'config/config_test.toml'
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
    date_today = datetime.datetime.now().strftime("%Y-%m-%d")
    return render_template('file_download.html', config=date_today)


if __name__ == '__main__':
    app.run(debug=True)

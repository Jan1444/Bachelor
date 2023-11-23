import matplotlib.pyplot as plt
import tomli
import tomli_w
from flask import Flask, render_template, request

import classes

app = Flask(__name__)


def init_classes(latitude: float, longitude: float, module_efficiency: float, module_area: int, tilt_angle: float,
                 exposure_angle: float, mounting_type: int, costs: float) -> (object, object, object, object):
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


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@app.route('/download')
def download():
    # Hier könnte Code zum Exportieren von Daten als Excel-Datei stehen
    pass


@app.route('/settings')
def settings():
    toml_file_path = 'config/config_test.toml'

    # TOML-Datei lesen
    with open(toml_file_path, 'rb') as f:
        config_data = tomli.load(f)

    return render_template('set_vals.html', config=config_data)


@app.route('/save_settings', methods=['POST'])
def safe_settings():
    if request.method == 'POST':
        # Pfad zur TOML-Datei
        toml_file_path = 'config/config_test.toml'

        # Formulardaten empfangen
        data = request.form.to_dict()

        # TOML-Datei lesen, aktualisieren und zurückschreiben
        with open(toml_file_path, 'rb') as f:
            config_data = tomli.load(f)

        # Aktualisieren Sie hier die Konfigurationsdaten mit den Formulardaten
        # Beispiel:
        config_data['coordinates']['latitude'] = float(data['latitude'])
        config_data['coordinates']['longitude'] = float(data['longitude'])
        config_data['pv']['tilt_angle'] = float(data['tilt_angle'])
        config_data['pv']['area'] = float(data['area'])
        config_data['pv']['module_efficiency'] = float(data['module_efficiency'])
        config_data['pv']['exposure_angle'] = float(data['exposure_angle'])
        config_data['pv']['temperature_coefficient'] = float(data['temperature_coefficient'])
        config_data['pv']['nominal_temperature'] = float(data['nominal_temperature'])
        config_data['pv']['mounting_type'] = int(data['mounting_type'])
        config_data['market']['consumer_price'] = float(data['consumer_price'])

        # TOML-Datei mit aktualisierten Daten schreiben
        with open(toml_file_path, 'wb') as f:
            tomli_w.dump(config_data, f)

        return render_template('index.html')


def test_day_data(weather_data: dict, sun: object, pv: object, market: object) -> (list, list, list, list):
    time_list: list = []
    energy_list: list = []
    market_list: list = []
    pv_eff: list = []
    zeit = 0
    count = -3
    for t in weather_data.keys():
        if t != "daily":
            radiation = float(weather_data[t]["radiation"])
            pv_temp = pv.calc_pv_temp(weather_data[t]["temp"], 100)
            time_float = float(t[:2]) + float(t[3:]) / 100
            time_list.append(t)
            sun_height = sun.calc_solar_elevation(time_float)
            sun_azimuth = sun.calc_azimuth(time_float)
            incidence = pv.calc_incidence_angle(sun_height, sun_azimuth)
            curr_eff = pv.calc_temp_dependency(weather_data[t]["temp"], radiation)
            energy = pv.calc_energy(radiation, incidence, sun_height, curr_eff)
            energy_list.append(energy)
            market_list.append(market.data[zeit]["consumerprice"])
            pv_eff.append(curr_eff * 100)
            print("time: ", time_float)
            print("pv temp: ", pv_temp)
            print("radiation: ", radiation)
            print("sun height: ", sun_height)
            print("sun azimuth: ", sun_azimuth)
            print("incidence: ", incidence)
            print("Efficiency: ", curr_eff)
            print("energy: ", energy)
            print("price", market.data[zeit]["consumerprice"])
            print("-" * 30)
            if count % 4 == 0:
                zeit += 1
            count += 1
    data_mean = []
    data_mean_list = []
    for count in range(len(energy_list)):
        if energy_list[count] > 0:
            data_mean.append(energy_list[count])
    if len(data_mean) != 0:
        data_mean = sum(data_mean) / len(data_mean)
    for count in range(len(time_list)):
        data_mean_list.append(data_mean)
    x = time_list

    plt.plot(x, energy_list, label="Energie")
    plt.plot(x, market_list, label="Strompreis")
    plt.plot(x, data_mean_list, label="Durchschnittsleistung")
    plt.plot(x, pv_eff, label="PV Effizienz")
    return x, energy_list, market_list, pv_eff


if __name__ == '__main__':
    app.run(debug=True)

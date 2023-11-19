import matplotlib.pyplot as plt
import pandas as pd

import classes
from config import settings as consts


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
    weather = classes.weather(latitude, longitude)
    market = classes.market_data(costs)
    sun = classes.calc_sun_pos(latitude, longitude)
    pv = classes.pv_profit(module_efficiency, module_area, tilt_angle, exposure_angle, -0.35, 25, mounting_type)
    return weather, market, sun, pv


def to_excel(w, col):
    df = pd.DataFrame.from_dict(w.data[list(w.data.keys())[0]])
    df = df.iloc[6]
    with pd.ExcelWriter(r'/Users/jan/Documents/Weiterbildung/Bachelor/7. Semester/Bachelorarbeit/SolarDaten/'
                        r'2023_11_17_data.xlsx',
                        mode='a', if_sheet_exists="overlay") as wr:
        df.to_excel(wr, index=True, startrow=1, startcol=col)

    # print(df)


def test_day_data(weather_data: dict, sun: object, pv: object, market: object) -> (list, list, list, list):
    t_list: list = []
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
            t_list.append(t)
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
    for count in range(len(t_list)):
        data_mean_list.append(data_mean)
    x = t_list

    plt.plot(x, energy_list, label="Energie")
    plt.plot(x, market_list, label="Strompreis")
    plt.plot(x, data_mean_list, label="Durchschnittsleistung")
    plt.plot(x, pv_eff, label="PV Effizienz")


def main1():
    plt.figure(figsize=(60, 15))
    plt.grid()
    coordinates = consts["coordinates"]
    pv_consts = consts["pv"]
    market_consts = consts["market"]

    w, m, sun, pv = init_classes(coordinates["latitude"], coordinates["longitude"],
                                 pv_consts["module_efficiency"], pv_consts["area"],
                                 pv_consts["tilt_angle"], pv_consts["exposure_angle"],
                                 pv_consts["mounting_type"], market_consts["consumer_price"])
    test_day_data(w.data[list(w.data.keys())[0]], sun, pv, m)

    plt.legend(loc="upper left")
    plt.show()


def main2(count):
    w, m, sun, pv = init_classes(consts["coordinates"]["latitude"], consts["coordinates"]["longitude"],
                                 consts["pv"]["module_efficiency"], consts["pv"]["area"],
                                 consts["pv"]["tilt_angle"], consts["pv"]["exposure_angle"],
                                 consts["pv"]["mounting_type"], consts["market"]["consumer_price"])
    test_day_data(w.data[list(w.data.keys())[0]], sun, pv, m)
    to_excel(w, count)


if __name__ == "__main__":
    i = 0
    main1()
    '''
    while True:
        main2(i)
        i += 2
        print("i = ", i)
        minute = 15
        for t in range(0, minute, 1):
            print("verbleibende minuten: ", minute - t)
            time.sleep(60)
    '''

# mitsubishi pymelcloud
# Daikin gibts auch Lsg
# IR sollte immer funktionieren

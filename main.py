import matplotlib.pyplot as plt
import requests
import classes
from config import settings as consts


def init_classes(latitude: float, longitude: float, module_efficiency: float, module_area: int, tilt_angle: float,
                 exposure_angle: float, mounting_type: int, costs: float) -> (classmethod, classmethod, classmethod, classmethod):
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
    weather: classmethod = classes.Weather(latitude, longitude)
    market: classmethod = classes.MarketData(costs)
    sun: classmethod = classes.CalcSunPos(latitude, longitude)
    pv: classmethod = classes.PVProfit(module_efficiency, module_area, tilt_angle, exposure_angle, -0.35, 25, mounting_type)
    return weather, market, sun, pv


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
    interval = 0.25

    power_values = list(map(lambda x: x / 1000, energy_list))
    total_energy = sum((power_values[i] + power_values[i + 1]) / 2 * interval for i in range(len(power_values) - 1))

    print(f"Energie über den Tag: {round(total_energy, 2)}kWh")

    x = t_list

    plt.plot(x, energy_list, label="Energie")
    plt.plot(x, market_list, label="Strompreis")
    plt.plot(x, data_mean_list, label="Durchschnittsleistung")
    plt.plot(x, pv_eff, label="PV Effizienz")


def main():
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


if __name__ == "__main__":
    main()

# mitsubishi pymelcloud
# Daikin gibts auch Lsg
# IR sollte immer funktionieren

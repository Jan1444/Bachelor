#  -*- coding: utf-8 -*-

import datetime
from functools import lru_cache

# import ADS1x15
# import RPi.GPIO as GPIO
import requests
import toml
from numpy import float32, float16, uint16
from pandas import ExcelFile

# from module import GP8403
from module import classes, debug, own_wrapper as wrap


def read_data_from_file(file_path: str) -> dict | None:
    """

    :param file_path:
    :return:
    """
    try:
        with open(file_path, 'r') as f:
            data = toml.load(f)
        return data
    except FileNotFoundError:
        print("No File at " + file_path)
        print("Try again")
        file_path = file_path[1:]
        print("Try again with: " + file_path)
        try:
            with open(file_path, 'r') as f:
                data = toml.load(f)
            return data
        except FileNotFoundError:
            return None


def write_data_to_file(data: dict, file_path: str) -> dict:
    """

    :param data:
    :param file_path:
    :return:
    """
    try:
        with open(file_path, 'w') as f:
            toml.dump(data, f)
        return data
    except FileNotFoundError:
        print("No File at " + file_path)
        print("Try again")
        file_path = file_path[1:]
        print("Try again with: " + file_path)
        try:
            with open(file_path, 'w') as f:
                toml.dump(data, f)
        except FileNotFoundError:
            print("No File at " + file_path)


def get_coord(street: str, nr: str, city: str, postalcode: int, country: str) -> (str, str):
    # https://nominatim.org/release-docs/develop/api/Search/
    """

    :param street:
    :param nr:
    :param city:
    :param postalcode:
    :param country:
    :return:
    """
    street_rep = street.replace(" ", "&20")
    city_rep = city.replace(" ", "&20")
    url = (f"https://nominatim.openstreetmap.org/search?q={street_rep}%20{nr}%20{city_rep}%20{postalcode}%20{country}"
           f"&format=json&addressdetails=1")
    debug.printer(url)
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


@wrap.precision()
@wrap.formatter
@wrap.freeze_all
@lru_cache(maxsize=1_000)
def calc_energy(power: list, interval: float = 0.25, kwh: bool = True, round_: None | int = None) -> float:
    """

    :param power:
    :param interval:
    :param kwh:
    :param round_:
    :return:
    """
    multiplier = 1
    if kwh:
        multiplier = 1000
    power_values = list(map(lambda x: x / multiplier, power))
    total_energy = sum(power * interval for power in power_values)

    if round_ is not None:
        total_energy = round(total_energy, round_)

    return float(total_energy)


def get_weather_data(config_data: dict, start: str | None = None, end: str | None = None, days: int | None = None):
    coord = config_data["coordinates"]
    w = classes.Weather(coord["latitude"], coord["longitude"], start, end, days)
    return w.data


def init_sun(config_data: dict, date: str | None = None) -> classes.CalcSunPos:
    coord = config_data["coordinates"]
    s = classes.CalcSunPos(coord["latitude"], coord["longitude"], date)
    return s


def get_sun_data(sun_class: classes.CalcSunPos, tme: float) -> (float, float):
    az = sun_class.calc_azimuth(tme)
    el = sun_class.calc_solar_elevation(tme)
    return az, el


def init_pv(config_data: dict, number: int = 1) -> classes.PVProfit:
    pv = config_data["pv"]
    p = classes.PVProfit(pv[f"module_efficiency{number}"], pv[f"area{number}"], pv[f"tilt_angle{number}"],
                         pv[f"exposure_angle{number}"], pv[f"temperature_coefficient{number}"],
                         pv[f"nominal_temperature{number}"], pv[f"mounting_type{number}"])
    return p


def get_pv_data(pv_class: classes.PVProfit, temp: float, radiation: float, azimuth: float, elevation: float,
                dni: bool = False) -> float32:
    incidence_angle: float32 = pv_class.calc_incidence_angle(elevation, azimuth)
    if dni:
        power: float32 = pv_class.calc_power_with_dni(radiation, incidence_angle, temp)
        return power
    eff: float32 = pv_class.calc_temp_dependency(temp, radiation)
    power: float32 = pv_class.calc_power(radiation, incidence_angle, elevation, eff)
    return power


def init_market(config_data: dict, start_time: int | None = None, end_time: int | None = None) -> classes.MarketData:
    cc: float = config_data["market"].get("consumer_price", 0)
    m = classes.MarketData(cc, start_time, end_time)
    return m


@lru_cache(maxsize=100)
def string_time_to_float(tme: str) -> float16:
    tme_list: list = tme.split(":")
    return float16(uint16(tme_list[0]) + float16(tme_list[1]) / 100)


def save_mor_ev_data(config_data: dict) -> dict:
    power_list: list = []
    write_dict: dict = {}

    weather_data: dict = get_weather_data(config_data)
    today_data = list(weather_data.keys())[0]
    weather_data_today = weather_data[today_data]

    sun_class = init_sun(config_data)
    pv_class = init_pv(config_data)

    for tme, data in weather_data_today.items():
        tme_float: float = string_time_to_float(tme)
        azimuth, elevation = get_sun_data(sun_class, tme_float)
        temp: float = float(data.get("temp", 0))
        radiation: float = float(data.get("dni_radiation", 0))
        radiation_ghi: float = float(data.get("ghi_radiation", 0))
        # power: float = get_pv_data(pv_class, temp, radiation, azimuth, elevation, True)
        power: float = get_pv_data(pv_class, temp, radiation_ghi, azimuth, elevation, False)

        write_dict.update(
            {
                tme: {
                    "dni_radiation": radiation,
                    "ghi_radiation": radiation_ghi,
                    "cloudcover": data.get("cloudcover", 0),
                    "temp": temp,
                    "power": power
                }
            }
        )

        power_list.append(power)

    energy: float = calc_energy(power_list, round_=3)
    write_dict.update(
        {
            "energy": energy
        }
    )

    return write_dict


@wrap.precision()
@wrap.freeze_all
@lru_cache(maxsize=1_000)
def unpack_data(data: dict) -> (list[str], list[float], list[float], list[float]):
    """

    :param data:
    :return:
    """
    weather_time: list[str] = []
    radiation_data: list[float] = []
    power_data: list[float] = []

    market_time: list[float] = []
    market_price: list[float] = []

    error_key: int = 0

    try:
        if "dni_radiation" in data["00:00"].keys():
            radiation_key = "dni_radiation"
        elif "radiation" in data["00:00"].keys():
            radiation_key = "radiation"
        else:
            raise KeyError("No key: dni_radiation or radiation")
    except KeyError as error:
        print(error)
        return -1, -1, -1, -1

    try:
        for t in data.keys():
            if t != "write_time":
                weather_time.append(t)
                radiation_data.append(data[t][radiation_key])
                power_data.append(data[t]["power"])
                if t[3:] == "00":
                    market_time.append(t)
                    market_price.append(data[t]["market_price"])
                error_key += 1
        return weather_time, radiation_data, power_data, market_time, market_price
    except KeyError as error:
        print(f"No key: {error}")
        print(f"In line: {error_key * 5 + 7}")


def comp_mor_ev_data(morning_data, evening_data):
    debug.printer(evening_data, description="evening_data: ")
    debug.printer(morning_data, description="morning_data: ")

    tme_ev = evening_data.get("write_time", {"time": "0", "format": "0"})
    time_evening = datetime.datetime.strptime(tme_ev.get("time"), tme_ev.get("format"))

    tme_mor = morning_data.get("write_time", {"time": "0", "format": "0"})
    time_morning = datetime.datetime.strptime(tme_mor.get("time"), tme_mor.get("format"))

    if time_evening <= time_morning:
        print("No comparison available, no right time!")
        return {}

    total_dni_difference = 0
    count = 0

    for time_point, evening_values in evening_data.items():
        if time_point in ["energy", "write_time"]:
            continue

        morning_values = morning_data.get(time_point)
        if morning_values:
            total_dni_difference += abs(evening_values.get('dni_radiation', 0) - morning_values.get('dni_radiation', 0))
            total_dni_difference += abs(evening_values.get('ghi_radiation', 0) - morning_values.get('ghi_radiation', 0))
            count += 1

    # energy_difference = abs(evening_data.get("energy", 0) - morning_data.get("energy", 0))
    energy_difference = abs(evening_data.get("energy", 0) / morning_data.get("energy", 0)) * 100

    if count > 0:
        average_dni_difference = total_dni_difference / count
    else:
        average_dni_difference = None

    return {
        "average_dni_difference": average_dni_difference,
        "energy_difference": energy_difference
    }


def calc_diff_hp_energy(hp: list, cop: list, power: list) -> list:
    heating_energy: list = list(map(lambda p, c: (p * c) if p is not None else None, power, cop))
    diff: list = list(map(lambda e, p: e - p, heating_energy, hp))

    return diff


def load_load_profile(path: str | None) -> dict:
    def _create_null_profile() -> dict:
        empty_dict: dict = {}
        start = datetime.date(2024, 1, 1)
        end = datetime.date(2024, 12, 31)

        delta = (end - start).days

        for i in range(0, delta + 1):
            day = start + datetime.timedelta(days=i)
            date_ = day.strftime("%d-%m")
            empty_dict[date_] = {}
            for hour in range(0, 24):
                for minute in range(0, 60, 15):
                    tme = f'{str(hour).zfill(2)}:{str(minute).zfill(2)}'
                    empty_dict[date_][tme] = 0
        return empty_dict

    if path is None or 'None' in path:
        return _create_null_profile()

    data_extension = path[path.rfind('.'):]

    if '.json' in data_extension:
        print('json File')
        return _create_null_profile()
        # sheet = json.load(open(path, "rb+"))

    elif '.xlsx' in data_extension or '.xls' in data_extension:
        try:
            xl = ExcelFile(path)
        except FileNotFoundError:
            print('File Not Found')
            return _create_null_profile()

        df = xl.parse(xl.sheet_names[0])
        data_dict = {}
        date_str = ''
        for row in df.values:
            try:
                date_str, load = row[0], row[1]

                if 'datetime' in str(type(date_str)) or 'timestamp' in str(type(date_str)):
                    date_time = date_str

                else:
                    date_time = datetime.datetime.strptime(date_str, "%d.%m.%Y %H:%M:%S")

                date = date_time.date().strftime("%d-%m")
                time = date_time.time().strftime("%H:%M")

                if date not in data_dict:
                    data_dict[date] = {}
                data_dict[date][time] = float(str(load).replace(",", '.'))  # * 1000
            except Exception as e:
                print(date_str)
                print(f'Following error is occurred by loading load_profile: {e}')
                return _create_null_profile()

        return data_dict


@wrap.precision()
@wrap.formatter
@lru_cache(maxsize=100)
def calc_fuel_consumption(heating: float32, efficiency: float32, energy_density: float32 = float32(11.8),
                          density: float32 = float32(0.85)) -> float32:
    heating: float32 = float32(heating / 1000.0)

    required_energy: float32 = heating / (efficiency / 100.0)

    fuel_mass: float32 = required_energy / energy_density

    fuel_volume: float32 = fuel_mass / density

    return fuel_volume


@wrap.precision()
@wrap.formatter
@lru_cache(maxsize=100)
def calc_gas_consumption(heating: float32, efficiency: float32) -> float32:
    heating = float32(heating / 1000.0)

    required_energy: float32 = heating / (efficiency / 100.0)

    return required_energy


@wrap.precision()
@wrap.formatter
@lru_cache(maxsize=100)
def calc_fuel_gas_consumption(heating: float32, efficiency: float32, fuel: str):
    if fuel == 'gas':
        required_energy: float32 = heating / (efficiency / 100.0)
        return required_energy

    elif fuel == 'fuel':
        energy_density: float32 = float32(11.8)

        required_energy: float32 = heating / (efficiency / 100.0)
        fuel_volume: float32 = required_energy / energy_density
        return fuel_volume
    return 1


def read_val_from_adc(channel: int, address: hex = 0x48) -> float32:
    # https://github.com/chandrawi/ADS1x15-ADC/blob/main/README.md
    r1: float32 = float32(1_000)
    r2: float32 = float32(1_000)

    ads = ADS1x15.ADS1115(1, address)
    ads.setGain(ads.PGA_6_144V)

    vol: float32 = float32(ads.toVoltage(channel))
    return (vol * (r1 + r2)) / r2


def write_val_to_dac(channel: int, val: float32, address: hex = 0x58):
    # https://github.com/DFRobot/DFRobot_GP8403/blob/master/python/raspberryPi/README.md
    dac = GP8403.DFRobot_GP8403(address)
    while dac.begin() != 0:
        print("init error")

    dac.set_dac_outrange(GP8403.OUTPUT_RANGE_10V)
    dac.set_dac_out_voltage(val, channel)


def relay(channel: int, val: bool):
    if channel == 1:
        pin = 4
    elif channel == 2:
        pin = 18
    elif channel == 3:
        pin = 27
    elif channel == 4:
        pin = 23
    else:
        return

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, val)
    GPIO.cleanup()

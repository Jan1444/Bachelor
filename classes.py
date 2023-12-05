import datetime
from functools import lru_cache

import numpy as np
import requests_cache


class MarketData:
    """
    Gets the market data to the given time interval
    """

    def __init__(self, consumer_costs) -> None:
        """
        Initialize the market data class
        :param consumer_costs: The cost of the grid
        :return: None
        """
        date_today: str = datetime.datetime.today().strftime("%Y-%m-%d")
        time_start: str = "00:00:00,00"
        self.session = requests_cache.CachedSession('marketdata.cache', expire_after=datetime.timedelta(hours=1))
        time_start_ms: int = self.convert_time_to_ms(date_today, time_start)
        self.data: dict = self.get_data(start=time_start_ms)
        self.convert_dict(consumer_costs)

    def __str__(self) -> str:
        """
        can be used to print easily the data
        :return: The market as string
        """
        return str(self.data)

    @staticmethod
    def convert_ms_to_time(ms: int) -> str:
        """
        convert the given ms to a time string (hour and minutes)
        :param ms: The ms to convert
        :return: the time in hour and minutes
        """
        date_time = datetime.datetime.fromtimestamp(ms / 1000).time()
        t = f"{date_time.hour}:00"
        return t

    @staticmethod
    def convert_time_to_ms(date: str, t: str) -> int:
        """
        convert the given date and time to milliseconds
        :param date: As str
        :param t: time as string in format %H:%M:%S,%f
        :return: milliseconds
        """
        dt_obj = int(datetime.datetime.strptime(f"{date} {t}", '%Y-%m-%d %H:%M:%S,%f').timestamp() * 1000)
        return dt_obj

    def get_data(self, start: int | None = None, end: int | None = None) -> dict:
        """
        Gets the data from the awattar api for 24 hours or the given start and end time
        https://www.awattar.de/services/api
        :param start: start time in millisecond
        :param end: end time in milliseconds
        :return: json string of the data as dict
        """
        if start and not end:
            url = rf"https://api.awattar.de/v1/marketdata?start={int(start)}"
            print(url)
        elif end and not start:
            url = rf"https://api.awattar.de/v1/marketdata?end={int(end)}"
        elif start and end:
            url = rf"https://api.awattar.de/v1/marketdata?start={int(start)}&end={int(end)}"
        else:
            url = r"https://api.awattar.de/v1/marketdata"
        return self.session.get(url).json()['data']

    def convert_dict(self, consumer_costs) -> None:
        """
        converts the millisecond timestamp in the dict to time
        :return: None
        """
        for i, old_data in enumerate(self.data):
            self.data[i]['start_timestamp'] = self.convert_ms_to_time(old_data['start_timestamp'])
            self.data[i]['end_timestamp'] = self.convert_ms_to_time(old_data['end_timestamp'])
            self.data[i]['marketprice'] = round(old_data['marketprice'] / 10, 3)
            self.data[i]['consumerprice'] = round((old_data['marketprice'] + consumer_costs) * 1.19, 3)
            self.data[i]['unit'] = 'EUR/kWh'


class Weather:
    """
    Gets the needed weather data from open-meteo.com
    """

    # https://open-meteo.com/en/docs#latitude=49.5139&longitude=11.2825&minutely_15=diffuse_radiation_instant&
    # hourly=temperature_2m,cloudcover

    def __init__(self, latitude: float, longitude: float, start_date: str | None = None, end_date: str | None = None) \
            -> None:
        """
        initialize the class
        :param latitude:
        :param longitude:
        :return: none
        """
        self.latitude: float = latitude
        self.longitude: float = longitude
        self._expire_time = 1
        self.session = requests_cache.CachedSession('weatherdata.cache',
                                                    expire_after=datetime.timedelta(hours=self._expire_time))
        weather_data: dict = self.get_weather(start_date, end_date)
        self.data: dict = {}
        try:
            self.create_dict(weather_data, start_date, end_date)
            self.sort_weather(weather_data)
        except LookupError as e:
            if "reason" in weather_data.keys():
                print(weather_data["reason"])
            else:
                print(e)
        except Exception as e:
            print("Exceptions has occurred: ", e)

    def __str__(self) -> str:
        """
        can be used to easily print the data
        :return: str of the data
        """
        return str(self.data)

    def create_dict(self, weather_data: dict, start_date: str | None, end_date: str | None) -> None:
        days: list = []
        if start_date is not None and end_date is not None:
            for date in weather_data["hourly"]["time"]:
                date = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M').strftime('%d-%m-%Y')
                days.append(date)
        else:
            for date in weather_data["hourly"]["time"]:
                date = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M').strftime('%d-%m-%Y')
                days.append(date)
        times: list = [f"{str(hour).zfill(2)}:{str(minute).zfill(2)}"
                       for hour in range(24)
                       for minute in range(0, 60, 15)]
        for day in days:
            self.data[str(day)] = {}
            self.data[str(day)]["daily"] = {
                "temp_max": "",
                "temp_min": "",
                "sunrise": "",
                "sunset": ""
            }
            for t in times:
                self.data[day][t] = {
                    "temp": "",
                    "cloudcover": "",
                    "radiation": ""
                }

    def get_weather(self, start_date: str | None, end_date: str | None) -> dict:
        """
        Gets the weather for the given latitude and longitude
        :return: A dict with the following variables: direct radiation, temperatur, cloudcover, temperature max,
                 temperatur min, sunrise, sunset
        """
        if start_date is None or end_date is None:
            url: str = (f"https://api.open-meteo.com/v1/forecast?latitude={self.latitude}&longitude={self.longitude}&"
                        "minutely_15=direct_radiation&hourly=temperature_2m,cloudcover&models=best_match&"
                        "daily=temperature_2m_max,temperature_2m_min,sunrise,sunset&"
                        "timezone=Europe%2FBerlin&forecast_days=3")
        else:
            start: datetime = datetime.datetime.strptime(start_date, "%d-%m-%Y")
            end: datetime = datetime.datetime.strptime(end_date, "%d-%m-%Y")
            url: str = (f"https://api.open-meteo.com/v1/forecast?latitude={self.latitude}&longitude={self.longitude}&"
                        f"minutely_15=direct_radiation&hourly=temperature_2m,cloudcover&models=best_match&"
                        f"daily=temperature_2m_max,temperature_2m_min,sunrise,sunset&"
                        f"timezone=Europe%2FBerlin&start_date={start.year}-{str(start.month).zfill(2)}"
                        f"-{str(start.day).zfill(2)}"
                        f"&end_date={end.year}-{str(end.month).zfill(2)}-{str(end.day).zfill(2)}")
        print(url)
        return self.session.get(url).json()

    def sort_weather(self, unsorted_data: dict) -> None:
        """
        Sorts the weather in a dictionary
        :return: None
        """
        date = datetime.datetime.strptime(unsorted_data["minutely_15"]["time"][0],
                                          '%Y-%m-%dT%H:%M').strftime('%d-%m-%Y')
        for i, t in enumerate(unsorted_data["minutely_15"]["time"]):
            self.data[date][t[11:]]["radiation"] = unsorted_data["minutely_15"]["direct_radiation"][i]
            if t[11:] == "23:45":
                date = datetime.datetime.strptime(date, '%d-%m-%Y') + datetime.timedelta(days=1)
                date = date.strftime('%d-%m-%Y')
        date = datetime.datetime.strptime(unsorted_data["minutely_15"]["time"][0],
                                          '%Y-%m-%dT%H:%M').strftime('%d-%m-%Y')
        tt: str | None = None
        for i, t in enumerate(unsorted_data["hourly"]["time"]):
            for x in range(0, 60, 15):
                tt = f"{t[11:13]}:{str(x).zfill(2)}"
                self.data[date][tt]["temp"] = unsorted_data["hourly"]["temperature_2m"][i]
                self.data[date][tt]["cloudcover"] = unsorted_data["hourly"]["cloudcover"][i]
            if tt == "23:45":
                date = datetime.datetime.strptime(date, '%d-%m-%Y') + datetime.timedelta(days=1)
                date = date.strftime('%d-%m-%Y')
        date = datetime.datetime.strptime(unsorted_data["minutely_15"]["time"][0],
                                          '%Y-%m-%dT%H:%M').strftime('%d-%m-%Y')
        for i, d in enumerate(unsorted_data["daily"]["time"]):
            self.data[date]["daily"]["temp_max"] = unsorted_data["daily"]["temperature_2m_max"][i]
            self.data[date]["daily"]["temp_min"] = unsorted_data["daily"]["temperature_2m_min"][i]
            self.data[date]["daily"]["sunrise"] = unsorted_data["daily"]["sunrise"][i][11:]
            self.data[date]["daily"]["sunset"] = unsorted_data["daily"]["sunset"][i][11:]
            date = datetime.datetime.strptime(date, '%d-%m-%Y') + datetime.timedelta(days=1)
            date = date.strftime('%d-%m-%Y')


class CalcSunPos:
    """
    calcs the position of the sun
    """

    def __init__(self, latitude, longitude, date: str | None = None) -> None:
        """
        initialize the class
        :param latitude:
        :param longitude:
        """
        self.time_last_calc: float | None = None
        self.hour_angle: float | None = None
        self.real_local_time: float | None = None
        self.mid_local_time: float | None = None
        self.latitude: float = np.deg2rad(latitude)
        self.longitude: float = np.deg2rad(longitude)
        if date is None:
            self.current_date: datetime.datetime.time = datetime.datetime.now()
        else:
            self.current_date: datetime.datetime.time = datetime.datetime.strptime(date, "%d-%m-%Y")
        self.left_days: int = (self.current_date - datetime.datetime(self.current_date.year, 1, 1)).days
        self.days_per_year: int = (datetime.datetime(self.current_date.year, 12, 31) -
                                   datetime.datetime(self.current_date.year, 1, 1)).days + 1
        self.day_angle: float = np.deg2rad(360.0) * self.left_days / self.days_per_year

        self.sun_declination: float = (  # rad
                np.deg2rad(0.3948) - np.deg2rad(23.2559) * np.cos(self.day_angle + np.deg2rad(9.1)) -
                np.deg2rad(0.3915) * np.cos(2.0 * self.day_angle + np.deg2rad(5.4)) -
                np.deg2rad(0.1764) * np.cos(3.0 * self.day_angle + np.deg2rad(26.0)))

        self.time_equation: float = (
                np.deg2rad(0.0066) + np.deg2rad(7.3525) * np.cos(self.day_angle + np.deg2rad(85.9)) +
                np.deg2rad(9.9359) * np.cos(2.0 * self.day_angle + np.deg2rad(108.9)) +
                np.deg2rad(0.3387) * np.cos(3.0 * self.day_angle + np.deg2rad(105.2)))

    def __str__(self) -> str:
        """
        can be used to easily print the data
        :return: str of the data
        """
        t: float = float(datetime.datetime.now().time().strftime("%H.%M"))
        return (f"Uhrzeit: {str(t)[:2]}:{str(t)[3:]} Uhr\n"
                f"Die aktuelle Sonnenposition ist: {round(self.calc_azimuth(t), 2)}°\n"
                f"und die aktuelle Sonnenhöhe beträgt {round(self.calc_solar_elevation(t), 2)}°")

    @lru_cache(maxsize=None)
    def calc_azimuth(self, t: float) -> float:
        """
        calcs the azimuth to the given time
        :param t:  as float
        :return: The azimuth in degrees
        """
        sun_height: float = np.deg2rad(self.calc_solar_elevation(t))
        if self.real_local_time > 12:
            sun_azimuth: float = np.deg2rad(180) + np.arccos(
                (np.sin(sun_height) * np.sin(self.latitude) - np.sin(self.sun_declination)) /
                (np.cos(sun_height) * np.cos(self.latitude)))
        else:
            sun_azimuth: float = np.deg2rad(180) - np.arccos(
                (np.sin(sun_height) * np.sin(self.latitude) - np.sin(self.sun_declination)) /
                (np.cos(sun_height) * np.cos(self.latitude)))
        return np.rad2deg(sun_azimuth)

    @lru_cache(maxsize=None)
    def calc_solar_elevation(self, t: float) -> float:
        """
        calcs solar elevation to the given time
        :param t:  as a float
        :return: The solar elevation in degrees
        """
        self.time_last_calc: float = round((int(t)) + ((t - int(t)) * 100 / 60), 2) - 0.25
        self.mid_local_time: float = self.time_last_calc + self.longitude * np.deg2rad(4)
        self.real_local_time: float = self.mid_local_time + self.time_equation
        self.hour_angle: float = (12.00 - self.real_local_time) * np.deg2rad(15)
        sun_height: float = np.arcsin(np.cos(self.hour_angle) * np.cos(self.latitude) * np.cos(self.sun_declination)
                                      + np.sin(self.latitude) * np.sin(self.sun_declination))
        return np.rad2deg(sun_height)


class PVProfit:
    """
    calculates the profit for the pv system
    """

    def __init__(self, module_efficiency: float, module_area: int, tilt_angle: float, exposure_angle: float,
                 temperature_coefficient: float, nominal_temperature: float, mounting_type_index: int) -> None:
        """
        initialize the class
        :param module_efficiency: the module efficiency in percent
        :param module_area: the module area in m^2
        :param tilt_angle: the tilt angle in degrees
        :param exposure_angle: the exposure angle in degrees
        :param temperature_coefficient: the temperature coefficient in %/°C
        :param nominal_temperature: the nominal temperature in °C
        """
        self.module_efficiency: float = module_efficiency / 100
        self.module_area: int = module_area
        self.tilt_angle: float = tilt_angle
        self.exposure_angle: float = exposure_angle
        self.temperature_coefficient: float = temperature_coefficient / 100
        self.nominal_temperature: float = nominal_temperature
        self.mounting_type_dict: dict = {0: 22,  # Völlig freie Aufständerung
                                         1: 28,  # Auf dem Dach, großer Abstand
                                         2: 29,  # Auf dem Dach bzw. dach integriert, gute Hinterlüftung
                                         3: 32,  # Auf dem Dach bzw. dach integriert, schlechte Hinterlüftung
                                         4: 35,  # An der Fassade bzw. fassaden integriert, gute Hinterlüftung
                                         5: 39,  # An der Fassade bzw. fassaden integriert, schlechte Hinterlüftung
                                         6: 43,  # Dachintegration, ohne Hinterlüftung
                                         7: 55  # Fassaden integriert, ohne Hinterlüftung
                                         }
        self.mounting_type: int = self.mounting_type_dict[mounting_type_index]

    def __str__(self) -> str:
        """
        can be used to easily print the data
        :return: str of the data
        """
        val = (f"Die Modul Effizienz ist: {self.module_efficiency * 100}%\n"
               f"Die Modulfläche ist: {self.module_area}m^2\n"
               f"Der Neigungswinkel ist: {self.tilt_angle}°\n"
               f"Der Ausrichtungswinkel ist: {self.exposure_angle}°")
        return val

    @lru_cache(maxsize=None)
    def calc_incidence_angle(self, sun_height: float, sun_azimuth: float) -> float:
        """

        :param sun_height:
        :param sun_azimuth:
        :return:
        """
        if sun_height > 0:
            return np.rad2deg(np.arccos(-np.cos(np.deg2rad(sun_height)) * np.sin(np.deg2rad(self.tilt_angle)) *
                                        np.cos(np.deg2rad(sun_azimuth) - np.deg2rad(self.exposure_angle)) +
                                        np.sin(np.deg2rad(sun_height)) * np.cos(np.deg2rad(self.tilt_angle))))
        return -1

    @lru_cache(maxsize=None)
    def calc_pv_temp(self, temperature: float, radiation: float) -> float:
        """
        calcs the temperature of the pv system
        :param temperature: the surrounding temperature in °C
        :param radiation: the current radiation in W/m^2
        :return: the temperatur of the pv panel in °C
        """
        try:
            return temperature + self.mounting_type * radiation / 1000
        except (ValueError, TypeError):
            if temperature is None:
                print("No temperature")
            if radiation is None:
                print("No radiation")
            return 0

    @lru_cache(maxsize=None)
    def calc_temp_dependency(self, temperature: float, radiation: float) -> float:
        """
        calcs the current efficiency of the pv panel
        :param temperature: the current surrounding temperatur in °C
        :param radiation: the current radiation in W/m^2
        :return: the current efficiency as float
        """
        current_efficiency = self.module_efficiency + (self.calc_pv_temp(temperature, radiation)
                                                       - self.nominal_temperature) * self.temperature_coefficient
        return current_efficiency

    @lru_cache(maxsize=None)
    def calc_power(self, power_direct_horizontal: float, incidence_angle: float, sun_height: float,
                   current_efficiency) -> float:
        """
        calcs the energy output of the pv panel
        :param power_direct_horizontal: the direct radiation of the weather data
        :param incidence_angle: the incidence angle of the sun
        :param sun_height: the height of the sun
        :param current_efficiency: the current efficiency of the panel
        :return: the current energy of the panel
        """
        if incidence_angle == -1:
            return 0
        try:
            power_direct_gen = (power_direct_horizontal * np.cos(np.deg2rad(incidence_angle)) /
                                np.sin(np.deg2rad(90 - sun_height)))
            return abs(power_direct_gen * current_efficiency * self.module_area)
        except (ValueError, TypeError):
            if power_direct_horizontal is None:
                print("No radiation")
            return 0


class ShellyControl:
    def __init__(self, ip_address: str):
        self.ip_address: str = ip_address


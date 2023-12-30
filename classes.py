# -*- coding: utf-8 -*-

import datetime
from functools import lru_cache

import numpy as np
import requests
import requests_cache

import debug


class MarketData:
    """
    Gets the market data to the given time interval
    """

    def __init__(self, consumer_costs, start_time: None | str = None, end_time: None | str = None) -> None:
        """
        Initialize the market data class
        :param consumer_costs: The cost of the grid
        :return: None.
        """
        time_start: str = "00:00:00,00"
        self.session = requests_cache.CachedSession(r'cache/marketdata.cache', expire_after=datetime.timedelta(hours=1))

        if start_time is None and end_time is None:
            date_today: str = datetime.datetime.today().strftime("%Y-%m-%d")
            time_start_ms: int = self.convert_time_to_ms(date_today, time_start)
            self.data: dict = self.get_data(start=time_start_ms)
        else:
            time_start: str = datetime.datetime.strptime(start_time, "%Y-%m-%dT%H:%M")
            time_end: str = datetime.datetime.strptime(end_time, "%Y-%m-%dT%H:%M")

            date_start = time_start.strftime('%Y-%m-%d')
            date_end = time_end.strftime('%Y-%m-%d')

            time_start = time_start.strftime('%H:%M:%S,%f')
            time_end = time_end.strftime('%H:%M:%S,%f')

            time_start_ms: int = self.convert_time_to_ms(date_start, time_start)
            end_time_ms: int = self.convert_time_to_ms(date_end, time_end)

            self.data: dict = self.get_data(start=time_start_ms, end=end_time_ms)

        self.convert_dict(consumer_costs)

    def __str__(self) -> str:
        """
        Can be used to print the data
        :return: The market as string.
        """
        return str(self.data)

    @staticmethod
    def convert_ms_to_time(ms: int) -> str:
        """
        Convert the given ms to a time string (hour and minutes)
        :param ms: The ms to convert
        :return: the time in hour and minutes.
        """
        time = datetime.datetime.fromtimestamp(ms / 1000).time()
        date = datetime.datetime.fromtimestamp(ms / 1000).date()
        t = f"{str(time.hour).zfill(2)}:00"
        d = f"{str(date.day).zfill(2)}-{str(date.month).zfill(2)}-{str(date.year)}"
        return t, d

    @staticmethod
    def convert_time_to_ms(date: str, t: str) -> int:
        """
        Convert the given date and time to milliseconds
        :param date: As str
        :param t: time as string in a format %H:%M:%S,%f
        :return: milliseconds.
        """
        dt_obj = int(datetime.datetime.strptime(f"{date} {t}", '%Y-%m-%d %H:%M:%S,%f').timestamp() * 1000)
        return dt_obj

    def get_data(self, start: int | None = None, end: int | None = None) -> dict:
        """
        Gets the data from the awattar api for 24 hours, or the given start and end time
        https://www.awattar.de/services/api
        :param start: start time in millisecond
        :param end: end time in milliseconds
        :return: json string of the data as dict.
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
        print(url)
        return self.session.get(url).json()['data']

    def convert_dict(self, consumer_costs) -> None:
        """
        Converts the millisecond timestamp in the dict to time
        :return: None
        """
        for i, old_data in enumerate(self.data):
            self.data[i]['start_timestamp'], self.data[i]['date'] = self.convert_ms_to_time(old_data['start_timestamp'])
            self.data[i]['end_timestamp'] = self.convert_ms_to_time(old_data['end_timestamp'])[0]
            self.data[i]['marketprice'] = round(old_data['marketprice'] / 10, 3)
            self.data[i]['consumerprice'] = round(((old_data['marketprice'] + consumer_costs) * 1.19), 3)
            self.data[i]['unit'] = 'ct/kWh'


class Weather:
    """
    Gets the needed weather data from open-meteo.com
    """

    # https://open-meteo.com/en/docs#latitude=49.5139&longitude=11.2825&minutely_15=diffuse_radiation_instant&
    # hourly=temperature_2m,cloudcover

    def __init__(self, latitude: float, longitude: float, start_date: str | None = None, end_date: str | None = None) \
            -> None:
        """
        Initialize the class
        :param latitude:
        :param longitude:
        :param start_date: Format %d-%m-%Y
        :return: none
        """
        self.latitude: float = latitude
        self.longitude: float = longitude
        self._expire_time = 1
        self.session = requests_cache.CachedSession(r'cache/weatherdata.cache',
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
        Can be used to print the data
        :return: str of the data.
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
                    "direct_radiation": "",
                    "dni_radiation": ""
                }

    def get_weather(self, start_date: str | None, end_date: str | None) -> dict:
        """
        Gets the weather for the given latitude and longitude
        :return: A dict with the following variables: direct radiation, temperatur, cloudcover, temperature max,
                 temperatur min, sunrise, sunset.
        """
        if start_date is None or end_date is None:
            url: str = (f"https://api.open-meteo.com/v1/forecast?latitude={self.latitude}&longitude={self.longitude}&"
                        "minutely_15=direct_normal_irradiance,direct_radiation&hourly=temperature_2m,cloudcover&"
                        "models=best_match&daily=temperature_2m_max,temperature_2m_min,sunrise,sunset&"
                        "timezone=Europe%2FBerlin&forecast_days=3")
        else:
            start: datetime = datetime.datetime.strptime(start_date, "%d-%m-%Y")
            end: datetime = datetime.datetime.strptime(end_date, "%d-%m-%Y")
            url: str = (f"https://api.open-meteo.com/v1/forecast?latitude={self.latitude}&longitude={self.longitude}&"
                        f"minutely_15=direct_normal_irradiance,direct_radiation&hourly=temperature_2m,cloudcover&"
                        f"models=best_match&daily=temperature_2m_max,temperature_2m_min,sunrise,sunset&"
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
            self.data[date][t[11:]]["direct_radiation"] = unsorted_data["minutely_15"]["direct_radiation"][i]
            self.data[date][t[11:]]["dni_radiation"] = unsorted_data["minutely_15"]["direct_normal_irradiance"][i]
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
    Calcs the position of the sun
    """

    def __init__(self, latitude, longitude, date: str | None = None) -> None:
        """
        Initialize the class
        :param latitude:
        :param longitude:
        :param date: Format %d-%m-%Y
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
        Can be used to print the data
        :return: str of the data.
        """
        t: float = float(datetime.datetime.now().time().strftime("%H.%M"))
        return (f"Uhrzeit: {str(t)[:2]}:{str(t)[3:]} Uhr\n"
                f"Die aktuelle Sonnenposition ist: {round(self.calc_azimuth(t), 2)}°\n"
                f"und die aktuelle Sonnenhöhe beträgt {round(self.calc_solar_elevation(t), 2)}°")

    @lru_cache(maxsize=None)
    def calc_azimuth(self, t: float) -> float:
        """
        Calcs the azimuth to the given time
        :param t:  as float
        :return: The azimuth in degrees.
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
        Calcs solar elevation to the given time
        :param t:  as a float
        :return: The solar elevation in degrees.
        """
        self.time_last_calc: float = round((int(t)) + ((t - int(t)) * 100 / 60), 2) - 0.25
        self.mid_local_time: float = self.time_last_calc + self.longitude * np.deg2rad(4)
        self.real_local_time: float = self.mid_local_time + self.time_equation
        self.hour_angle: float = (12.00 - self.real_local_time) * np.deg2rad(15)
        sun_height: float = np.arcsin(np.cos(self.hour_angle) * np.cos(self.latitude) * np.cos(self.sun_declination)
                                      + np.sin(self.latitude) * np.sin(self.sun_declination))
        return np.rad2deg(sun_height)

    @lru_cache(maxsize=None)
    def adjust_for_new_angle(self, original_gb, original_tilt_angle, original_azimuth_angle, new_tilt_angle,
                             new_azimuth_angle, time):
        @lru_cache(maxsize=None)
        def calc_incidence_angle(elevation_sun, azimuth_sun, tilt_angle, panel_azimuth):
            return np.rad2deg(
                np.arccos(
                    np.cos(np.deg2rad(elevation_sun)) * np.sin(np.deg2rad(tilt_angle)) *
                    np.cos(np.deg2rad(azimuth_sun - panel_azimuth)) + np.sin(np.deg2rad(elevation_sun)) *
                    np.cos(np.deg2rad(tilt_angle))
                )
            )

        sun_azimuth = self.calc_azimuth(time)
        sun_elevation = self.calc_solar_elevation(time)
        incidence_angle_original = calc_incidence_angle(sun_elevation, sun_azimuth, original_tilt_angle,
                                                        original_azimuth_angle)
        gb_horizontal = original_gb / np.cos(np.deg2rad(incidence_angle_original))
        incidence_angle_new = calc_incidence_angle(sun_elevation, sun_azimuth, new_tilt_angle, new_azimuth_angle)
        adjusted_gb = gb_horizontal * np.cos(np.deg2rad(incidence_angle_new))

        return adjusted_gb


class PVProfit:
    """
    Calculates the profit for the pv system
    """

    def __init__(self, module_efficiency: float, module_area: int, tilt_angle: float, exposure_angle: float,
                 temperature_coefficient: float, nominal_temperature: float, mounting_type_index: int) -> None:
        """
        Initialize the class
        :param module_efficiency: the module efficiency in percent
        :param module_area: the module area in m^2
        :param tilt_angle: the tilt angle in degrees
        :param exposure_angle: the exposure angle in degrees
        :param temperature_coefficient: the temperature coefficient in %/°C
        :param nominal_temperature: the nominal temperature in °C.
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
        Can be used to print the data
        :return: str of the data.
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
        Calcs the temperature of the pv system
        :param temperature: the surrounding temperature in °C
        :param radiation: the current radiation in W/m^2
        :return: the temperatur of the pv panel in °C.
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
        Calcs the current efficiency of the pv panel
        :param temperature: the current surrounding temperatur in °C
        :param radiation: the current radiation in W/m^2
        :return: the current efficiency as float.
        """
        current_efficiency = self.module_efficiency + (self.calc_pv_temp(temperature, radiation)
                                                       - self.nominal_temperature) * self.temperature_coefficient
        return current_efficiency

    @lru_cache(maxsize=None)
    def calc_power(self, power_direct_horizontal: float, incidence_angle: float, sun_height: float,
                   current_efficiency: float) -> float:
        """
        Calcs the energy output of the pv panel,
        :param power_direct_horizontal: the direct radiation of the weather data,
        :param incidence_angle: the incidence angle of the sun,
        :param sun_height: the height of the sun,
        :param current_efficiency: the current efficiency of the panel,
        :return: the current energy of the panel.
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

    @lru_cache(maxsize=None)
    def calc_power_with_dni(self, dni: float, incidence_angle: float, temperature: float) -> float:
        """
        Calculates the energy output of the PV panel using Direct Normal Irradiance (DNI)
        :param temperature:
        :param incidence_angle: The incidence angle of the sun
        :param dni: Direct Normal Irradiance in W/m^2
        :return: Current energy output of the panel in Watts.
        """
        if incidence_angle == -1:
            return 0

        try:
            adjusted_dni = dni * np.cos(np.deg2rad(incidence_angle))

            pv_temperature = self.calc_pv_temp(temperature, adjusted_dni)
            current_efficiency = self.calc_temp_dependency(pv_temperature, adjusted_dni)

            return adjusted_dni * current_efficiency * self.module_area
        except (ValueError, TypeError):
            if dni is None:
                print("No radiation")
            return 0


class RequiredHeatingPower:
    # https://www.bosch-homecomfort.com/de/de/wohngebaeude/wissen/heizungsratgeber/heizleistung-berechnen/
    def __init__(self):
        u_value: dict = {
            "Fenster": {
                "Holzrahmen": {
                    "Einfachverglasung": {
                        1918: 5, 1919: 5, 1920: 5, 1921: 5, 1922: 5, 1923: 5, 1924: 5, 1925: 5, 1926: 5, 1927: 5,
                        1928: 5, 1929: 5, 1930: 5, 1931: 5, 1932: 5, 1933: 5, 1934: 5, 1935: 5, 1936: 5, 1937: 5,
                        1938: 5, 1939: 5, 1940: 5, 1941: 5, 1942: 5, 1943: 5, 1944: 5, 1945: 5, 1946: 5, 1947: 5,
                        1948: 5, 1949: 5, 1950: 5, 1951: 5, 1952: 5, 1953: 5, 1954: 5, 1955: 5, 1956: 5, 1957: 5,
                        1958: 5, 1959: 5, 1960: 5, 1961: 5, 1962: 5, 1963: 5, 1964: 5, 1965: 5, 1966: 5, 1967: 5,
                        1968: 5, 1969: 5, 1970: 5, 1971: 5, 1972: 5, 1973: 5, 1974: 5, 1975: 5, 1976: 5, 1977: 5,
                        1978: 5, 1979: 5, 1980: 5, 1981: 5, 1982: 5, 1983: 5
                    },
                    "Doppelverglasung": {
                        1918: 2.7, 1919: 2.7, 1920: 2.7, 1921: 2.7, 1922: 2.7, 1923: 2.7, 1924: 2.7, 1925: 2.7,
                        1926: 2.7, 1927: 2.7, 1928: 2.7, 1929: 2.7, 1930: 2.7, 1931: 2.7, 1932: 2.7, 1933: 2.7,
                        1934: 2.7, 1935: 2.7, 1936: 2.7, 1937: 2.7, 1938: 2.7, 1939: 2.7, 1940: 2.7, 1941: 2.7,
                        1942: 2.7, 1943: 2.7, 1944: 2.7, 1945: 2.7, 1946: 2.7, 1947: 2.7, 1948: 2.7, 1949: 2.7,
                        1950: 2.7, 1951: 2.7, 1952: 2.7, 1953: 2.7, 1954: 2.7, 1955: 2.7, 1956: 2.7, 1957: 2.7,
                        1958: 2.7, 1959: 2.7, 1960: 2.7, 1961: 2.7, 1962: 2.7, 1963: 2.7, 1964: 2.7, 1965: 2.7,
                        1966: 2.7, 1967: 2.7, 1968: 2.7, 1969: 2.7, 1970: 2.7, 1971: 2.7, 1972: 2.7, 1973: 2.7,
                        1974: 2.7, 1975: 2.7, 1976: 2.7, 1977: 2.7, 1978: 2.7, 1979: 2.7, 1980: 2.7, 1981: 2.7,
                        1982: 2.7, 1983: 2.7, 1984: 2.7, 1985: 2.7, 1986: 2.7, 1987: 2.7, 1988: 2.7, 1989: 2.7,
                        1990: 2.7, 1991: 2.7, 1992: 2.7, 1993: 2.7, 1994: 2.7
                    },
                    "Isolierverglasung": {
                        1995: 1.8
                    }

                },
                "Kunststoffrahmen": {
                    "Isolierverglasung": {
                        1958: 3.0, 1959: 3.0, 1960: 3.0, 1961: 3.0, 1962: 3.0, 1963: 3.0, 1964: 3.0, 1965: 3.0,
                        1966: 3.0, 1967: 3.0, 1968: 3.0, 1969: 3.0, 1970: 3.0, 1971: 3.0, 1972: 3.0, 1973: 3.0,
                        1974: 3.0, 1975: 3.0, 1976: 3.0, 1977: 3.0, 1978: 3.0, 1979: 3.0, 1980: 3.0, 1981: 3.0,
                        1982: 3.0, 1983: 3.0, 1984: 3.0, 1985: 3.0, 1986: 3.0, 1987: 3.0, 1988: 3.0, 1989: 3.0,
                        1990: 3.0, 1991: 3.0, 1992: 3.0, 1993: 3.0, 1994: 3.0, 1995: 1.8
                    }
                },
                "Metallrahmen": {
                    "Isolierverglasung": {
                        1958: 4.3, 1959: 4.3, 1960: 4.3, 1961: 4.3, 1962: 4.3, 1963: 4.3, 1964: 4.3, 1965: 4.3,
                        1966: 4.3, 1967: 4.3, 1968: 4.3, 1969: 4.3, 1970: 4.3, 1971: 4.3, 1972: 4.3, 1973: 4.3,
                        1974: 4.3, 1975: 4.3, 1976: 4.3, 1977: 4.3, 1978: 4.3, 1979: 4.3, 1980: 4.3, 1981: 4.3,
                        1982: 4.3, 1983: 4.3, 1984: 4.3, 1985: 4.3, 1986: 4.3, 1987: 4.3, 1988: 4.3, 1989: 4.3,
                        1990: 4.3, 1991: 4.3, 1992: 4.3, 1993: 4.3, 1994: 4.3, 1995: 1.8
                    }
                }
            },
            "Rollladen": {
                "ungedämmt": {
                    1918: 3.0, 1919: 3.0, 1920: 3.0, 1921: 3.0, 1922: 3.0, 1923: 3.0, 1924: 3.0, 1925: 3.0, 1926: 3.0,
                    1927: 3.0, 1928: 3.0, 1929: 3.0, 1930: 3.0, 1931: 3.0, 1932: 3.0, 1933: 3.0, 1934: 3.0, 1935: 3.0,
                    1936: 3.0, 1937: 3.0, 1938: 3.0, 1939: 3.0, 1940: 3.0, 1941: 3.0, 1942: 3.0, 1943: 3.0, 1944: 3.0,
                    1945: 3.0, 1946: 3.0, 1947: 3.0, 1948: 3.0, 1949: 3.0, 1950: 3.0, 1951: 3.0, 1952: 3.0, 1953: 3.0,
                    1954: 3.0, 1955: 3.0, 1956: 3.0, 1957: 3.0, 1958: 3.0, 1959: 3.0, 1960: 3.0, 1961: 3.0, 1962: 3.0,
                    1963: 3.0, 1964: 3.0, 1965: 3.0, 1966: 3.0, 1967: 3.0, 1968: 3.0, 1969: 3.0, 1970: 3.0, 1971: 3.0,
                    1972: 3.0, 1973: 3.0, 1974: 3.0, 1975: 3.0, 1976: 3.0, 1977: 3.0, 1978: 3.0, 1979: 3.0, 1980: 3.0,
                    1981: 3.0, 1982: 3.0, 1983: 3.0, 1984: 3.0, 1985: 3.0, 1986: 3.0, 1987: 3.0, 1988: 3.0, 1989: 3.0,
                    1990: 3.0, 1991: 3.0, 1992: 3.0, 1993: 3.0, 1994: 3.0, 1995: 3.0
                },
                "gedämmt": {
                    1918: 1.8, 1919: 1.8, 1920: 1.8, 1921: 1.8, 1922: 1.8, 1923: 1.8, 1924: 1.8, 1925: 1.8, 1926: 1.8,
                    1927: 1.8, 1928: 1.8, 1929: 1.8, 1930: 1.8, 1931: 1.8, 1932: 1.8, 1933: 1.8, 1934: 1.8, 1935: 1.8,
                    1936: 1.8, 1937: 1.8, 1938: 1.8, 1939: 1.8, 1940: 1.8, 1941: 1.8, 1942: 1.8, 1943: 1.8, 1944: 1.8,
                    1945: 1.8, 1946: 1.8, 1947: 1.8, 1948: 1.8, 1949: 1.8, 1950: 1.8, 1951: 1.8, 1952: 1.8, 1953: 1.8,
                    1954: 1.8, 1955: 1.8, 1956: 1.8, 1957: 1.8, 1958: 1.8, 1959: 1.8, 1960: 1.8, 1961: 1.8, 1962: 1.8,
                    1963: 1.8, 1964: 1.8, 1965: 1.8, 1966: 1.8, 1967: 1.8, 1968: 1.8, 1969: 1.8, 1970: 1.8, 1971: 1.8,
                    1972: 1.8, 1973: 1.8, 1974: 1.8, 1975: 1.8, 1976: 1.8, 1977: 1.8, 1978: 1.8, 1979: 1.8, 1980: 1.8,
                    1981: 1.8, 1982: 1.8, 1983: 1.8, 1984: 1.8, 1985: 1.8, 1986: 1.8, 1987: 1.8, 1988: 1.8, 1989: 1.8,
                    1990: 1.8, 1991: 1.8, 1992: 1.8, 1993: 1.8, 1994: 1.8, 1995: 1.8
                }
            },
            "Türen": {
                "alle": {
                    1918: 3.5, 1919: 3.5, 1920: 3.5, 1921: 3.5, 1922: 3.5, 1923: 3.5, 1924: 3.5, 1925: 3.5, 1926: 3.5,
                    1927: 3.5, 1928: 3.5, 1929: 3.5, 1930: 3.5, 1931: 3.5, 1932: 3.5, 1933: 3.5, 1934: 3.5, 1935: 3.5,
                    1936: 3.5, 1937: 3.5, 1938: 3.5, 1939: 3.5, 1940: 3.5, 1941: 3.5, 1942: 3.5, 1943: 3.5, 1944: 3.5,
                    1945: 3.5, 1946: 3.5, 1947: 3.5, 1948: 3.5, 1949: 3.5, 1950: 3.5, 1951: 3.5, 1952: 3.5, 1953: 3.5,
                    1954: 3.5, 1955: 3.5, 1956: 3.5, 1957: 3.5, 1958: 3.5, 1959: 3.5, 1960: 3.5, 1961: 3.5, 1962: 3.5,
                    1963: 3.5, 1964: 3.5, 1965: 3.5, 1966: 3.5, 1967: 3.5, 1968: 3.5, 1969: 3.5, 1970: 3.5, 1971: 3.5,
                    1972: 3.5, 1973: 3.5, 1974: 3.5, 1975: 3.5, 1976: 3.5, 1977: 3.5, 1978: 3.5, 1979: 3.5, 1980: 3.5,
                    1981: 3.5, 1982: 3.5, 1983: 3.5, 1984: 3.5, 1985: 3.5, 1986: 3.5, 1987: 3.5, 1988: 3.5, 1989: 3.5,
                    1990: 3.5, 1991: 3.5, 1992: 3.5, 1993: 3.5, 1994: 3.5, 1995: 3.5
                }
            },
            "Außenwände": {
                "Massivbauweise": {
                    1918: 1.7, 1919: 1.7, 1920: 1.7, 1921: 1.7, 1922: 1.7, 1923: 1.7, 1924: 1.7, 1925: 1.7, 1926: 1.7,
                    1927: 1.7, 1928: 1.7, 1929: 1.7, 1930: 1.7, 1931: 1.7, 1932: 1.7, 1933: 1.7, 1934: 1.7, 1935: 1.7,
                    1936: 1.7, 1937: 1.7, 1938: 1.7, 1939: 1.7, 1940: 1.7, 1941: 1.7, 1942: 1.7, 1943: 1.7, 1944: 1.7,
                    1945: 1.7, 1946: 1.7, 1947: 1.7, 1948: 1.7, 1949: 1.4, 1950: 1.4, 1951: 1.4, 1952: 1.4, 1953: 1.4,
                    1954: 1.4, 1955: 1.4, 1956: 1.4, 1957: 1.4, 1958: 1.4, 1959: 1.4, 1960: 1.4, 1961: 1.4, 1962: 1.4,
                    1963: 1.4, 1964: 1.4, 1965: 1.4, 1966: 1.4, 1967: 1.4, 1968: 1.4, 1969: 1.0, 1970: 1.0, 1971: 1.0,
                    1972: 1.0, 1973: 1.0, 1974: 1.0, 1975: 1.0, 1976: 1.0, 1977: 1.0, 1978: 1.0, 1979: 0.8, 1980: 0.8,
                    1981: 0.8, 1982: 0.8, 1983: 0.8, 1984: 0.6, 1985: 0.6, 1986: 0.6, 1987: 0.6, 1988: 0.6, 1989: 0.6,
                    1990: 0.6, 1991: 0.6, 1992: 0.6, 1993: 0.6, 1994: 0.6, 1995: 0.5
                },
                "Holzkonstruktion": {
                    1918: 2.0, 1919: 2.0, 1920: 2.0, 1921: 2.0, 1922: 2.0, 1923: 2.0, 1924: 2.0, 1925: 2.0, 1926: 2.0,
                    1927: 2.0, 1928: 2.0, 1929: 2.0, 1930: 2.0, 1931: 2.0, 1932: 2.0, 1933: 2.0, 1934: 2.0, 1935: 2.0,
                    1936: 2.0, 1937: 2.0, 1938: 2.0, 1939: 2.0, 1940: 2.0, 1941: 2.0, 1942: 2.0, 1943: 2.0, 1944: 2.0,
                    1945: 2.0, 1946: 2.0, 1947: 2.0, 1948: 2.0, 1949: 1.4, 1950: 1.4, 1951: 1.4, 1952: 1.4, 1953: 1.4,
                    1954: 1.4, 1955: 1.4, 1956: 1.4, 1957: 1.4, 1958: 1.4, 1959: 1.4, 1960: 1.4, 1961: 1.4, 1962: 1.4,
                    1963: 1.4, 1964: 1.4, 1965: 1.4, 1966: 1.4, 1967: 1.4, 1968: 1.4, 1969: 0.6, 1970: 0.6, 1971: 0.6,
                    1972: 0.6, 1973: 0.6, 1974: 0.6, 1975: 0.6, 1976: 0.6, 1977: 0.6, 1978: 0.6, 1979: 0.5, 1980: 0.5,
                    1981: 0.5, 1982: 0.5, 1983: 0.5, 1984: 0.4, 1985: 0.4, 1986: 0.4, 1987: 0.4, 1988: 0.4, 1989: 0.4,
                    1990: 0.4, 1991: 0.4, 1992: 0.4, 1993: 0.4, 1994: 0.4, 1995: 0.4
                }
            },
            "Wände gegen Erdreich": {
                "Massivbauweise": {
                    1918: 1.7, 1919: 1.7, 1920: 1.7, 1921: 1.7, 1922: 1.7, 1923: 1.7, 1924: 1.7, 1925: 1.7, 1926: 1.7,
                    1927: 1.7, 1928: 1.7, 1929: 1.7, 1930: 1.7, 1931: 1.7, 1932: 1.7, 1933: 1.7, 1934: 1.7, 1935: 1.7,
                    1936: 1.7, 1937: 1.7, 1938: 1.7, 1939: 1.7, 1940: 1.7, 1941: 1.7, 1942: 1.7, 1943: 1.7, 1944: 1.7,
                    1945: 1.7, 1946: 1.7, 1947: 1.7, 1948: 1.7, 1949: 1.4, 1950: 1.4, 1951: 1.4, 1952: 1.4, 1953: 1.4,
                    1954: 1.4, 1955: 1.4, 1956: 1.4, 1957: 1.4, 1958: 1.4, 1959: 1.4, 1960: 1.4, 1961: 1.4, 1962: 1.4,
                    1963: 1.4, 1964: 1.4, 1965: 1.4, 1966: 1.4, 1967: 1.4, 1968: 1.4, 1969: 1.0, 1970: 1.0, 1971: 1.0,
                    1972: 1.0, 1973: 1.0, 1974: 1.0, 1975: 1.0, 1976: 1.0, 1977: 1.0, 1978: 1.0, 1979: 0.8, 1980: 0.8,
                    1981: 0.8, 1982: 0.8, 1983: 0.8, 1984: 0.6, 1985: 0.6, 1986: 0.6, 1987: 0.6, 1988: 0.6, 1989: 0.6,
                    1990: 0.6, 1991: 0.6, 1992: 0.6, 1993: 0.6, 1994: 0.6, 1995: 0.5
                },
                "Holzkonstruktion": {
                    1918: 2.0, 1919: 2.0, 1920: 2.0, 1921: 2.0, 1922: 2.0, 1923: 2.0, 1924: 2.0, 1925: 2.0, 1926: 2.0,
                    1927: 2.0, 1928: 2.0, 1929: 2.0, 1930: 2.0, 1931: 2.0, 1932: 2.0, 1933: 2.0, 1934: 2.0, 1935: 2.0,
                    1936: 2.0, 1937: 2.0, 1938: 2.0, 1939: 2.0, 1940: 2.0, 1941: 2.0, 1942: 2.0, 1943: 2.0, 1944: 2.0,
                    1945: 2.0, 1946: 2.0, 1947: 2.0, 1948: 2.0, 1949: 1.4, 1950: 1.4, 1951: 1.4, 1952: 1.4, 1953: 1.4,
                    1954: 1.4, 1955: 1.4, 1956: 1.4, 1957: 1.4, 1958: 1.4, 1959: 1.4, 1960: 1.4, 1961: 1.4, 1962: 1.4,
                    1963: 1.4, 1964: 1.4, 1965: 1.4, 1966: 1.4, 1967: 1.4, 1968: 1.4, 1969: 0.6, 1970: 0.6, 1971: 0.6,
                    1972: 0.6, 1973: 0.6, 1974: 0.6, 1975: 0.6, 1976: 0.6, 1977: 0.6, 1978: 0.6, 1979: 0.5, 1980: 0.5,
                    1981: 0.5, 1982: 0.5, 1983: 0.5, 1984: 0.4, 1985: 0.4, 1986: 0.4, 1987: 0.4, 1988: 0.4, 1989: 0.4,
                    1990: 0.4, 1991: 0.4, 1992: 0.4, 1993: 0.4, 1994: 0.4, 1995: 0.4
                }
            },
            "Innenwände gegen unbeheizte Kellergeschosse": {
                "Massivbauweise": {
                    1918: 1.7, 1919: 1.7, 1920: 1.7, 1921: 1.7, 1922: 1.7, 1923: 1.7, 1924: 1.7, 1925: 1.7, 1926: 1.7,
                    1927: 1.7, 1928: 1.7, 1929: 1.7, 1930: 1.7, 1931: 1.7, 1932: 1.7, 1933: 1.7, 1934: 1.7, 1935: 1.7,
                    1936: 1.7, 1937: 1.7, 1938: 1.7, 1939: 1.7, 1940: 1.7, 1941: 1.7, 1942: 1.7, 1943: 1.7, 1944: 1.7,
                    1945: 1.7, 1946: 1.7, 1947: 1.7, 1948: 1.7, 1949: 1.4, 1950: 1.4, 1951: 1.4, 1952: 1.4, 1953: 1.4,
                    1954: 1.4, 1955: 1.4, 1956: 1.4, 1957: 1.4, 1958: 1.4, 1959: 1.4, 1960: 1.4, 1961: 1.4, 1962: 1.4,
                    1963: 1.4, 1964: 1.4, 1965: 1.4, 1966: 1.4, 1967: 1.4, 1968: 1.4, 1969: 1.0, 1970: 1.0, 1971: 1.0,
                    1972: 1.0, 1973: 1.0, 1974: 1.0, 1975: 1.0, 1976: 1.0, 1977: 1.0, 1978: 1.0, 1979: 0.8, 1980: 0.8,
                    1981: 0.8, 1982: 0.8, 1983: 0.8, 1984: 0.6, 1985: 0.6, 1986: 0.6, 1987: 0.6, 1988: 0.6, 1989: 0.6,
                    1990: 0.6, 1991: 0.6, 1992: 0.6, 1993: 0.6, 1994: 0.6, 1995: 0.5
                },
                "Holzkonstruktion": {
                    1918: 2.0, 1919: 2.0, 1920: 2.0, 1921: 2.0, 1922: 2.0, 1923: 2.0, 1924: 2.0, 1925: 2.0, 1926: 2.0,
                    1927: 2.0, 1928: 2.0, 1929: 2.0, 1930: 2.0, 1931: 2.0, 1932: 2.0, 1933: 2.0, 1934: 2.0, 1935: 2.0,
                    1936: 2.0, 1937: 2.0, 1938: 2.0, 1939: 2.0, 1940: 2.0, 1941: 2.0, 1942: 2.0, 1943: 2.0, 1944: 2.0,
                    1945: 2.0, 1946: 2.0, 1947: 2.0, 1948: 2.0, 1949: 1.4, 1950: 1.4, 1951: 1.4, 1952: 1.4, 1953: 1.4,
                    1954: 1.4, 1955: 1.4, 1956: 1.4, 1957: 1.4, 1958: 1.4, 1959: 1.4, 1960: 1.4, 1961: 1.4, 1962: 1.4,
                    1963: 1.4, 1964: 1.4, 1965: 1.4, 1966: 1.4, 1967: 1.4, 1968: 1.4, 1969: 0.6, 1970: 0.6, 1971: 0.6,
                    1972: 0.6, 1973: 0.6, 1974: 0.6, 1975: 0.6, 1976: 0.6, 1977: 0.6, 1978: 0.6, 1979: 0.5, 1980: 0.5,
                    1981: 0.5, 1982: 0.5, 1983: 0.5, 1984: 0.4, 1985: 0.4, 1986: 0.4, 1987: 0.4, 1988: 0.4, 1989: 0.4,
                    1990: 0.4, 1991: 0.4, 1992: 0.4, 1993: 0.4, 1994: 0.4, 1995: 0.4
                }
            },
            "Decken gegen das Erdreich": {
                "Massivbauweise": {
                    1918: 1.2, 1919: 1.2, 1920: 1.2, 1921: 1.2, 1922: 1.2, 1923: 1.2, 1924: 1.2, 1925: 1.2, 1926: 1.2,
                    1927: 1.2, 1928: 1.2, 1929: 1.2, 1930: 1.2, 1931: 1.2, 1932: 1.2, 1933: 1.2, 1934: 1.2, 1935: 1.2,
                    1936: 1.2, 1937: 1.2, 1938: 1.2, 1939: 1.2, 1940: 1.2, 1941: 1.2, 1942: 1.2, 1943: 1.2, 1944: 1.2,
                    1945: 1.2, 1946: 1.2, 1947: 1.2, 1948: 1.2, 1949: 1.5, 1950: 1.5, 1951: 1.5, 1952: 1.5, 1953: 1.5,
                    1954: 1.5, 1955: 1.5, 1956: 1.5, 1957: 1.5, 1958: 1.0, 1959: 1.0, 1960: 1.0, 1961: 1.0, 1962: 1.0,
                    1963: 1.0, 1964: 1.0, 1965: 1.0, 1966: 1.0, 1967: 1.0, 1968: 1.0, 1969: 1.0, 1970: 1.0, 1971: 1.0,
                    1972: 1.0, 1973: 1.0, 1974: 1.0, 1975: 1.0, 1976: 1.0, 1977: 1.0, 1978: 1.0, 1979: 0.8, 1980: 0.8,
                    1981: 0.8, 1982: 0.8, 1983: 0.8, 1984: 0.6, 1985: 0.6, 1986: 0.6, 1987: 0.6, 1988: 0.6, 1989: 0.6,
                    1990: 0.6, 1991: 0.6, 1992: 0.6, 1993: 0.6, 1994: 0.6, 1995: 0.6
                },
                "Holzbalkendecke": {
                    1918: 1.0, 1919: 0.8, 1920: 0.8, 1921: 0.8, 1922: 0.8, 1923: 0.8, 1924: 0.8, 1925: 0.8, 1926: 0.8,
                    1927: 0.8, 1928: 0.8, 1929: 0.8, 1930: 0.8, 1931: 0.8, 1932: 0.8, 1933: 0.8, 1934: 0.8, 1935: 0.8,
                    1936: 0.8, 1937: 0.8, 1938: 0.8, 1939: 0.8, 1940: 0.8, 1941: 0.8, 1942: 0.8, 1943: 0.8, 1944: 0.8,
                    1945: 0.8, 1946: 0.8, 1947: 0.8, 1948: 0.8, 1949: 0.8, 1950: 0.8, 1951: 0.8, 1952: 0.8, 1953: 0.8,
                    1954: 0.8, 1955: 0.8, 1956: 0.8, 1957: 0.8, 1958: 0.8, 1959: 0.8, 1960: 0.8, 1961: 0.8, 1962: 0.8,
                    1963: 0.8, 1964: 0.8, 1965: 0.8, 1966: 0.8, 1967: 0.8, 1968: 0.8, 1969: 0.6, 1970: 0.6, 1971: 0.6,
                    1972: 0.6, 1973: 0.6, 1974: 0.6, 1975: 0.6, 1976: 0.6, 1977: 0.6, 1978: 0.6, 1979: 0.6, 1980: 0.6,
                    1981: 0.6, 1982: 0.6, 1983: 0.6, 1984: 0.4, 1985: 0.4, 1986: 0.4, 1987: 0.4, 1988: 0.4, 1989: 0.4,
                    1990: 0.4, 1991: 0.4, 1992: 0.4, 1993: 0.4, 1994: 0.4, 1995: 0.4
                }
            },
            "unbeheizte Kellergeschosse": {
                "Massivbauweise": {
                    1918: 1.2, 1919: 1.2, 1920: 1.2, 1921: 1.2, 1922: 1.2, 1923: 1.2, 1924: 1.2, 1925: 1.2, 1926: 1.2,
                    1927: 1.2, 1928: 1.2, 1929: 1.2, 1930: 1.2, 1931: 1.2, 1932: 1.2, 1933: 1.2, 1934: 1.2, 1935: 1.2,
                    1936: 1.2, 1937: 1.2, 1938: 1.2, 1939: 1.2, 1940: 1.2, 1941: 1.2, 1942: 1.2, 1943: 1.2, 1944: 1.2,
                    1945: 1.2, 1946: 1.2, 1947: 1.2, 1948: 1.2, 1949: 1.5, 1950: 1.5, 1951: 1.5, 1952: 1.5, 1953: 1.5,
                    1954: 1.5, 1955: 1.5, 1956: 1.5, 1957: 1.5, 1958: 1.0, 1959: 1.0, 1960: 1.0, 1961: 1.0, 1962: 1.0,
                    1963: 1.0, 1964: 1.0, 1965: 1.0, 1966: 1.0, 1967: 1.0, 1968: 1.0, 1969: 1.0, 1970: 1.0, 1971: 1.0,
                    1972: 1.0, 1973: 1.0, 1974: 1.0, 1975: 1.0, 1976: 1.0, 1977: 1.0, 1978: 1.0, 1979: 0.8, 1980: 0.8,
                    1981: 0.8, 1982: 0.8, 1983: 0.8, 1984: 0.6, 1985: 0.6, 1986: 0.6, 1987: 0.6, 1988: 0.6, 1989: 0.6,
                    1990: 0.6, 1991: 0.6, 1992: 0.6, 1993: 0.6, 1994: 0.6, 1995: 0.6
                },
                "Holzbalkendecke": {
                    1918: 1.0, 1919: 0.8, 1920: 0.8, 1921: 0.8, 1922: 0.8, 1923: 0.8, 1924: 0.8, 1925: 0.8, 1926: 0.8,
                    1927: 0.8, 1928: 0.8, 1929: 0.8, 1930: 0.8, 1931: 0.8, 1932: 0.8, 1933: 0.8, 1934: 0.8, 1935: 0.8,
                    1936: 0.8, 1937: 0.8, 1938: 0.8, 1939: 0.8, 1940: 0.8, 1941: 0.8, 1942: 0.8, 1943: 0.8, 1944: 0.8,
                    1945: 0.8, 1946: 0.8, 1947: 0.8, 1948: 0.8, 1949: 0.8, 1950: 0.8, 1951: 0.8, 1952: 0.8, 1953: 0.8,
                    1954: 0.8, 1955: 0.8, 1956: 0.8, 1957: 0.8, 1958: 0.8, 1959: 0.8, 1960: 0.8, 1961: 0.8, 1962: 0.8,
                    1963: 0.8, 1964: 0.8, 1965: 0.8, 1966: 0.8, 1967: 0.8, 1968: 0.8, 1969: 0.6, 1970: 0.6, 1971: 0.6,
                    1972: 0.6, 1973: 0.6, 1974: 0.6, 1975: 0.6, 1976: 0.6, 1977: 0.6, 1978: 0.6, 1979: 0.6, 1980: 0.6,
                    1981: 0.6, 1982: 0.6, 1983: 0.6, 1984: 0.4, 1985: 0.4, 1986: 0.4, 1987: 0.4, 1988: 0.4, 1989: 0.4,
                    1990: 0.4, 1991: 0.4, 1992: 0.4, 1993: 0.4, 1994: 0.4, 1995: 0.4
                }
            },
            "Dächer zwischen beheizten und unbeheizten Dachgeschoss": {
                "Massivbauweise": {
                    1918: 2.1, 1919: 2.1, 1920: 2.1, 1921: 2.1, 1922: 2.1, 1923: 2.1, 1924: 2.1, 1925: 2.1, 1926: 2.1,
                    1927: 2.1, 1928: 2.1, 1929: 2.1, 1930: 2.1, 1931: 2.1, 1932: 2.1, 1933: 2.1, 1934: 2.1, 1935: 2.1,
                    1936: 2.1, 1937: 2.1, 1938: 2.1, 1939: 2.1, 1940: 2.1, 1941: 2.1, 1942: 2.1, 1943: 2.1, 1944: 2.1,
                    1945: 2.1, 1946: 2.1, 1947: 2.1, 1948: 2.1, 1949: 2.1, 1950: 2.1, 1951: 2.1, 1952: 2.1, 1953: 2.1,
                    1954: 2.1, 1955: 2.1, 1956: 2.1, 1957: 2.1, 1958: 2.1, 1959: 2.1, 1960: 2.1, 1961: 2.1, 1962: 2.1,
                    1963: 2.1, 1964: 2.1, 1965: 2.1, 1966: 2.1, 1967: 2.1, 1968: 2.1, 1969: 0.6, 1970: 0.6, 1971: 0.6,
                    1972: 0.6, 1973: 0.6, 1974: 0.6, 1975: 0.6, 1976: 0.6, 1977: 0.6, 1978: 0.6, 1979: 0.5, 1980: 0.5,
                    1981: 0.5, 1982: 0.5, 1983: 0.5, 1984: 0.4, 1985: 0.4, 1986: 0.4, 1987: 0.4, 1988: 0.4, 1989: 0.4,
                    1990: 0.4, 1991: 0.4, 1992: 0.4, 1993: 0.4, 1994: 0.4, 1995: 0.3
                },
                "Holzkonstruktion": {
                    1918: 2.6, 1919: 1.4, 1920: 1.4, 1921: 1.4, 1922: 1.4, 1923: 1.4, 1924: 1.4, 1925: 1.4, 1926: 1.4,
                    1927: 1.4, 1928: 1.4, 1929: 1.4, 1930: 1.4, 1931: 1.4, 1932: 1.4, 1933: 1.4, 1934: 1.4, 1935: 1.4,
                    1936: 1.4, 1937: 1.4, 1938: 1.4, 1939: 1.4, 1940: 1.4, 1941: 1.4, 1942: 1.4, 1943: 1.4, 1944: 1.4,
                    1945: 1.4, 1946: 1.4, 1947: 1.4, 1948: 1.4, 1949: 1.4, 1950: 1.4, 1951: 1.4, 1952: 1.4, 1953: 1.4,
                    1954: 1.4, 1955: 1.4, 1956: 1.4, 1957: 1.4, 1958: 1.4, 1959: 1.4, 1960: 1.4, 1961: 1.4, 1962: 1.4,
                    1963: 1.4, 1964: 1.4, 1965: 1.4, 1966: 1.4, 1967: 1.4, 1968: 1.4, 1969: 0.8, 1970: 0.8, 1971: 0.8,
                    1972: 0.8, 1973: 0.8, 1974: 0.8, 1975: 0.8, 1976: 0.8, 1977: 0.8, 1978: 0.8, 1979: 0.5, 1980: 0.5,
                    1981: 0.5, 1982: 0.5, 1983: 0.5, 1984: 0.4, 1985: 0.4, 1986: 0.4, 1987: 0.4, 1988: 0.4, 1989: 0.4,
                    1990: 0.4, 1991: 0.4, 1992: 0.4, 1993: 0.4, 1994: 0.4, 1995: 0.3
                }
            },
            "Wände zwischen beheizten und unbeheizten Dachgeschoss": {
                "Massivbauweise": {
                    1918: 2.1, 1919: 2.1, 1920: 2.1, 1921: 2.1, 1922: 2.1, 1923: 2.1, 1924: 2.1, 1925: 2.1, 1926: 2.1,
                    1927: 2.1, 1928: 2.1, 1929: 2.1, 1930: 2.1, 1931: 2.1, 1932: 2.1, 1933: 2.1, 1934: 2.1, 1935: 2.1,
                    1936: 2.1, 1937: 2.1, 1938: 2.1, 1939: 2.1, 1940: 2.1, 1941: 2.1, 1942: 2.1, 1943: 2.1, 1944: 2.1,
                    1945: 2.1, 1946: 2.1, 1947: 2.1, 1948: 2.1, 1949: 2.1, 1950: 2.1, 1951: 2.1, 1952: 2.1, 1953: 2.1,
                    1954: 2.1, 1955: 2.1, 1956: 2.1, 1957: 2.1, 1958: 2.1, 1959: 2.1, 1960: 2.1, 1961: 2.1, 1962: 2.1,
                    1963: 2.1, 1964: 2.1, 1965: 2.1, 1966: 2.1, 1967: 2.1, 1968: 2.1, 1969: 0.6, 1970: 0.6, 1971: 0.6,
                    1972: 0.6, 1973: 0.6, 1974: 0.6, 1975: 0.6, 1976: 0.6, 1977: 0.6, 1978: 0.6, 1979: 0.5, 1980: 0.5,
                    1981: 0.5, 1982: 0.5, 1983: 0.5, 1984: 0.4, 1985: 0.4, 1986: 0.4, 1987: 0.4, 1988: 0.4, 1989: 0.4,
                    1990: 0.4, 1991: 0.4, 1992: 0.4, 1993: 0.4, 1994: 0.4, 1995: 0.3
                },
                "Holzkonstruktion": {
                    1918: 2.6, 1919: 1.4, 1920: 1.4, 1921: 1.4, 1922: 1.4, 1923: 1.4, 1924: 1.4, 1925: 1.4, 1926: 1.4,
                    1927: 1.4, 1928: 1.4, 1929: 1.4, 1930: 1.4, 1931: 1.4, 1932: 1.4, 1933: 1.4, 1934: 1.4, 1935: 1.4,
                    1936: 1.4, 1937: 1.4, 1938: 1.4, 1939: 1.4, 1940: 1.4, 1941: 1.4, 1942: 1.4, 1943: 1.4, 1944: 1.4,
                    1945: 1.4, 1946: 1.4, 1947: 1.4, 1948: 1.4, 1949: 1.4, 1950: 1.4, 1951: 1.4, 1952: 1.4, 1953: 1.4,
                    1954: 1.4, 1955: 1.4, 1956: 1.4, 1957: 1.4, 1958: 1.4, 1959: 1.4, 1960: 1.4, 1961: 1.4, 1962: 1.4,
                    1963: 1.4, 1964: 1.4, 1965: 1.4, 1966: 1.4, 1967: 1.4, 1968: 1.4, 1969: 0.8, 1970: 0.8, 1971: 0.8,
                    1972: 0.8, 1973: 0.8, 1974: 0.8, 1975: 0.8, 1976: 0.8, 1977: 0.8, 1978: 0.8, 1979: 0.5, 1980: 0.5,
                    1981: 0.5, 1982: 0.5, 1983: 0.5, 1984: 0.4, 1985: 0.4, 1986: 0.4, 1987: 0.4, 1988: 0.4, 1989: 0.4,
                    1990: 0.4, 1991: 0.4, 1992: 0.4, 1993: 0.4, 1994: 0.4, 1995: 0.3
                }
            },
            "Decken im obersten Geschoss": {
                "Massiv": {
                    1918: 2.1, 1919: 2.1, 1920: 2.1, 1921: 2.1, 1922: 2.1, 1923: 2.1, 1924: 2.1, 1925: 2.1, 1926: 2.1,
                    1927: 2.1, 1928: 2.1, 1929: 2.1, 1930: 2.1, 1931: 2.1, 1932: 2.1, 1933: 2.1, 1934: 2.1, 1935: 2.1,
                    1936: 2.1, 1937: 2.1, 1938: 2.1, 1939: 2.1, 1940: 2.1, 1941: 2.1, 1942: 2.1, 1943: 2.1, 1944: 2.1,
                    1945: 2.1, 1946: 2.1, 1947: 2.1, 1948: 2.1, 1949: 2.1, 1950: 2.1, 1951: 2.1, 1952: 2.1, 1953: 2.1,
                    1954: 2.1, 1955: 2.1, 1956: 2.1, 1957: 2.1, 1958: 2.1, 1959: 2.1, 1960: 2.1, 1961: 2.1, 1962: 2.1,
                    1963: 2.1, 1964: 2.1, 1965: 2.1, 1966: 2.1, 1967: 2.1, 1968: 2.1, 1969: 0.6, 1970: 0.6, 1971: 0.6,
                    1972: 0.6, 1973: 0.6, 1974: 0.6, 1975: 0.6, 1976: 0.6, 1977: 0.6, 1978: 0.6, 1979: 0.5, 1980: 0.5,
                    1981: 0.5, 1982: 0.5, 1983: 0.5, 1984: 0.4, 1985: 0.4, 1986: 0.4, 1987: 0.4, 1988: 0.4, 1989: 0.4,
                    1990: 0.4, 1991: 0.4, 1992: 0.4, 1993: 0.4, 1994: 0.4, 1995: 0.3
                },
                "Holzbalkendecke": {
                    1918: 1.0, 1919: 0.8, 1920: 0.8, 1921: 0.8, 1922: 0.8, 1923: 0.8, 1924: 0.8, 1925: 0.8, 1926: 0.8,
                    1927: 0.8, 1928: 0.8, 1929: 0.8, 1930: 0.8, 1931: 0.8, 1932: 0.8, 1933: 0.8, 1934: 0.8, 1935: 0.8,
                    1936: 0.8, 1937: 0.8, 1938: 0.8, 1939: 0.8, 1940: 0.8, 1941: 0.8, 1942: 0.8, 1943: 0.8, 1944: 0.8,
                    1945: 0.8, 1946: 0.8, 1947: 0.8, 1948: 0.8, 1949: 0.8, 1950: 0.8, 1951: 0.8, 1952: 0.8, 1953: 0.8,
                    1954: 0.8, 1955: 0.8, 1956: 0.8, 1957: 0.8, 1958: 0.8, 1959: 0.8, 1960: 0.8, 1961: 0.8, 1962: 0.8,
                    1963: 0.8, 1964: 0.8, 1965: 0.8, 1966: 0.8, 1967: 0.8, 1968: 0.8, 1969: 0.6, 1970: 0.6, 1971: 0.6,
                    1972: 0.6, 1973: 0.6, 1974: 0.6, 1975: 0.6, 1976: 0.6, 1977: 0.6, 1978: 0.6, 1979: 0.4, 1980: 0.4,
                    1981: 0.4, 1982: 0.4, 1983: 0.4, 1984: 0.3, 1985: 0.3, 1986: 0.3, 1987: 0.3, 1988: 0.3, 1989: 0.3,
                    1990: 0.3, 1991: 0.3, 1992: 0.3, 1993: 0.3, 1994: 0.3, 1995: 0.3
                }
            },
            "Decken über Außenbereich": {
                "Massiv": {
                    1918: 2.1, 1919: 2.1, 1920: 2.1, 1921: 2.1, 1922: 2.1, 1923: 2.1, 1924: 2.1, 1925: 2.1, 1926: 2.1,
                    1927: 2.1, 1928: 2.1, 1929: 2.1, 1930: 2.1, 1931: 2.1, 1932: 2.1, 1933: 2.1, 1934: 2.1, 1935: 2.1,
                    1936: 2.1, 1937: 2.1, 1938: 2.1, 1939: 2.1, 1940: 2.1, 1941: 2.1, 1942: 2.1, 1943: 2.1, 1944: 2.1,
                    1945: 2.1, 1946: 2.1, 1947: 2.1, 1948: 2.1, 1949: 2.1, 1950: 2.1, 1951: 2.1, 1952: 2.1, 1953: 2.1,
                    1954: 2.1, 1955: 2.1, 1956: 2.1, 1957: 2.1, 1958: 2.1, 1959: 2.1, 1960: 2.1, 1961: 2.1, 1962: 2.1,
                    1963: 2.1, 1964: 2.1, 1965: 2.1, 1966: 2.1, 1967: 2.1, 1968: 2.1, 1969: 0.6, 1970: 0.6, 1971: 0.6,
                    1972: 0.6, 1973: 0.6, 1974: 0.6, 1975: 0.6, 1976: 0.6, 1977: 0.6, 1978: 0.6, 1979: 0.5, 1980: 0.5,
                    1981: 0.5, 1982: 0.5, 1983: 0.5, 1984: 0.4, 1985: 0.4, 1986: 0.4, 1987: 0.4, 1988: 0.4, 1989: 0.4,
                    1990: 0.4, 1991: 0.4, 1992: 0.4, 1993: 0.4, 1994: 0.4, 1995: 0.3
                },
                "Holzbalkendecke": {
                    1918: 1.0, 1919: 0.8, 1920: 0.8, 1921: 0.8, 1922: 0.8, 1923: 0.8, 1924: 0.8, 1925: 0.8, 1926: 0.8,
                    1927: 0.8, 1928: 0.8, 1929: 0.8, 1930: 0.8, 1931: 0.8, 1932: 0.8, 1933: 0.8, 1934: 0.8, 1935: 0.8,
                    1936: 0.8, 1937: 0.8, 1938: 0.8, 1939: 0.8, 1940: 0.8, 1941: 0.8, 1942: 0.8, 1943: 0.8, 1944: 0.8,
                    1945: 0.8, 1946: 0.8, 1947: 0.8, 1948: 0.8, 1949: 0.8, 1950: 0.8, 1951: 0.8, 1952: 0.8, 1953: 0.8,
                    1954: 0.8, 1955: 0.8, 1956: 0.8, 1957: 0.8, 1958: 0.8, 1959: 0.8, 1960: 0.8, 1961: 0.8, 1962: 0.8,
                    1963: 0.8, 1964: 0.8, 1965: 0.8, 1966: 0.8, 1967: 0.8, 1968: 0.8, 1969: 0.6, 1970: 0.6, 1971: 0.6,
                    1972: 0.6, 1973: 0.6, 1974: 0.6, 1975: 0.6, 1976: 0.6, 1977: 0.6, 1978: 0.6, 1979: 0.4, 1980: 0.4,
                    1981: 0.4, 1982: 0.4, 1983: 0.4, 1984: 0.3, 1985: 0.3, 1986: 0.3, 1987: 0.3, 1988: 0.3, 1989: 0.3,
                    1990: 0.3, 1991: 0.3, 1992: 0.3, 1993: 0.3, 1994: 0.3, 1995: 0.3
                }
            }
        }



class ShellyTRVControl:
    def __init__(self, ip_address: str):
        self.ip_address: str = ip_address

    def get_status(self):
        url = f"http://{self.ip_address}/status"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data
            return None
        except (requests.exceptions.ConnectTimeout, OSError) as exceptions:
            print("No Shelly TRV reached")
            debug.printer(exceptions)
            return None

    def get_settings(self):
        url = f"http://{self.ip_address}/settings"
        try:
            response = requests.get(url, timeout=8)
            if response.status_code == 200:
                data = response.json()
                return data
            return None
        except (requests.exceptions.ConnectTimeout, OSError) as exceptions:
            print("No Shelly TRV reached")
            debug.printer(exceptions)
            return None

    def get_thermostat(self):
        url = f"http://{self.ip_address}/thermostats/0"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data
            return None
        except (requests.exceptions.ConnectTimeout, OSError) as exceptions:
            print("No Shelly TRV reached")
            debug.printer(exceptions)
            return None

    def set_valve_pos(self, position):
        url = f"http://{self.ip_address}/thermostat/0?pos={position}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data["pos"] == position:
                    return True
            return False
        except (requests.exceptions.ConnectTimeout, OSError) as exceptions:
            print("No Shelly TRV reached")
            debug.printer(exceptions)
            return False

    def set_temperature(self, temperature):
        url = f"http://{self.ip_address}/thermostat/0?target_t_enabled=1&target_t={temperature}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data["target_t"]["value"] == temperature:
                    return True
            return False
        except (requests.exceptions.ConnectTimeout, OSError) as exceptions:
            print("No Shelly TRV reached")
            debug.printer(exceptions)
            return False

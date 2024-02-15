# -*- coding: utf-8 -*-
import dataclasses
import datetime
from functools import lru_cache

import numpy as np
import requests
import requests_cache

from module import debug


class MarketData:
    """
    Gets the market data to the given time interval
    """

    def __init__(self, consumer_costs, start_time: None | str = None, end_time: None | str = None) -> None:
        """
        Initialise the class object.
        :param consumer_costs: The cost of the network.
        :param start_time: Start time, if only return data is given, the time is 24 hours.
        :param end_time: End time, start time must be given.
        """
        time_start: str = "00:00:00,00"
        self.session = requests_cache.CachedSession(r'cache/marketdata.cache', expire_after=datetime.timedelta(hours=1))

        if start_time is None and end_time is None:
            date_today: str = datetime.datetime.today().strftime("%Y-%m-%d")
            time_start_ms: int = self.convert_time_to_ms(date_today, time_start)
            self.data: dict = self.get_data(start=time_start_ms)
        else:
            time_start: datetime.datetime = datetime.datetime.strptime(start_time, "%Y-%m-%dT%H:%M")
            time_end: datetime.datetime = datetime.datetime.strptime(end_time, "%Y-%m-%dT%H:%M")

            date_start: str = time_start.strftime('%Y-%m-%d')
            date_end: str = time_end.strftime('%Y-%m-%d')

            time_start: str = time_start.strftime('%H:%M:%S,%f')
            time_end: str = time_end.strftime('%H:%M:%S,%f')

            time_start_ms: int = self.convert_time_to_ms(date_start, time_start)
            end_time_ms: int = self.convert_time_to_ms(date_end, time_end)

            self.data: dict = self.get_data(start=time_start_ms, end=end_time_ms)

        self.convert_dict(consumer_costs)

    def __str__(self) -> str:
        """
        The function can be used to print the market data.
        :return: It returns the market as a string.
        """
        return str(self.data)

    @staticmethod
    def convert_ms_to_time(ms: int) -> tuple[str, str]:
        """
        Convert the given milliseconds to a time string representing hours and minutes.
        :param ms: The ms to convert.
        :return: The time in hours and minutes.
        """
        time = datetime.datetime.fromtimestamp(ms / 1000).time()
        date = datetime.datetime.fromtimestamp(ms / 1000).date()
        t = f"{str(time.hour).zfill(2)}:00"
        d = f"{str(date.day).zfill(2)}-{str(date.month).zfill(2)}-{str(date.year)}"
        return t, d

    @staticmethod
    def convert_time_to_ms(date: str, t: str) -> int:
        """
        Convert the given date and time into milliseconds.
        :param date: As str
        :param t: time as string in the format %H:%M:%S,%f
        :return: milliseconds.
        """
        dt_obj = int(datetime.datetime.strptime(f"{date} {t}", '%Y-%m-%d %H:%M:%S,%f').timestamp() * 1000)
        return dt_obj

    def get_data(self, start: int | None = None, end: int | None = None) -> dict:
        """
        Retrieves data from the AWATTAR API for 24 hours, or the specified start and end time.
        Https://www.awattar.de/services/api
        :param start: start time in a millisecond.
        :param end: End time in milliseconds.
        :return: Json string of the data as dict.
        """
        if start and not end:
            url = rf"https://api.awattar.de/v1/marketdata?start={int(start)}"
        elif end and not start:
            url = rf"https://api.awattar.de/v1/marketdata?end={int(end)}"
        elif start and end:
            url = rf"https://api.awattar.de/v1/marketdata?start={int(start)}&end={int(end)}"
        else:
            url = r"https://api.awattar.de/v1/marketdata"
        print(url)
        response = self.session.get(url)
        if response.from_cache:
            print('Market data cached object')
        else:
            print('Market data new object')
        return response.json().get('data')

    def convert_dict(self, consumer_costs) -> None:
        """
        Converts the millisecond timestamp in the dict to time
        :return: None
        """
        for i, old_data in enumerate(self.data):
            self.data[i]['start_timestamp'], self.data[i]['date'] = self.convert_ms_to_time(old_data.get(
                'start_timestamp', 0))
            self.data[i]['end_timestamp'] = self.convert_ms_to_time(old_data.get('end_timestamp', 0))[0]
            self.data[i]['marketprice'] = round(old_data.get('marketprice', 0) / 10, 3)
            self.data[i]['consumerprice'] = round(((old_data.get('marketprice', 0) + consumer_costs) * 1.19), 3)
            self.data[i]['unit'] = 'ct/kWh'


class Weather:
    """
    Gets the needed weather data from open-meteo.com
    """

    # https://open-meteo.com/en/docs#latitude=49.5139&longitude=11.2825&minutely_15=diffuse_radiation_instant&
    # hourly=temperature_2m,cloudcover

    def __init__(self, latitude: float, longitude: float, start_date: str | None = None, end_date: str | None = None,
                 api: str = 'weather') -> None:
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
        if api == 'ensemble':
            weather = False
        else:
            weather = True

        weather_data: dict = self.get_weather(start_date, end_date, weather)
        self.data: dict = {}
        try:
            self._create_dict(weather_data)
            self._sort_weather(weather_data)
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

    def _create_dict(self, weather_data: dict) -> None:
        """
        Creates the dictionary for the weather data
        :param weather_data: received weather data from the api.
        :return:
        """
        days: list = [datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M').strftime('%d-%m-%Y')
                      for date in weather_data["hourly"]["time"]]

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
                    "dni_radiation": "",
                    "ghi_radiation": ""
                }

    def _sort_weather(self, unsorted_data: dict) -> None:
        """
        Sorts the weather in the created dictionary
        :return: None
        """
        min15 = unsorted_data["minutely_15"]
        hour = unsorted_data["hourly"]
        daily = unsorted_data["daily"]

        date = datetime.datetime.strptime(min15["time"][0], '%Y-%m-%dT%H:%M').strftime('%d-%m-%Y')
        for indx, tme in enumerate(min15["time"]):
            self.data[date][tme[11:]]["direct_radiation"] = min15["direct_radiation"][indx]
            self.data[date][tme[11:]]["dni_radiation"] = min15["direct_normal_irradiance"][indx]
            self.data[date][tme[11:]]["ghi_radiation"] = min15["shortwave_radiation"][indx]
            if tme[11:] == "23:45":
                date = (datetime.datetime.strptime(date, '%d-%m-%Y') +
                        datetime.timedelta(days=1)).strftime('%d-%m-%Y')

        date = datetime.datetime.strptime(min15["time"][0], '%Y-%m-%dT%H:%M').strftime('%d-%m-%Y')

        tme: str | None = None
        for indx, t in enumerate(hour["time"]):
            for x in range(0, 60, 15):
                tme = f"{t[11:13]}:{str(x).zfill(2)}"
                self.data[date][tme]["temp"] = hour["temperature_2m"][indx]
                self.data[date][tme]["cloudcover"] = hour["cloudcover"][indx]
            if tme == "23:45":
                date = (datetime.datetime.strptime(date, '%d-%m-%Y') +
                        datetime.timedelta(days=1)).strftime('%d-%m-%Y')

        date = datetime.datetime.strptime(min15["time"][0], '%Y-%m-%dT%H:%M').strftime('%d-%m-%Y')

        for indx, d in enumerate(unsorted_data["daily"]["time"]):
            self.data[date]["daily"]["temp_max"] = daily["temperature_2m_max"][indx]
            self.data[date]["daily"]["temp_min"] = daily["temperature_2m_min"][indx]
            self.data[date]["daily"]["sunrise"] = daily["sunrise"][indx][11:]
            self.data[date]["daily"]["sunset"] = daily["sunset"][indx][11:]
            date = (datetime.datetime.strptime(date, '%d-%m-%Y') +
                    datetime.timedelta(days=1)).strftime('%d-%m-%Y')

    def get_weather(self, start_date: str | None, end_date: str | None, weather: bool = True) -> dict:
        """
        Gets the weather for the given latitude and longitude
        :return: A dict with the following variables: direct radiation, temperatur, cloudcover, temperature max,
                 temperatur min, sunrise, sunset.
        """
        url: str = ''
        if start_date is None or end_date is None:
            if weather:
                url: str = (f"https://api.open-meteo.com/v1/forecast?"
                            f"latitude={self.latitude}&longitude={self.longitude}&"
                            "minutely_15=direct_normal_irradiance,direct_radiation,shortwave_radiation"
                            "&hourly=temperature_2m,cloudcover&"
                            "models=best_match&"
                            "daily=temperature_2m_max,temperature_2m_min,sunrise,sunset&"
                            "timezone=Europe%2FBerlin&forecast_days=3")
            elif not weather:
                url: str = (f"https://ensemble-api.open-meteo.com/v1/ensemble?"
                            f"latitude={self.latitude}&longitude={self.longitude}&"
                            f"hourly=shortwave_radiation&"
                            f"timezone=Europe%2FBerlin&"
                            f"forecast_days=35&"
                            f"models=gfs05")
        else:
            start: datetime = datetime.datetime.strptime(start_date, "%d-%m-%Y")
            end: datetime = datetime.datetime.strptime(end_date, "%d-%m-%Y")

            if weather:
                url: str = (f"https://api.open-meteo.com/v1/forecast?"
                            f"latitude={self.latitude}&longitude={self.longitude}&"
                            f"minutely_15=direct_normal_irradiance,direct_radiation,shortwave_radiation"
                            f"&hourly=temperature_2m,cloudcover&"
                            f"models=best_match&"
                            f"daily=temperature_2m_max,temperature_2m_min,sunrise,sunset&"
                            f"timezone=Europe%2FBerlin&"
                            f"start_date={start.year}-{str(start.month).zfill(2)}-{str(start.day).zfill(2)}&"
                            f"end_date={end.year}-{str(end.month).zfill(2)}-{str(end.day).zfill(2)}")
            elif not weather:
                url: str = (f"https://ensemble-api.open-meteo.com/v1/ensemble?"
                            f"latitude={self.latitude}&longitude={self.longitude}&"
                            f"hourly=weather_code&"
                            f"timezone=Europe%2FBerlin&"
                            f"start_date={start.year}-{str(start.month).zfill(2)}-{str(start.day).zfill(2)}&"
                            f"end_date={end.year}-{str(end.month).zfill(2)}-{str(end.day).zfill(2)}&"
                            f"models=gfs05")

            else:
                return {}

        print(url)
        response = self.session.get(url)
        if response.from_cache:
            print('Weather data cached object')
        else:
            print('Weather data new object')
        return response.json()

    @staticmethod
    def weather_code(code: str, day_or_night: str) -> dict:
        data = {
            "0": {
                "day": {
                    "description": "Sunny",
                    "image": "http://openweathermap.org/img/wn/01d@2x.png"
                },
                "night": {
                    "description": "Clear",
                    "image": "http://openweathermap.org/img/wn/01n@2x.png"
                }
            },
            "1": {
                "day": {
                    "description": "Mainly Sunny",
                    "image": "http://openweathermap.org/img/wn/01d@2x.png"
                },
                "night": {
                    "description": "Mainly Clear",
                    "image": "http://openweathermap.org/img/wn/01n@2x.png"
                }
            },
            "2": {
                "day": {
                    "description": "Partly Cloudy",
                    "image": "http://openweathermap.org/img/wn/02d@2x.png"
                },
                "night": {
                    "description": "Partly Cloudy",
                    "image": "http://openweathermap.org/img/wn/02n@2x.png"
                }
            },
            "3": {
                "day": {
                    "description": "Cloudy",
                    "image": "http://openweathermap.org/img/wn/03d@2x.png"
                },
                "night": {
                    "description": "Cloudy",
                    "image": "http://openweathermap.org/img/wn/03n@2x.png"
                }
            },
            "45": {
                "day": {
                    "description": "Foggy",
                    "image": "http://openweathermap.org/img/wn/50d@2x.png"
                },
                "night": {
                    "description": "Foggy",
                    "image": "http://openweathermap.org/img/wn/50n@2x.png"
                }
            },
            "48": {
                "day": {
                    "description": "Rime Fog",
                    "image": "http://openweathermap.org/img/wn/50d@2x.png"
                },
                "night": {
                    "description": "Rime Fog",
                    "image": "http://openweathermap.org/img/wn/50n@2x.png"
                }
            },
            "51": {
                "day": {
                    "description": "Light Drizzle",
                    "image": "http://openweathermap.org/img/wn/09d@2x.png"
                },
                "night": {
                    "description": "Light Drizzle",
                    "image": "http://openweathermap.org/img/wn/09n@2x.png"
                }
            },
            "53": {
                "day": {
                    "description": "Drizzle",
                    "image": "http://openweathermap.org/img/wn/09d@2x.png"
                },
                "night": {
                    "description": "Drizzle",
                    "image": "http://openweathermap.org/img/wn/09n@2x.png"
                }
            },
            "55": {
                "day": {
                    "description": "Heavy Drizzle",
                    "image": "http://openweathermap.org/img/wn/09d@2x.png"
                },
                "night": {
                    "description": "Heavy Drizzle",
                    "image": "http://openweathermap.org/img/wn/09n@2x.png"
                }
            },
            "56": {
                "day": {
                    "description": "Light Freezing Drizzle",
                    "image": "http://openweathermap.org/img/wn/09d@2x.png"
                },
                "night": {
                    "description": "Light Freezing Drizzle",
                    "image": "http://openweathermap.org/img/wn/09n@2x.png"
                }
            },
            "57": {
                "day": {
                    "description": "Freezing Drizzle",
                    "image": "http://openweathermap.org/img/wn/09d@2x.png"
                },
                "night": {
                    "description": "Freezing Drizzle",
                    "image": "http://openweathermap.org/img/wn/09n@2x.png"
                }
            },
            "61": {
                "day": {
                    "description": "Light Rain",
                    "image": "http://openweathermap.org/img/wn/10d@2x.png"
                },
                "night": {
                    "description": "Light Rain",
                    "image": "http://openweathermap.org/img/wn/10n@2x.png"
                }
            },
            "63": {
                "day": {
                    "description": "Rain",
                    "image": "http://openweathermap.org/img/wn/10d@2x.png"
                },
                "night": {
                    "description": "Rain",
                    "image": "http://openweathermap.org/img/wn/10n@2x.png"
                }
            },
            "65": {
                "day": {
                    "description": "Heavy Rain",
                    "image": "http://openweathermap.org/img/wn/10d@2x.png"
                },
                "night": {
                    "description": "Heavy Rain",
                    "image": "http://openweathermap.org/img/wn/10n@2x.png"
                }
            },
            "66": {
                "day": {
                    "description": "Light Freezing Rain",
                    "image": "http://openweathermap.org/img/wn/10d@2x.png"
                },
                "night": {
                    "description": "Light Freezing Rain",
                    "image": "http://openweathermap.org/img/wn/10n@2x.png"
                }
            },
            "67": {
                "day": {
                    "description": "Freezing Rain",
                    "image": "http://openweathermap.org/img/wn/10d@2x.png"
                },
                "night": {
                    "description": "Freezing Rain",
                    "image": "http://openweathermap.org/img/wn/10n@2x.png"
                }
            },
            "71": {
                "day": {
                    "description": "Light Snow",
                    "image": "http://openweathermap.org/img/wn/13d@2x.png"
                },
                "night": {
                    "description": "Light Snow",
                    "image": "http://openweathermap.org/img/wn/13n@2x.png"
                }
            },
            "73": {
                "day": {
                    "description": "Snow",
                    "image": "http://openweathermap.org/img/wn/13d@2x.png"
                },
                "night": {
                    "description": "Snow",
                    "image": "http://openweathermap.org/img/wn/13n@2x.png"
                }
            },
            "75": {
                "day": {
                    "description": "Heavy Snow",
                    "image": "http://openweathermap.org/img/wn/13d@2x.png"
                },
                "night": {
                    "description": "Heavy Snow",
                    "image": "http://openweathermap.org/img/wn/13n@2x.png"
                }
            },
            "77": {
                "day": {
                    "description": "Snow Grains",
                    "image": "http://openweathermap.org/img/wn/13d@2x.png"
                },
                "night": {
                    "description": "Snow Grains",
                    "image": "http://openweathermap.org/img/wn/13n@2x.png"
                }
            },
            "80": {
                "day": {
                    "description": "Light Showers",
                    "image": "http://openweathermap.org/img/wn/09d@2x.png"
                },
                "night": {
                    "description": "Light Showers",
                    "image": "http://openweathermap.org/img/wn/09n@2x.png"
                }
            },
            "81": {
                "day": {
                    "description": "Showers",
                    "image": "http://openweathermap.org/img/wn/09d@2x.png"
                },
                "night": {
                    "description": "Showers",
                    "image": "http://openweathermap.org/img/wn/09n@2x.png"
                }
            },
            "82": {
                "day": {
                    "description": "Heavy Showers",
                    "image": "http://openweathermap.org/img/wn/09d@2x.png"
                },
                "night": {
                    "description": "Heavy Showers",
                    "image": "http://openweathermap.org/img/wn/09n@2x.png"
                }
            },
            "85": {
                "day": {
                    "description": "Light Snow Showers",
                    "image": "http://openweathermap.org/img/wn/13d@2x.png"
                },
                "night": {
                    "description": "Light Snow Showers",
                    "image": "http://openweathermap.org/img/wn/13n@2x.png"
                }
            },
            "86": {
                "day": {
                    "description": "Snow Showers",
                    "image": "http://openweathermap.org/img/wn/13d@2x.png"
                },
                "night": {
                    "description": "Snow Showers",
                    "image": "http://openweathermap.org/img/wn/13n@2x.png"
                }
            },
            "95": {
                "day": {
                    "description": "Thunderstorm",
                    "image": "http://openweathermap.org/img/wn/11d@2x.png"
                },
                "night": {
                    "description": "Thunderstorm",
                    "image": "http://openweathermap.org/img/wn/11n@2x.png"
                }
            },
            "96": {
                "day": {
                    "description": "Light Thunderstorms With Hail",
                    "image": "http://openweathermap.org/img/wn/11d@2x.png"
                },
                "night": {
                    "description": "Light Thunderstorms With Hail",
                    "image": "http://openweathermap.org/img/wn/11n@2x.png"
                }
            },
            "99": {
                "day": {
                    "description": "Thunderstorm With Hail",
                    "image": "http://openweathermap.org/img/wn/11d@2x.png"
                },
                "night": {
                    "description": "Thunderstorm With Hail",
                    "image": "http://openweathermap.org/img/wn/11n@2x.png"
                }
            }
        }
        return data.get(code).get(day_or_night)


class CalcSunPos:
    """
    Calcs the position of the sun
    """

    def __init__(self, latitude, longitude, date: str | None = None) -> None:
        """
        Initialize the class
        :param latitude: latitude
        :param longitude:longitude
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
        self.day_angle: float = np.deg2rad(360.0, dtype=np.float32) * self.left_days / self.days_per_year

        self.sun_declination: float = (
                np.deg2rad(0.3948, dtype=np.float32) - np.deg2rad(23.2559, dtype=np.float32) *
                np.cos(self.day_angle + np.deg2rad(9.1, dtype=np.float32), dtype=np.float32) -
                np.deg2rad(0.3915, dtype=np.float32) *
                np.cos(2.0 * self.day_angle + np.deg2rad(5.4, dtype=np.float32), dtype=np.float32) -
                np.deg2rad(0.1764, dtype=np.float32) *
                np.cos(3.0 * self.day_angle + np.deg2rad(26.0, dtype=np.float32), dtype=np.float32))

        self.time_equation: float = (
                np.deg2rad(0.0066, dtype=np.float32) + np.deg2rad(7.3525, dtype=np.float32) *
                np.cos(self.day_angle + np.deg2rad(85.9, dtype=np.float32), dtype=np.float32) +
                np.deg2rad(9.9359, dtype=np.float32) *
                np.cos(2.0 * self.day_angle + np.deg2rad(108.9, dtype=np.float32), dtype=np.float32) +
                np.deg2rad(0.3387, dtype=np.float32) *
                np.cos(3.0 * self.day_angle + np.deg2rad(105.2, dtype=np.float32), dtype=np.float32))

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
        Calcs the azimuth to the given time.
        :param t: Time as float.
        :return: The azimuth in degrees.
        """
        sun_height: float = np.deg2rad(self.calc_solar_elevation(t), dtype=np.float32)
        if self.real_local_time > 12:
            sun_azimuth: float = np.deg2rad(180) + np.arccos(
                (np.sin(sun_height, dtype=np.float32) *
                 np.sin(self.latitude, dtype=np.float32) - np.sin(self.sun_declination, dtype=np.float32)) /
                (np.cos(sun_height, dtype=np.float32) * np.cos(self.latitude, dtype=np.float32)))
        else:
            sun_azimuth: float = np.deg2rad(180, dtype=np.float32) - np.arccos(
                (np.sin(sun_height, dtype=np.float32) *
                 np.sin(self.latitude, dtype=np.float32) - np.sin(self.sun_declination, dtype=np.float32)) /
                (np.cos(sun_height, dtype=np.float32) * np.cos(self.latitude, dtype=np.float32)))
        return np.rad2deg(sun_azimuth)

    @lru_cache(maxsize=None)
    def calc_solar_elevation(self, t: float) -> float:
        """
        Calcs solar elevation to the given time.
        :param t: Time as a float.
        :return: The solar elevation in degrees.
        """
        self.time_last_calc: float = round((int(t)) + ((t - int(t)) * 100 / 60), 2) - 0.25
        self.mid_local_time: float = self.time_last_calc + self.longitude * np.deg2rad(4, dtype=np.float32)
        self.real_local_time: float = self.mid_local_time + self.time_equation
        self.hour_angle: float = (12.00 - self.real_local_time) * np.deg2rad(15)
        sun_height: float = np.arcsin(np.cos(self.hour_angle, dtype=np.float32) *
                                      np.cos(self.latitude, dtype=np.float32) *
                                      np.cos(self.sun_declination, dtype=np.float32)
                                      + np.sin(self.latitude, dtype=np.float32) *
                                      np.sin(self.sun_declination, dtype=np.float32), dtype=np.float32)
        return np.rad2deg(sun_height, dtype=np.float32)

    @lru_cache(maxsize=None)
    def adjust_for_new_angle(self, original_gb, original_tilt_angle, original_azimuth_angle, new_tilt_angle,
                             new_azimuth_angle, tme):
        """

        :param original_gb:
        :param original_tilt_angle:
        :param original_azimuth_angle:
        :param new_tilt_angle:
        :param new_azimuth_angle:
        :param tme:
        :return:
        """

        @lru_cache(maxsize=None)
        def _calc_incidence_angle(elevation_sun, azimuth_sun, tilt_angle, panel_azimuth):
            """

            :param elevation_sun:
            :param azimuth_sun:
            :param tilt_angle:
            :param panel_azimuth:
            :return:
            """
            return np.rad2deg(
                np.arccos(
                    np.cos(np.deg2rad(elevation_sun, dtype=np.float32), dtype=np.float32) *
                    np.sin(np.deg2rad(tilt_angle, dtype=np.float32), dtype=np.float32) *
                    np.cos(np.deg2rad(azimuth_sun - panel_azimuth, dtype=np.float32), dtype=np.float32) +
                    np.sin(np.deg2rad(elevation_sun, dtype=np.float32), dtype=np.float32) *
                    np.cos(np.deg2rad(tilt_angle, dtype=np.float32), dtype=np.float32)
                )
            )

        sun_azimuth = self.calc_azimuth(tme)
        sun_elevation = self.calc_solar_elevation(tme)
        incidence_angle_original = _calc_incidence_angle(sun_elevation, sun_azimuth, original_tilt_angle,
                                                         original_azimuth_angle)
        gb_horizontal = original_gb / np.cos(np.deg2rad(incidence_angle_original))
        incidence_angle_new = _calc_incidence_angle(sun_elevation, sun_azimuth, new_tilt_angle, new_azimuth_angle)
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
        self.mounting_type_dict: dict = {
            -1: 100,
            0: 22,  # Völlig freie Aufständerung
            1: 28,  # Auf dem Dach, großer Abstand
            2: 29,  # Auf dem Dach bzw. dach integriert, gute Hinterlüftung
            3: 32,  # Auf dem Dach bzw. dach integriert, schlechte Hinterlüftung
            4: 35,  # An der Fassade bzw. fassaden integriert, gute Hinterlüftung
            5: 39,  # An der Fassade bzw. fassaden integriert, schlechte Hinterlüftung
            6: 43,  # Dachintegration, ohne Hinterlüftung
            7: 55  # Fassaden integriert, ohne Hinterlüftung
        }
        self.diffuse_index_F11: dict = {
            1: -0.008, 2: 0.13, 3: 0.33, 4: 0.568, 5: 0.873, 6: 1.132, 7: 1.06, 8: 0.678
        }
        self.diffuse_index_F12: dict = {
            1: 0.588, 2: 0.683, 3: 0.487, 4: 0.187, 5: -0.392, 6: -1.237, 7: -1.6, 8: -0.327
        }
        self.diffuse_index_F13: dict = {
            1: -0.062, 2: -0.151, 3: -0.221, 4: -0.295, 5: -0.362, 6: -0.412, 7: -0.359, 8: -0.25
        }
        self.diffuse_index_F21: dict = {
            1: -0.06, 2: -0.019, 3: 0.055, 4: 0.109, 5: 0.226, 6: 0.288, 7: 0.264, 8: 0.156
        }
        self.diffuse_index_F22: dict = {
            1: 0.072, 2: 0.066, 3: -0.064, 4: -0.152, 5: -0.462, 6: -0.823, 7: -1.127, 8: -1.377
        }
        self.diffuse_index_F23: dict = {
            1: -0.022, 2: -0.029, 3: -0.026, 4: -0.014, 5: 0.001, 6: 0.056, 7: 0.131, 8: 0.251
        }
        self.mounting_type: int = self.mounting_type_dict[mounting_type_index]

    def __str__(self) -> str:
        """
        Can be used to print the data
        :return: str of the data.
        """
        val = (f"Die Modul Effizienz ist: {self.module_efficiency * 100}%\n"
               f"Die Modulfläche ist: {self.module_area}m²\n"
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
        :param radiation: the current radiation in W/m²
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
        :param radiation: the current radiation in W/m²
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
            power_direct_gen = (power_direct_horizontal *
                                np.cos(np.deg2rad(incidence_angle, dtype=np.float32), dtype=np.float32) /
                                np.sin(np.deg2rad(90 - sun_height, dtype=np.float32), dtype=np.float32))
            return abs(power_direct_gen * current_efficiency * self.module_area)
        except (ValueError, TypeError):
            if power_direct_horizontal is None:
                print("No radiation")
            return 0

    def calc_diffuse_radiation(self, sun_height: float, diffuse_radiation, direct_radiation, incidence_angle: float):
        """
        Calcs the diffuse radiation with the Perez Model
        :param sun_height:
        :param diffuse_radiation:
        :param direct_radiation:
        :param incidence_angle:
        :return:
        """
        kappa: float = 1.041
        air_mass: float = 1 / np.sin(np.deg2rad(sun_height))
        clarity_index: float = ((((diffuse_radiation + direct_radiation * np.arcsin(sun_height)) /
                                  diffuse_radiation) + kappa * np.power(incidence_angle, 3)) /
                                (1 + kappa * np.power(incidence_angle, 3, dtype=np.float32)))  # Epsilon
        brightness_index: float = air_mass * direct_radiation / 1361  # Delta

        index: int = 0

        if 1 <= clarity_index <= 1.065:
            index = 1
        elif 1.065 < clarity_index <= 1.230:
            index = 2
        elif 1.230 < clarity_index <= 1.5:
            index = 3
        elif 1.5 < clarity_index <= 1.95:
            index = 4
        elif 1.95 < clarity_index <= 2.8:
            index = 5
        elif 2.8 < clarity_index <= 4.5:
            index = 6
        elif 4.5 < clarity_index <= 6.2:
            index = 7
        elif clarity_index > 6.2:
            index = 8

        f_1: float = (self.diffuse_index_F11[index] +
                      self.diffuse_index_F12[index] * brightness_index +
                      self.diffuse_index_F13[index] * incidence_angle)

        f_2: float = (self.diffuse_index_F21[index] +
                      self.diffuse_index_F22[index] * brightness_index +
                      self.diffuse_index_F23[index] * incidence_angle)

        a: float = max(0, np.cos(np.deg2rad(incidence_angle)))
        b: float = max(0.087, np.sin(np.deg2rad(sun_height)))

        diffuse_energy: float = diffuse_radiation * (
                0.5 * (
                    1 + np.cos(np.deg2rad(self.tilt_angle))) * (1 - f_1) + a / b * f_1 + f_2 *
                np.sin(np.deg2rad(self.tilt_angle))
        )

        return diffuse_energy

    @lru_cache(maxsize=None)
    def calc_power_with_dni(self, dni: float, incidence_angle: float, temperature: float) -> float:
        """
        Calculates the energy output of the PV panel using Direct Normal Irradiance (DNI)
        :param temperature:
        :param incidence_angle: The incidence angle of the sun
        :param dni: Direct Normal Irradiance in W/m²
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
    @dataclasses.dataclass
    class Room:
        volume: float = 0.0

        @dataclasses.dataclass
        class Wall1:
            u_wert: float = 0.0
            area: float = 0.0
            temp_diff: float = 0.0
            interior_wall_temp: float = 0.0

            @dataclasses.dataclass
            class Window1:
                u_wert: float = 0.0
                area: float = 0.0

            @dataclasses.dataclass
            class Window2:
                u_wert: float = 0.0
                area: float = 0.0

            @dataclasses.dataclass
            class Window3:
                u_wert: float = 0.0
                area: float = 0.0

            @dataclasses.dataclass
            class Window4:
                u_wert: float = 0.0
                area: float = 0.0

            @dataclasses.dataclass
            class Door:
                u_wert: float = 0.0
                area: float = 0.0

        @dataclasses.dataclass
        class Wall2:
            u_wert: float = 0.0
            area: float = 0.0
            temp_diff: float = 0.0
            interior_wall_temp: float = 0.0

            @dataclasses.dataclass
            class Window1:
                u_wert: float = 0.0
                area: float = 0.0

            @dataclasses.dataclass
            class Window2:
                u_wert: float = 0.0
                area: float = 0.0

            @dataclasses.dataclass
            class Window3:
                u_wert: float = 0.0
                area: float = 0.0

            @dataclasses.dataclass
            class Window4:
                u_wert: float = 0.0
                area: float = 0.0

            @dataclasses.dataclass
            class Door:
                u_wert: float = 0.0
                area: float = 0.0

        @dataclasses.dataclass
        class Wall3:
            u_wert: float = 0.0
            area: float = 0.0
            temp_diff: float = 0.0
            interior_wall_temp: float = 0.0

            @dataclasses.dataclass
            class Window1:
                u_wert: float = 0.0
                area: float = 0.0

            @dataclasses.dataclass
            class Window2:
                u_wert: float = 0.0
                area: float = 0.0

            @dataclasses.dataclass
            class Window3:
                u_wert: float = 0.0
                area: float = 0.0

            @dataclasses.dataclass
            class Window4:
                u_wert: float = 0.0
                area: float = 0.0

            @dataclasses.dataclass
            class Door:
                u_wert: float = 0.0
                area: float = 0.0

        @dataclasses.dataclass
        class Wall4:
            u_wert: float = 0.0
            area: float = 0.0
            temp_diff: float = 0.0
            interior_wall_temp: float = 0.0

            @dataclasses.dataclass
            class Window1:
                u_wert: float = 0.0
                area: float = 0.0

            @dataclasses.dataclass
            class Window2:
                u_wert: float = 0.0
                area: float = 0.0

            @dataclasses.dataclass
            class Window3:
                u_wert: float = 0.0
                area: float = 0.0

            @dataclasses.dataclass
            class Window4:
                u_wert: float = 0.0
                area: float = 0.0

            @dataclasses.dataclass
            class Door:
                u_wert: float = 0.0
                area: float = 0.0

        @dataclasses.dataclass
        class Floor:
            u_wert: float = 0.0
            area: float = 0.0
            temp_diff: float = 0.0

        @dataclasses.dataclass
        class Ceiling:
            u_wert: float = 0.0
            area: float = 0.0
            temp_diff: float = 0.0

    def __init__(self) -> None:
        """
        # https://www.raum-analyse.de/waermedaemmung/enev/
        """
        self.u_value: dict = {
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
                },
                "ENEV": {
                    2009: 1.3, 2014: 1.3, 2016: 0.98
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
                },
                "ENEV": {
                    2009: 1.8, 2014: 1.8, 2016: 1.35
                }
            },
            "Wand": {
                "Außenwand": {
                    "Massivbauweise": {
                        1918: 1.7, 1919: 1.7, 1920: 1.7, 1921: 1.7, 1922: 1.7, 1923: 1.7, 1924: 1.7, 1925: 1.7,
                        1926: 1.7,
                        1927: 1.7, 1928: 1.7, 1929: 1.7, 1930: 1.7, 1931: 1.7, 1932: 1.7, 1933: 1.7, 1934: 1.7,
                        1935: 1.7,
                        1936: 1.7, 1937: 1.7, 1938: 1.7, 1939: 1.7, 1940: 1.7, 1941: 1.7, 1942: 1.7, 1943: 1.7,
                        1944: 1.7,
                        1945: 1.7, 1946: 1.7, 1947: 1.7, 1948: 1.7, 1949: 1.4, 1950: 1.4, 1951: 1.4, 1952: 1.4,
                        1953: 1.4,
                        1954: 1.4, 1955: 1.4, 1956: 1.4, 1957: 1.4, 1958: 1.4, 1959: 1.4, 1960: 1.4, 1961: 1.4,
                        1962: 1.4,
                        1963: 1.4, 1964: 1.4, 1965: 1.4, 1966: 1.4, 1967: 1.4, 1968: 1.4, 1969: 1.0, 1970: 1.0,
                        1971: 1.0,
                        1972: 1.0, 1973: 1.0, 1974: 1.0, 1975: 1.0, 1976: 1.0, 1977: 1.0, 1978: 1.0, 1979: 0.8,
                        1980: 0.8,
                        1981: 0.8, 1982: 0.8, 1983: 0.8, 1984: 0.6, 1985: 0.6, 1986: 0.6, 1987: 0.6, 1988: 0.6,
                        1989: 0.6,
                        1990: 0.6, 1991: 0.6, 1992: 0.6, 1993: 0.6, 1994: 0.6, 1995: 0.5
                    },
                    "Holzkonstruktion": {
                        1918: 2.0, 1919: 2.0, 1920: 2.0, 1921: 2.0, 1922: 2.0, 1923: 2.0, 1924: 2.0, 1925: 2.0,
                        1926: 2.0,
                        1927: 2.0, 1928: 2.0, 1929: 2.0, 1930: 2.0, 1931: 2.0, 1932: 2.0, 1933: 2.0, 1934: 2.0,
                        1935: 2.0,
                        1936: 2.0, 1937: 2.0, 1938: 2.0, 1939: 2.0, 1940: 2.0, 1941: 2.0, 1942: 2.0, 1943: 2.0,
                        1944: 2.0,
                        1945: 2.0, 1946: 2.0, 1947: 2.0, 1948: 2.0, 1949: 1.4, 1950: 1.4, 1951: 1.4, 1952: 1.4,
                        1953: 1.4,
                        1954: 1.4, 1955: 1.4, 1956: 1.4, 1957: 1.4, 1958: 1.4, 1959: 1.4, 1960: 1.4, 1961: 1.4,
                        1962: 1.4,
                        1963: 1.4, 1964: 1.4, 1965: 1.4, 1966: 1.4, 1967: 1.4, 1968: 1.4, 1969: 0.6, 1970: 0.6,
                        1971: 0.6,
                        1972: 0.6, 1973: 0.6, 1974: 0.6, 1975: 0.6, 1976: 0.6, 1977: 0.6, 1978: 0.6, 1979: 0.5,
                        1980: 0.5,
                        1981: 0.5, 1982: 0.5, 1983: 0.5, 1984: 0.4, 1985: 0.4, 1986: 0.4, 1987: 0.4, 1988: 0.4,
                        1989: 0.4,
                        1990: 0.4, 1991: 0.4, 1992: 0.4, 1993: 0.4, 1994: 0.4, 1995: 0.4
                    }
                },
                "Innenwand": {
                    "Massivbauweise": {
                        1918: 1.7, 1919: 1.7, 1920: 1.7, 1921: 1.7, 1922: 1.7, 1923: 1.7, 1924: 1.7, 1925: 1.7,
                        1926: 1.7,
                        1927: 1.7, 1928: 1.7, 1929: 1.7, 1930: 1.7, 1931: 1.7, 1932: 1.7, 1933: 1.7, 1934: 1.7,
                        1935: 1.7,
                        1936: 1.7, 1937: 1.7, 1938: 1.7, 1939: 1.7, 1940: 1.7, 1941: 1.7, 1942: 1.7, 1943: 1.7,
                        1944: 1.7,
                        1945: 1.7, 1946: 1.7, 1947: 1.7, 1948: 1.7, 1949: 1.4, 1950: 1.4, 1951: 1.4, 1952: 1.4,
                        1953: 1.4,
                        1954: 1.4, 1955: 1.4, 1956: 1.4, 1957: 1.4, 1958: 1.4, 1959: 1.4, 1960: 1.4, 1961: 1.4,
                        1962: 1.4,
                        1963: 1.4, 1964: 1.4, 1965: 1.4, 1966: 1.4, 1967: 1.4, 1968: 1.4, 1969: 1.0, 1970: 1.0,
                        1971: 1.0,
                        1972: 1.0, 1973: 1.0, 1974: 1.0, 1975: 1.0, 1976: 1.0, 1977: 1.0, 1978: 1.0, 1979: 0.8,
                        1980: 0.8,
                        1981: 0.8, 1982: 0.8, 1983: 0.8, 1984: 0.6, 1985: 0.6, 1986: 0.6, 1987: 0.6, 1988: 0.6,
                        1989: 0.6,
                        1990: 0.6, 1991: 0.6, 1992: 0.6, 1993: 0.6, 1994: 0.6, 1995: 0.5
                    },
                    "Holzkonstruktion": {
                        1918: 2.0, 1919: 2.0, 1920: 2.0, 1921: 2.0, 1922: 2.0, 1923: 2.0, 1924: 2.0, 1925: 2.0,
                        1926: 2.0,
                        1927: 2.0, 1928: 2.0, 1929: 2.0, 1930: 2.0, 1931: 2.0, 1932: 2.0, 1933: 2.0, 1934: 2.0,
                        1935: 2.0,
                        1936: 2.0, 1937: 2.0, 1938: 2.0, 1939: 2.0, 1940: 2.0, 1941: 2.0, 1942: 2.0, 1943: 2.0,
                        1944: 2.0,
                        1945: 2.0, 1946: 2.0, 1947: 2.0, 1948: 2.0, 1949: 1.4, 1950: 1.4, 1951: 1.4, 1952: 1.4,
                        1953: 1.4,
                        1954: 1.4, 1955: 1.4, 1956: 1.4, 1957: 1.4, 1958: 1.4, 1959: 1.4, 1960: 1.4, 1961: 1.4,
                        1962: 1.4,
                        1963: 1.4, 1964: 1.4, 1965: 1.4, 1966: 1.4, 1967: 1.4, 1968: 1.4, 1969: 0.6, 1970: 0.6,
                        1971: 0.6,
                        1972: 0.6, 1973: 0.6, 1974: 0.6, 1975: 0.6, 1976: 0.6, 1977: 0.6, 1978: 0.6, 1979: 0.5,
                        1980: 0.5,
                        1981: 0.5, 1982: 0.5, 1983: 0.5, 1984: 0.4, 1985: 0.4, 1986: 0.4, 1987: 0.4, 1988: 0.4,
                        1989: 0.4,
                        1990: 0.4, 1991: 0.4, 1992: 0.4, 1993: 0.4, 1994: 0.4, 1995: 0.4
                    }
                },
                "gegen Erdreich": {
                    "Massivbauweise": {
                        1918: 1.7, 1919: 1.7, 1920: 1.7, 1921: 1.7, 1922: 1.7, 1923: 1.7, 1924: 1.7, 1925: 1.7,
                        1926: 1.7,
                        1927: 1.7, 1928: 1.7, 1929: 1.7, 1930: 1.7, 1931: 1.7, 1932: 1.7, 1933: 1.7, 1934: 1.7,
                        1935: 1.7,
                        1936: 1.7, 1937: 1.7, 1938: 1.7, 1939: 1.7, 1940: 1.7, 1941: 1.7, 1942: 1.7, 1943: 1.7,
                        1944: 1.7,
                        1945: 1.7, 1946: 1.7, 1947: 1.7, 1948: 1.7, 1949: 1.4, 1950: 1.4, 1951: 1.4, 1952: 1.4,
                        1953: 1.4,
                        1954: 1.4, 1955: 1.4, 1956: 1.4, 1957: 1.4, 1958: 1.4, 1959: 1.4, 1960: 1.4, 1961: 1.4,
                        1962: 1.4,
                        1963: 1.4, 1964: 1.4, 1965: 1.4, 1966: 1.4, 1967: 1.4, 1968: 1.4, 1969: 1.0, 1970: 1.0,
                        1971: 1.0,
                        1972: 1.0, 1973: 1.0, 1974: 1.0, 1975: 1.0, 1976: 1.0, 1977: 1.0, 1978: 1.0, 1979: 0.8,
                        1980: 0.8,
                        1981: 0.8, 1982: 0.8, 1983: 0.8, 1984: 0.6, 1985: 0.6, 1986: 0.6, 1987: 0.6, 1988: 0.6,
                        1989: 0.6,
                        1990: 0.6, 1991: 0.6, 1992: 0.6, 1993: 0.6, 1994: 0.6, 1995: 0.5
                    },
                    "Holzkonstruktion": {
                        1918: 2.0, 1919: 2.0, 1920: 2.0, 1921: 2.0, 1922: 2.0, 1923: 2.0, 1924: 2.0, 1925: 2.0,
                        1926: 2.0,
                        1927: 2.0, 1928: 2.0, 1929: 2.0, 1930: 2.0, 1931: 2.0, 1932: 2.0, 1933: 2.0, 1934: 2.0,
                        1935: 2.0,
                        1936: 2.0, 1937: 2.0, 1938: 2.0, 1939: 2.0, 1940: 2.0, 1941: 2.0, 1942: 2.0, 1943: 2.0,
                        1944: 2.0,
                        1945: 2.0, 1946: 2.0, 1947: 2.0, 1948: 2.0, 1949: 1.4, 1950: 1.4, 1951: 1.4, 1952: 1.4,
                        1953: 1.4,
                        1954: 1.4, 1955: 1.4, 1956: 1.4, 1957: 1.4, 1958: 1.4, 1959: 1.4, 1960: 1.4, 1961: 1.4,
                        1962: 1.4,
                        1963: 1.4, 1964: 1.4, 1965: 1.4, 1966: 1.4, 1967: 1.4, 1968: 1.4, 1969: 0.6, 1970: 0.6,
                        1971: 0.6,
                        1972: 0.6, 1973: 0.6, 1974: 0.6, 1975: 0.6, 1976: 0.6, 1977: 0.6, 1978: 0.6, 1979: 0.5,
                        1980: 0.5,
                        1981: 0.5, 1982: 0.5, 1983: 0.5, 1984: 0.4, 1985: 0.4, 1986: 0.4, 1987: 0.4, 1988: 0.4,
                        1989: 0.4,
                        1990: 0.4, 1991: 0.4, 1992: 0.4, 1993: 0.4, 1994: 0.4, 1995: 0.4
                    }},
                "ENEV Außenwand": {
                    2009: 0.28, 2014: 0.28, 2016: 0.21
                },
                "ENEV Innenwand": {
                    2009: 0, 2014: 0, 2016: 0
                }
            },
            "Decke": {
                "Decke über Außenbereich": {
                    "Massiv": {
                        1918: 2.1, 1919: 2.1, 1920: 2.1, 1921: 2.1, 1922: 2.1, 1923: 2.1, 1924: 2.1, 1925: 2.1,
                        1926: 2.1,
                        1927: 2.1, 1928: 2.1, 1929: 2.1, 1930: 2.1, 1931: 2.1, 1932: 2.1, 1933: 2.1, 1934: 2.1,
                        1935: 2.1,
                        1936: 2.1, 1937: 2.1, 1938: 2.1, 1939: 2.1, 1940: 2.1, 1941: 2.1, 1942: 2.1, 1943: 2.1,
                        1944: 2.1,
                        1945: 2.1, 1946: 2.1, 1947: 2.1, 1948: 2.1, 1949: 2.1, 1950: 2.1, 1951: 2.1, 1952: 2.1,
                        1953: 2.1,
                        1954: 2.1, 1955: 2.1, 1956: 2.1, 1957: 2.1, 1958: 2.1, 1959: 2.1, 1960: 2.1, 1961: 2.1,
                        1962: 2.1,
                        1963: 2.1, 1964: 2.1, 1965: 2.1, 1966: 2.1, 1967: 2.1, 1968: 2.1, 1969: 0.6, 1970: 0.6,
                        1971: 0.6,
                        1972: 0.6, 1973: 0.6, 1974: 0.6, 1975: 0.6, 1976: 0.6, 1977: 0.6, 1978: 0.6, 1979: 0.5,
                        1980: 0.5,
                        1981: 0.5, 1982: 0.5, 1983: 0.5, 1984: 0.4, 1985: 0.4, 1986: 0.4, 1987: 0.4, 1988: 0.4,
                        1989: 0.4,
                        1990: 0.4, 1991: 0.4, 1992: 0.4, 1993: 0.4, 1994: 0.4, 1995: 0.3
                    },
                    "Holzbalkendecke": {
                        1918: 1.0, 1919: 0.8, 1920: 0.8, 1921: 0.8, 1922: 0.8, 1923: 0.8, 1924: 0.8, 1925: 0.8,
                        1926: 0.8,
                        1927: 0.8, 1928: 0.8, 1929: 0.8, 1930: 0.8, 1931: 0.8, 1932: 0.8, 1933: 0.8, 1934: 0.8,
                        1935: 0.8,
                        1936: 0.8, 1937: 0.8, 1938: 0.8, 1939: 0.8, 1940: 0.8, 1941: 0.8, 1942: 0.8, 1943: 0.8,
                        1944: 0.8,
                        1945: 0.8, 1946: 0.8, 1947: 0.8, 1948: 0.8, 1949: 0.8, 1950: 0.8, 1951: 0.8, 1952: 0.8,
                        1953: 0.8,
                        1954: 0.8, 1955: 0.8, 1956: 0.8, 1957: 0.8, 1958: 0.8, 1959: 0.8, 1960: 0.8, 1961: 0.8,
                        1962: 0.8,
                        1963: 0.8, 1964: 0.8, 1965: 0.8, 1966: 0.8, 1967: 0.8, 1968: 0.8, 1969: 0.6, 1970: 0.6,
                        1971: 0.6,
                        1972: 0.6, 1973: 0.6, 1974: 0.6, 1975: 0.6, 1976: 0.6, 1977: 0.6, 1978: 0.6, 1979: 0.4,
                        1980: 0.4,
                        1981: 0.4, 1982: 0.4, 1983: 0.4, 1984: 0.3, 1985: 0.3, 1986: 0.3, 1987: 0.3, 1988: 0.3,
                        1989: 0.3,
                        1990: 0.3, 1991: 0.3, 1992: 0.3, 1993: 0.3, 1994: 0.3, 1995: 0.3
                    },
                    "ENEV": {
                        2009: 0.24, 2014: 0.20, 2016: 0.15
                    }
                },
                "unbeheiztes Geschoss": {
                    "Massiv": {
                        1918: 1.7, 1919: 1.7, 1920: 1.7, 1921: 1.7, 1922: 1.7, 1923: 1.7, 1924: 1.7, 1925: 1.7,
                        1926: 1.7,
                        1927: 1.7, 1928: 1.7, 1929: 1.7, 1930: 1.7, 1931: 1.7, 1932: 1.7, 1933: 1.7, 1934: 1.7,
                        1935: 1.7,
                        1936: 1.7, 1937: 1.7, 1938: 1.7, 1939: 1.7, 1940: 1.7, 1941: 1.7, 1942: 1.7, 1943: 1.7,
                        1944: 1.7,
                        1945: 1.7, 1946: 1.7, 1947: 1.7, 1948: 1.7, 1949: 1.4, 1950: 1.4, 1951: 1.4, 1952: 1.4,
                        1953: 1.4,
                        1954: 1.4, 1955: 1.4, 1956: 1.4, 1957: 1.4, 1958: 1.4, 1959: 1.4, 1960: 1.4, 1961: 1.4,
                        1962: 1.4,
                        1963: 1.4, 1964: 1.4, 1965: 1.4, 1966: 1.4, 1967: 1.4, 1968: 1.4, 1969: 1.0, 1970: 1.0,
                        1971: 1.0,
                        1972: 1.0, 1973: 1.0, 1974: 1.0, 1975: 1.0, 1976: 1.0, 1977: 1.0, 1978: 1.0, 1979: 0.8,
                        1980: 0.8,
                        1981: 0.8, 1982: 0.8, 1983: 0.8, 1984: 0.6, 1985: 0.6, 1986: 0.6, 1987: 0.6, 1988: 0.6,
                        1989: 0.6,
                        1990: 0.6, 1991: 0.6, 1992: 0.6, 1993: 0.6, 1994: 0.6, 1995: 0.5
                    },
                    "Holzbalkendecke": {
                        1918: 2.0, 1919: 2.0, 1920: 2.0, 1921: 2.0, 1922: 2.0, 1923: 2.0, 1924: 2.0, 1925: 2.0,
                        1926: 2.0,
                        1927: 2.0, 1928: 2.0, 1929: 2.0, 1930: 2.0, 1931: 2.0, 1932: 2.0, 1933: 2.0, 1934: 2.0,
                        1935: 2.0,
                        1936: 2.0, 1937: 2.0, 1938: 2.0, 1939: 2.0, 1940: 2.0, 1941: 2.0, 1942: 2.0, 1943: 2.0,
                        1944: 2.0,
                        1945: 2.0, 1946: 2.0, 1947: 2.0, 1948: 2.0, 1949: 1.4, 1950: 1.4, 1951: 1.4, 1952: 1.4,
                        1953: 1.4,
                        1954: 1.4, 1955: 1.4, 1956: 1.4, 1957: 1.4, 1958: 1.4, 1959: 1.4, 1960: 1.4, 1961: 1.4,
                        1962: 1.4,
                        1963: 1.4, 1964: 1.4, 1965: 1.4, 1966: 1.4, 1967: 1.4, 1968: 1.4, 1969: 0.6, 1970: 0.6,
                        1971: 0.6,
                        1972: 0.6, 1973: 0.6, 1974: 0.6, 1975: 0.6, 1976: 0.6, 1977: 0.6, 1978: 0.6, 1979: 0.5,
                        1980: 0.5,
                        1981: 0.5, 1982: 0.5, 1983: 0.5, 1984: 0.4, 1985: 0.4, 1986: 0.4, 1987: 0.4, 1988: 0.4,
                        1989: 0.4,
                        1990: 0.4, 1991: 0.4, 1992: 0.4, 1993: 0.4, 1994: 0.4, 1995: 0.4
                    }
                },
                "ENEV unbeheiztes Geschoss": {
                    2009: 0.35, 2014: 0.35, 2016: 0.26
                },
                "ENEV beheiztes Geschoss": {
                    2009: 0, 2014: 0, 2016: 0
                },
                "ENEV Dach": {
                    2009: 0.24, 2014: 0.20, 2016: 0.15
                }
            },
            "Boden": {
                "gegen Erdreich": {
                    "Massivbauweise": {
                        1918: 1.7, 1919: 1.7, 1920: 1.7, 1921: 1.7, 1922: 1.7, 1923: 1.7, 1924: 1.7, 1925: 1.7,
                        1926: 1.7,
                        1927: 1.7, 1928: 1.7, 1929: 1.7, 1930: 1.7, 1931: 1.7, 1932: 1.7, 1933: 1.7, 1934: 1.7,
                        1935: 1.7,
                        1936: 1.7, 1937: 1.7, 1938: 1.7, 1939: 1.7, 1940: 1.7, 1941: 1.7, 1942: 1.7, 1943: 1.7,
                        1944: 1.7,
                        1945: 1.7, 1946: 1.7, 1947: 1.7, 1948: 1.7, 1949: 1.4, 1950: 1.4, 1951: 1.4, 1952: 1.4,
                        1953: 1.4,
                        1954: 1.4, 1955: 1.4, 1956: 1.4, 1957: 1.4, 1958: 1.4, 1959: 1.4, 1960: 1.4, 1961: 1.4,
                        1962: 1.4,
                        1963: 1.4, 1964: 1.4, 1965: 1.4, 1966: 1.4, 1967: 1.4, 1968: 1.4, 1969: 1.0, 1970: 1.0,
                        1971: 1.0,
                        1972: 1.0, 1973: 1.0, 1974: 1.0, 1975: 1.0, 1976: 1.0, 1977: 1.0, 1978: 1.0, 1979: 0.8,
                        1980: 0.8,
                        1981: 0.8, 1982: 0.8, 1983: 0.8, 1984: 0.6, 1985: 0.6, 1986: 0.6, 1987: 0.6, 1988: 0.6,
                        1989: 0.6,
                        1990: 0.6, 1991: 0.6, 1992: 0.6, 1993: 0.6, 1994: 0.6, 1995: 0.5
                    },
                    "Holzkonstruktion": {
                        1918: 2.0, 1919: 2.0, 1920: 2.0, 1921: 2.0, 1922: 2.0, 1923: 2.0, 1924: 2.0, 1925: 2.0,
                        1926: 2.0,
                        1927: 2.0, 1928: 2.0, 1929: 2.0, 1930: 2.0, 1931: 2.0, 1932: 2.0, 1933: 2.0, 1934: 2.0,
                        1935: 2.0,
                        1936: 2.0, 1937: 2.0, 1938: 2.0, 1939: 2.0, 1940: 2.0, 1941: 2.0, 1942: 2.0, 1943: 2.0,
                        1944: 2.0,
                        1945: 2.0, 1946: 2.0, 1947: 2.0, 1948: 2.0, 1949: 1.4, 1950: 1.4, 1951: 1.4, 1952: 1.4,
                        1953: 1.4,
                        1954: 1.4, 1955: 1.4, 1956: 1.4, 1957: 1.4, 1958: 1.4, 1959: 1.4, 1960: 1.4, 1961: 1.4,
                        1962: 1.4,
                        1963: 1.4, 1964: 1.4, 1965: 1.4, 1966: 1.4, 1967: 1.4, 1968: 1.4, 1969: 0.6, 1970: 0.6,
                        1971: 0.6,
                        1972: 0.6, 1973: 0.6, 1974: 0.6, 1975: 0.6, 1976: 0.6, 1977: 0.6, 1978: 0.6, 1979: 0.5,
                        1980: 0.5,
                        1981: 0.5, 1982: 0.5, 1983: 0.5, 1984: 0.4, 1985: 0.4, 1986: 0.4, 1987: 0.4, 1988: 0.4,
                        1989: 0.4,
                        1990: 0.4, 1991: 0.4, 1992: 0.4, 1993: 0.4, 1994: 0.4, 1995: 0.4
                    }
                },
                "unbeheiztes Geschoss": {
                    "Massivbauweise": {
                        1918: 1.7, 1919: 1.7, 1920: 1.7, 1921: 1.7, 1922: 1.7, 1923: 1.7, 1924: 1.7, 1925: 1.7,
                        1926: 1.7,
                        1927: 1.7, 1928: 1.7, 1929: 1.7, 1930: 1.7, 1931: 1.7, 1932: 1.7, 1933: 1.7, 1934: 1.7,
                        1935: 1.7,
                        1936: 1.7, 1937: 1.7, 1938: 1.7, 1939: 1.7, 1940: 1.7, 1941: 1.7, 1942: 1.7, 1943: 1.7,
                        1944: 1.7,
                        1945: 1.7, 1946: 1.7, 1947: 1.7, 1948: 1.7, 1949: 1.4, 1950: 1.4, 1951: 1.4, 1952: 1.4,
                        1953: 1.4,
                        1954: 1.4, 1955: 1.4, 1956: 1.4, 1957: 1.4, 1958: 1.4, 1959: 1.4, 1960: 1.4, 1961: 1.4,
                        1962: 1.4,
                        1963: 1.4, 1964: 1.4, 1965: 1.4, 1966: 1.4, 1967: 1.4, 1968: 1.4, 1969: 1.0, 1970: 1.0,
                        1971: 1.0,
                        1972: 1.0, 1973: 1.0, 1974: 1.0, 1975: 1.0, 1976: 1.0, 1977: 1.0, 1978: 1.0, 1979: 0.8,
                        1980: 0.8,
                        1981: 0.8, 1982: 0.8, 1983: 0.8, 1984: 0.6, 1985: 0.6, 1986: 0.6, 1987: 0.6, 1988: 0.6,
                        1989: 0.6,
                        1990: 0.6, 1991: 0.6, 1992: 0.6, 1993: 0.6, 1994: 0.6, 1995: 0.5
                    },
                    "Holzkonstruktion": {
                        1918: 2.0, 1919: 2.0, 1920: 2.0, 1921: 2.0, 1922: 2.0, 1923: 2.0, 1924: 2.0, 1925: 2.0,
                        1926: 2.0,
                        1927: 2.0, 1928: 2.0, 1929: 2.0, 1930: 2.0, 1931: 2.0, 1932: 2.0, 1933: 2.0, 1934: 2.0,
                        1935: 2.0,
                        1936: 2.0, 1937: 2.0, 1938: 2.0, 1939: 2.0, 1940: 2.0, 1941: 2.0, 1942: 2.0, 1943: 2.0,
                        1944: 2.0,
                        1945: 2.0, 1946: 2.0, 1947: 2.0, 1948: 2.0, 1949: 1.4, 1950: 1.4, 1951: 1.4, 1952: 1.4,
                        1953: 1.4,
                        1954: 1.4, 1955: 1.4, 1956: 1.4, 1957: 1.4, 1958: 1.4, 1959: 1.4, 1960: 1.4, 1961: 1.4,
                        1962: 1.4,
                        1963: 1.4, 1964: 1.4, 1965: 1.4, 1966: 1.4, 1967: 1.4, 1968: 1.4, 1969: 0.6, 1970: 0.6,
                        1971: 0.6,
                        1972: 0.6, 1973: 0.6, 1974: 0.6, 1975: 0.6, 1976: 0.6, 1977: 0.6, 1978: 0.6, 1979: 0.5,
                        1980: 0.5,
                        1981: 0.5, 1982: 0.5, 1983: 0.5, 1984: 0.4, 1985: 0.4, 1986: 0.4, 1987: 0.4, 1988: 0.4,
                        1989: 0.4,
                        1990: 0.4, 1991: 0.4, 1992: 0.4, 1993: 0.4, 1994: 0.4, 1995: 0.4
                    }
                },
                "beheiztes Geschoss": {
                    "Massivbauweise": {
                        1918: 1.7, 1919: 1.7, 1920: 1.7, 1921: 1.7, 1922: 1.7, 1923: 1.7, 1924: 1.7, 1925: 1.7,
                        1926: 1.7,
                        1927: 1.7, 1928: 1.7, 1929: 1.7, 1930: 1.7, 1931: 1.7, 1932: 1.7, 1933: 1.7, 1934: 1.7,
                        1935: 1.7,
                        1936: 1.7, 1937: 1.7, 1938: 1.7, 1939: 1.7, 1940: 1.7, 1941: 1.7, 1942: 1.7, 1943: 1.7,
                        1944: 1.7,
                        1945: 1.7, 1946: 1.7, 1947: 1.7, 1948: 1.7, 1949: 1.4, 1950: 1.4, 1951: 1.4, 1952: 1.4,
                        1953: 1.4,
                        1954: 1.4, 1955: 1.4, 1956: 1.4, 1957: 1.4, 1958: 1.4, 1959: 1.4, 1960: 1.4, 1961: 1.4,
                        1962: 1.4,
                        1963: 1.4, 1964: 1.4, 1965: 1.4, 1966: 1.4, 1967: 1.4, 1968: 1.4, 1969: 1.0, 1970: 1.0,
                        1971: 1.0,
                        1972: 1.0, 1973: 1.0, 1974: 1.0, 1975: 1.0, 1976: 1.0, 1977: 1.0, 1978: 1.0, 1979: 0.8,
                        1980: 0.8,
                        1981: 0.8, 1982: 0.8, 1983: 0.8, 1984: 0.6, 1985: 0.6, 1986: 0.6, 1987: 0.6, 1988: 0.6,
                        1989: 0.6,
                        1990: 0.6, 1991: 0.6, 1992: 0.6, 1993: 0.6, 1994: 0.6, 1995: 0.5
                    },
                    "Holzkonstruktion": {
                        1918: 2.0, 1919: 2.0, 1920: 2.0, 1921: 2.0, 1922: 2.0, 1923: 2.0, 1924: 2.0, 1925: 2.0,
                        1926: 2.0,
                        1927: 2.0, 1928: 2.0, 1929: 2.0, 1930: 2.0, 1931: 2.0, 1932: 2.0, 1933: 2.0, 1934: 2.0,
                        1935: 2.0,
                        1936: 2.0, 1937: 2.0, 1938: 2.0, 1939: 2.0, 1940: 2.0, 1941: 2.0, 1942: 2.0, 1943: 2.0,
                        1944: 2.0,
                        1945: 2.0, 1946: 2.0, 1947: 2.0, 1948: 2.0, 1949: 1.4, 1950: 1.4, 1951: 1.4, 1952: 1.4,
                        1953: 1.4,
                        1954: 1.4, 1955: 1.4, 1956: 1.4, 1957: 1.4, 1958: 1.4, 1959: 1.4, 1960: 1.4, 1961: 1.4,
                        1962: 1.4,
                        1963: 1.4, 1964: 1.4, 1965: 1.4, 1966: 1.4, 1967: 1.4, 1968: 1.4, 1969: 0.6, 1970: 0.6,
                        1971: 0.6,
                        1972: 0.6, 1973: 0.6, 1974: 0.6, 1975: 0.6, 1976: 0.6, 1977: 0.6, 1978: 0.6, 1979: 0.5,
                        1980: 0.5,
                        1981: 0.5, 1982: 0.5, 1983: 0.5, 1984: 0.4, 1985: 0.4, 1986: 0.4, 1987: 0.4, 1988: 0.4,
                        1989: 0.4,
                        1990: 0.4, 1991: 0.4, 1992: 0.4, 1993: 0.4, 1994: 0.4, 1995: 0.4
                    }
                },
                "ENEV unbeheiztes Geschoss": {
                    2009: 0.35, 2014: 0.35, 2016: 0.26
                },
                "ENEV beheiztes Geschoss": {
                    2009: 0, 2014: 0, 2016: 0
                }
            }
        }

    @staticmethod
    def calc_heating_power(room: Room) -> float:
        """

        :param room:
        :return:
        """

        @lru_cache(maxsize=None)
        def _calc(wall_obj: room.Wall1 | room.Wall2 | room.Wall3 | room.Wall4) -> (float, float, float, float,
                                                                                   float, float):
            """

            :param wall_obj:
            :return:
            """
            wall: float = (
                    (
                            wall_obj.area - wall_obj.Door.area - wall_obj.Window1.area -
                            wall_obj.Window2.area - wall_obj.Window3.area - wall_obj.Window4.area
                    ) * wall_obj.u_wert * wall_obj.temp_diff
            )
            window1: float = 0
            window2: float = 0
            window3: float = 0
            window4: float = 0
            door: float = 0

            try:
                window1: float = wall_obj.Window1.area * wall_obj.Window1.u_wert * wall_obj.temp_diff
            except TypeError:
                pass
            try:
                window2: float = wall_obj.Window2.area * wall_obj.Window2.u_wert * wall_obj.temp_diff
            except TypeError:
                pass
            try:
                window3: float = wall_obj.Window3.area * wall_obj.Window3.u_wert * wall_obj.temp_diff
            except TypeError:
                pass
            try:
                window4: float = wall_obj.Window4.area * wall_obj.Window4.u_wert * wall_obj.temp_diff
            except TypeError:
                pass
            try:
                door: float = wall_obj.Door.area * wall_obj.Door.u_wert * wall_obj.temp_diff
            except TypeError:
                pass

            return wall, window1, window2, window3, window4, door

        wall_1, wall_1_window_1, wall_1_window_2, wall_1_window_3, wall_1_window_4, wall_1_door = _calc(room.Wall1)
        wall_2, wall_2_window_1, wall_2_window_2, wall_2_window_3, wall_2_window_4, wall_2_door = _calc(room.Wall2)
        wall_3, wall_3_window_1, wall_3_window_2, wall_3_window_3, wall_3_window_4, wall_3_door = _calc(room.Wall3)
        wall_4, wall_4_window_1, wall_4_window_2, wall_4_window_3, wall_4_window_4, wall_4_door = _calc(room.Wall4)

        floor: float = room.Floor.area * room.Floor.u_wert * room.Floor.temp_diff

        ceiling: float = room.Ceiling.area * room.Ceiling.u_wert * room.Floor.temp_diff

        heating_power: float = (wall_1 + wall_1_window_1 + wall_1_window_2 + wall_1_window_3 + wall_1_window_4 +
                                wall_1_door +
                                wall_2 + wall_2_window_1 + wall_2_window_2 + wall_2_window_3 + wall_2_window_4 +
                                wall_2_door +
                                wall_3 + wall_3_window_1 + wall_3_window_2 + wall_3_window_3 + wall_3_window_4 +
                                wall_3_door +
                                wall_4 + wall_4_window_1 + wall_4_window_2 + wall_4_window_3 + wall_4_window_4 +
                                wall_4_door +
                                floor + ceiling)

        return heating_power

    @staticmethod
    def adjust_thermal_mass(heizlast: float, v: float, delta_temp: float, time_interval: int,
                            previous_mass_estimate: float, c_air: float = 1005, rho_air: float = 1.225,
                            c_material: float = 840, learning_rate: float = 0.1):

        thermal_mass_air: float = v * rho_air * c_air

        thermal_mass_material: float = previous_mass_estimate

        total_thermal_mass: float = thermal_mass_air + thermal_mass_material

        energy_input: float = heizlast * time_interval

        expected_temp_change: float = energy_input / total_thermal_mass

        error: float = expected_temp_change - delta_temp

        thermal_mass_material_adjusted: float = (thermal_mass_material - learning_rate * error *
                                                 total_thermal_mass / c_material)

        return max(thermal_mass_material_adjusted, 0)


class ShellyTRVControl:
    """

    """

    def __init__(self, ip_address: str) -> None:
        """

        :param ip_address:
        """
        self.ip_address: str = ip_address

    def get_status(self, timeout: int = 5) -> dict | None:
        """

        :param timeout:
        :return:
        """
        url: str = f"http://{self.ip_address}/status"
        try:
            response: requests.models.Response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                data: dict = response.json()
                return data
            return None
        except (requests.exceptions.ConnectTimeout, OSError) as exceptions:
            print("No Shelly TRV reached")
            debug.printer(exceptions)
            return None

    def get_settings(self, timeout: int = 8) -> dict | None:
        """

        :param timeout:
        :return:
        """
        url: str = f"http://{self.ip_address}/settings"
        try:
            response: requests.models.Response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                data: dict = response.json()
                return data
            return None
        except (requests.exceptions.ConnectTimeout, OSError) as exceptions:
            print("No Shelly TRV reached")
            debug.printer(exceptions)
            return None

    def get_thermostat(self, timeout: int = 5) -> dict | None:
        """

        :param timeout:
        :return:
        """
        url: str = f"http://{self.ip_address}/thermostats/0"
        try:
            response: requests.models.Response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                data: dict = response.json()
                return data
            return None
        except (requests.exceptions.ConnectTimeout, OSError) as exceptions:
            print("No Shelly TRV reached")
            debug.printer(exceptions)
            return None

    def set_valve_pos(self, position: int, timeout: int = 5) -> bool:
        """

        :param position:
        :param timeout:
        :return:
        """
        url: str = f"http://{self.ip_address}/thermostat/0?pos={position}"
        try:
            response: requests.models.Response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                data: dict = response.json()
                if data["pos"] == position:
                    return True
            return False
        except (requests.exceptions.ConnectTimeout, OSError) as exceptions:
            print("No Shelly TRV reached")
            debug.printer(exceptions)
            return False

    def set_temperature(self, temperature: float, timeout: int = 5) -> bool:
        """

        :param temperature:
        :param timeout:
        :return:
        """
        url: str = f"http://{self.ip_address}/thermostat/0?target_t_enabled=1&target_t={temperature}"
        try:
            response: requests.models.Response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                data: dict = response.json()
                if data["target_t"]["value"] == temperature:
                    return True
            return False
        except (requests.exceptions.ConnectTimeout, OSError) as exceptions:
            print("No Shelly TRV reached")
            debug.printer(exceptions)
            return False

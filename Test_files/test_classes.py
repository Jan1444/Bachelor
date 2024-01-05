# -*- coding: utf-8 -*-
import classes
import datetime
import matplotlib.pyplot as plt
import numpy as np

time_data: list = []
azimuth_data: list = []
elevation_data: list = []

for day in range(1, 2, 1):
    # date = (datetime.datetime.now().date() + datetime.timedelta(days=day)).strftime("%d-%m-%Y")
    date = datetime.date(2024, 7, 21).strftime("%d-%m-%Y")
    sun = classes.CalcSunPos(52.5, 13.4, date)
    for hour in range(0, 25, 1):
        for minute in range(0, 60, 15):
            az = sun.calc_azimuth((hour + minute / 100))
            ele = sun.calc_solar_elevation((hour + minute / 100))
            time_data.append(f"{str(hour).zfill(2)}:{str(minute).zfill(2)}")
            azimuth_data.append(az)
            elevation_data.append(ele)

font1 = {'family': 'Times New Roman', 'size': 20}

plt.figure(figsize=(35, 15))
plt.grid(which="both")
# plt.minorticks_on()
# plt.plot(azimuth_data, elevation_data, linewidth=3)
plt.plot(time_data, elevation_data, linewidth=3)
plt.xticks(rotation=90, fontsize=14)
# plt.xticks(rotation=90, fontsize=14, ticks=[0, 45, 90, 135, 180, 225, 270, 315, 360])
plt.yticks(fontsize=14)
# plt.yticks(fontsize=14, ticks=[-20, -10, 0, 10, 20, 30, 40, 50, 60, 70])
plt.xlabel("Uhrzeit", fontdict=font1)
# plt.xlabel("Azimuth [°]", fontdict=font1)
plt.ylabel("Sonnenhöhe [°]", fontdict=font1)
plt.title("Verlauf der Sonne in Berlin am 21.07.2024 (Längengrad = 52,5°, Breitengrad = 13,4°)", fontdict=font1)

plt.show()

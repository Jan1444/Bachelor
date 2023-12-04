import time

import pandas as pd

import classes
from config import settings as consts


def init_classes(latitude: float, longitude: float, module_efficiency: float, module_area: int, tilt_angle: float,
                 exposure_angle: float, mounting_type: int, costs: float) -> (object, object, object, object):
    weather = classes.Weather(latitude, longitude)
    market = classes.MarketData(costs)
    sun = classes.CalcSunPos(latitude, longitude)
    pv = classes.PVProfit(module_efficiency, module_area, tilt_angle, exposure_angle, -0.35, 25, mounting_type)
    return weather, market, sun, pv


def to_excel(w, col, path_):
    df = pd.DataFrame.from_dict(w.data[list(w.data.keys())[0]])
    df = df.iloc[6]
    with pd.ExcelWriter(path_, mode='a', if_sheet_exists="overlay") as wr:
        df.to_excel(wr, index=True, startrow=1, startcol=col)


def main(count, path_):
    w, m, sun, pv = init_classes(consts["coordinates"]["latitude"], consts["coordinates"]["longitude"],
                                 consts["pv"]["module_efficiency"], consts["pv"]["area"],
                                 consts["pv"]["tilt_angle"], consts["pv"]["exposure_angle"],
                                 consts["pv"]["mounting_type"], consts["market"]["consumer_price"])
    w._expire_time = 0
    to_excel(w, count, path_)


if __name__ == "__main__":
    i = 0
    path = r'/Users/jan/Documents/Weiterbildung/Bachelor/7. Semester/Bachelorarbeit/SolarDaten/2023_11_21_data.xlsx'
    while True:
        main(i, path)
        i += 2
        print("i = ", i)
        minute = 15
        for t in range(0, minute, 1):
            print("verbleibende minuten: ", minute - t)
            time.sleep(60)

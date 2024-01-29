#  -*- coding: utf-8 -*-

from module import debug


def prepare_data_to_write(time, power: list[float], market_price: list[float], energy: float,
                          radiation: None | list[float] = None, radiation_dni: None | list[float] = None) -> dict:
    data: dict = {
        "write_time": {
            "time": datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
            "format": "%d-%m-%Y %H:%M:%S"
        },
        "energy": {
            "energy": energy
        }
    }
    # write radiation
    try:
        if radiation is not None:
            h = -1
            for i, k in enumerate(time):
                if k != "daily":
                    data.update({
                        k: {
                            "direct_radiation": radiation[i],
                            "power": round(power[i], 3),
                            "market_price": market_price[h]
                        }
                    })

                if (i - 4) % 4 == 0:
                    h += 1

            return data

    except KeyError as error:
        print(f"Key {error} is not a valid")
        return -1

    except IndexError as error:
        print(f"List is to short or long, need same length as time\n"
              f"len(time) -> {len(time)}\n"
              f"len(radiation) -> {len(radiation)}, {'✅' if len(radiation) == len(time) else '❌'}\n"
              f"len(power) -> {len(power)}, {'✅' if len(power) == len(time) else '❌'}\n"
              f"len(market_price) -> {len(market_price)}, {'✅' if len(market_price) * 4 + 1 == len(time) else '❌'}\n"
              f"{error}")
        return -1

    # write radiation_dni
    try:
        if radiation_dni:
            h = -1
            for i, k in enumerate(time):
                if k != "daily":
                    data.update({
                        k: {"dni_radiation": radiation_dni[i],
                            "power": round(power[i], 3),
                            "market_price": market_price[h]
                            }
                    })

                if (i - 4) % 4 == 0:
                    h += 1

            return data

    except KeyError as error:
        print(f"Key {error} is not a valid")
        return -1

    except IndexError as error:
        print(f"List is to short or long, need same length as time\n"
              f"len(time) -> {len(time)}\n"
              f"len(radiation_dni) -> {len(radiation_dni)}, {'✅' if len(radiation_dni) == len(time) else '❌'}\n"
              f"len(power) -> {len(power)}, {'✅' if len(power) == len(time) else '❌'}\n"
              f"len(market_price) -> {len(market_price)}, {'✅' if len(market_price) == len(time) else '❌'}\n"
              f"{error}")
        return -1

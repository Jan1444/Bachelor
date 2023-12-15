import tomli
import tomli_w
from pprint import pprint
import debug
import json
import datetime


def load_write_config(data: dict | None = None, path: str | None = None) -> dict | None:
    if path is None:
        path = 'config/config_test.toml'
    if data:
        tomli_w.dump(config, open(path, "wb"))
    else:
        debug.printer("opened config file")
        return tomli.load(open(path, "rb"))


if __name__ == '__main__':
    # 'https://re.jrc.ec.europa.eu/pvg_tools/en/#api_5.2'
    path = r"/Users/jan/Downloads/Timeseries_49.520_11.295_SA2_0deg_0deg_2005_2020.json"
    data = json.load(open(path, "rb+"))
    print(data["inputs"].keys())

    for element in (data["outputs"]["hourly"]):
        print(datetime.datetime.strptime(element["time"], "%Y%m%d:%H%M").strftime("%H:%M - %d.%m.%Y"))
        print("radiation: ", element["Gb(i)"])

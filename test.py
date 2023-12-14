import tomli
import tomli_w
from pprint import pprint
import debug


def load_write_config(data: dict | None = None, path: str | None = None) -> dict | None:
    if path is None:
        path = 'config/config_test.toml'
    if data:
        tomli_w.dump(config, open(path, "wb"))
    else:
        debug.printer("opened config file")
        return tomli.load(open(path, "rb"))


if __name__ == '__main__':

    config = load_write_config()
    pprint(config)

    config["trv"].update({"ip": "192.168.178.xxx"})
    config["trv"].update({"test": "zzz"})

    pprint(config)
    load_write_config(config)
    # tomli_w.dump(config, open(path, "wb"))

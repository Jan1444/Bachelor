import tomli
import tomli_w


def safe_settings():
    # Pfad zur TOML-Datei
    toml_file_path = 'config/config_test.toml'

    # Formulardaten empfangen
    data = {
        'latitude': 50,
        'longitude': 50,
        'tilt_angle': 50,
        'area': 50,
        'module_efficiency': 50,
        'exposure_angle': 50,
        'temperature_coefficient': 50,
        'nominal_temperature': 50,
        'mounting_type': 50,
        'consumer_price': 50
    }

    # TOML-Datei lesen, aktualisieren und zurückschreiben
    with open(toml_file_path, 'rb') as f:
        config_data = tomli.load(f)

    # Aktualisieren Sie hier die Konfigurationsdaten mit den Formulardaten
    # Beispiel:

    config_data['coordinates']['latitude'] = float(data['latitude'])
    config_data['coordinates']['longitude'] = float(data['longitude'])
    config_data['pv']['tilt_angle'] = float(data['tilt_angle'])
    config_data['pv']['area'] = float(data['area'])
    config_data['pv']['module_efficiency'] = float(data['module_efficiency'])
    config_data['pv']['exposure_angle'] = float(data['exposure_angle'])
    # config_data['pv']['temperature_coefficient'] = float(data['temperature_coefficient'])
    config_data['pv']['nominal_temperature'] = float(data['nominal_temperature'])
    config_data['pv']['mounting_type'] = int(data['mounting_type'])
    config_data['market']['consumer_price'] = float(data['consumer_price'])
    # ... und so weiter für andere Felder

    # TOML-Datei mit aktualisierten Daten schreiben
    with open(toml_file_path, 'wb') as f:
        tomli_w.dump(config_data, f)


if __name__ == '__main__':
    safe_settings()

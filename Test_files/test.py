import subprocess
import getpass


def get_network_services():
    result = subprocess.run(["networksetup", "-listallnetworkservices"], capture_output=True, text=True)
    services = result.stdout.split('\n')
    return [service for service in services if service]


def set_service_order(services):
    # Konvertiert die Liste der Dienste in einen einzigen String
    services_str = ' '.join(f'"{service}"' for service in services)
    command_ = f"networksetup -ordernetworkservices {services_str}"
    return command_


def run_command_with_sudo(password, command):
    try:
        # Der Befehl ist jetzt ein einzelner String
        sudo_command = f"echo {password} | sudo -S {command}"
        subprocess.run(sudo_command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Ein Fehler ist aufgetreten: {e}")



ethernet = ["USB 10/100/1000 LAN", "USB 10/100/1000 LAN 2", "USB 10/100/1000 LAN 3", "Thunderbolt Bridge", "Wi-Fi",
            "iPad USB", "iPhone USB"]
wifi = ["Wi-Fi", "USB 10/100/1000 LAN", "USB 10/100/1000 LAN 2", "USB 10/100/1000 LAN 3", "Thunderbolt Bridge",
        "iPad USB", "iPhone USB"]

# Passwort zur Laufzeit abfragen
sudo_password = getpass.getpass("Bitte geben Sie Ihr Sudo-Passwort ein: ")
command = set_service_order(wifi)

run_command_with_sudo(sudo_password, command)

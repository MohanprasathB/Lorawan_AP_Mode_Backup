from gpiozero import Button
from gpiozero.pins.lgpio import LGPIOFactory
import subprocess
import time

BUTTON_GPIO = 27
HOLD_SECONDS = 3

AP_CONNECTION = "sarayu-ap"
NETWORK_SERVICE = "sarayu-network.service"


def run(cmd):

    print("CMD:", " ".join(cmd))

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    if result.stdout:
        print(result.stdout.strip())

    if result.stderr:
        print(result.stderr.strip())

    return result


def enter_setup_mode():

    print("")
    print("======================================")
    print("GPIO TRIGGERED")
    print("ENTERING NETWORK SETUP MODE")
    print("======================================")

    # IMPORTANT:
    # Stop the boot network service first.
    # This prevents network.json retry logic from fighting the AP.
    print("Stopping Sarayu network service...")

    result = run([
        "systemctl",
        "stop",
        NETWORK_SERVICE
    ])

    if result.returncode != 0:
        print("Warning: failed to stop network service")

    time.sleep(1)

    # Disconnect Ethernet
    print("Disconnecting Ethernet...")

    run([
        "nmcli",
        "device",
        "disconnect",
        "eth0"
    ])

    # Disconnect Wi-Fi client
    print("Disconnecting Wi-Fi...")

    run([
        "nmcli",
        "device",
        "disconnect",
        "wlan0"
    ])

    time.sleep(1)

    # Start setup AP
    print("Starting Sarayu AP...")

    result = run([
        "nmcli",
        "connection",
        "up",
        AP_CONNECTION
    ])

    if result.returncode == 0:

        print("")
        print("======================================")
        print("NETWORK SETUP MODE ACTIVE")
        print("SSID : SARAYU-GATEWAY")
        print("IP   : 192.168.4.1")
        print("URL  : http://192.168.4.1")
        print("======================================")

    else:

        print("Failed to start AP")
        print(result.stderr)


button = Button(
    BUTTON_GPIO,
    pull_up=True,
    hold_time=HOLD_SECONDS,
    bounce_time=0.05,
    pin_factory=LGPIOFactory()
)

button.when_held = enter_setup_mode


print("======================================")
print("Sarayu Gateway Button Monitor")
print("GPIO      : 27")
print("Hold time : 3 seconds")
print("======================================")


try:

    while True:
        time.sleep(1)

except KeyboardInterrupt:

    pass

finally:

    button.close()

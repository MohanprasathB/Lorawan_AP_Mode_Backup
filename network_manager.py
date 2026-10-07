#!/usr/bin/env python3

import json
import os
import subprocess
import time
import ipaddress

CONFIG_FILE = "/etc/sarayu-gateway/network.json"
BACKUP_FILE = "/etc/sarayu-gateway/network_backup.json"

AP_CONNECTION = "sarayu-ap"

WIFI_CONNECTION = "sarayu-wifi"
ETH_CONNECTION = "sarayu-ethernet"


def run_cmd(cmd):
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


def load_config(path=CONFIG_FILE):
    with open(path, "r") as f:
        return json.load(f)


def save_config(config, path=CONFIG_FILE):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    tmp = path + ".tmp"

    with open(tmp, "w") as f:
        json.dump(config, f, indent=2)

    os.replace(tmp, path)

    os.chmod(path, 0o600)


def backup_current_config():
    if os.path.exists(CONFIG_FILE):
        config = load_config()
        save_config(config, BACKUP_FILE)
        print("Network configuration backed up")


def restore_backup():
    if not os.path.exists(BACKUP_FILE):
        print("No backup configuration found")
        return False

    config = load_config(BACKUP_FILE)
    save_config(config, CONFIG_FILE)

    print("Previous configuration restored")
    return True


def netmask_to_prefix(netmask):
    return ipaddress.IPv4Network(
        "0.0.0.0/" + netmask
    ).prefixlen


def stop_ap():
    run_cmd([
        "nmcli",
        "connection",
        "down",
        AP_CONNECTION
    ])


def start_ap():
    print("Starting setup AP")

    result = run_cmd([
        "nmcli",
        "connection",
        "up",
        AP_CONNECTION
    ])

    return result.returncode == 0


def disconnect_interfaces():
    print("Disconnecting current network connections")

    run_cmd([
        "nmcli",
        "device",
        "disconnect",
        "eth0"
    ])

    run_cmd([
        "nmcli",
        "device",
        "disconnect",
        "wlan0"
    ])

    time.sleep(1)


def delete_old_profiles():
    run_cmd([
        "nmcli",
        "connection",
        "delete",
        WIFI_CONNECTION
    ])

    run_cmd([
        "nmcli",
        "connection",
        "delete",
        ETH_CONNECTION
    ])


def configure_wifi(wifi, metric=100):
    ssid = wifi.get("ssid", "").strip()
    security = wifi.get("security", "closed")
    password = wifi.get("password", "")

    if not ssid:
        raise ValueError("Wi-Fi SSID is empty")

    print("Configuring Wi-Fi:", ssid)

    # Remove previous profile
    run_cmd([
        "nmcli",
        "connection",
        "delete",
        WIFI_CONNECTION
    ])

    if security == "open":

        result = run_cmd([
            "nmcli",
            "connection",
            "add",
            "type",
            "wifi",
            "ifname",
            "wlan0",
            "con-name",
            WIFI_CONNECTION,
            "ssid",
            ssid
        ])

    else:

        if len(password) < 8:
            raise ValueError(
                "Wi-Fi password must contain at least 8 characters"
            )

        result = run_cmd([
            "nmcli",
            "connection",
            "add",
            "type",
            "wifi",
            "ifname",
            "wlan0",
            "con-name",
            WIFI_CONNECTION,
            "ssid",
            ssid
        ])

        if result.returncode != 0:
            raise RuntimeError(
                "Failed to create Wi-Fi connection"
            )

        result = run_cmd([
            "nmcli",
            "connection",
            "modify",
            WIFI_CONNECTION,
            "wifi-sec.key-mgmt",
            "wpa-psk",
            "wifi-sec.psk",
            password
        ])

    if result.returncode != 0:
        raise RuntimeError(
            "Failed to configure Wi-Fi"
        )

    run_cmd([
        "nmcli",
        "connection",
        "modify",
        WIFI_CONNECTION,
        "ipv4.method",
        "auto",
        "ipv4.route-metric",
        str(metric),
        "ipv6.method",
        "disabled",
        "connection.autoconnect",
        "no"
    ])


def configure_ethernet(ethernet, metric=200):
    ip_mode = ethernet.get("ip_mode", "dhcp")

    print("Configuring Ethernet:", ip_mode)

    run_cmd([
        "nmcli",
        "connection",
        "delete",
        ETH_CONNECTION
    ])

    result = run_cmd([
        "nmcli",
        "connection",
        "add",
        "type",
        "ethernet",
        "ifname",
        "eth0",
        "con-name",
        ETH_CONNECTION
    ])

    if result.returncode != 0:
        raise RuntimeError(
            "Failed to create Ethernet connection"
        )

    if ip_mode == "dhcp":

        run_cmd([
            "nmcli",
            "connection",
            "modify",
            ETH_CONNECTION,
            "ipv4.method",
            "auto",
            "ipv4.route-metric",
            str(metric),
            "ipv6.method",
            "disabled",
            "connection.autoconnect",
            "no"
        ])

    else:

        ip = ethernet.get("ip", "")
        netmask = ethernet.get("netmask", "")
        gateway = ethernet.get("gateway", "")
        dns = ethernet.get("dns", "")

        if not ip or not netmask or not gateway:
            raise ValueError(
                "Static Ethernet fields are incomplete"
            )

        prefix = netmask_to_prefix(netmask)

        address = f"{ip}/{prefix}"

        run_cmd([
            "nmcli",
            "connection",
            "modify",
            ETH_CONNECTION,
            "ipv4.method",
            "manual",
            "ipv4.addresses",
            address,
            "ipv4.gateway",
            gateway,
            "ipv4.dns",
            dns,
            "ipv4.route-metric",
            str(metric),
            "ipv6.method",
            "disabled",
            "connection.autoconnect",
            "no"
        ])


def apply_config(config):
    mode = config.get("mode")

    print("======================================")
    print("Applying network configuration")
    print("Mode:", mode)
    print("======================================")

    # Stop AP first
    stop_ap()

    time.sleep(1)

    # Disconnect everything
    disconnect_interfaces()

    # Remove old product profiles
    delete_old_profiles()

    if mode == "wifi":

        configure_wifi(
            config["wifi"],
            metric=100
        )

        result = run_cmd([
            "nmcli",
            "connection",
            "up",
            WIFI_CONNECTION
        ])

        if result.returncode != 0:
            raise RuntimeError(
                "Failed to connect to Wi-Fi"
            )

    elif mode == "ethernet":

        configure_ethernet(
            config["ethernet"],
            metric=100
        )

        result = run_cmd([
            "nmcli",
            "connection",
            "up",
            ETH_CONNECTION
        ])

        if result.returncode != 0:
            raise RuntimeError(
                "Failed to connect Ethernet"
            )

    elif mode == "both":

        priority = config.get(
            "priority",
            "wifi_first"
        )

        if priority == "wifi_first":
            wifi_metric = 100
            eth_metric = 200
        else:
            wifi_metric = 200
            eth_metric = 100

        configure_wifi(
            config["wifi"],
            metric=wifi_metric
        )

        configure_ethernet(
            config["ethernet"],
            metric=eth_metric
        )

        wifi_result = run_cmd([
            "nmcli",
            "connection",
            "up",
            WIFI_CONNECTION
        ])

        eth_result = run_cmd([
            "nmcli",
            "connection",
            "up",
            ETH_CONNECTION
        ])

        if (
            wifi_result.returncode != 0
            and eth_result.returncode != 0
        ):
            raise RuntimeError(
                "Both Wi-Fi and Ethernet failed"
            )

    else:
        raise ValueError(
            "Invalid network mode"
        )

    time.sleep(3)

    print("Network configuration applied")

    return True


def cancel_setup():
    print("======================================")
    print("Cancelling setup")
    print("Restoring previous configuration")
    print("======================================")

    if not restore_backup():
        return False

    config = load_config()

    try:
        apply_config(config)
        print("Previous network restored")
        return True

    except Exception as e:
        print("Failed to restore network:", e)

        # Try to bring AP back
        start_ap()

        return False


if __name__ == "__main__":

    print("Network manager test")

    config = load_config()

    print(json.dumps(config, indent=2))

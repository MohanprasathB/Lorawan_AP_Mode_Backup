#!/usr/bin/env python3

import sys
import network_manager


def main():
    print("======================================")
    print("Sarayu Gateway Boot Network")
    print("Source: /etc/sarayu-gateway/network.json")
    print("======================================")

    try:
        # IMPORTANT:
        # Only network.json is used here.
        # network_backup.json is NEVER used during boot.
        config = network_manager.load_config()

        print("Loaded active network configuration:")
        print(config)

        network_manager.apply_config(config)

        print("======================================")
        print("BOOT NETWORK CONFIGURATION SUCCESS")
        print("======================================")

        return 0

    except Exception as e:
        print("======================================")
        print("BOOT NETWORK CONFIGURATION FAILED")
        print("ERROR:", e)
        print("systemd will retry...")
        print("======================================")

        return 1


if __name__ == "__main__":
    sys.exit(main())

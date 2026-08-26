# Tasmota Firmware Update for Home Assistant

[![GitHub Release][releases-shield]][releases]
[![License][license-shield]][license]
[![hacs][hacs-shield]][hacs]
[![Maintainability][maintainability-shield]][maintainability]

This custom integration provides firmware update functionality for Tasmota devices in Home Assistant. It works alongside the official Tasmota integration and adds an `update` entity to existing Tasmota devices, mapping them via MAC address.

This custom integration is only needed until [this Pull Request has been merged](https://github.com/emontnemery/hatasmota/pull/389).
More information [are available here](https://github.com/emontnemery/hatasmota/issues/151).

---

## ❤️ Support This Project

> I maintain this integration in my **free time alongside my regular job** — bug hunting, new features, and testing on real hardware. Test devices cost money, and every donation helps me stay independent and free up more time for open-source work.
>
> Donations are completely voluntary — but the more support I receive, the less I depend on other income sources and the more time I can realistically invest into these GitHub projects. 💪

<div align="center">

[![GitHub Sponsors](https://img.shields.io/badge/Sponsor%20on-GitHub-%23EA4AAA?style=for-the-badge&logo=github-sponsors&logoColor=white)](https://github.com/sponsors/FaserF)&nbsp;&nbsp;
[![PayPal](https://img.shields.io/badge/Donate%20via-PayPal-%2300457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/FaserF)

</div>

---
## Features

- **Standard Update Entities**: Adds official Home Assistant `update` entities to your Tasmota devices.
- **Staged Upgrades**: Automatically handles Tasmota's staged upgrade path for older firmware versions.
- **Release Notes**: Fetches and displays release notes from the official Tasmota GitHub repository.
- **Coexistence**: Designed to work perfectly with the official Tasmota integration.

### HACS (Recommended)
[![Downloads (Current release)](https://img.shields.io/github/downloads/FaserF/ha-tasmota-update/latest/tasmota_fwupdate.zip?label=Downloads%20(Current%20release)&style=for-the-badge)](https://github.com/FaserF/ha-tasmota-update/releases)

This integration is fully compatible with [HACS](https://hacs.xyz/).

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=FaserF&repository=ha-tasmota-update&category=integration)

1. Click the button above to add the custom repository to HACS.
2. Search for "Tasmota Firmware Update".
3. Install and restart Home Assistant.

### Manual
1. Download the `tasmota_fwupdate` folder from `custom_components` in this repository.
2. Copy it into your Home Assistant `custom_components` directory.
3. Restart Home Assistant.

## Configuration

1. Go to "Settings" -> "Devices & Services".
2. Click "Add Integration" and search for "Tasmota Firmware Update".
3. Follow the instructions. By default, it uses `tasmota/discovery/` as the MQTT discovery prefix.

## Disclaimer & Best Practices

> [!WARNING]
> **Firmware updates always carry inherent risks!**
> While this integration initiates official Tasmota upgrade commands (`OtaUrl` & `Upgrade 1`), the actual download, partition handling, decompression, and flashing are performed by Tasmota itself directly on the hardware.

- **Hardware & Memory Constraints:** Devices with 1MB flash (such as many ESP8266/ESP8285 smart plugs) perform a multi-step update internally (downloading minimal firmware first before fetching the full binary). Network drops, weak Wi-Fi signal, or low free RAM during this stage can trigger Tasmota's native Safeboot / recovery fallback AP (`tasmota-XXXXXX-XXXX`).
- **Test Before Bulk Updating:** Always test the update process on **one single device** before triggering updates across dozens of devices simultaneously.
- **Integration vs. Firmware Failures:** A failed update, bootloop, or safeboot state on an individual device does **not** automatically indicate a bug in this integration. This integration merely triggers Tasmota's official OTA process over MQTT.
- **Safeboot Recovery:** If a device drops offline and enters Safeboot, it will typically broadcast its own temporary Wi-Fi access point (e.g. `tasmota-XXXXXX-XXXX` at `192.168.4.1`). Connect to it to re-apply Wi-Fi settings or complete the OTA firmware flash.

Use this integration at your own risk.

## License

[MIT License](LICENSE)

[releases-shield]: https://img.shields.io/github/v/release/FaserF/ha-tasmota-update?style=for-the-badge
[releases]: https://github.com/FaserF/ha-tasmota-update/releases
[license-shield]: https://img.shields.io/github/license/FaserF/ha-tasmota-update?style=for-the-badge
[license]: LICENSE
[hacs-shield]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[hacs]: https://github.com/hacs/integration
[maintainability-shield]: https://img.shields.io/codeclimate/maintainability/FaserF/ha-tasmota-update?style=for-the-badge
[maintainability]: https://codeclimate.com/github/FaserF/ha-tasmota-update
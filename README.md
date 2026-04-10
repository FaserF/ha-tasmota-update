# Tasmota Firmware Update for Home Assistant

[![GitHub Release][releases-shield]][releases]
[![License][license-shield]][license]
[![hacs][hacs-shield]][hacs]
[![Maintainability][maintainability-shield]][maintainability]

This custom integration provides firmware update functionality for Tasmota devices in Home Assistant. It works alongside the official Tasmota integration and adds an `update` entity to existing Tasmota devices, mapping them via MAC address.

This custom integration is only needed until [this Pull Request has been merged](https://github.com/emontnemery/hatasmota/pull/389).
More information [are available here](https://github.com/emontnemery/hatasmota/issues/151).

## Features

- **Standard Update Entities**: Adds official Home Assistant `update` entities to your Tasmota devices.
- **Staged Upgrades**: Automatically handles Tasmota's staged upgrade path for older firmware versions.
- **Release Notes**: Fetches and displays release notes from the official Tasmota GitHub repository.
- **Coexistence**: Designed to work perfectly with the official Tasmota integration.

### HACS (Recommended)

This integration is fully compatible with [HACS](https://hacs.xyz/).

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?repository=FaserF/ha-tasmota-update&category=integration)

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

## Disclaimer

Firmware updates always carry a small risk. While this integration follows official Tasmota upgrade paths, use it at your own risk.

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

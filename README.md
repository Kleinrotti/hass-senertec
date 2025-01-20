
# Home Assistant integration for Senertec

[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)

Custom component to support Senertec energy systems.

## Table of Contents

- [Home Assistant integration for Senertec](#home-assistant-integration-for-senertec)
  - [Table of Contents](#table-of-contents)
  - [About](#about)
  - [Installation](#installation)
    - [Installation through HACS](#installation-through-hacs)
    - [Manual installation](#manual-installation)
  - [Updating](#updating)
    - [Before updating please read the release changelog and backup your productGroups.json](#before-updating-please-read-the-release-changelog-and-backup-your-productgroupsjson)
  - [Configuration](#configuration)
    - [Home Assistant](#home-assistant)
  - [Supported devices](#supported-devices)
    - [Debugging](#debugging)

## About

With this integration you can integrate the sensors of your senertec heating system into Home Assistant.

## Installation

Requires Home Assistant 2024.10.0 or newer.
You need an account for Senertec Dachsconnect Gen2.

### Installation through HACS

If you have not yet installed HACS, go get it at https://hacs.xyz/ and walk through the installation and configuration.

Then find the Senertec energy system integration in HACS and install it.

Restart Home Assistant!

Install the new integration through *Configuration -> Integrations* in HA (see below).

### Manual installation

Copy the sub-path `/hass-senertec/custom_components/senertec` of this repo into the path
`/config/custom_components/senertec` of your HA installation.

Alternatively use the following commands within an SSH shell into your HA system.
Do NOT try to execute these commands directly your PC on a mounted HA file system. The resulting symlink would be broken for the HA file system.

```bash

cd /config
git clone https://github.com/Kleinrotti/hass-senertec.git

# if folder custom_components does not yet exist:
mkdir custom_components

cd custom_components
ln -s ../hass-senertec/custom_components/senertec
```

## Updating

### Before updating please read the release changelog and backup your productGroups.json

## Configuration

### Home Assistant

Setup under Integrations in Home Assistant, search for "Senertec energy system". You need to enter e-mail and password of your Senertec Dachsconnect account.

After setting up the integration, you can adjust some options on the
integration panel for it.

Even though this integration can be installed and configured via the
Home Assistant GUI (uses config flow), you might have to restart Home
Assistant to get it working.

## Supported devices

The following devices are currently supported:

- Senertec Dachs 0.8
- Senertec Dachs Gen2 F5.5
- Remeha eLecta Ace 300

Other devices should work too if you extend the shipped productGroups.json.
How that file works is described [here](https://github.com/Kleinrotti/py-senertec?tab=readme-ov-file#filtering-recommended). It's located in the integration folder.

### Debugging

To enable debug logging for this integration and related libraries you
can control this in your Home Assistant `configuration.yaml`
file. Example:

```yaml
logger:
  default: info
  logs:
    custom_components.senertec: debug

    py-senertec: debug
    websocket: debug
```

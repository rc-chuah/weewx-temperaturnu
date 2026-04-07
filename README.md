# weewx-temperaturnu

A WeeWX extension that uploads weather data to [Temperatur.nu](https://www.temperatur.nu/)

![License](https://img.shields.io/badge/License-GPLv3-blue.svg)
![Python](https://img.shields.io/badge/Python-2.7%2B%20%7C%203.x-blue.svg)
![WeeWX](https://img.shields.io/badge/WeeWX-3.8.0%2B-blue.svg)

## Overview

**weewx-temperaturnu** is a WeeWX extension that automatically uploads your weather station's temperature data to [Temperatur.nu](https://www.temperatur.nu/), a Swedish weather data collection service. The extension is designed to be lightweight and simple, requiring no external Python dependencies.

## Features

- ✅ Automatic temperature conversion to Celsius using WeeWX unit helpers
- ✅ Lightweight with zero external dependencies
- ✅ Compatible with Python 2.7+ and Python 3.x
- ✅ Works with WeeWX v3.8.0 and later
- ✅ Support for both WeeWX v4 and v5 installers
- ✅ Simple configuration via weewx.conf

## Requirements

- **Python:** 2.7+ or 3.x
- **WeeWX:** v3.8.0 or later
- **API Key:** from [Temperatur.nu](https://www.temperatur.nu/nystation/)
- **External Libraries:** None (uses only Python standard library)

## Installation

### Step 1: Get an API Key

Visit [Temperatur.nu New Station](https://www.temperatur.nu/nystation/) to register your weather station and obtain an API key.

### Step 2: Download the Extension

```bash
wget -O weewx-temperaturnu.zip https://github.com/rc-chuah/weewx-temperaturnu/archive/master.zip
```

### Step 3: Install the Extension

**For WeeWX v4 and earlier:**
```bash
wee_extension --install weewx-temperaturnu.zip
```

**For WeeWX v5:**
```bash
weectl extension install weewx-temperaturnu.zip
```

### Step 4: Configure

Edit `/etc/weewx/weewx.conf` and add the following section:

```ini
[StdRESTful]
    [[TemperaturNu]]
        apikey = YOUR_API_KEY_FROM_TEMPERATUR.NU
```

Optional configuration parameters:

```ini
[StdRESTful]
    [[TemperaturNu]]
        # Your API key from temperatur.nu (required)
        apikey = YOUR_API_KEY_HERE
        
        # Enable or disable uploads (default: true)
        enabled = true
        
        # Server URL (default: https://www.temperatur.nu/rapportera.php)
        server_url = https://www.temperatur.nu/rapportera.php
```

### Step 5: Restart WeeWX

```bash
sudo systemctl restart weewx
```

## How It Works

The extension performs the following tasks:

1. **Monitors** archive records from your WeeWX weather station
2. **Extracts** the outdoor temperature (`outTemp`)
3. **Converts** temperature to Celsius (if your station uses Fahrenheit or other units)
4. **Uploads** the temperature data to Temperatur.nu via HTTP POST for each new archive record

## Temperature Conversion

The extension automatically converts your weather station's temperature to Celsius using WeeWX's built-in `weewx.units.to_METRICWX()` helper function. This ensures accuracy regardless of your station's native unit system.

### Example Conversions

| Fahrenheit | Celsius |
|-----------|---------|
| 32°F      | 0°C     |
| 68°F      | 20°C    |
| 72.5°F    | 22.5°C  |
| 212°F     | 100°C   |

## Upload Method

This extension uses HTTP GET to upload data to Temperatur.nu with the following format:

```
GET /rapportera.php?hash=YOUR_API_KEY&t=22.5 HTTP/1.1
Host: www.temperatur.nu
```

## Troubleshooting

### Check WeeWX Logs

```bash
tail -f /var/log/syslog | grep temperaturnu
```

### Enable Debug Logging

Add to `/etc/weewx/weewx.conf`:

```ini
debug = 2
```

Then restart WeeWX:

```bash
sudo systemctl restart weewx
```

### Test the Extension Manually

```bash
cd /usr/share/weewx
PYTHONPATH=bin python bin/user/temperaturnu.py
```

Expected output:
```
Test 1 - US Units (Fahrenheit):
https://www.temperatur.nu/rapportera.php?hash=test_key_12345&t=22.5

Test 2 - Metric Units (Celsius):
https://www.temperatur.nu/rapportera.php?hash=test_key_12345&t=22.5
```

### Common Issues

| Issue | Solution |
|-------|----------|
| No data uploading | Verify API key in `weewx.conf` is correct |
| Temperature missing | Ensure your station records temperature (`outTemp`) |
| Connection errors | Check internet connectivity; test URL with `curl` |
| Wrong temperature | Check your station's unit system setting |

### Test Manually with curl

```bash
curl "https://www.temperatur.nu/rapportera.php?hash=YOUR_API_KEY&t=20"
```

## Dependencies

This extension uses **only Python's standard library**. The following modules are utilized:

- `Queue` (Python 2) / `queue` (Python 3)
- `urllib` / `urllib.parse` (Python 3)
- `sys`
- `time`
- `logging` / `syslog`

**No external pip packages are required.**

## License

Copyright © 2026 RC Chuah

Distributed under the terms of the [GNU General Public License t (GPLv3)](LICENSE.md)

## Credits

- **Original Concept:** Based on [weewx-windy](https://github.com/Jterrettaz/weewx-windy) by Matthew Wall and Jacques Terrettaz
- **Modified for Temperatur.nu:** RC Chuah

## Links

- **WeeWX:** https://www.weewx.com/
- **Temperatur.nu:** https://www.temperatur.nu/
- **WeeWX Documentation:** https://www.weewx.com/docs/
- **weewx-windy:** https://github.com/Jterrettaz/weewx-windy

# PiHoleAlerts

Alert device status based on Pi-Hole FTP database information.

## Config

Loads config from local file (Example bellow)

```
{
  "PIHOLE-FTP_DB": "/etc/pihole/pihole-FTL.db",
  "LAST_SEEN_DELTA_MINS": 5,
  "DEVICES": {
    "X3R7Z.xhico": {
      "notified": true,
      "status": true
    },
    "X3RTZ.xhico": {
      "notified": true,
      "status": true
    },
    "iXhico.xhico": {
      "notified": true,
      "status": true
    }
  }
}
```

## Usage

Manual

```
python3 PiHoleAlerts.py
```

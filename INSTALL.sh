#!/bin/bash

sudo mv /home/pi/PiHoleAlerts/PiHoleAlerts.service /etc/systemd/system/ && sudo systemctl daemon-reload
chmod +x -R /home/pi/PiHoleAlerts/*
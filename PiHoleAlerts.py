# -*- coding: utf-8 -*-
# !/usr/bin/python3

import os
import json
import logging
import sqlite3
import datetime
import traceback
from Misc import get911, sendEmail


def getNetworkInfo(piHoleFTPdb):
    """
    Retrieve network information for devices from the database.

    Args:
        piHoleFTPdb (str): Path to database

    Returns:
        dict: A dictionary containing device information with device names as keys,
              and corresponding IP addresses and last seen timestamps as values.
    """
    logger.info(f"Loading {piHoleFTPdb} database")

    # Connect to the SQLite database
    conn = sqlite3.connect(piHoleFTPdb)

    # Create a cursor object to interact with the database
    cursor = conn.cursor()

    # Iterate through the list of devices defined in CONFIG
    dbData = {}
    for deviceName in CONFIG["DEVICES"]:
        # Execute a query to get IP address and last seen timestamp from the database
        cursor.execute(f"""
            SELECT queries.client, queries.timestamp
            FROM network_addresses, queries
            WHERE network_addresses.name='{deviceName.lower()}' AND network_addresses.ip = queries.client
            ORDER BY queries.timestamp DESC
            LIMIT 1
        """)

        # Fetch the results of the query
        deviceIp, deviceLastQuery = cursor.fetchone()

        # Store the device information in the dictionary
        dbData[deviceName] = {"ip": deviceIp, "lastQuery": deviceLastQuery}

    # Close the connection
    conn.close()

    # Return the collected device information
    return dbData


def withinDeltaMins(epochTime1, epochTime2, deltaMins):
    """
    Check if the difference between two epoch times is within 5 minutes.

    Args:
        epochTime1 (int): Epoch time in seconds.
        epochTime2 (int): Epoch time in seconds.
        deltaMins (int): Difference in minutes

    Returns:
        bool: True if the difference is within deltaMins minutes, False otherwise.
    """
    # Calculate the absolute difference between the two epoch times
    timeDifference = abs(epochTime1 - epochTime2)

    # Define the threshold for deltaMins minutes in seconds
    deltaMinutesInSeconds = deltaMins * 60

    # Check if the difference is within the specified threshold
    return timeDifference < deltaMinutesInSeconds


def main():
    """
    Main function to update device status based on Pi-Hole FTP database information.
    """

    # Set Pi-Hole FTP Database path
    piHoleFTPdb = CONFIG["PIHOLE-FTP_DB"]

    # Get CONFIG Devices
    configDevices = CONFIG["DEVICES"]

    # Get DELTA MINS
    deltaMins = CONFIG["LAST_SEEN_DELTA_MINS"]

    # Get Network Info base on device name
    dbData = getNetworkInfo(piHoleFTPdb)

    # Get Current Epoch Timestamp
    currTimestamp = int(datetime.datetime.utcnow().timestamp())

    # Check for changes
    for deviceName, deviceInfo in dbData.items():

        # Get CONFIG Device
        configDevice = configDevices[deviceName]

        # Get CONFIG DEVICE Info && DB Device Info
        configNotified, configStatus, = configDevice["notified"], configDevice["status"]
        dbLastQuery = deviceInfo["lastQuery"]
        dbLastQueryDatetime = datetime.datetime.utcfromtimestamp(dbLastQuery)

        # Get WithInDeltaMins result
        withinDeltaMinsFlag = withinDeltaMins(currTimestamp, dbLastQuery, deltaMins)

        # Check if device is active/inactive again
        changeFlag = (withinDeltaMinsFlag != configStatus) and not configNotified

        # Update CONFIG Device Status
        configDevice["status"] = withinDeltaMinsFlag

        # Send user notifications? && Update CONFIG Device Info
        statusMsg = "ACTIVE" if withinDeltaMinsFlag else "INACTIVE"
        if changeFlag:
            configDevice["notified"] = True
            updateMsg = f"Device {deviceName} changed to {statusMsg} - lastQuery {dbLastQueryDatetime}"
            logger.info(updateMsg)
            sendEmail(updateMsg, "")
        else:
            logging.info(f"Device {deviceName} not changed - {statusMsg}")
            configDevice["notified"] = False

        # Update CONFIG FILE
        CONFIG["DEVICES"][deviceName] = configDevice

    # Save CONFIG_FILE
    with open(CONFIG_FILE, 'w') as outFile:
        json.dump(CONFIG, outFile, indent=2)


if __name__ == '__main__':
    # Set Logging
    LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.path.abspath(__file__).replace(".py", ".log"))
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()])
    logger = logging.getLogger()

    logger.info("----------------------------------------------------")

    # Open the configuration file in read mode
    CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    with open(CONFIG_FILE) as inFile:
        CONFIG = json.load(inFile)

    try:
        main()
    except Exception as ex:
        logger.error(traceback.format_exc())
        sendEmail(os.path.basename(__file__), str(traceback.format_exc()))
    finally:
        logger.info("End")

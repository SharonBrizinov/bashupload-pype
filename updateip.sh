#!/bin/bash

# Variables
USERNAME=""
PASSWORD=""
HOSTNAME=""

while true
do
    # Get the current public IP
    IP=$(curl -s http://checkip.amazonaws.com)

    # Update No-IP
    RESPONSE=$(curl -s -u $USERNAME:$PASSWORD "https://dynupdate.no-ip.com/nic/update?hostname=$HOSTNAME&myip=$IP")

    # Log the response
    echo "$(date) - IP: $IP - Response: $RESPONSE" | tee -a ./noip_update.log

    sleep 3600
done
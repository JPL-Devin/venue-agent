#!/bin/bash
# VENUE SERVER
export ING_VENUE_DIR=/home/hongmank/github/venueserver2
export ING_MTAK_DIR=/home/hongmank/github/mtak/r8.x/python
export ING_LOG_DIR=/home/hongmank/github/venueserver2
# Custom Script
export CUSTOM_SCRIPT_BASE_DIR=/teamtools/ingenium
# GLAD
# if LAD_HOST is not set, it will default to HOSTNAME env variable
# export LAD_HOST=
export LAD_PORT=8887
export LAD_HTTPS=true
# Bus 1553 Step
export BUS_1553_LOGFILE_PATH='/var/ammos/archive/$YYYY/$DOY/sse/$GDS_HOSTNAME/session_*/$USER/wsts-gds.results/psyche_*'
export LOGFILE_1553_DICTIONARY_FILE_PATH='/gds/psyche/dictionary/psyche1553/current'
export IRIG_SOURCE='false'
# AMPCS
export CHILL_GDS=/ammos/ampcs/mpcs/psyche/current
export PATH=$CHILL_GDS/bin:$CHILL_GDS/bin/tools:/usr/local/bin:/usr/bin:/usr/local/sbin:/usr/sbin
export GDS_JAVA_OPTS="-DGdsUserConfigDir=$ING_VENUE_DIR/config/gds_config"

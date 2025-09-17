#!/bin/bash
SCRIPT_FILE=$(realpath $0)
SCRIPT_DIR=$(dirname $SCRIPT_FILE)

usage() {
  echo "
  Usage: $0 start|stop|reload
  
  Example:
  $0 start
  " 
}

input_error() {
  usage
  exit 1
}


COMMAND=$1

echo "COMMAND: $COMMAND"

CONF_PATH="$SCRIPT_DIR/nginx.conf"
echo "CONF_PATH: $CONF_PATH"

ERROR_LOG_PATH=$(cat $CONF_PATH | grep error_log | head -1 | awk '{print $2}')
echo "ERROR_LOG_PATH: $ERROR_LOG_PATH"

PID_PATH=$(cat $CONF_PATH | grep nginx.pid | head -1 | awk -F'[ |;]' '{print $2}')
echo "PID_PATH: $PID_PATH"

if [[ "$COMMAND" == "start" ]]
then
    # Use -e to supress spurious error messages about
    # not being able to write to the default error location 
    nginx -c $CONF_PATH -e $ERROR_LOG_PATH
    # wait a bit for nginx to create the PID file
    sleep 2
    echo "PID: $(cat $PID_PATH)"
elif [[ "$COMMAND" == "stop" ]]
then
    # need to pass configuration file to locate pid file
    nginx -c $CONF_PATH -s stop -e $ERROR_LOG_PATH
elif [[ "$COMMAND" == "reload" ]]
then
    nginx -c $CONF_PATH -s stop -e $ERROR_LOG_PATH
else
    echo "ERROR: Invalid command: ${COMMAND}"
    usage
    exit 1
fi


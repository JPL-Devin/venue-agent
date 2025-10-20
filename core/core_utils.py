import logging
logger = logging.getLogger(__name__)

from enum import Enum
import csv
import sys
from datetime import datetime, timedelta
import os
import traceback
from datetime import datetime, timezone
import socket
import glob

import subprocess
from io import StringIO


###########################################################
###### MAPPINGS BETWEEN JSON INPUTS AND CHILL INPUTS ######
###########################################################


def get_env (env_var,cast_type=str):
  val = os.environ.get(env_var)
  if (val is not None and val.strip() != ''):
    if (cast_type == str):
      return str(val)
    elif (cast_type == int):
      return int(val)
  return None

class TimeoutError(Exception):
  pass

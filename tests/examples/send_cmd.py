import requests
import time
import json
from datetime import datetime, timezone, timedelta
from session_info import server, sessionId, exec_shared_dict, CMD_NO_OP

if __name__ == '__main__':

    # send a FSW command
    cmd_start_time = datetime.strftime(datetime.now(tz=timezone.utc), '%Y-%jT%H:%M:%S')
    print('send command')
    url = f'{server}/cmd/fsw_cmd'
    res = requests.post(url, json={
            'sessionId': sessionId, 
            'commandString': CMD_NO_OP, 
            'validate': False,
            'stringSelection': 'DEFAULT',
            'timeout': 10
    	},
        headers=exec_shared_dict['headers']
    )
    print(res.status_code)
    print(res.text)


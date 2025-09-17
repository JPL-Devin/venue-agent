import requests
import time
import json
from datetime import datetime, timezone, timedelta
from session_info import server, sessionId, exec_shared_dict, CMD_DOWN_DP

if __name__ == '__main__':

    print('Enable data products')
    url = f'{server}/cmd/fsw_cmd'
    res = requests.post(url, json={
            'sessionId': sessionId, 
            'commandString': CMD_DOWN_DP, 
            'validate': False,
            'stringSelection': 'DEFAULT',
            'timeout': 10
        },
        headers=exec_shared_dict['headers']
    )
    print(res.status_code)
    print(res.text)

    sent_time = datetime.now(tz=timezone.utc)
    print(f'sent_time: {sent_time.isoformat()}')

    wait_secs = 10

    print(f'wait for {wait_secs} secs')
    time.sleep(wait_secs)
    
    # check data product
    utc_now = datetime.now(tz=timezone.utc)

    query_start_time = datetime.strftime(utc_now - timedelta(seconds=7200), '%Y-%jT%H:%M:%S')
    query_end_time = datetime.strftime(utc_now, '%Y-%jT%H:%M:%S')

    print('Check data products')
    url = f'{server}/dp'
    res = requests.get(url, json={
            'sessionId': sessionId, 
            'dpStatus': 'COMPLETE', 
            'apId': [301],
            'timeType': 'ERT',
            'startTime': query_start_time,
            'endTime': query_end_time,
            'timeout': 10
    	},
        headers=exec_shared_dict['headers']
    )
    print(res.status_code)
    print(res.text)
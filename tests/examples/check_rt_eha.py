import requests
import time
import json
from datetime import datetime, timezone, timedelta
from session_info import server, sessionId, exec_shared_dict, CMD_COUNTER_EHA

def run_eha_query():
    utc_now = datetime.now(tz=timezone.utc)

    query_start_time = datetime.strftime(utc_now - timedelta(seconds=120), '%Y-%jT%H:%M:%S')
    query_end_time = datetime.strftime(utc_now, '%Y-%jT%H:%M:%S')

    print('query realtime eha')
    url = f'{server}/eha/realtime'
    res = requests.get(url, 
        json= {
            'sessionId': sessionId,
            'channelId': CMD_COUNTER_EHA, 
            'startTime': query_start_time,
            'endTime': query_end_time
        },
        headers=exec_shared_dict['headers']
    )
    status_code = res.status_code
    print(f'status_code: {status_code}')
    if status_code == 200:
        print(f'respose: {json.dumps(res.json(), indent=4)}')        
    else:
        print(f'text: {res.text}')

def run_eha_multi_query():
    utc_now = datetime.now(tz=timezone.utc)

    query_start_time = datetime.strftime(utc_now - timedelta(seconds=120), '%Y-%jT%H:%M:%S')
    query_end_time = datetime.strftime(utc_now, '%Y-%jT%H:%M:%S')

    print('query realtime eha (multi)')
    url = f'{server}/eha/realtime_multi'
    res = requests.get(url, 
        json= {
            'sessionId': sessionId,
            'channelIds': [CMD_COUNTER_EHA, 'CMD-0026'], 
            'startTime': query_start_time,
            'endTime': query_end_time
        },
        headers=exec_shared_dict['headers']
    )
    status_code = res.status_code
    print(f'status_code: {status_code}')
    if status_code == 200:
        print(f'respose: {json.dumps(res.json(), indent=4)}')        
    else:
        print(f'text: {res.text}')

if __name__ == '__main__':    
    run_eha_query()
    run_eha_multi_query()

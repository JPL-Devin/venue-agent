import requests
import time
import json
from datetime import datetime, timezone, timedelta
from session_info import server, sessionId, exec_shared_dict

if __name__ == '__main__':
    
    # restart 1553 log
    print('send sse command')
    sse_cmds = [
        'bti1553 psyche buslog stop',
        'bti1553 psyche buslog start'
    ]
    
    for sse_cmd in sse_cmds:
        url = f'{server}/cmd/sse'
        res = requests.post(url, json={
                'sessionId': sessionId,
                'commandString': sse_cmd,
                'timeout': 60
            },
            headers=exec_shared_dict['headers']
        )
        print(res.status_code)
        print(res.text)
    
    # 

    sent_time = datetime.now(tz=timezone.utc)
    print(f'sent_time: {sent_time.isoformat()}')

    wait_secs = 40

    print(f'wait for {wait_secs} secs')
    time.sleep(wait_secs)
    
    # Verify RSB Command in bus log
    print('Check 1553 log')
    utc_now = datetime.now(tz=timezone.utc)

    query_start_time = datetime.strftime(utc_now - timedelta(seconds=wait_secs), '%Y-%jT%H:%M:%S')
    query_end_time = datetime.strftime(utc_now, '%Y-%jT%H:%M:%S')


    url = f'{server}/bus1553'
    res = requests.get(url, 
        json= {
            'start_time': query_start_time, 
            'end_time': query_end_time,
            'duration': None, 
            'time_type': 'SCET',
            'variables': 'REU_A_RSB_CMD_WORD_1'
        },
        headers=exec_shared_dict['headers']
    )
    status_code = res.status_code
    print(f'status_code: {status_code}')
    print(res.text)


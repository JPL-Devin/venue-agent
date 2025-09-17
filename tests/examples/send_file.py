import sys
import requests
import time
import json
from datetime import datetime, timezone, timedelta
from session_info import server, sessionId, exec_shared_dict

if __name__ == '__main__':

    # increase uplink speed (Psyche WSTS)
    cmd_start_time = datetime.strftime(datetime.now(tz=timezone.utc), '%Y-%jT%H:%M:%S')
    print('send sse command')
    url = f'{server}/cmd/sse'
    res = requests.post(url, json={
            'sessionId': sessionId,
            'commandString': 'cmd putp avsim.RceA.mtif.mtifUpl.uplinkRateBitPerSec value 64000',
            'timeout': 60
        },
        headers=exec_shared_dict['headers']
    )
    print(res.status_code)
    print(res.text)

    # uplink file
    if False:
        cmd_start_time = datetime.strftime(datetime.now(tz=timezone.utc), '%Y-%jT%H:%M:%S')
        print('send file')
        url = f'{server}/cmd/binary_file'
        res = requests.post(url, json={
                'sessionId': sessionId,
                'sourceFilePath': '/teamtools/avstb/files/system-sequencing/seqs/VA-SEQ-06_884688/cmd_no_op.bin',
                'targetFilePath': '/eng/seq/cmd_no_op.seq',
                'overwrite': True,
                'fileType': 0,
                'stringSelection': 'DEFAULT',
                'timeout': 60
        	},
            headers=exec_shared_dict['headers']
        )
        print(res.status_code)
        print(res.text)


    # uplink SCMF file
    if True:
        cmd_start_time = datetime.strftime(datetime.now(tz=timezone.utc), '%Y-%jT%H:%M:%S')
        print('send SCMF file')
        url = f'{server}/cmd/scmf'
        res = requests.post(url, json={
                'sessionId': sessionId,
                'filePath': '/teamtools/atlo/production/uplink-files/scmfs/ctt22/10_cmd_no_ops_a.scmf',
                'disableChecks': False,
                'timeout': 60
            },
            headers=exec_shared_dict['headers']
        )
        print(res.status_code)
        print(res.text)


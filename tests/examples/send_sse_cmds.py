import logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
CONSOLE_LOG_FORMAT = '[%(asctime)s] [%(funcName)s] %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S'
formatter = logging.Formatter(CONSOLE_LOG_FORMAT, LOG_DATE_FORMAT)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
handler.setFormatter(formatter)
logger.addHandler(handler)

import requests
import time
import argparse
import matplotlib.pyplot as plt
import json
import sys
from datetime import datetime, timezone, timedelta
import session_info
from session_info import server, exec_shared_dict, CMD_NO_OP

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Sends SSE commands to venueserver', 
        prog='send_sse_cmds.py',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('session_id', type=int,
                        help='AMPCS session id')
    parser.add_argument('num_runs', type=int,
                        help='Number of runs')
    parser.add_argument('--timeout', type=int, default=10,
                        help='Timeout in seconds')
    
    args = parser.parse_args()
    
    session_info.sessionId = args.session_id

    logger.info(f'session_id: {args.session_id} num_runs: {args.num_runs} timeout: {args.timeout}')

    # send SSE commands
    fail_count = 0
    commands = [
        'dss version',
        'wde nop',
        'dss nop',
        'sru sruA nop',
        'instr eisnac nop',
    ]
    count = 0
    counts = []
    durations = []
    for i in range(args.num_runs):
        for command in commands:
            count += 1
            logger.info(f'command count: {count}')
            url = f'{server}/cmd/sse'
            time0 = time.time()
            res = requests.post(url, json={
                    'sessionId': session_info.sessionId, 
                    'commandString': command, 
                    'timeout': args.timeout
                },
                headers=exec_shared_dict['headers']
            )
            duration = time.time() - time0

            counts.append(count)
            durations.append(duration)
            max_duration = max(durations)

            if res.status_code != 200:
                fail_count += 1
            logger.info(res.status_code)
            logger.info(res.text)
            logger.info(f'max_duration: {max_duration}')
            # logger.info(f'fail_count: {fail_count}')
            
            if fail_count > 0:
                break

        if fail_count > 0:
            break

    logger.info(f'count: {count}')
    logger.info(f'fail_count: {fail_count}')

    plt.scatter(counts, durations)
    plt.show()

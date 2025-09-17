import os
import sys
import time
import jwt
import socket

PRIVATE_PEM_FILE = 'exec_venue_private_pem.pem'

server = 'http://localhost:19443/api/v3'
sessionId = 25

private_pem_path = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 
                               PRIVATE_PEM_FILE)
exec_venue_private_pem_file = open(private_pem_path, 'r')
exec_venue_private_pem = exec_venue_private_pem_file.read()

username = os.environ.get('USER', '')

exec_shared_dict = {}

def generate_exec_token():
    iat = int(time.time()) - 60
    # use 24hr expiration for stress test
    exp = iat + (24*60*60)
    exec_headers = {'Content-Type': 'application/json',
              'Accept': 'application/json'}
    encoded_token = jwt.encode({'scopes': ['basic', 'execute:wsts', 'execute:testbed', 'execute:sit', 'execute:other', 'redline', 'config_mgmt', 'admin'],
                        'exp':exp,
                        'iat':iat,
                        'username': username},
                         exec_venue_private_pem,
                         algorithm='RS256')

    token_str = encoded_token.decode('utf-8')
    auth_header = 'Bearer {0}'.format(token_str)
    exec_headers['Authorization'] = auth_header
    exec_shared_dict['headers'] = exec_headers  

generate_exec_token()

###
hostname = socket.gethostname()
if hostname.startswith('eurc'):
    CMD_NO_OP = 'CMD_NO_OP'
    CMD_COMP_EVR = 'CMD_SVC_EVR_CMD_COMPLETED_SUCCESS'
    CMD_DISPATCHED_EVR = 'CMD_SVC_EVR_VC1_CMD_DISPATCHED'
    CMD_COUNTER_EHA = 'CMD-0027'
    CMD_DOWN_DP = 'DDM_MANAGE_DWN_PB,DATA_PRODUCTS,ENABLE'
elif hostname.startswith('psyche'):
    CMD_NO_OP = 'CMD_NO_OP'
    CMD_COMP_EVR = 'CMD_SVC_EVR_CMD_COMPLETED_SUCCESS'
    CMD_DISPATCHED_EVR = ''  # TODO: set this
    CMD_COUNTER_EHA = 'CMD-0002'
    CMD_DOWN_DP = 'DWN_MANAGE_PB,DATA_PRODUCTS,ENABLE'
else:
    print(f'Error: Unrecognized hostname: {hostname}')
    sys.exit(1)

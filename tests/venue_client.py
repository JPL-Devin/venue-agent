import requests
import os
import time
import jwt


PRIVATE_PEM_FILE = 'exec_venue_private_pem.pem'

server_1 = 'http://localhost:19443/api/v3'
server_2 = 'http://localhost:19444/api/v3'

private_pem_path = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), 
                               PRIVATE_PEM_FILE)
exec_venue_private_pem_file = open(private_pem_path, 'r')
exec_venue_private_pem = exec_venue_private_pem_file.read()

username = os.environ.get('USER', '')

exec_shared_dict = {}

def generate_exec_token():
    iat = int(time.time()) - 60
    exp = iat + (30*60)
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

def run_custom_script(server, startInput):
    url = f'{server}/custom_script/start'
    res = requests.post(url, json=startInput,
        headers=exec_shared_dict['headers']
    )
    return res

def get_custom_script_status(server, statusInput):
    url = f'{server}/custom_script/status'
    res = requests.get(url, json=statusInput, 
        headers=exec_shared_dict['headers']
    )
    return res

def download_custom_script_files(server, scriptRunId):
    url = f'{server}/custom_script/{scriptRunId}/files'
    res = requests.get(url, 
        headers=exec_shared_dict['headers']
    )
    return res

def halt_custom_script(server, haltInput):
    url = f'{server}/custom_script/halt'
    res = requests.post(url, json=haltInput,
        headers=exec_shared_dict['headers']
    )
    return res
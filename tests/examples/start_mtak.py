import requests
from session_info import server, sessionId, exec_shared_dict
if __name__ == '__main__':
    print('start mtak')
    url = f'{server}/mtak/start'
    res = requests.post(url, 
	json={'sessionIds': [sessionId], 'timeout': 60, 'defaultCmdString': 'AB'},
        headers=exec_shared_dict['headers']
    )
    print(res.status_code)
    print(res.text)


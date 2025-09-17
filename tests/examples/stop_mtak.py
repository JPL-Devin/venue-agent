import requests

from session_info import server, sessionId, exec_shared_dict

if __name__ == '__main__':
    print('shutdown mtak')
    url = f'{server}/mtak/shutdown'
    res = requests.post(url, headers=exec_shared_dict['headers'])
    print(res.status_code)
    print(res.text)

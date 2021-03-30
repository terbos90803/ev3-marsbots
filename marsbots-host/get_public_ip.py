import requests

server_address = 'https://api.ipify.org'


def _get(endpoint, attrs=dict()):
    uri = f'{server_address}{endpoint}'
    try:
        response = requests.get(uri, params=attrs, timeout=5)
        response.raise_for_status()
        # Code here will only run if the request is successful
        # print(response)
        return response.json()
    except requests.exceptions.HTTPError as err:
        return {'status': 'fail', 'reason': err}
    except requests.exceptions.ConnectionError as err:
        return {'status': 'fail', 'reason': err}
    except requests.exceptions.Timeout as err:
        return {'status': 'fail', 'reason': err}
    except requests.exceptions.RequestException as err:
        return {'status': 'fail', 'reason': err}


def get_public_ip():
    ip = _get('/', {'format': 'json'}).get('ip')
    if ip is not None:
        return ip
    else:
        return 'unknown'

import requests
from requests.auth import HTTPBasicAuth

def wtLogin():
    login_url = 'https://api2.watttime.org/v2/login'
    token = requests.get(login_url, auth=HTTPBasicAuth('longbranchflyer', 'AJqPC4aXQLo*gm8mQEoWHcWK')).json()['token']
    return token

def wtGetIndex(token):
    index_url = 'https://api2.watttime.org/index'
    headers = {'Authorization': 'Bearer {}'.format(token)}
    params = {'ba': 'IESO_NORTH'}
    rsp=requests.get(index_url, headers=headers, params=params)
    return rsp.text

def wtGetBA(token):
    region_url = 'https://api2.watttime.org/v2/ba-from-loc'
    headers = {'Authorization': 'Bearer {}'.format(token)}
    params = {'latitude': '43.255707196639314', 'longitude': '-79.95159344351713'}
    rsp=requests.get(region_url, headers=headers, params=params)
    return rsp.text

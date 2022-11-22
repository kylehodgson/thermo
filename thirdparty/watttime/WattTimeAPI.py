from codecs import getincrementaldecoder
from decimal import InvalidOperation
import string
import requests
from requests.auth import HTTPBasicAuth
import json

class WattTime:
    token=""
    def __init__(self, username: string, password: string) -> None:
        login_url = 'https://api2.watttime.org/v2/login'
        self.token = requests.get(login_url, auth=HTTPBasicAuth(username, password)).json()['token']

    def getIndex(self, ba):
        if self.token=="":
            raise InvalidOperation("please login first.")
        index_url = 'https://api2.watttime.org/index'
        headers = {'Authorization': 'Bearer {}'.format(self.token)}
        params = {'ba': '{}'.format(ba)}
        rsp=requests.get(index_url, headers=headers, params=params)
        return rsp.text

    def get_index_json(self,ba):
        rsp=self.getIndex(ba)
        formatted=json.loads(rsp)
        return formatted


    def getBA(self, latt, long)->string:
        if self.token=="":
            raise InvalidOperation("please login first.")
        region_url = 'https://api2.watttime.org/v2/ba-from-loc'
        headers = {'Authorization': 'Bearer {}'.format(self.token)}
        params = {'latitude': '{}'.format(latt), 'longitude': '{}'.format(long)}
        rsp=requests.get(region_url, headers=headers, params=params)
        return rsp.text

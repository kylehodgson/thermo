# /usr/bin/env python
from os import environ
from sys import exit
from requests import get, delete, post
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
import json
import random
import string
import time
import subprocess

class MythicBeasts:
    LOGIN_URL = 'https://auth.mythic-beasts.com/login'
    PROVISION_URL = 'https://api.mythic-beasts.com/beta/pi/servers/'
    token = {}

    def __init__(self, mbkey="", mbsecret="") -> None:
        if not mbkey:
            mbkey = environ.get('MBKEY')
        if not mbsecret:
            mbsecret = environ.get('MBSECRET')
        client = BackendApplicationClient(client_id=mbkey)
        oauth = OAuth2Session(client=client)
        self.token = oauth.fetch_token(
            token_url=self.LOGIN_URL, client_id=mbkey, client_secret=mbsecret)

    def _prepForThermo(self, fqdn: str):
        # apt-get -y install sudo
        # useradd thermo -m -s $(which bash)
        # usermod -aG sudo thermo
        # echo "thermo ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
        # mkdir /home/thermo/.ssh
        # echo $PUBKEY >> /home/thermo/.ssh/authorized_keys
        # echo -e "127.0.0.1\t$(hostname)" >> /etc/hosts
        pass

    def _getFQDN(self, hostname: str) -> str:
        return "ssh." + hostname + ".hostedpi.com"

    def _getAuthHeader(self) -> dict:
        if not self.token:
            raise Exception(
                "Cannot construct header without a token. "
                "Were the oAuth secret and key provided?")

        return {'Authorization': 'Bearer {}'.format(self.token['access_token'])}

    def deprovision(self, host: dict) -> None:
        deprovision_response = delete(
            self.PROVISION_URL+host['name'], headers=self._getAuthHeader())
        print(f"deprovisioning response: {deprovision_response.text}")

    def provision(self, name="", machine_config={}) -> dict:
        if not machine_config:
            with open('scripts/newserver.json') as f:
                machine_config = json.load(f)
        if not name:
            letters = string.ascii_lowercase
            name = ''.join(random.choice(letters) for i in range(10))
        if 'ssh_key' not in machine_config:
            pubkey = environ.get('PUBKEY')
            if pubkey:
                machine_config['ssh_key'] = pubkey
            else:
                raise Exception(
                    "no ssh key provided. this can be passed in via provision's"
                    "machine_config['ssh_key'] parameter, or provided in an environment variable PUBKEY.")
        
        authHeader = self._getAuthHeader()
        provision_response = post(
            self.PROVISION_URL+name, headers=authHeader, json=machine_config)

        if provision_response.status_code == 202 and provision_response.headers['Location']:
            queue_url = provision_response.headers['Location']
            initial_queue_info = get(queue_url, headers=authHeader)
            while initial_queue_info.json()['status'] != "live":
                time.sleep(5)
                qi = get(queue_url, headers=authHeader)
                provisioned_host = qi.json()
                if provisioned_host['status'] != "live":
                    print(f"Status: {qi.text}")
                else:
                    print(f"Server is live. info: {qi.text}")
                    provisioned_host['name'] = name
                    provisioned_host['fqdn'] = self._getFQDN(name)
                    return provisioned_host

        if provision_response.status_code == 401:
            raise Exception(
                f"Authentication issue. Error text was {provision_response.json()['error']}")
        elif provision_response.status_code == 409:
            raise Exception(
                f"Name {name} already exists. "
                f"Error text was {provision_response.json()['error']}")
        elif provision_response.status_code == 503:
            raise Exception(
                f"Out of stock for configuration {machine_config['model']}.  "
                f"Error text was {provision_response.json()['error']}")
        elif provision_response.status_code == 400:
            raise Exception(
                f"Invalid model number {machine_config['model']}.  "
                f"Error text was {provision_response.json()['error']}")
        else:
            raise Exception(
                f"status: {provision_response.status_code} text: {provision_response.text} "
                f"headers: {provision_response.headers} "
                f"Error text was {provision_response.json()['error']}")


def main() -> None:
    cloud = MythicBeasts()
    host = cloud.provision()
    print(f"Host info: {host}")
    print(f"Connect via SSH: ssh -p {host['ssh_port']} root@{host['fqdn']}")
    
    subprocess.Popen(
        f"scp -P {host['ssh_port']} scripts/linux-provision.sh root@{host['fqdn']}:~/", 
        shell=True, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE).communicate()
    subprocess.Popen(
        f"ssh -p {host['ssh_port']} root@{host['fqdn']} 'chmod +x ~/linux-provision.sh'", 
        shell=True, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE).communicate()
    subprocess.Popen(
        f"ssh -p {host['ssh_port']} root@{host['fqdn']} '~/linux-provision.sh'", 
        shell=True, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE).communicate()
    
    # echo "$PUBKEYS" >> /home/thermo/.ssh/authorized_keys
    # cloud.deprovision(host)


if __name__ == '__main__':
    exit(main())

from urllib3 import disable_warnings
import requests
import json
from datetime import datetime
disable_warnings()


class WebAPI:
    def __init__(self, url: str, username: str, password: str):
        self.url = f"{url.rstrip('/')}/api"
        self.username = username
        self.password = password

        self.session = requests.Session()
        self.session.verify = False
        self.session.headers.update({'User-Agent': 'Forescout TOOLS', 'Content-Type': 'application/json'})
        self.token = ""

    def login(self) -> bool:
        url = f"{self.url}/login"
        data = {
            "username": self.username,
            "password": self.password
        }
        headers = self.session.headers.copy()
        headers.update({'Content-Type': 'application/x-www-form-urlencoded'})
        r = self.session.post(url, headers=headers, data=data)

        if r.status_code == 200:
            self.token = r.text
            self.session.headers.update({'Authorization': self.token})
            return True
    
    def fetch_hosts(self) -> dict:
        url = f"{self.url}/hosts"
        r = self.session.get(url)
        return r.json()
    
    def backup_hosts(self, location: str):
        hosts = self.fetch_hosts()
        file_path = f"{location}/hosts_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
        with open(file_path, 'w') as f:
            json.dump(hosts, f, indent=4)
        return file_path
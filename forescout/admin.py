"""
Manage segments trhough Forescout Admin API
"""
import requests
import json
import time
from datetime import datetime
from forescout.utils.log import get_logger
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


logger = get_logger()


class Admin:
    def __init__(self, url:str, username:str, password:str):
        self.url = url.rstrip('/')
        self.username = username
        self.password = password
        self.token = ""
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Forescout TOOLS', 'Content-Type': 'application/json'})
        self.session.verify = False

    def check_rate_limit(self, response: requests.Response):
        """Check rate limit"""
        if response.status_code == 429:
            wait_after = int(response.json()["errors"][0].split("Wait ")[-1].split(" seconds")[0])
            logger.warning(f"偵測到Rate Limit，等待 {wait_after} 秒...")
            time.sleep(wait_after+1)
            return True

    @logger.catch
    def login(self) -> bool:
        """Login to Forescout API"""
        url = f"{self.url}/fsum/oauth2.0/token"
        headers = self.session.headers.copy()
        headers.update({
            'Content-Type': 'application/x-www-form-urlencoded',
        })
        payload = f'username={self.username}&password={self.password}&grant_type=password&client_id=fs-oauth-client'

        while 1:
            r = self.session.post(url, data=payload, headers=headers, timeout=10)
            rate_limit = self.check_rate_limit(r)
            if not rate_limit:
                break

        # logger.debug(r.json())

        if r.status_code == 200:
            self.token = r.json().get("access_token")
            self.session.headers.update({'Authorization': f'Bearer {self.token}'})
            return True

    def fetch_segments(self):
        """Fetch segments"""
        url = f"{self.url}/adminapi/segments"
        
        while 1:
            response = self.session.get(url)
            rate_limit = self.check_rate_limit(response)
            if not rate_limit:
                break

        logger.debug(f"{response.json()} | {response.status_code}")
        return response.json()
    
    def update_segments(self, segment_json: dict) -> requests.Response:
        """Update segment"""
        url = f"{self.url}/adminapi/segments"
        while 1:
            response = self.session.put(url, json=segment_json, timeout=10)
            rate_limit = self.check_rate_limit(response)
            if not rate_limit:
                break

        logger.debug(f"Respone : {response.json()} | Status code: {response.status_code} | Respone Headers: {response.headers}")
        return response
    
    def backup_segments(self, location:str = "./backups"):
        """Backup segments to file"""
        segments = self.fetch_segments()
        file_name = f"{location}/segments_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
        with open(file_name, "w", encoding='utf-8') as f:
            json.dump(segments, f, indent=4, ensure_ascii=False)
        return file_name

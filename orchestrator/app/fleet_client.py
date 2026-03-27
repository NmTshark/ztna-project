import requests

class FleetClient:
    def __init__(self, base_url: str, token: str, verify_tls: bool):
        self.base_url = base_url.rstrip("/")
        self.s = requests.Session()
        self.s.headers.update({"Authorization": f"Bearer {token}"})
        self.verify = verify_tls

    def list_hosts(self, per_page: int = 200):
        url = f"{self.base_url}/api/v1/fleet/hosts?per_page={per_page}"
        r = self.s.get(url, verify=self.verify, timeout=15)
        r.raise_for_status()
        return r.json()

    def get_host(self, host_id: int):
        url = f"{self.base_url}/api/v1/fleet/hosts/{host_id}"
        r = self.s.get(url, verify=self.verify, timeout=15)
        r.raise_for_status()
        return r.json()

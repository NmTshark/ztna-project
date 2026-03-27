import requests

class ZitiMgmt:
    def __init__(self, mgmt_url: str, username: str, password: str, verify_tls: bool):
        self.base_url = mgmt_url.rstrip("/")
        self.user = username
        self.pw = password
        self.verify = verify_tls
        self.s = requests.Session()
        self.token = None

    def login(self):
        url = f"{self.base_url}/edge/management/v1/authenticate?method=password"
        r = self.s.post(
            url,
            json={"username": self.user, "password": self.pw},
            verify=self.verify,
            timeout=15
        )
        r.raise_for_status()
        data = r.json().get("data", {})
        self.token = data.get("token")
        if not self.token:
            raise RuntimeError("Ziti login ok but missing data.token")
        self.s.headers.update({"zt-session": self.token})

    def list_identities(self, limit: int = 500):
        url = f"{self.base_url}/edge/management/v1/identities?limit={limit}&offset=0"
        r = self.s.get(url, verify=self.verify, timeout=15)
        r.raise_for_status()
        return r.json()

    def patch_identity_role_attributes(self, identity_id: str, role_attributes: list[str]):
        url = f"{self.base_url}/edge/management/v1/identities/{identity_id}"
        payload = {"roleAttributes": role_attributes}
        r = self.s.patch(url, json=payload, verify=self.verify, timeout=15)
        r.raise_for_status()
        return r.json()

    def list_sessions(self, limit: int = 1000):
        url = f"{self.base_url}/edge/management/v1/sessions?limit={limit}&offset=0"
        r = self.s.get(url, verify=self.verify, timeout=15)
        r.raise_for_status()
        return r.json()

    def delete_session(self, session_id: str):
        url = f"{self.base_url}/edge/management/v1/sessions/{session_id}"
        r = self.s.delete(url, verify=self.verify, timeout=15)
        r.raise_for_status()

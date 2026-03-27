import requests

class OPAClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.s = requests.Session()

    def decide(self, decision_path: str, opa_input: dict):
        url = f"{self.base_url}{decision_path}"
        r = self.s.post(url, json={"input": opa_input}, timeout=10)
        r.raise_for_status()
        return r.json()

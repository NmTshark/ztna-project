import csv
import os
import time
import json
import sqlite3
from datetime import datetime, timezone

import yaml

from fleet_client import FleetClient
from opa_client import OPAClient
from ziti_mgmt import ZitiMgmt


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def ensure_dirs(path):
    os.makedirs(path, exist_ok=True)


def db_init(db_path: str):
    ensure_dirs(os.path.dirname(db_path))
    conn = sqlite3.connect(db_path)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS posture_events (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      ts TEXT NOT NULL,
      hostname TEXT,
      fleet_host_id INTEGER,
      ziti_identity TEXT,
      ziti_identity_id TEXT,
      prev_state TEXT,
      new_state TEXT,
      score INTEGER,
      reasons TEXT,
      tdetect TEXT,
      tdecision TEXT,
      tenforce TEXT
    )
    """)
    conn.commit()
    return conn


def csv_init(csv_path: str):
    ensure_dirs(os.path.dirname(csv_path))
    exists = os.path.exists(csv_path)
    f = open(csv_path, "a", newline="", encoding="utf-8")
    w = csv.writer(f)
    if not exists:
        w.writerow([
            "ts", "hostname", "fleet_host_id", "ziti_identity", "ziti_identity_id",
            "prev_state", "new_state", "score", "reasons", "tdetect", "tdecision", "tenforce"
        ])
    return f, w


def load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def normalize_hostname(value: str) -> str:
    if not value:
        return ""
    return value.strip()


def refresh_identity_cache(ziti):
    identities = ziti.list_identities()
    return {i["name"]: i for i in identities.get("data", [])}


def reset_identities_to_base_roles(ziti, devices, identity_prefix="ep-"):
    print("[INFO] resetting endpoint identities to base roles from device_map")

    id_by_name = refresh_identity_cache(ziti)

    for d in devices:
        hostname = normalize_hostname(d.get("hostname", ""))
        base_role = (d.get("role") or "").strip()

        if not hostname or not base_role:
            print(f"[WARN] skipping invalid device map entry: {d}")
            continue

        identity_name = f"{identity_prefix}{hostname}"
        ident = id_by_name.get(identity_name)

        if not ident:
            print(f"[WARN] identity not found for reset: {identity_name}")
            continue

        current_attrs = ident.get("roleAttributes", []) or []
        desired_attrs = [base_role]

        if set(current_attrs) != set(desired_attrs):
            try:
                ziti.patch_identity_role_attributes(ident["id"], desired_attrs)
                print(f"[INFO] reset {identity_name}: {current_attrs} -> {desired_attrs}")
            except Exception as e:
                print(f"[ERROR] failed to reset {identity_name}: {e}")
        else:
            print(f"[INFO] {identity_name} already at baseline role")


def build_failing_policies(host_obj: dict) -> list[str]:
    host = host_obj.get("host", host_obj.get("data", host_obj))

    print("\n[DEBUG] Inspecting Fleet host detail...")
    print(f"[DEBUG] host keys = {list(host.keys())}")

    if "policies" in host:
        print(f"[DEBUG] host['policies'] = {json.dumps(host['policies'], ensure_ascii=False)[:3000]}")
    if "issues" in host:
        print(f"[DEBUG] host['issues'] = {json.dumps(host['issues'], ensure_ascii=False)[:3000]}")
    if "software" in host:
        print(f"[DEBUG] host['software'] exists")
    if "mdm" in host:
        print(f"[DEBUG] host['mdm'] exists")

    policies = host.get("policies", []) or []

    failing = []
    for p in policies:
        name = p.get("name")
        is_failing = False

        if p.get("passing") is False:
            is_failing = True
        elif str(p.get("status")).strip().lower() == "fail":
            is_failing = True
        elif str(p.get("response")).strip().lower() == "fail":
            is_failing = True

        if name and is_failing:
            failing.append(name)

    print(f"[DEBUG] parsed failing_policies = {failing}")
    return failing


def main():
    base_dir = os.path.dirname(os.path.dirname(__file__))

    cfg = load_yaml(os.path.join(base_dir, "config", "orchestrator.yaml"))
    devmap = load_yaml(os.path.join(base_dir, "config", "device_map.yaml"))
    devices = devmap.get("devices", [])

    fleet = FleetClient(
        cfg["fleet"]["url"],
        cfg["fleet"]["api_token"],
        cfg["fleet"]["verify_tls"]
    )
    opa = OPAClient(cfg["opa"]["url"])
    ziti = ZitiMgmt(
        cfg["ziti"]["mgmt_url"],
        cfg["ziti"]["username"],
        cfg["ziti"]["password"],
        cfg["ziti"]["verify_tls"]
    )

    # IMPORTANT: authenticate to Ziti BEFORE any management API call
    ziti.login()

    # Reset all endpoint identities to baseline role on startup
    reset_identities_to_base_roles(
        ziti=ziti,
        devices=devices,
        identity_prefix=cfg["mapping"]["ziti_identity_prefix"]
    )

    poll = int(cfg["poll_interval_seconds"])
    decision_path = cfg["opa"]["decision_path"]

    db = db_init(cfg["logging"]["sqlite_path"])
    csv_f, csv_w = csv_init(cfg["logging"]["csv_path"])

    id_by_name = refresh_identity_cache(ziti)

    posture_attr_ok = cfg["posture_attributes"]["compliant"]
    posture_attr_q = cfg["posture_attributes"]["quarantine"]
    revoke = bool(cfg["enforcement"]["revoke_sessions_on_quarantine"])

    # state cache in memory
    last_state = {}

    last_identity_refresh = time.time()

    while True:
        try:
            # Refresh identity cache every 60 seconds
            if time.time() - last_identity_refresh >= 60:
                try:
                    id_by_name = refresh_identity_cache(ziti)
                    last_identity_refresh = time.time()
                    print("[INFO] identity cache refreshed")
                except Exception as e:
                    print(f"[WARN] failed to refresh identity cache: {e}")

            # Fetch hosts from Fleet
            hosts_resp = fleet.list_hosts(per_page=500)
            hosts = hosts_resp.get("hosts", hosts_resp.get("data", [])) or []

            # Build hostname index from Fleet
            host_by_hostname = {}
            for h in hosts:
                # Lấy tất cả các loại tên mà FleetDM giấu bên trong
                names_to_check = [
                    h.get("hostname", ""),
                    h.get("display_name", ""),
                    h.get("computer_name", "")
                ]
                
                # Lưu toàn bộ các tên này vào từ điển để đối chiếu
                for name in names_to_check:
                    hn = normalize_hostname(name)
                    if hn:
                        host_by_hostname[hn] = h

            # Process each mapped device
            for d in devices:
                try:
                    hostname = normalize_hostname(d.get("hostname", ""))
                    role_attr = (d.get("role") or "").strip()

                    if not hostname or not role_attr:
                        print(f"[WARN] invalid device map entry: {d}")
                        continue

                    fleet_host = host_by_hostname.get(hostname)
                    if not fleet_host:
                        print(f"[INFO] Fleet host not found or offline for hostname={hostname}")
                        continue

                    fleet_id = fleet_host.get("id")
                    tdetect = now_iso()

                    # Get host detail from Fleet and compute failing policies
                    host_detail = fleet.get_host(fleet_id)
                    failing = build_failing_policies(host_detail)

                    print(f"[INFO] host={hostname} failing_policies={failing}")

                    # Send data to OPA
                    opa_input = {
                        "device": {
                            "hostname": hostname,
                            "fleet_host_id": fleet_id
                        },
                        "fleet": {
                            "failing_policies": failing
                        }
                    }

                    tdecision = now_iso()
                    opa_resp = opa.decide(decision_path, opa_input)
                    result = opa_resp.get("result", {})

                    new_state = result.get("state", "quarantine")
                    score = int(result.get("score", 0))
                    reasons = result.get("reasons", [])

                    print(f"[INFO] host={hostname} opa_state={new_state} score={score} reasons={reasons}")

                    prev_state = last_state.get(hostname)

                    # Only enforce when state changes
                    if prev_state != new_state:
                        identity_name = f'{cfg["mapping"]["ziti_identity_prefix"]}{hostname}'
                        ident = id_by_name.get(identity_name)

                        ziti_identity_id = ""
                        if not ident:
                            print(f"[WARN] identity not found for hostname={hostname}, identity={identity_name}")
                        else:
                            ziti_identity_id = ident["id"]

                            current_attrs = set(ident.get("roleAttributes", []) or [])
                            current_attrs.add(role_attr)

                            # Remove old posture flags
                            current_attrs.discard(posture_attr_ok)
                            current_attrs.discard(posture_attr_q)

                            # Add new posture flag
                            if new_state == "compliant":
                                current_attrs.add(posture_attr_ok)
                            else:
                                current_attrs.add(posture_attr_q)

                            desired_attrs = sorted(current_attrs)
                            tenforce = now_iso()

                            ziti.patch_identity_role_attributes(ziti_identity_id, desired_attrs)
                            print(f"[INFO] patched {identity_name} -> {desired_attrs}")

                            # Keep local cache in sync
                            ident["roleAttributes"] = desired_attrs
                            id_by_name[identity_name] = ident

                            # Optional: revoke active sessions for fast enforcement
                            if revoke and new_state == "quarantine":
                                try:
                                    sess = ziti.list_sessions(limit=1000).get("data", [])
                                    for s in sess:
                                        if s.get("identityId") == ziti_identity_id:
                                            ziti.delete_session(s["id"])
                                            print(f"[INFO] revoked session {s['id']} for identity {identity_name}")
                                except Exception as e:
                                    print(f"[WARN] failed to revoke sessions for {identity_name}: {e}")

                        # Log event
                        ts = now_iso()
                        tenforce = now_iso()

                        db.execute("""
                          INSERT INTO posture_events(
                            ts, hostname, fleet_host_id, ziti_identity, ziti_identity_id,
                            prev_state, new_state, score, reasons, tdetect, tdecision, tenforce
                          )
                          VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
                        """, (
                            ts,
                            hostname,
                            fleet_id,
                            f'{cfg["mapping"]["ziti_identity_prefix"]}{hostname}',
                            ziti_identity_id,
                            prev_state,
                            new_state,
                            score,
                            json.dumps(reasons),
                            tdetect,
                            tdecision,
                            tenforce
                        ))
                        db.commit()

                        csv_w.writerow([
                            ts,
                            hostname,
                            fleet_id,
                            f'{cfg["mapping"]["ziti_identity_prefix"]}{hostname}',
                            ziti_identity_id,
                            prev_state,
                            new_state,
                            score,
                            json.dumps(reasons),
                            tdetect,
                            tdecision,
                            tenforce
                        ])
                        csv_f.flush()

                        last_state[hostname] = new_state

                except Exception as e:
                    print(f"[ERROR] failed processing device entry {d}: {e}")

        except Exception as e:
            print(f"[ERROR] main loop failure: {e}")

        time.sleep(poll)


if __name__ == "__main__":
    main()

package posture

import rego.v1

# ======= SỬA CÁC TÊN POLICY CHO KHỚP 100% VỚI FLEET UI =======
POLICY_MARKER := "All - Compliance marker present"
POLICY_FORBID_WIN := "Windows - Forbidden process not running (Calculator)"
POLICY_FORBID_MAC := "macOS - Forbidden process not running (Calculator)"
POLICY_FIREWALL_WIN := "Firewall Defender"
POLICY_MALWARE_LINUX := "[Security] No Crypto-Miner (XMRig) Running"
# =============================================================

default decision := {
  "state": "quarantine",
  "score": 0,
  "reasons": ["default_deny"],
  "ttl_seconds": 300
}

# fallback nếu input không có failing_policies
failing := input.fleet.failing_policies if {
  input.fleet.failing_policies
} else := []

policy_failing(name) if {
  name == failing[_]
}

# Marker phải pass
has_marker if {
  not policy_failing(POLICY_MARKER)
}

# Không được fail policy forbidden process (Bao trùm cả Windows, Mac và Linux)
no_forbidden if {
  not policy_failing(POLICY_FORBID_WIN)
  not policy_failing(POLICY_FORBID_MAC)
  not policy_failing(POLICY_MALWARE_LINUX)
}

# Firewall phải bật
firewall_ok if {
  not policy_failing(POLICY_FIREWALL_WIN)
}

marker_ok_score := 1 if { has_marker } else := 0
forbid_ok_score := 1 if { no_forbidden } else := 0
firewall_ok_score := 1 if { firewall_ok } else := 0

# Chia điểm đều cho 3 điều kiện
score := (34 * marker_ok_score) + (33 * forbid_ok_score) + (33 * firewall_ok_score)

reasons := sort(failing)

authorize if {
  has_marker
  no_forbidden
  firewall_ok
}

decision := {
  "state": "compliant",
  "score": score,
  "reasons": reasons,
  "ttl_seconds": 3600
} if {
  authorize
}

decision := {
  "state": "quarantine",
  "score": score,
  "reasons": reasons,
  "ttl_seconds": 300
} if {
  not authorize
}

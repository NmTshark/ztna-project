package posture

import rego.v1

default decision := {"state": "quarantine", "score": 0, "reasons": ["default_deny"], "ttl_seconds": 300}

score_weights := {
  "compliance_marker": 50,
  "no_forbidden_process": 50
}

policy_failing(name) {
  name == input.fleet.failing_policies[_]
}

has_marker := not policy_failing("All - Compliance marker present")

no_forbidden := not (
  policy_failing("Windows - Forbidden process not running (Calculator)")
  or policy_failing("macOS - Forbidden process not running (Calculator)")
)

bool_to_int(true) := 1
bool_to_int(false) := 0

score := s {
  s := 0
  s := s + (score_weights.compliance_marker * bool_to_int(has_marker))
  s := s + (score_weights.no_forbidden_process * bool_to_int(no_forbidden))
}

reasons[r] {
  policy_failing(_)
  r := input.fleet.failing_policies[_]
}

# critical violation: forbidden process policy failing => quarantine
critical := not no_forbidden

authorize {
  has_marker
  no_forbidden
}

decision := {
  "state": "compliant",
  "score": score,
  "reasons": sort(reasons),
  "ttl_seconds": 3600
} {
  authorize
  not critical
}

decision := {
  "state": "quarantine",
  "score": score,
  "reasons": sort(reasons),
  "ttl_seconds": 300
} {
  not authorize
}

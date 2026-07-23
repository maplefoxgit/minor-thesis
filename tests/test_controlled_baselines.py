from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
EXPERIMENTS_DIR = ROOT / "experiments"
for candidate in (ROOT, EXPERIMENTS_DIR):
    candidate_text = str(candidate)
    if candidate_text not in sys.path:
        sys.path.insert(0, candidate_text)

from run_e6_controlled_baselines import (  # noqa: E402
    DENY_ALL_CONDITION,
    PERMISSIVE_CONDITION,
    PROPOSED_CONDITION,
    run,
)


def test_controlled_baselines_isolate_safety_availability_tradeoff() -> None:
    result = run()
    conditions = result["conditions"]

    permissive = conditions[PERMISSIVE_CONDITION]
    assert permissive["required_reachability_rate"] == 1.0
    assert permissive["forbidden_path_block_rate"] == 0.0
    assert permissive["terminal_service_passed"] is False
    assert permissive["balanced_objective_passed"] is False

    deny_all = conditions[DENY_ALL_CONDITION]
    assert deny_all["required_reachability_rate"] == 0.0
    assert deny_all["forbidden_path_block_rate"] == 1.0
    assert deny_all["terminal_service_passed"] is True
    assert deny_all["balanced_objective_passed"] is False

    proposed = conditions[PROPOSED_CONDITION]
    assert proposed["required_reachability_rate"] == 1.0
    assert proposed["forbidden_path_block_rate"] == 1.0
    assert proposed["terminal_service_passed"] is True
    assert proposed["balanced_objective_passed"] is True

    assert result["comparison"]["only_condition_satisfying_all_objectives"] == PROPOSED_CONDITION
    assert result["status"] == "pass"

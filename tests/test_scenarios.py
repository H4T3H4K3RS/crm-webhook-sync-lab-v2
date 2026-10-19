"""Прогон всех сценариев из events/scenarios."""

import pytest

from tests.conftest import SCENARIOS, assert_deal, load, send


@pytest.mark.parametrize("path", SCENARIOS, ids=[p.stem for p in SCENARIOS])
def test_scenario(client, path):
    scenario = load(path)
    results = [send(client, e).json().get("result") for e in scenario["events"]]
    assert results == scenario["expected_results"], scenario["description"]
    for final in scenario["expected_final_state"]:
        assert_deal(client, final["deal_id"], final["status"], final["version"])

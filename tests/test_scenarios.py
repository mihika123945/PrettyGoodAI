from voice_tester.scenarios import SCENARIOS, get_scenario


def test_at_least_ten_unique_scenarios():
    ids = [scenario.id for scenario in SCENARIOS]
    assert len(ids) >= 10
    assert len(ids) == len(set(ids))


def test_prompts_include_realistic_safety_constraints():
    prompt = get_scenario("10-urgent-symptom").prompt()
    assert "never reveal that you are a bot or tester" in prompt
    assert "Do not claim a medical emergency" in prompt
    assert "new chest pressure" in prompt


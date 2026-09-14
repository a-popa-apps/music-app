from app import ai_budget

# ai_budget._calls is reset around every test by the autouse fixture in
# tests/conftest.py -- no file-local reset needed here.


def test_allows_calls_under_the_limit(monkeypatch):
    monkeypatch.setattr(ai_budget, "DAILY_AI_CALL_LIMIT", 3)
    assert ai_budget.allow_ai_call() is True
    assert ai_budget.allow_ai_call() is True
    assert ai_budget.allow_ai_call() is True


def test_blocks_once_the_daily_limit_is_reached(monkeypatch):
    monkeypatch.setattr(ai_budget, "DAILY_AI_CALL_LIMIT", 2)
    assert ai_budget.allow_ai_call() is True
    assert ai_budget.allow_ai_call() is True
    assert ai_budget.allow_ai_call() is False
    # still blocked, and doesn't somehow "use up" further slots
    assert ai_budget.allow_ai_call() is False


def test_calls_used_today_reflects_reservations(monkeypatch):
    monkeypatch.setattr(ai_budget, "DAILY_AI_CALL_LIMIT", 5)
    assert ai_budget.calls_used_today() == 0
    ai_budget.allow_ai_call()
    ai_budget.allow_ai_call()
    assert ai_budget.calls_used_today() == 2


def test_calls_used_today_does_not_reserve_a_slot(monkeypatch):
    monkeypatch.setattr(ai_budget, "DAILY_AI_CALL_LIMIT", 1)
    ai_budget.calls_used_today()
    ai_budget.calls_used_today()
    # reading status repeatedly didn't consume the one available slot
    assert ai_budget.allow_ai_call() is True


def test_a_new_day_gets_a_fresh_budget(monkeypatch):
    monkeypatch.setattr(ai_budget, "DAILY_AI_CALL_LIMIT", 1)
    monkeypatch.setattr(ai_budget, "_today_key", lambda: "2026-01-01")
    assert ai_budget.allow_ai_call() is True
    assert ai_budget.allow_ai_call() is False

    monkeypatch.setattr(ai_budget, "_today_key", lambda: "2026-01-02")
    assert ai_budget.allow_ai_call() is True


def test_limit_is_configurable_via_env_var(monkeypatch):
    monkeypatch.setenv("DAILY_AI_CALL_LIMIT", "42")
    import importlib

    reloaded = importlib.reload(ai_budget)
    assert reloaded.DAILY_AI_CALL_LIMIT == 42
    importlib.reload(ai_budget)  # restore the default for later tests

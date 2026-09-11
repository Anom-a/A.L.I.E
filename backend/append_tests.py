import os

tests = """

# ---------------------------------------------------------------------------
# Phase 5: Critic behavior
# ---------------------------------------------------------------------------

def test_primary_succeeds_critic_unsatisfied_fallback_succeeds(router: RouteToolUseCase) -> None:
    sq = _sq("How to repair an iPhone screen?")
    ev1 = _make_evidence(sub_question_id=sq.id, content="primary evidence")
    ev2 = _make_evidence(sub_question_id=sq.id, content="fallback evidence")
    
    primary = _FakeGateway(evidence=[ev1])
    fallback = _FakeGateway(evidence=[ev2])
    critic = _FakeCritic(satisfied=False)

    result = _build_use_case(router, primary, fallback, critic=critic).execute(sq)

    assert primary.call_count == 1
    assert critic.call_count == 1
    assert fallback.call_count == 1
    assert result.fallback_used is True
    assert result.resolved is True
    assert result.evidence == [ev2]


def test_primary_succeeds_critic_unsatisfied_fallback_fails(router: RouteToolUseCase) -> None:
    sq = _sq("How to repair an iPhone screen?")
    ev1 = _make_evidence(sub_question_id=sq.id, content="primary evidence")
    
    primary = _FakeGateway(evidence=[ev1])
    fallback = _FakeGateway(error=RuntimeError("fallback down"))
    critic = _FakeCritic(satisfied=False)

    result = _build_use_case(router, primary, fallback, critic=critic).execute(sq)

    assert primary.call_count == 1
    assert critic.call_count == 1
    assert fallback.call_count == 1
    assert result.fallback_used is True
    assert result.resolved is False
    assert result.evidence == []


def test_primary_empty_critic_not_called(router: RouteToolUseCase) -> None:
    sq = _sq("How to repair an iPhone screen?")
    fallback_ev = _make_evidence(sub_question_id=sq.id)
    
    primary = _FakeGateway(evidence=[])
    fallback = _FakeGateway(evidence=[fallback_ev])
    critic = _FakeCritic(satisfied=True)

    result = _build_use_case(router, primary, fallback, critic=critic).execute(sq)

    assert primary.call_count == 1
    assert critic.call_count == 0
    assert fallback.call_count == 1


def test_primary_fails_critic_not_called(router: RouteToolUseCase) -> None:
    sq = _sq("How to repair an iPhone screen?")
    fallback_ev = _make_evidence(sub_question_id=sq.id)
    
    primary = _FakeGateway(error=RuntimeError("primary down"))
    fallback = _FakeGateway(evidence=[fallback_ev])
    critic = _FakeCritic(satisfied=True)

    result = _build_use_case(router, primary, fallback, critic=critic).execute(sq)

    assert primary.call_count == 1
    assert critic.call_count == 0
    assert fallback.call_count == 1


def test_critic_failure_raises_critique_error(router: RouteToolUseCase) -> None:
    sq = _sq("How to repair an iPhone screen?")
    ev = _make_evidence(sub_question_id=sq.id)
    
    primary = _FakeGateway(evidence=[ev])
    fallback = _FakeGateway()
    critic = _FakeCritic(error=CritiqueError("LLM offline"))

    with pytest.raises(CritiqueError, match="LLM offline"):
        _build_use_case(router, primary, fallback, critic=critic).execute(sq)
"""

with open("tests/unit/test_retrieve_evidence.py", "a") as f:
    f.write(tests)

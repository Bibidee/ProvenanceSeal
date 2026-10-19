from pathlib import Path


def test_only_one_deployable_contract_source():
    contracts = sorted(path.name for path in Path("contracts").glob("*.py"))
    assert contracts == ["provenanceseal.py"]


def test_contract_contains_escrow_safety_choke_point():
    source = Path("contracts/provenanceseal.py").read_text(encoding="utf-8")
    assert "seal.deposit = u256(0)" in source
    assert "_send_gen(recipient, amount)" in source
    assert source.index("seal.deposit = u256(0)") < source.index("_send_gen(recipient, amount)")


def test_contract_preserves_requirements_and_challenge_origin():
    source = Path("contracts/provenanceseal.py").read_text(encoding="utf-8")
    assert "sponsor_requirements" in source
    assert "beneficiary_claim" in source
    assert "def _restore_challenge" in source
    assert 'self._restore_challenge(seal, "challenge_expired")' in source
    assert 'self._restore_challenge(seal, "challenge_invalid_evidence")' in source
    assert "challenge_review_deadline" in source
    assert "MAX_CHALLENGE_WINDOW - CHALLENGE_ADJUDICATION_WINDOW" in source
    assert '"original_evidence"' in source
    assert '"challenge_evidence"' in source
    assert 'identifier = _identifier(item.get("id"), "evidence id", 48).lower()' in source
    assert "challenge_sponsor_used" in source
    assert "challenge_beneficiary_used" in source
    assert "challenge_consumer_used" in source


def test_contract_has_no_unbounded_challenge_reversal():
    source = Path("contracts/provenanceseal.py").read_text(encoding="utf-8")
    challenge_block = source[source.index("def expire"):source.index("@gl.public.view", source.index("def expire"))]
    assert "self._restore_challenge(seal, \"challenge_expired\")" in challenge_block
    assert "self._settle(seal, seal.sponsor, REFUNDED_SPONSOR)" in challenge_block
    assert "challenge_review_deadline" in challenge_block
    assert "challenge_sponsor_used" in source
    assert "challenge_beneficiary_used" in source
    assert "challenge_consumer_used" in source

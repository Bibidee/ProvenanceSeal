from pathlib import Path


def test_only_one_deployable_contract_source():
    contracts = sorted(path.name for path in Path("contracts").glob("*.py"))
    assert contracts == ["provenanceseal.py"]


def test_contract_contains_escrow_safety_choke_point():
    source = Path("contracts/provenanceseal.py").read_text(encoding="utf-8")
    assert "seal.deposit = u256(0)" in source
    assert "_send_gen(recipient, amount)" in source
    assert source.index("seal.deposit = u256(0)") < source.index("_send_gen(recipient, amount)")

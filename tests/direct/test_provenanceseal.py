import hashlib
import json
from datetime import datetime, timezone

import pytest


CONTRACT = "contracts/provenanceseal.py"
ARTIFACT_URL = "https://release.example.org/build.txt"
MANIFEST_URL = "https://release.example.org/manifest.json"
EV1_URL = "https://ci.example.org/attestation.txt"
EV2_URL = "https://audit.example.net/attestation.txt"
ARTIFACT = b"ProvenanceSeal package 1.0.0 build PS-001."
MANIFEST = b'{"name":"provenanceseal","version":"1.0.0","build":"PS-001"}'
EV1 = b"CI confirms build PS-001 passed the release checks."
EV2 = b"Audit confirms build PS-001 matches the declared release manifest."


def digest(value):
    return "0x" + hashlib.sha256(value).hexdigest()


def address(value):
    return "0x" + value.hex() if isinstance(value, bytes) else value.as_hex


def now(vm):
    return int(datetime.fromisoformat(vm._datetime.replace("Z", "+00:00")).replace(tzinfo=timezone.utc).timestamp())


def deploy(vm, direct_deploy, alice):
    vm.sender = alice
    vm.check_pickling = True
    return direct_deploy(CONTRACT, sdk_version="v0.2.16")


def manifest():
    return json.dumps({"evidence": [
        {"id": "EV1", "authority": "ci.example.org", "url": EV1_URL, "hash": digest(EV1), "build_id": "PS-001", "claim": "Build passed release checks."},
        {"id": "EV2", "authority": "audit.example.net", "url": EV2_URL, "hash": digest(EV2), "build_id": "PS-001", "claim": "Build matches release manifest."},
    ]})


def setup(vm, answer=None):
    vm.mock_web(r"release\.example\.org/build\.txt", {"status": 200, "body": ARTIFACT})
    vm.mock_web(r"release\.example\.org/manifest\.json", {"status": 200, "body": MANIFEST})
    vm.mock_web(r"ci\.example\.org/attestation\.txt", {"status": 200, "body": EV1})
    vm.mock_web(r"audit\.example\.net/attestation\.txt", {"status": 200, "body": EV2})
    vm.mock_llm(r"Assess the exact hash-verified release artifacts", json.dumps(answer or {
        "artifact_match": "yes", "manifest_match": "yes", "evidence_support": "yes",
        "risk": "no", "confidence": 94, "rationale": "Both independent attestations support the exact build."}))


def create(contract, vm, alice, bob, charlie, **changes):
    vm.sender, vm.value = alice, 10**15
    values = {"seal_id": "PS-001", "beneficiary": address(bob), "consumer": address(charlie),
              "package_name": "provenanceseal", "claimed_version": "1.0.0", "artifact_url": ARTIFACT_URL,
              "artifact_hash": digest(ARTIFACT), "manifest_url": MANIFEST_URL, "manifest_hash": digest(MANIFEST),
              "summary": "Release PS-001 is ready for provenance verification.", "submission_window": 7200, "review_window": 7200}
    values.update(changes)
    contract.create_seal(**values)
    vm.value = 0
    return values


def activate(contract, vm, bob):
    vm.sender = bob
    contract.accept_seal("PS-001")
    contract.submit_release("PS-001", manifest(), "Release PS-001 includes the exact artifact and manifest.")


def test_valid_proposal_persists_exact_commitments(direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie):
    contract = deploy(direct_vm, direct_deploy, direct_alice)
    create(contract, direct_vm, direct_alice, direct_bob, direct_charlie)
    row = contract.get_seal("PS-001")
    assert row.status == "funded"
    assert row.artifact_hash == digest(ARTIFACT)
    assert row.manifest_hash == digest(MANIFEST)
    assert int(row.deposit) == 10**15
    assert contract.get_info()["version"] == "0.1.1"


@pytest.mark.parametrize("field,value", [
    ("seal_id", "bad id"), ("artifact_hash", "0x12"), ("manifest_hash", "0x12"),
    ("artifact_url", "http://release.example.org/build.txt"), ("artifact_url", "https://127.0.0.1/build"),
    ("artifact_url", "https://10.0.0.1/build"), ("artifact_url", "https://172.16.0.1/build"),
    ("artifact_url", "https://192.168.1.1/build"), ("artifact_url", "https://169.254.1.1/build"),
    ("artifact_url", "https://[::1]/build"), ("artifact_url", "https://[fc00::1]/build"),
    ("artifact_url", "https://[fe80::1]/build"), ("artifact_url", "https://[::ffff:192.168.1.1]/build"),
    ("artifact_url", "https://metadata.internal/build"), ("artifact_url", "https://service.home.arpa/build"),
    ("summary", " "), ("package_name", ""),
])
def test_creation_rejects_malformed_inputs(direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie, field, value):
    contract = deploy(direct_vm, direct_deploy, direct_alice)
    with direct_vm.expect_revert():
        create(contract, direct_vm, direct_alice, direct_bob, direct_charlie, **{field: value})


def test_approved_review_enters_challenge_window(direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie):
    contract = deploy(direct_vm, direct_deploy, direct_alice)
    create(contract, direct_vm, direct_alice, direct_bob, direct_charlie)
    activate(contract, direct_vm, direct_bob)
    setup(direct_vm)
    direct_vm.sender = direct_alice
    contract.review("PS-001")
    row = contract.get_seal("PS-001")
    assert row.status == "preliminary_approved"
    assert int(row.confidence) == 94


def test_pending_cannot_be_consumed_and_only_consumer_can_settle(direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie):
    contract = deploy(direct_vm, direct_deploy, direct_alice)
    create(contract, direct_vm, direct_alice, direct_bob, direct_charlie)
    direct_vm.sender = direct_charlie
    with direct_vm.expect_revert():
        contract.settle_approved("PS-001")


def test_malformed_model_output_is_retryable(direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie):
    contract = deploy(direct_vm, direct_deploy, direct_alice)
    create(contract, direct_vm, direct_alice, direct_bob, direct_charlie)
    activate(contract, direct_vm, direct_bob)
    setup(direct_vm, answer={"artifact_match": True})
    direct_vm.sender = direct_alice
    contract.review("PS-001")
    row = contract.get_seal("PS-001")
    assert row.status == "retryable"
    assert int(row.deposit) == 10**15


def test_string_confidence_is_normalized_without_changing_approval(direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie):
    contract = deploy(direct_vm, direct_deploy, direct_alice)
    create(contract, direct_vm, direct_alice, direct_bob, direct_charlie)
    activate(contract, direct_vm, direct_bob)
    setup(direct_vm, answer={"artifact_match": "yes", "manifest_match": "yes", "evidence_support": "yes", "risk": "no", "confidence": "90", "rationale": "Verified."})
    direct_vm.sender = direct_alice
    contract.review("PS-001")
    assert contract.get_seal("PS-001").status == "preliminary_approved"


def test_material_semantic_rejection_blocks_without_payout(direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie):
    contract = deploy(direct_vm, direct_deploy, direct_alice)
    create(contract, direct_vm, direct_alice, direct_bob, direct_charlie)
    activate(contract, direct_vm, direct_bob)
    setup(direct_vm, answer={"artifact_match": "no", "manifest_match": "yes", "evidence_support": "yes", "risk": "yes", "confidence": 95, "rationale": "The committed build does not match."})
    direct_vm.sender = direct_alice
    contract.review("PS-001")
    row = contract.get_seal("PS-001")
    assert row.status == "preliminary_blocked"
    assert int(row.deposit) == 10**15


def test_blocked_refund_requires_sponsor(direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie):
    contract = deploy(direct_vm, direct_deploy, direct_alice)
    create(contract, direct_vm, direct_alice, direct_bob, direct_charlie)
    activate(contract, direct_vm, direct_bob)
    setup(direct_vm, answer={"artifact_match": "no", "manifest_match": "yes", "evidence_support": "yes",
                            "risk": "yes", "confidence": 95, "rationale": "The committed build does not match."})
    direct_vm.sender = direct_alice
    contract.review("PS-001")
    row = contract.get_seal("PS-001")
    direct_vm._datetime = datetime.fromtimestamp(int(row.challenge_deadline), timezone.utc).isoformat().replace("+00:00", "Z")
    contract.finalize_preliminary("PS-001")
    assert contract.get_seal("PS-001").status == "blocked"
    direct_vm.sender = direct_bob
    with direct_vm.expect_revert():
        contract.refund_blocked("PS-001")
    assert int(contract.get_seal("PS-001").deposit) == 10**15
    direct_vm.sender = direct_alice
    contract.refund_blocked("PS-001")
    assert contract.get_seal("PS-001").status == "refunded_sponsor"
    assert int(contract.get_seal("PS-001").deposit) == 0


def test_evidence_manifest_rejects_duplicate_origins(direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie):
    contract = deploy(direct_vm, direct_deploy, direct_alice)
    create(contract, direct_vm, direct_alice, direct_bob, direct_charlie)
    direct_vm.sender = direct_bob
    contract.accept_seal("PS-001")
    duplicate_origin = json.dumps({"evidence": [
        {"id": "EV1", "authority": "ci.example.org", "url": EV1_URL, "hash": digest(EV1), "build_id": "PS-001", "claim": "Build passed release checks."},
        {"id": "EV2", "authority": "audit.example.net", "url": "https://ci.example.org/second.txt", "hash": digest(EV2), "build_id": "PS-001", "claim": "Build matches release manifest."},
    ]})
    with direct_vm.expect_revert():
        contract.submit_release("PS-001", duplicate_origin, "Release PS-001 includes the exact artifact and manifest.")


def test_approved_guard_can_be_finalized_and_settled_by_consumer(direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie):
    contract = deploy(direct_vm, direct_deploy, direct_alice)
    create(contract, direct_vm, direct_alice, direct_bob, direct_charlie)
    activate(contract, direct_vm, direct_bob)
    setup(direct_vm)
    direct_vm.sender = direct_alice
    contract.review("PS-001")
    row = contract.get_seal("PS-001")
    direct_vm._datetime = datetime.fromtimestamp(int(row.challenge_deadline), timezone.utc).isoformat().replace("+00:00", "Z")
    contract.finalize_preliminary("PS-001")
    direct_vm.sender = direct_charlie
    contract.settle_approved("PS-001")
    settled = contract.get_seal("PS-001")
    assert settled.status == "paid_beneficiary"
    assert int(settled.deposit) == 0
    assert int(settled.settled_amount) == 10**15

import hashlib
import json
from datetime import datetime, timezone

import pytest


CONTRACT = "contracts/provenanceseal.py"
ARTIFACT_URL = "https://release.example.org/build.txt"
MANIFEST_URL = "https://release.example.org/manifest.json"
EV1_URL = "https://ci.example.org/attestation.txt"
EV2_URL = "https://audit.example.net/attestation.txt"
CHALLENGE_URL = "https://challenge.example.com/attestation.txt"
ARTIFACT = b"ProvenanceSeal package 1.0.0 build PS-001."
MANIFEST = b'{"name":"provenanceseal","version":"1.0.0","build":"PS-001"}'
EV1 = b"CI confirms build PS-001 passed the release checks."
EV2 = b"Audit confirms build PS-001 matches the declared release manifest."
CHALLENGE = b"Challenge evidence for PS-001."


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


def challenge_manifest(challenge_hash=None):
    return json.dumps({"evidence": [
        {"id": "CH1", "authority": "challenge.example.com", "url": CHALLENGE_URL,
         "hash": challenge_hash or digest(CHALLENGE), "build_id": "PS-001",
         "claim": "Challenge evidence addresses the committed build."},
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
    assert contract.get_info()["version"] == "0.2.0"


def test_sponsor_requirements_are_immutable_after_beneficiary_submission(direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie):
    contract = deploy(direct_vm, direct_deploy, direct_alice)
    create(contract, direct_vm, direct_alice, direct_bob, direct_charlie)
    original = contract.get_seal("PS-001").sponsor_requirements
    direct_vm.sender = direct_bob
    contract.accept_seal("PS-001")
    contract.submit_release("PS-001", manifest(), "Beneficiary claim with different wording.")
    row = contract.get_seal("PS-001")
    assert row.sponsor_requirements == original
    assert row.summary == "Beneficiary claim with different wording."


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


def test_provider_failure_is_retryable_and_keeps_escrow(direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie):
    contract = deploy(direct_vm, direct_deploy, direct_alice)
    create(contract, direct_vm, direct_alice, direct_bob, direct_charlie)
    activate(contract, direct_vm, direct_bob)
    direct_vm.mock_web(r"release\.example\.org/build\.txt", {"status": 503, "body": b"offline"})
    direct_vm.mock_web(r"release\.example\.org/manifest\.json", {"status": 200, "body": MANIFEST})
    direct_vm.mock_web(r"ci\.example\.org/attestation\.txt", {"status": 200, "body": EV1})
    direct_vm.mock_web(r"audit\.example\.net/attestation\.txt", {"status": 200, "body": EV2})
    direct_vm.mock_llm(r"Assess the exact hash-verified release artifacts", json.dumps({
        "artifact_match": "yes", "manifest_match": "yes", "evidence_support": "yes",
        "risk": "no", "confidence": 95, "rationale": "Unused because the provider is unavailable.",
    }))
    direct_vm.sender = direct_alice
    contract.review("PS-001")
    row = contract.get_seal("PS-001")
    assert row.status == "retryable"
    assert row.reason == "fetch_unavailable"
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


def test_finalize_and_consumer_timeout_are_strictly_deadline_bound(direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie):
    contract = deploy(direct_vm, direct_deploy, direct_alice)
    create(contract, direct_vm, direct_alice, direct_bob, direct_charlie)
    activate(contract, direct_vm, direct_bob)
    setup(direct_vm)
    direct_vm.sender = direct_alice
    contract.review("PS-001")
    row = contract.get_seal("PS-001")
    assert int(row.challenge_deadline) - now(direct_vm) == 3600
    before = datetime.fromtimestamp(int(row.challenge_deadline) - 1, timezone.utc).isoformat().replace("+00:00", "Z")
    direct_vm._datetime = before
    with direct_vm.expect_revert():
        contract.finalize_preliminary("PS-001")
    direct_vm._datetime = datetime.fromtimestamp(int(row.challenge_deadline), timezone.utc).isoformat().replace("+00:00", "Z")
    contract.finalize_preliminary("PS-001")
    approved = contract.get_seal("PS-001")
    assert int(approved.consumer_settle_after) == int(row.challenge_deadline) + 2 * 3600
    direct_vm.sender = direct_bob
    with direct_vm.expect_revert():
        contract.settle_after_consumer_timeout("PS-001")
    assert approved.status == "approved"
    assert int(approved.deposit) == 10**15


def test_settlement_is_terminal_and_replay_is_rejected(direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie):
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
    with direct_vm.expect_revert():
        contract.settle_approved("PS-001")
    with direct_vm.expect_revert():
        contract.settle_after_consumer_timeout("PS-001")
    settled = contract.get_seal("PS-001")
    assert settled.status == "paid_beneficiary"
    assert int(settled.deposit) == 0
    assert int(settled.settled_amount) == 10**15


def test_failed_payable_creation_does_not_leave_a_seal_or_active_count(direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie):
    contract = deploy(direct_vm, direct_deploy, direct_alice)
    direct_vm.sender, direct_vm.value = direct_alice, 10**15
    with direct_vm.expect_revert():
        create(contract, direct_vm, direct_alice, direct_bob, direct_charlie, summary=" ")
    with direct_vm.expect_revert():
        contract.get_seal("PS-001")
    direct_vm.value = 0
    create(contract, direct_vm, direct_alice, direct_bob, direct_charlie)
    assert int(contract.get_seal("PS-001").deposit) == 10**15


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


def test_challenge_expiry_preserves_approved_outcome_and_escrow(direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie):
    contract = deploy(direct_vm, direct_deploy, direct_alice)
    create(contract, direct_vm, direct_alice, direct_bob, direct_charlie)
    activate(contract, direct_vm, direct_bob)
    setup(direct_vm)
    direct_vm.sender = direct_alice
    contract.review("PS-001")
    row = contract.get_seal("PS-001")
    contract.challenge("PS-001", "CH-001", challenge_manifest(), "Please re-check this release.")
    assert contract.get_seal("PS-001").status == "challenged"
    direct_vm._datetime = datetime.fromtimestamp(int(row.challenge_deadline), timezone.utc).isoformat().replace("+00:00", "Z")
    contract.expire("PS-001")
    restored = contract.get_seal("PS-001")
    assert restored.status == "preliminary_approved"
    assert int(restored.deposit) == 10**15
    direct_vm.sender = direct_charlie
    with direct_vm.expect_revert():
        contract.settle_approved("PS-001")
    contract.finalize_preliminary("PS-001")
    contract.settle_approved("PS-001")
    assert contract.get_seal("PS-001").status == "paid_beneficiary"


def test_consumer_can_settle_immediately_and_sponsor_cannot_refund_approved_escrow(direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie):
    contract = deploy(direct_vm, direct_deploy, direct_alice)
    create(contract, direct_vm, direct_alice, direct_bob, direct_charlie)
    activate(contract, direct_vm, direct_bob)
    setup(direct_vm)
    direct_vm.sender = direct_alice
    contract.review("PS-001")
    row = contract.get_seal("PS-001")
    direct_vm._datetime = datetime.fromtimestamp(int(row.challenge_deadline), timezone.utc).isoformat().replace("+00:00", "Z")
    contract.finalize_preliminary("PS-001")
    direct_vm.sender = direct_alice
    with direct_vm.expect_revert():
        contract.refund_blocked("PS-001")
    direct_vm.sender = direct_charlie
    contract.settle_approved("PS-001")
    settled = contract.get_seal("PS-001")
    assert settled.status == "paid_beneficiary"
    assert int(settled.deposit) == 0
    assert int(settled.settled_amount) == 10**15
    assert int(contract.sponsor_counts[address(direct_alice).lower()]) == 0


@pytest.mark.parametrize("offset", [0, 1])
def test_beneficiary_fallback_requires_exact_two_hour_boundary(direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie, offset):
    contract = deploy(direct_vm, direct_deploy, direct_alice)
    create(contract, direct_vm, direct_alice, direct_bob, direct_charlie)
    activate(contract, direct_vm, direct_bob)
    setup(direct_vm)
    direct_vm.sender = direct_alice
    contract.review("PS-001")
    row = contract.get_seal("PS-001")
    direct_vm._datetime = datetime.fromtimestamp(int(row.challenge_deadline), timezone.utc).isoformat().replace("+00:00", "Z")
    contract.finalize_preliminary("PS-001")
    approved = contract.get_seal("PS-001")
    direct_vm.sender = direct_bob
    before_timeout = datetime.fromtimestamp(int(approved.consumer_settle_after) - 1, timezone.utc).isoformat().replace("+00:00", "Z")
    direct_vm._datetime = before_timeout
    with direct_vm.expect_revert():
        contract.settle_after_consumer_timeout("PS-001")
    direct_vm._datetime = datetime.fromtimestamp(int(approved.consumer_settle_after) + offset, timezone.utc).isoformat().replace("+00:00", "Z")
    contract.settle_after_consumer_timeout("PS-001")
    settled = contract.get_seal("PS-001")
    assert settled.status == "paid_beneficiary"
    assert int(settled.deposit) == 0
    assert int(settled.settled_amount) == 10**15


def test_approved_escrow_is_not_automatically_refunded_when_consumer_window_expires(direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie):
    contract = deploy(direct_vm, direct_deploy, direct_alice)
    create(contract, direct_vm, direct_alice, direct_bob, direct_charlie)
    activate(contract, direct_vm, direct_bob)
    setup(direct_vm)
    direct_vm.sender = direct_alice
    contract.review("PS-001")
    row = contract.get_seal("PS-001")
    direct_vm._datetime = datetime.fromtimestamp(int(row.challenge_deadline), timezone.utc).isoformat().replace("+00:00", "Z")
    contract.finalize_preliminary("PS-001")
    approved = contract.get_seal("PS-001")
    direct_vm._datetime = datetime.fromtimestamp(int(approved.consumer_settle_after) + 1, timezone.utc).isoformat().replace("+00:00", "Z")
    still_available = contract.get_seal("PS-001")
    assert still_available.status == "approved"
    assert int(still_available.deposit) == 10**15
    assert int(still_available.settled_amount) == 0
    direct_vm.sender = direct_alice
    with direct_vm.expect_revert():
        contract.settle_approved("PS-001")


def test_invalid_challenge_evidence_cannot_block_original_approval(direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie):
    contract = deploy(direct_vm, direct_deploy, direct_alice)
    create(contract, direct_vm, direct_alice, direct_bob, direct_charlie)
    activate(contract, direct_vm, direct_bob)
    setup(direct_vm)
    direct_vm.sender = direct_alice
    contract.review("PS-001")
    direct_vm.mock_web(r"challenge\.example\.com/attestation\.txt", {"status": 200, "body": CHALLENGE})
    contract.challenge("PS-001", "CH-INVALID", challenge_manifest(digest(b"not-the-response")), "Malformed challenge source.")
    contract.review_challenge("PS-001")
    row = contract.get_seal("PS-001")
    assert row.status == "preliminary_approved"
    assert row.reason == "challenge_invalid_evidence"
    assert int(row.deposit) == 10**15


def test_valid_challenge_can_overturn_approval_and_refund_sponsor(direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie):
    contract = deploy(direct_vm, direct_deploy, direct_alice)
    create(contract, direct_vm, direct_alice, direct_bob, direct_charlie)
    activate(contract, direct_vm, direct_bob)
    setup(direct_vm)
    direct_vm.sender = direct_alice
    contract.review("PS-001")
    contract.challenge("PS-001", "CH-VALID", challenge_manifest(), "Adverse evidence is attached.")
    direct_vm.clear_mocks()
    direct_vm.mock_web(r"release\.example\.org/build\.txt", {"status": 200, "body": ARTIFACT})
    direct_vm.mock_web(r"release\.example\.org/manifest\.json", {"status": 200, "body": MANIFEST})
    direct_vm.mock_web(r"ci\.example\.org/attestation\.txt", {"status": 200, "body": EV1})
    direct_vm.mock_web(r"audit\.example\.net/attestation\.txt", {"status": 200, "body": EV2})
    direct_vm.mock_web(r"challenge\.example\.com/attestation\.txt", {"status": 200, "body": CHALLENGE})
    direct_vm.mock_llm(r"Assess the exact hash-verified release artifacts", json.dumps({
        "artifact_match": "no", "manifest_match": "yes", "evidence_support": "no",
        "risk": "yes", "confidence": 95, "rationale": "The challenge identifies an adverse release mismatch.",
    }))
    contract.review_challenge("PS-001")
    assert contract.get_seal("PS-001").status == "blocked"
    contract.refund_blocked("PS-001")
    row = contract.get_seal("PS-001")
    assert row.status == "refunded_sponsor"
    assert int(row.deposit) == 0


def test_challenge_slot_cannot_be_reused_after_invalid_review(direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie):
    contract = deploy(direct_vm, direct_deploy, direct_alice)
    create(contract, direct_vm, direct_alice, direct_bob, direct_charlie)
    activate(contract, direct_vm, direct_bob)
    setup(direct_vm)
    direct_vm.sender = direct_alice
    contract.review("PS-001")
    direct_vm.mock_web(r"challenge\.example\.com/attestation\.txt", {"status": 200, "body": CHALLENGE})
    contract.challenge("PS-001", "CH-ONCE", challenge_manifest(digest(b"wrong")), "Invalid evidence.")
    contract.review_challenge("PS-001")
    with direct_vm.expect_revert():
        contract.challenge("PS-001", "CH-TWICE", challenge_manifest(), "Try again.")


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

# ProvenanceSeal

Current contract release: **v0.2.0**, deployed and source-verified on GenLayer
Studionet (chain ID `61999`).

ProvenanceSeal is a standalone GenLayer Intelligent Contract primitive for
hash-bound software release provenance with GEN escrow. A sponsor commits to a
package and version, a beneficiary submits a release artifact, dependency
manifest, and corroborating evidence, and independent validators determine
whether all of those exact bytes describe the same build.

It is intentionally not a frontend or a generic AI oracle. The contract keeps
the authorization consequence small and auditable: approve, block, retry, or
refund.

## Why GenLayer

A conventional single verifier could selectively fetch favorable evidence or
accept a summary without checking the committed bytes. ProvenanceSeal makes the
leader and validators independently retrieve the artifact, manifest, and
evidence, verify each SHA-256 commitment, and independently judge the bounded
semantic fields. Consensus is required before escrow can become payable.

## Core flow

`funded -> active -> submitted -> preliminary_approved | preliminary_blocked`

An approved preliminary result has a one-hour challenge filing window. A
challenge accepted during that window starts its own bounded adjudication
deadline, so a legitimate challenge filed just before the filing cutoff remains
reviewable after that cutoff. An unchallenged result becomes `approved` only
after the filing window closes; the designated consumer can settle immediately,
and the beneficiary receives the escrow. The consumer has an exclusive two-hour
settlement window; once it expires, the beneficiary can settle independently.
That timeout only unlocks the beneficiary fallback: it never refunds the
sponsor, cancels the release, or pays automatically. A blocked result refunds
the sponsor. Challenge opportunities are role-scoped and bounded: a preliminary
approval can be challenged only by the sponsor, while a preliminary block gives
the beneficiary and consumer one independent adverse-review opportunity each.
An invalid, expired, or unavailable attempt clears only the active challenge and
marks that role as used, so a benefiting participant cannot exhaust the
opposing party's path and no role can retry indefinitely. Challenge evidence
must use IDs normalized to lowercase and URL origins distinct from the original
evidence, and semantic review receives original and challenge evidence in
separate labeled fields. Only a consensus-backed adverse challenge changes an
approval to `blocked`; only the sponsor can claim a blocked refund.
Provider/network errors and malformed model output become `retryable`, never an
approval. Every payout zeros the stored deposit and persists the terminal state
before the single transfer helper emits GEN.

## Settlement timing

- Preliminary approval opens a **1-hour challenge filing window**.
- Accepting a challenge starts a separate bounded **1-hour adjudication
  deadline**; the filing deadline never controls review eligibility.
- After finalization, the designated consumer may call `settle_approved`
  immediately and exclusively for **2 hours**.
- At exactly 2 hours, and after it, the beneficiary may call
  `settle_after_consumer_timeout` independently.
- The timeout does not trigger a callback, refund, cancellation, or automatic
  payout. If neither authorized party acts, the approved escrow remains held
  and available for settlement.

## What is committed

The sponsor commits exact HTTPS URLs, SHA-256 hashes, and immutable acceptance
requirements for the release artifact and dependency manifest. The beneficiary
submits a canonical evidence manifest and a separate untrusted claim summary
with evidence IDs, declared authorities, URLs, hashes, build IDs, and claims.
Declared authorities are corroboration labels, not proof of real-world identity.
The model receives the sponsor requirements, beneficiary claim, verified artifact
and evidence as quoted untrusted data; instructions inside those values are never
reviewer instructions.

## Security boundaries

The contract rejects malformed IDs, zero addresses, non-HTTPS or credentialed
URLs, IP literals, local/internal hostnames, bad hashes, oversized/empty artifacts,
duplicate evidence IDs (after lowercase normalization) or origins, insufficient declared-authority corroboration,
and illegal lifecycle transitions. Evidence origins must be distinct within a
manifest; declared authority labels remain descriptive and are not identity
proofs. The model response must contain exactly the six documented keys,
tri-state semantic strings, integer confidence, and a nonempty string rationale.
Validator equivalence compares the final authorization outcome, all material
semantic fields, and a bounded confidence delta; malformed payloads fail closed
and rationale text is not authorization data. Uncertainty, provider failure,
unavailable evidence, invalid UTF-8, and semantic risk fail closed.

URL admission cannot prove DNS resolution or redirect safety, declared
authorities do not establish identity, and semantic-model judgments can still
be wrong or unavailable. Response-size limits are enforced after the runtime
returns a response because the runtime does not expose a trusted pre-fetch byte
limit. Integrators must verify the finalized child transfer receipt and credited
value after settlement; a dispatched child transfer is not proof of beneficiary
credit. Direct Mode can exercise settlement ordering and replay guards, but it
does not expose atomic rollback for a mocked external transfer failure; that
property remains a supported-runtime verification item.

## Development

```text
python -m pip install -r requirements.txt
python -m pytest tests -q
python scripts/preflight.py
genvm-lint check contracts/provenanceseal.py --json
genvm-lint schema contracts/provenanceseal.py --output artifacts/provenanceseal.abi.json
```

Only `contracts/provenanceseal.py` is deployable. Tests and documentation are
kept outside `contracts/` so GenVM lint cannot mistake pytest imports for
contract sources. The v0.2.0 source is frozen, CI is green, and the current
Studionet deployment is compared byte-for-byte in `docs/DEPLOYMENT.md`. The
historical v0.1.1 deployment is documented separately and is not source-parity
evidence for this release.

## Current Studionet deployment

The finalized v0.2.0 deployment and its exact source hash are recorded in
`docs/DEPLOYMENT.md`. A bounded live seal was also exercised: the review failed
closed with `artifact_too_large` because the deployed source is larger than the
contract's 20,000-byte fetch limit, and the sponsor escrow was refunded after
the challenge window. No successful beneficiary payout is claimed. A future
successful lifecycle must use a smaller, independently hashable release
artifact; the contract source itself is not a suitable live artifact under the
current limit.

## Downstream integration

Another Intelligent Contract may treat `status == "approved"` as an
authorization gate for a release action, but it should require the designated
consumer to call `settle_approved`, verify the terminal `paid_beneficiary`
record, and independently inspect the child transfer receipt. ProvenanceSeal
does not execute the external release itself and does not prove identity or
truth outside the committed evidence.

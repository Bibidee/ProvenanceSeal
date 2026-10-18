# ProvenanceSeal

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

An approved preliminary result has a bounded challenge window. After an
unchallenged window it becomes `approved`; only the designated consumer can
settle it, and the beneficiary receives the escrow. A blocked result, expired
submission, unresolved challenge, or cancellation refunds the sponsor.
Provider/network errors and malformed model output become `retryable`, never an
approval. Every payout zeros the stored deposit and persists the terminal state
before the single transfer helper emits GEN.

## What is committed

The sponsor commits exact HTTPS URLs and SHA-256 hashes for the release artifact
and dependency manifest. The beneficiary submits a canonical evidence manifest
with evidence IDs, declared authorities, URLs, hashes, build IDs, and claims.
Declared authorities are corroboration labels, not proof of real-world identity.
The model receives the verified artifact and evidence as quoted untrusted data;
instructions inside those artifacts are never reviewer instructions.

## Security boundaries

The contract rejects malformed IDs, zero addresses, non-HTTPS or credentialed
URLs, IP literals, local hostnames, bad hashes, oversized/empty artifacts,
duplicate evidence IDs, insufficient declared-authority corroboration, and
illegal lifecycle transitions. Validator equivalence compares the final
authorization outcome, all material semantic fields, and confidence within a
bounded range; rationale text is not authorization data. Uncertainty, provider
failure, unavailable evidence, invalid UTF-8, and semantic risk fail closed.

URL admission cannot prove DNS resolution or redirect safety, declared
authorities do not establish identity, and semantic-model judgments can still
be wrong or unavailable. Integrators must verify the finalized child transfer
receipt and credited value after settlement.

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
contract sources. StudioNet deployment and live evidence will be added only
after the source is frozen, CI is green, and the deployed source is compared
byte-for-byte.

## Downstream integration

Another Intelligent Contract may treat `status == "approved"` as an
authorization gate for a release action, but it should require the designated
consumer to call `settle_approved`, verify the terminal `paid_beneficiary`
record, and independently inspect the child transfer receipt. ProvenanceSeal
does not execute the external release itself and does not prove identity or
truth outside the committed evidence.

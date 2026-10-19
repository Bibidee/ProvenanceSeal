# ProvenanceSeal

Current contract release: **v0.2.0** (remediation branch; not yet deployed).

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
settle it, and the beneficiary receives the escrow. A blocked result refunds the
sponsor. A challenge is single-use and bounded: expiry, malformed evidence, or
provider uncertainty restores the original preliminary outcome and never moves
the escrow. Only a consensus-backed adverse challenge changes an approval to
`blocked`; only the sponsor can claim a blocked refund. Provider/network errors
and malformed model output become `retryable`, never an approval. Every payout
zeros the stored deposit and persists the terminal state before the single
transfer helper emits GEN.

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
duplicate evidence IDs or origins, insufficient declared-authority corroboration,
and illegal lifecycle transitions. Evidence origins must be distinct within a
manifest; declared authority labels remain descriptive and are not identity
proofs. Validator equivalence compares the final authorization outcome, all
material semantic fields, and a bounded confidence delta; rationale text is not
authorization data. Uncertainty, provider failure, unavailable evidence, invalid
UTF-8, and semantic risk fail closed.

URL admission cannot prove DNS resolution or redirect safety, declared
authorities do not establish identity, and semantic-model judgments can still
be wrong or unavailable. Response-size limits are enforced after the runtime
returns a response because the runtime does not expose a trusted pre-fetch byte
limit. Integrators must verify the finalized child transfer receipt and credited
value after settlement; a dispatched child transfer is not proof of beneficiary
credit.

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
contract sources. The v0.2.0 source must be frozen, CI must be green, and a
future Studionet 61999 deployment must be compared byte-for-byte before it is
described as current. The historical v0.1.1 deployment is documented separately
in `docs/DEPLOYMENT.md` and is not source-parity evidence for this branch.

## Downstream integration

Another Intelligent Contract may treat `status == "approved"` as an
authorization gate for a release action, but it should require the designated
consumer to call `settle_approved`, verify the terminal `paid_beneficiary`
record, and independently inspect the child transfer receipt. ProvenanceSeal
does not execute the external release itself and does not prove identity or
truth outside the committed evidence.

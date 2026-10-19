# ProvenanceSeal design (v0.2.0)

## Purpose

ProvenanceSeal binds a software artifact, its dependency manifest, and release
evidence to exact bytes. GenLayer validators inspect those bytes and agree on a
bounded semantic decision before escrow can settle. The contract is a release
gate, not an identity oracle or a guarantee that a release is truthful in the
real world.

## Decision model

The sponsor's requirements are immutable after `create_seal`. The beneficiary's
later `summary` is retained as a claim and is supplied as untrusted context; it
cannot replace the sponsor requirements.

The reviewer must return exactly six fields: `artifact_match`,
`manifest_match`, `evidence_support`, and `risk` (`yes`, `no`, or `unclear`), an
integer `confidence` from 0 to 100, and a bounded `rationale`. Approval requires
all three positive matches, `risk == no`, and confidence at least 75. A material
negative is `blocked`; uncertainty, low confidence, malformed output, or an
external execution failure is `retryable` or an integrity block. Rationale is
never used to authorize payment.

Validators must agree on the decision kind, outcome, all material semantic
fields, and confidence within 20 points. Malformed validator payloads fail
equivalence rather than being coerced. Validators do not need identical prose;
this allows harmless explanation variance without changing an authorization
consequence.

## Evidence independence

Each evidence record declares an authority label and a URL. A normal release
manifest must contain at least two distinct labels and distinct HTTPS host
origins, so two paths on one host cannot be counted as independent
corroboration. Labels remain descriptive metadata; they do not prove the
authority's real-world identity. Challenge manifests are smaller and single-use;
their evidence IDs and URL origins must not overlap the original manifest, and
the semantic review receives original and challenge evidence in separate fields.
Challenge evidence does not silently become original corroboration.

## Escrow ordering

GEN enters through `create_seal` and is tracked in `deposit`. All release paths
read that ledger, set it to zero, persist terminal state and accounting, then
call `_send_gen`. A second settlement therefore fails before any transfer. The
active-case counter is decremented exactly once on terminal settlement.

## Settlement timing

Preliminary approval opens a one-hour challenge filing window.
`finalize_preliminary` is rejected before the exact deadline and is allowed at
the deadline. A challenge accepted before filing closes starts a separate
one-hour adjudication deadline; review uses that deadline, not the filing
deadline, so a late-filed legitimate challenge remains reviewable. Final
approval gives the designated consumer an exclusive two-hour settlement window;
`settle_approved` is available immediately, while
`settle_after_consumer_timeout` is rejected before the exact two-hour boundary
and available at or after it. The fallback always pays the beneficiary. No
timer callback, expiry call, or consumer timeout can refund or pay an approved
escrow automatically; if nobody calls a settlement method, the approved escrow
remains in `deposit` and available to the authorized parties.

## Challenge state machine

`preliminary_approved` and `preliminary_blocked` retain the original consensus
outcome. A single authorized challenge may enter `challenged`, but it never
moves escrow by itself. If the challenge evidence is malformed, unavailable,
unclear, or times out, the seal returns to its original preliminary state and
the challenge slot remains consumed. A consensus-backed challenge result can
produce `approved` (the challenge is upheld) or `blocked` (the release is
overturned). Only a blocked terminal record can be refunded, and only by the
sponsor. This bounded one-challenge policy removes the forced-refund grief path
without adding a second custody pool for challenge bonds.

## Limitations

HTTPS availability, DNS and redirect behavior, declared authority identity,
model quality, and validator/provider availability remain external limits. The
URL admission filter rejects IP literals and common localhost/private/internal
hostname forms, but it cannot prove how a public hostname will resolve later or
force a redirect-free runtime. The response-size cap is applied after fetch
because the runtime does not expose a trusted pre-fetch limit.
`refund_blocked` is sponsor-authorized; timeout expiry remains permissionless
only after its recorded deadline.
Evidence hashes commit bytes but do not prove that a publisher is truthful. A
child transfer dispatch also does not prove recipient credit; consumers must
reconcile the finalized child receipt and its credited-value field.

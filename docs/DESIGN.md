# ProvenanceSeal design

## Purpose

ProvenanceSeal binds a software artifact, its dependency manifest, and release
evidence to exact bytes. GenLayer validators inspect those bytes and agree on a
bounded semantic decision before escrow can settle.

## Decision model

The reviewer must return exactly six fields: `artifact_match`,
`manifest_match`, `evidence_support`, and `risk` (`yes`, `no`, or `unclear`), an
integer `confidence` from 0 to 100, and a bounded `rationale`. Approval requires
all three positive matches, `risk == no`, and confidence at least 75. A material
negative is `blocked`; uncertainty, low confidence, malformed output, or an
external execution failure is `retryable` or an integrity block. Rationale is
never used to authorize payment.

Validators must agree on the decision kind, outcome, all material semantic
fields, and confidence within 20 points. They do not need identical prose.
This prevents a validator from changing an authorization consequence while
allowing harmless explanation variance.

## Evidence independence

Each evidence record declares an authority label and a URL. A normal release
manifest must contain at least two distinct labels and distinct HTTPS host
origins, so two paths on one host cannot be counted as independent
corroboration. Labels remain descriptive metadata; they do not prove the
authority's real-world identity.

## Escrow ordering

GEN enters through `create_seal` and is tracked in `deposit`. All release paths
read that ledger, set it to zero, persist terminal state and accounting, then
call `_send_gen`. A second settlement therefore fails before any transfer.

## Limitations

HTTPS availability, DNS and redirect behavior, declared authority identity,
model quality, and validator/provider availability remain external limits. The
URL admission filter rejects IP literals and common localhost/private/internal
hostname forms, but it cannot prove how a public hostname will resolve later.
`refund_blocked` is sponsor-authorized; timeout expiry remains permissionless
only after its recorded deadline.
Evidence hashes commit bytes but do not prove that a publisher is truthful.

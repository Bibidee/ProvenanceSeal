# Security notes (v0.2.0)

## Commitments and substitution

The sponsor's requirements, artifact URL/hash, and manifest URL/hash are fixed
at creation. A beneficiary release summary is a separate untrusted claim and
cannot overwrite those requirements. The contract hashes raw response bytes
before decoding them. A changed artifact, manifest, or evidence record therefore
cannot silently replace the committed release. Empty, oversized, non-UTF-8,
unavailable, redirected, or mismatched responses cannot produce approval.

## Semantic safety

Artifacts and evidence are untrusted quoted data. Prompt-injection text inside a
release file is not a reviewer instruction. Approval is derived only from the
bounded fields returned by the model and requires independent validator
agreement on every material field and the authorization outcome.

## Escrow safety

The only native-token emission path is `_send_gen`. Settlement functions debit
the stored deposit, persist the terminal status, decrement sponsor accounting,
and only then emit the transfer. The designated consumer gate prevents an
arbitrary caller from claiming an approved escrow; timeout and refund paths
prevent normal protocol states from locking funds forever. A terminal seal has
one settlement path: a second call sees a zero deposit or terminal status and
fails. Blocked refunds are sponsor-only.

## Challenge safety

Only one challenge slot exists per seal. Entering `challenged` does not move or
reverse escrow. Invalid, unavailable, unclear, or expired challenge evidence
restores the original preliminary decision, so a frivolous challenge cannot
force a sponsor refund or deny a valid beneficiary payment. A consensus-backed
adverse result may still overturn an approval into `blocked`; the sponsor must
then explicitly claim the refund.

## Explicit limitations

HTTPS does not prove DNS or redirect safety. The admission filter rejects
IP-literal, localhost, and common private/internal naming forms, and each
manifest requires distinct URL origins, but runtime DNS resolution remains an
external property. A redirect can only be rejected when the runtime exposes a
different final URL; the runtime does not provide a chain-enforceable DNS or
redirect guarantee. The response-size cap is applied after fetch. A declared
authority is not a cryptographic identity proof. External providers can be
unavailable, semantic models can be wrong, and validators can disagree. Those
conditions are handled as blocked or retryable outcomes, not as approval.
Integrators must verify the final child transfer receipt and `value_credited`
result; a child-transfer dispatch alone is not credit proof.

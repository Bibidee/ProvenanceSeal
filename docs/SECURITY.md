# Security notes

## Commitments and substitution

The contract hashes raw response bytes before decoding them. A changed artifact,
manifest, or evidence record therefore cannot silently replace the committed
release. Empty, oversized, non-UTF-8, unavailable, redirected, or mismatched
responses cannot produce approval.

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
prevent normal protocol states from locking funds forever.

## Explicit limitations

HTTPS does not prove DNS or redirect safety. A declared authority is not a
cryptographic identity proof. External providers can be unavailable, semantic
models can be wrong, and validators can disagree. Those conditions are handled
as blocked or retryable outcomes, not as approval. Integrators must verify the
final child transfer receipt and `value_credited` result.

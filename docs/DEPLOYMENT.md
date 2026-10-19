# Deployment status

The current remediation branch is **v0.2.0** and is not deployed. No v0.2.0
address, transaction, source-parity claim, or live lifecycle result may be
presented as current until the local release gate and CI are green and a fresh
Studionet deployment is explicitly authorized and finalized.

Current frozen-source candidate (before commit): SHA-256
`4d70c344386e76e617a9d5376c055f62f0e9e56a1e71f80311302433e433d3fc`.

## v0.2.0 pre-deployment acceptance checklist

- [ ] exactly one deployable contract source under `contracts/`
- [ ] Direct Mode lifecycle and adversarial tests pass
- [ ] the one-hour challenge filing boundary is strict and finalization is allowed at the exact deadline
- [ ] challenge acceptance starts a separate bounded adjudication deadline
- [ ] a challenge filed just before the filing deadline remains reviewable after that deadline
- [ ] challenge expiry preserves the original preliminary outcome
- [ ] consumer settlement is immediate after final approval
- [ ] beneficiary fallback is rejected before, and allowed at/after, the exact two-hour boundary
- [ ] approved escrow remains deposited after consumer-window expiry when nobody settles
- [ ] no timeout path automatically refunds or pays an approved escrow
- [ ] malformed challenge evidence cannot poison the original outcome
- [ ] challenge evidence IDs/origins cannot duplicate original evidence and semantic review labels evidence origins separately
- [ ] sponsor requirements remain immutable after beneficiary submission
- [ ] unauthorized settlement/refund and replay attempts are rejected
- [ ] malformed output, provider failures, and validator disagreement fail closed
- [ ] GenVM lint and ABI/schema generation pass
- [ ] final source SHA-256 and Git commit are recorded
- [ ] deployment is finalized on Studionet chain ID 61999 with GenVM success
- [ ] `gen_getContractCode` source matches local bytes exactly
- [ ] live `funded -> active -> submitted -> approved -> paid_beneficiary`
      evidence is recorded from finalized receipts and canonical state
- [ ] child transfer receipt and `value_credited` are independently verified

## Historical v0.1.1 Studionet record

This record is retained for audit history only. It is not source-parity evidence
for v0.2.0 because the contract source changed during this remediation.

- Network: GenLayer Studionet, chain ID `61999`
- Contract: `0x6232bF84b9341b0D932764DdCed7Bb05aA5A2E77`
- Deployment transaction: `0xdb41c0d6e985a30d499b334da5d60089239923631207f7bde0536e91e802d5b6`
- Explorer: https://explorer-studio.genlayer.com/address/0x6232bF84b9341b0D932764DdCed7Bb05aA5A2E77
- Historical release: v0.1.1, source SHA-256 `fc34ba788cb3edef7e0c9efc6e3d5e43bb2e2c79c70ba243f5829480619c2abc`
- Historical source parity: verified for v0.1.1 only
- Historical live seal: `PS-LIVE-001` (approval evidence exists; settlement remains
  governed by its recorded consumer delay and must not be reused as v0.2.0 proof)

Never copy an address or receipt from another project into a v0.2.0 release
claim. A dispatched child transfer is not credited-value evidence until its
finalized child receipt is independently checked.

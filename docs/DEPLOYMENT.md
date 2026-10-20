# Deployment status

The current **v0.2.0** source is deployed and independently verified on GenLayer
Studionet (chain ID `61999`).

- Contract: `0xe1F24C6e5caC09d4B596B548A7A440D68e115Df4`
- Deployment transaction: `0x90b6a5f0ddf1f20e65a20afa9f0a40e9132c63bfa1817fffaa1c5e14b968c831`
- Deployment sender: `0x527dA5f7022f14f7105e5f06cEc1a8EFf53556b5`
- Explorer: https://genlayer-explorer.vercel.app/address/0xe1F24C6e5caC09d4B596B548A7A440D68e115Df4
- Source commit: `158236e204d40a17cf31b6e725183bb010be9518`
- Merge commit: `164338c190d7cd1531742d81ec6d92b5339c5276`
- Source SHA-256: `d4645c806bb8b367c3ce47ecb30ee0dac564d7dc571a7b89b8b2c1c946320246`
- Deployment receipt: `FINALIZED`, `MAJORITY_AGREE`, GenVM execution successful
- Deployed source parity: exact byte-for-byte match
- `get_info()`: `ProvenanceSeal` v`0.2.0`, minimum confidence `75`, minimum deposit `1000000000000000`
- ABI/schema parity: verified against `artifacts/provenanceseal.abi.json`
- Main CI: [run 39339138615](https://github.com/Bibidee/ProvenanceSeal/actions/runs/39339138615), successful

The frozen-source candidate SHA-256 remains
`d4645c806bb8b367c3ce47ecb30ee0dac564d7dc571a7b89b8b2c1c946320246`.

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
- [ ] role-scoped challenge attempts cannot exhaust an opposing party's adverse-review path
- [ ] malformed challenge evidence cannot poison the original outcome
- [ ] challenge evidence IDs are normalized to lowercase, cannot duplicate original evidence IDs/origins, and semantic review labels evidence origins separately
- [ ] sponsor requirements remain immutable after beneficiary submission
- [ ] unauthorized settlement/refund and replay attempts are rejected
- [ ] malformed output, provider failures, and validator disagreement fail closed
- [ ] Direct Mode transfer-failure rollback is verified where the runtime exposes atomic external-transfer failure; otherwise the test is recorded as skipped
- [ ] GenVM lint and ABI/schema generation pass
- [ ] final source SHA-256 and Git commit are recorded
- [x] deployment is finalized on Studionet chain ID 61999 with GenVM success
- [x] `gen_getContractCode` source matches local bytes exactly
- [ ] live `funded -> active -> submitted -> approved -> paid_beneficiary`
      evidence is recorded from finalized receipts and canonical state
- [ ] child transfer receipt and `value_credited` are independently verified

## v0.2.0 bounded live lifecycle record

Seal `PS-LIVE-V020-004` was created with a 0.001 GEN escrow using the deployed
contract and then exercised with finalized receipts:

- `create_seal`: `0x4a31d1654e801fb217f9d52445e764651d6fd8289f3a7f1e1f9578172a54b986`
- `accept_seal`: `0xdc360ceaa81ccef3001727472a8e35754060cf9d2098a672d504beeafd1f232b`
- `submit_release`: `0x9d8c92255d83dee47b8fcaa4a2d640d95ed9729f096060deaa8181695a2f77d5`
- `review`: `0x29e42bda37c01cc661a41e42f202cc63fa3f3fe33fb767046956a6271fed5dea`
- Review result: `preliminary_blocked`, reason `artifact_too_large`, escrow retained
- Challenge deadline: `1792455324` (`2026-10-20 00:15:24 UTC`)
- `finalize_preliminary`: `0x8c988a84f255acabed486186e525cc3a9354ac1218f7b10e03c11e34d491bd96`
- `refund_blocked`: `0x075d1e4a878e88d4b40d031db9a23529927d55d1489495d99573c6910eb5467c`
- Final canonical state: `refunded_sponsor`, `deposit = 0`, `settled_amount = 1000000000000000`

The review's finalized leader result and validator consensus identified the
integrity failure: the deployed contract source is 36,756 bytes while the
contract's maximum fetched text size is 20,000 bytes. The contract therefore
failed closed and no beneficiary payout was attempted.

The refund receipt records a finalized child-transfer message to the sponsor
`0x7eB2a4B4e913Df62eAe807eF60509B3B7284C7FA` for `1000000000000000` wei, but
the parent receipt reports `value_credited = false` and this Studionet endpoint
does not expose an independently queryable child receipt. For this negative
path, that is transfer-intent evidence only; no beneficiary payout or
independently verified child credit is claimed.

## Successful live consensus review and settlement

Seal `PS-LIVE-V020-005` provides a separate positive live semantic-review
record on the same deployed v0.2.0 contract. Each transaction finalized with
`FINALIZED` and `MAJORITY_AGREE`:

- [`create_seal`](https://genlayer-explorer.vercel.app/tx/0xcaf66915f8b28e8d8c857e47ca4344ef79b12aff5d696ebb48ae9823a6ae2555): funded the seal with `1000000000000000` wei (`0.001 GEN`)
- [`accept_seal`](https://genlayer-explorer.vercel.app/tx/0xe6fd133c3ca487e9b9751cd6a929771de573d2d19f417a86c51d8bb5229295fb): accepted by the designated beneficiary
- [`submit_release`](https://genlayer-explorer.vercel.app/tx/0x7e9e8b8c7ffd811f56a1ab436b5594664cf9779abd8a82ac32360f96de400521): committed the pinned two-origin evidence manifest
- [`review`](https://genlayer-explorer.vercel.app/tx/0x474da1ce6d0c99bd1186353417083c2a9e00ae78f8bba1704de94e02b83642c2): finalized semantic consensus review

The canonical post-review state was `preliminary_approved` with confidence
`90`. The finalized leader result reported `artifact_match = yes`,
`manifest_match = yes`, `evidence_support = yes`, `risk = no`, and outcome
`approved`; validators reached majority agreement. The `0.001 GEN` escrow
remained held in the contract until the authorized consumer settlement below.

The sponsor then finalized the preliminary approval:

- [`finalize_preliminary`](https://genlayer-explorer.vercel.app/tx/0x15652fa9e2e00de280f357a7f7ea012438acbc7bb672057618bdf3808e46e55f): `FINALIZED`, `MAJORITY_AGREE`, GenVM `SUCCESS`

The designated consumer then settled the approved seal:

- [`settle_approved`](https://genlayer-explorer.vercel.app/tx/0x100a958ce3e281f9e94f1097619b18714af995a2bbd045738eb58847b59ec818): `FINALIZED`, `MAJORITY_AGREE`, GenVM `SUCCESS`

The final canonical `get_seal` state is `paid_beneficiary`, with
`deposit = 0`, `settled_amount = 1000000000000000` wei, and beneficiary
`0x8355d011e1fc874f3a91245711420d0c92cb3e47`. The settlement receipt records
a transfer message to that beneficiary for the same amount. The parent receipt
reports `value_credited = false`, and this Studionet endpoint does not expose an
independently queryable child receipt; therefore recipient balance credit is
not claimed beyond the canonical terminal contract state and transfer intent.

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

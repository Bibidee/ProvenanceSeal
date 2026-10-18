# Deployment status

ProvenanceSeal v0.1.1 is currently **undeployed**. No address, transaction, live
approval, or source-parity claim should be treated as current until the frozen
source passes the release gate and a fresh StudioNet deployment is finalized.

## Pre-deployment acceptance checklist

- [ ] one deployable contract source under `contracts/`
- [ ] Direct Mode lifecycle and adversarial tests pass
- [ ] Duplicate evidence origins and unauthorized refund attempts are rejected
- [ ] malformed output and provider failures remain fail-closed
- [ ] GenVM lint and ABI/schema generation pass
- [ ] source SHA-256 is recorded before deployment
- [ ] deployment is finalized with GenVM success
- [ ] `gen_getContractCode` source matches local bytes exactly
- [ ] live `funded -> active -> submitted -> approved -> paid_beneficiary`
      evidence is recorded
- [ ] child transfer receipt reports credited value

Historical deployments from other projects are unrelated and must not be
copied into this document.

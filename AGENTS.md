# Agent notes for this project

**Mandatory:** before helping with portfolio rebalancing, investing amounts, or weight tables, read and follow [`MONTHLY_REBALANCE.md`](MONTHLY_REBALANCE.md).

Key constraints from that doc:

- Exclude `TVBETETF` and cash from BET weight math
- Prefer updating `portofoliu.csv` + running `replicare_bet.py` over inventing allocations
- Do not change balancing / crawler logic unless the user asks (crawler constants only if BVB HTML broke the fetch)

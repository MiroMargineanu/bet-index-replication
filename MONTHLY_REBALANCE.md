# Monthly BET rebalance workflow

Use this every month when topping up the portfolio toward BET weights.

## Setup (once per month)

1. Update `portofoliu.csv` from Tradeville:
   - **Only individual BET stocks** you hold or want to hold
   - **Exclude** `TVBETETF` and cash (`RON`)
   - Fill **Simbol** + **Cantitate** only; leave `Pret` and `Pondere` empty (fetched from BVB)
2. Decide the investable sum = cash already in the account + new deposit (e.g. 4.9k + 10k → **14900**)

## Run the recommender

```bash
python3 replicare_bet.py <SUM>
```

Example: `python3 replicare_bet.py 14900`

If BVB scrape fails, the page HTML may have changed again (table id / column names in `src/crawler_bvb.py`). Do not change balancing logic unless asked.

## Weight table view (canvas + CSV)

Ask the agent (new chat in this project) with a prompt like:

### Full monthly prompt

```
Monthly BET rebalance view

1. Update portofoliu.csv from my Tradeville holdings: only individual BET stocks
   (exclude TVBETETF and cash). Quantities only; leave Pret / Pondere empty.
2. Run python3 replicare_bet.py <SUM> with this month’s investable amount.
3. Rebuild/update the canvas bet-weight-gap.canvas.tsx with columns:
   Symbol, Qty, Buy, Spend (RON), Value now, Value after, Held %, After %,
   BET norm. %, Diff now, Diff after, Rel. now, Rel. after, Status
4. Exclude TVBETETF and cash from all weight math. Use BVB prices/weights
   normalized among CSV names only.
5. Write/overwrite weight-gap-<SUM>.csv in the project root with the same data.
6. Short conclusion: who’s under/over, what to skip, where most money goes.

This month’s sum: <SUM> RON
```

### Short prompt (CSV already updated)

```
Run replicare_bet.py <SUM>, refresh the BET weight-gap canvas and
weight-gap-<SUM>.csv with the same columns as last time (buy, spend,
before/after value & weights, diffs, rel gaps). Exclude TVBETETF.
Summarize under/over and what to skip.
```

## How to read the columns

| Column | Meaning |
| --- | --- |
| BET norm. % | BET weight rescaled so CSV names sum to 100% |
| Held % / After % | Your weight before / after recommended buys |
| Diff | held − BET norm. (percentage points) |
| Rel. | diff ÷ BET norm. (relative gap) |
| Spend | buy × BVB ref. price |
| Status | UNDER / OVER / INLINE vs target **today** |

## Notes

- Skip names that are already overweight (no buy) unless you change goals.
- `*.csv` is gitignored; files stay local unless you force-add them.
- Canvas lives under Cursor’s project `canvases/` folder; the CSV export is the portable project copy.

# Ledger Reconciliation Demo

A standalone Python portfolio project that compares a ledger with a journal export and produces an exception report. The included files and business rules are fictional. The project demonstrates transaction matching and review workflows from my business analysis experience.

## Run the demo

Requires Python 3.9 or newer and uses the standard library.

```sh
python3 reconcile.py ledger.csv journal.csv -o results.csv
```

| Ledger entry | Result | Reason |
| --- | --- | --- |
| L-001 | Matched | The amount, vendor, and account agree within the date window. |
| L-002 | Review | Two consecutive entries for the same vendor and account total the ledger amount. |
| L-003 | Unmatched | The journal has no eligible candidate. |
| L-004 | Review | The amount and vendor agree, but the account differs. |

See [the sample report](expected.csv) for the matched journal IDs and reasons.

## How it works

- Convert positive USD amounts to integer cents. Compare normalized vendor and account names within a three-day window.
- Index journal entries by amount. Prefer an agreeing account and a closer date. Send tied candidates to review and reserve confirmed direct matches so each journal entry is confirmed at most once.
- For remaining ledger entries, scan consecutive journal rows with a sliding window. Split suggestions and account discrepancies stay in the review queue, where candidates can overlap until a human resolves them.

The input format is a CSV with `id,date,vendor,account,amount`. IDs must be unique per file, dates use ISO format, and journal row order defines adjacency. The tool is designed for positive payments in one currency.

## Verify the sample

```sh
python3 -m unittest discover
```

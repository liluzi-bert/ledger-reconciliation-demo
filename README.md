# Ledger Reconciliation Demo

A standalone Python portfolio project that compares a ledger with a journal export and produces an exception report. The included files and business rules are fictional. The project demonstrates transaction matching and review workflows from my business analysis experience.

## Sample accounting journal

This preview follows the layout of a historical accounting export. The counterparties, reference numbers, dates, and amounts below are fictional.

| Journal ID | Date | Type | Reference | Counterparty | Account | Debit (USD) | Credit (USD) |
| --- | --- | --- | --- | --- | --- | ---: | ---: |
| J-001 | 2025-01-11 | Expense | DEMO-101 | Example Supplier | Materials | 125.50 | |
| J-001 | 2025-01-11 | Expense | DEMO-101 | Example Supplier | Cash | | 125.50 |
| J-002 | 2025-01-12 | Expense | DEMO-102 | Sample Carrier | Shipping | 75.00 | |
| J-002 | 2025-01-12 | Expense | DEMO-102 | Sample Carrier | Cash | | 75.00 |
| J-003 | 2025-01-13 | Expense | DEMO-103 | Sample Carrier | Shipping | 105.00 | |
| J-003 | 2025-01-13 | Expense | DEMO-103 | Sample Carrier | Cash | | 105.00 |

The export shows the two sides of each entry. The demo starts from [a prepared journal CSV](journal.csv) with one row per journal ID. It uses the expense account and amount once, so the offsetting cash line does not double the transaction. The raw journal preview illustrates the source layout. The CLI takes prepared CSVs as input.

In the [ledger CSV](ledger.csv), L-001 matches J-001 for **$125.50**. L-002 records one **$180.00** shipping expense. The report flags it for review because J-002 and J-003 are consecutive entries for the same counterparty and account and sum to $180.00.
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

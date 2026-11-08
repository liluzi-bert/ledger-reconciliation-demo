"""Reconcile synthetic USD ledger entries against a journal export."""

import argparse
import csv
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path


def read_entries(path):
    entries = []
    seen = set()
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        required = {"id", "date", "vendor", "account", "amount"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"{path}: expected columns {', '.join(sorted(required))}")
        for row in reader:
            entry_id, day, vendor, account, amount = (
                row[key].strip() if row[key] is not None else ""
                for key in ("id", "date", "vendor", "account", "amount")
            )
            try:
                dollars = Decimal(amount)
                parsed_date = date.fromisoformat(day)
                if (not all((entry_id, vendor, account)) or entry_id in seen
                        or not dollars.is_finite() or dollars <= 0
                        or dollars != dollars.quantize(Decimal("0.01"))):
                    raise ValueError("expected a unique ID, vendor, account, and positive USD amount")
            except (ArithmeticError, ValueError) as exc:
                raise ValueError(f"{path}:{reader.line_num}: {exc}") from exc
            seen.add(entry_id)
            entries.append((entry_id, parsed_date, vendor.casefold(), account.casefold(),
                            int(dollars * 100)))
    return entries


def reconcile(ledger, journal, window=3):
    by_amount = defaultdict(list)
    for entry in journal:
        by_amount[entry[4]].append(entry)

    used = set()
    results = {}
    # Reserve exact matches before looking for split candidates.
    for entry_id, day, vendor, account, amount in ledger:
        candidates = [
            item for item in by_amount[amount]
            if item[0] not in used and item[2] == vendor
            and abs(item[1] - day) <= timedelta(days=window)
        ]
        if candidates:
            candidates.sort(key=lambda item: (item[3] != account, abs(item[1] - day), item[0]))
            match = candidates[0]
            ambiguous = len(candidates) > 1 and (
                match[3] == account, abs(match[1] - day)
            ) == (candidates[1][3] == account, abs(candidates[1][1] - day))
            if ambiguous:
                results[entry_id] = ("review", [], "Multiple equally ranked direct candidates")
            elif match[3] != account:
                results[entry_id] = ("review", [match[0]], "Direct amount match with a different account")
            else:
                used.add(match[0])
                results[entry_id] = ("matched", [match[0]], "Direct match on vendor, account, and amount")

    for entry_id, day, vendor, account, amount in ledger:
        if entry_id in results:
            continue
        # Positive amounts let a sliding window find consecutive splits.
        start = total = 0
        splits = []
        for end, item in enumerate(journal):
            item_id, item_date, item_vendor, item_account, cents = item
            if (item_id in used or (vendor, account) != (item_vendor, item_account)
                    or abs(item_date - day) > timedelta(days=window)):
                start, total = end + 1, 0
                continue
            total += cents
            while total > amount:
                total -= journal[start][4]
                start += 1
            if total == amount and end > start:
                splits.append([row[0] for row in journal[start:end + 1]])
                if len(splits) == 2:
                    break
        if len(splits) == 1:
            results[entry_id] = ("review", splits[0], "Consecutive journal entries sum to ledger amount")
        elif splits:
            results[entry_id] = ("review", [], "Multiple possible splits")
        else:
            results[entry_id] = ("unmatched", [], "No eligible direct match or consecutive split")

    return [
        (entry[0], status, " ".join(ids), reason)
        for entry in ledger
        for status, ids, reason in [results[entry[0]]]
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ledger", type=Path)
    parser.add_argument("journal", type=Path)
    parser.add_argument("-o", "--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.resolve() in {args.ledger.resolve(), args.journal.resolve()}:
        parser.error("choose an output path different from either input")
    try:
        rows = reconcile(read_entries(args.ledger), read_entries(args.journal))
        with args.output.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(("ledger_id", "status", "journal_ids", "reason"))
            writer.writerows(rows)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()

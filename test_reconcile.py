import csv
import unittest
from pathlib import Path

from reconcile import read_entries, reconcile


class ReconciliationTests(unittest.TestCase):
    def test_sample_report(self):
        examples = Path(__file__).parent
        ledger = read_entries(examples / "ledger.csv")
        journal = read_entries(examples / "journal.csv")
        with (examples / "expected.csv").open(newline="") as stream:
            expected = [tuple(row) for row in list(csv.reader(stream))[1:]]
        self.assertEqual(reconcile(ledger, journal), expected)

    def test_direct_match_is_reserved_before_split_review(self):
        examples = Path(__file__).parent
        ledger = read_entries(examples / "ledger.csv")
        journal = read_entries(examples / "journal.csv")
        direct = ("L-005", *journal[1][1:])
        results = reconcile([ledger[1], direct], journal)
        self.assertEqual([(row[0], row[1]) for row in results],
                         [("L-002", "unmatched"), ("L-005", "matched")])


if __name__ == "__main__":
    unittest.main()

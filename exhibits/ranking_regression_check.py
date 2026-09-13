"""The falsification test, made permanent. Runs at the start of every session.

Excerpted from a distributor sourcing pipeline. Client identities removed from
the calibration set; logic unmodified.

WHY THIS EXISTS
===============
An early version of this pipeline produced a shortlist that looked right and was
not. The only test that settled it was asking the client to name the companies he
was already selling to, then looking for them in the output. Four of the six were
in the data and had been discarded, for the crime of not having been researched
yet. The list was not padded. It was missing the answer.

Fixing that once is not enough. Every later change to the ranking, the scope
rules, the dedupe or the gate can reintroduce the same failure through a
different door, and nothing about a wrong shortlist announces itself. So the six
companies became a calibration set, and this check re-scores the ranking against
them before any work is done.

THE PASS CONDITION IS PRESENCE, NOT RANK
========================================
A confirmed company must be ON the list. Where it sits within its cohort is
reported but is not the pass condition, because the ledger provably cannot
discriminate rank inside the densest cohort and pretending otherwise would make
the test fail on noise. A check that fails on noise gets switched off, which is
worse than no check.

WHAT IT IS EVIDENCE OF
======================
Turning a one-off discovery into a standing invariant. The specific way this
system was once wrong cannot come back without someone being told, and being
told costs nothing, because the check runs itself at session start and stays
silent when it passes.
"""
from collections import OrderedDict

# The six companies the client confirmed, as the calibration set.
# "contact" = in contact, no sales yet. "bought" = has purchased before.
# The third field records whether the OLD shortlist of 85 had found them,
# which is the number this test exists to keep honest: two of six.
CALIBRATION = OrderedDict([
    ("client-confirmed-01", ("a New York wholesaler",     "bought",  True)),
    ("client-confirmed-02", ("a Pennsylvania wholesaler", "contact", True)),
    ("client-confirmed-03", ("a New York wholesaler",     "bought",  False)),
    ("client-confirmed-04", ("a New York wholesaler",     "contact", False)),
    ("client-confirmed-05", ("a Maryland wholesaler",     "contact", False)),
    ("client-confirmed-06", ("a South Carolina dealer",   "bought",  False)),
])


def validate(cohorts):
    """Is every confirmed company on the list at all?

    `cohorts` maps a cohort key to its ranked rows, each (score, company,
    rationale, evidence). A confirmed company may survive under a sibling's id
    after duplicate folding, so the folded ids are checked as well.
    """
    where = {}
    for key, rows in cohorts.items():
        for i, (pts, c, _, _) in enumerate(rows):
            for cid in [c["id"]] + list(c.get("_folded") or []):
                if cid in CALIBRATION:
                    where[cid] = (key, i + 1, len(rows), pts)

    print(f"{'company':28} {'signal':8} {'old 85':7} {'cohort':11} {'rank in cohort':>16}")
    print("-" * 78)
    ok = True
    for cid, (name, signal, made) in CALIBRATION.items():
        if cid not in where:
            print(f"{name:28} {signal:8} {'yes' if made else 'no':7} {'MISSING':11}")
            ok = False
            continue
        key, i, n, pts = where[cid]
        print(f"{name:28} {signal:8} {'yes' if made else 'no':7} {key:11} "
              f"{i:>6}/{n} (score {pts})")
    print()
    print("PASS: all six present" if ok else "FAIL: a confirmed company is missing from the list")
    return ok

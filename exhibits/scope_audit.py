"""The single definition of who is in scope, and an audit that proves none leak.

Excerpted from a distributor sourcing pipeline. Client identities removed from
the commentary; logic unmodified.

WHY THIS EXISTS
===============
The characteristic bug of that codebase was **filtering on a bookkeeping field
instead of on a judgment**. It happened four times, in four different files, each
time silently removing companies that had passed every real test:

  1. A shortlist banded on `confidence == "Medium"`, cutting three companies the
     client had actually sold to or was in conversation with.
  2. A discovery pass selected on `status == "qualified"`, skipping 291
     gate-passing records including 88 that held the strongest credential class
     in the dataset.
  3. An ingest rated 175 companies, 23 of them top-band, and left their status at
     "new" - making them invisible to ranking and to export.
  4. An enrichment pass wrote a base-rate guess into a field that ranking read as
     evidence, pushing 528 companies below the line on no evidence at all.

Each was fixed where it was found. That is not a fix; it is a pattern with three
more places to appear.

THE RULE
========
A company is a prospect if the qualification gate passed and nothing evidenced
rules it out. Not: whether anyone has researched it. Not: how confident we are.
Those describe our knowledge, not the company.

Scope is therefore defined ONCE, here. Every script imports it. `--audit` fails
loudly if any gate-passing company is unaccounted for.

WHAT IT IS EVIDENCE OF
======================
The difference between a fix and a constraint. Four fixes in four files left the
fifth occurrence free to happen; one definition plus an assertion that runs on
every session does not. Note that `unaccounted` is not a category to investigate
later - it is a number required to be zero, and anything above zero means
something is filtering on a bookkeeping field again.
"""


def gate_passed(c):
    """The qualification gate said yes. The only hard test there is."""
    return bool((c.get("gate") or {}).get("passed"))


def bucket(c):
    """Every gate-passing company lands in exactly one bucket, or leaks."""
    if not gate_passed(c):
        return "gate_failed"
    if is_grower(c):
        return "grower"              # a competitor as well as a buyer
    if is_excluded(c):
        return "excluded"            # ruled out WITH a written reason
    if (c.get("assessment") or {}).get("fit"):
        return "rated"
    if (c.get("enrichment") or {}).get("open_questions"):
        return "review"              # ambiguous, waiting on a human read
    if not is_researched(c):
        return "unresearched"        # nobody has looked yet. STILL A PROSPECT.
    return "unaccounted"             # must be zero


def audit(doc, verbose=True):
    counts, leaks = {}, []
    for c in doc["companies"]:
        b = bucket(c)
        counts[b] = counts.get(b, 0) + 1
        if b == "unaccounted":
            leaks.append(c)
        # A record excluded with NO written reason at all is unauditable. An
        # exclusion you cannot argue with is indistinguishable from a bug.
        if c.get("status") == "excluded" and not exclusion_reason(c):
            leaks.append(c)
            counts["excluded_without_reason"] = counts.get("excluded_without_reason", 0) + 1

    if verbose:
        print(f"ledger: {len(doc['companies'])} records\n")
        for k in ("rated", "review", "unresearched", "grower", "excluded", "gate_failed"):
            if k in counts:
                print(f"  {k:14} {counts[k]:5}")
        bad = counts.get("unaccounted", 0) + counts.get("excluded_without_reason", 0)
        if bad:
            print(f"\n  *** {bad} LEAKED - gate-passing companies in no bucket ***")
            for c in leaks[:15]:
                print(f"      {c['id']:16} status={c.get('status')}")
        else:
            print("\n  no leaks: every gate-passing company is accounted for")
    return counts, leaks

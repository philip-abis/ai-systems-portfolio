"""Assert the invariant dedupe depends on, because nothing else was asserting it.

Excerpted from a distributor sourcing pipeline. Client identities removed;
logic unmodified.

WHY THIS EXISTS
===============
Dedupe marks the losing rows of a cluster with `duplicate_of`, and every
downstream consumer excludes any row carrying it. That is only correct if each
cluster leaves EXACTLY ONE row unflagged.

When two rows point at each other, both are excluded and the company disappears
from every shortlist with no error raised anywhere.

That happened. Eleven of 73 clusters were mutually flagged, hiding seven of the
highest-rated companies in the dataset from the top band. The bug survived a full
1,221-company research run because nothing ever asserted the invariant. Every
individual step was correct. The failure was in the gap between them.

WHAT IT IS EVIDENCE OF
======================
The class of bug that produces no error, no exception and no log line, and is
therefore invisible until someone asks why a company they expected is missing.
The only defence is to state the invariant as an executable assertion and run it
on a schedule. This one runs in the session-start preflight, so a broken graph
is reported before any work is done rather than discovered afterwards.

REPAIR PICKS THE BEST-RATED MEMBER as the survivor, so the row that carries
forward holds the strongest assessment. It never re-rates and never merges
anything new. It only removes a flag that should not have been set on every
member of a cluster at once.
"""

from collections import defaultdict

FIT_RANK = {"Strong": 0, "Promising": 1, "Possible": 2, "Conditional": 3}
CONF_RANK = {"High": 0, "Medium": 1, "Low": 2}


def clusters(companies):
    """Connected components of the duplicate_of graph, via union-find.

    Union-find rather than following pointers, because the failure mode being
    detected is a CYCLE. Pointer-chasing on a cycle either loops forever or
    silently stops, and both hide the thing we are looking for.
    """
    dup = {c["id"]: (c.get("enrichment") or {}).get("duplicate_of") for c in companies}
    dup = {k: v for k, v in dup.items() if v}
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]      # path compression
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    dangling = []
    for a, b in dup.items():
        if b not in dup and not any(c["id"] == b for c in companies):
            dangling.append((a, b))            # points at a row that is not there
            continue
        union(a, b)

    groups = defaultdict(list)
    for c in companies:
        if c["id"] in parent:
            groups[find(c["id"])].append(c)
    return groups, dup, dangling


def check(companies):
    """Returns (broken, dangling). `broken` is the thing that must be empty."""
    groups, dup, dangling = clusters(companies)
    broken = []
    for root, members in groups.items():
        survivors = [c for c in members if not (c.get("enrichment") or {}).get("duplicate_of")]
        if len(survivors) != 1:
            # Zero survivors: the whole company vanished from every shortlist.
            # More than one: the same company is counted twice.
            broken.append((root, members, survivors))
    return broken, dangling

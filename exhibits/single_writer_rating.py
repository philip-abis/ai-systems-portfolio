"""The one function allowed to write a fit rating. Nothing else may set it.

Excerpted from a distributor sourcing pipeline built for a Long Island oyster
farm. Client identities have been removed from the commentary; the logic is
unmodified.

WHY THIS EXISTS
===============
On one working day in August the same defect surfaced six times. Each time it was
a different function, each time the reasoning was individually sensible, and each
time the effect was that a mechanical signal silently overrode a judgment that a
higher authority had already made:

  1. A roster flag treated as fatal. Deleted a company the client was actively
     selling to, plus 141 other permitted dealers.
  2. Absence from a federal list treated as disqualifying. Would have erased
     every buyer in seven states that run no such certification at all.
  3. Absence from one roster snapshot read as "not certified". Marked 160 live
     businesses uncertified; all 160 clustered on nine state renewal dates,
     which is renewal lag, not closure.
  4. A directory's "Market" category read as retail-only. Downgraded a wholesaler
     supplying 200+ restaurants.
  5. The decision function ignoring a must-buy credential. Demoted 76 companies
     for the crime of being read: their own sites confirmed the qualifying fact,
     but the copy never used the expected word, so the rating fell below what the
     credential alone had already established.
  6. The same bug in a second function, found only because the band totals moved
     and someone asked why.

Comments did not prevent it. Items 5 and 6 happened with the lesson from item 1
written in the file directly above them. The defect was STRUCTURAL: six code
paths wrote the same field independently and none could see what authority had
already settled it. Any new path reintroduces it.

THE FIX
=======
One chokepoint. Every writer declares WHO is speaking. A lower authority may
never push a rating below a floor a higher authority established. Refusals are
recorded on the record rather than swallowed, so a wrong floor is visible and
arguable instead of invisible.

This does not stop a rating going UP, and it does not stop a human review saying
"actually, no". It stops a machine rule quietly undoing a decision.

WHAT IT IS EVIDENCE OF
======================
Fixing a bug where you find it is not a fix when the bug is a shape. Six
independent writers is the shape; a chokepoint is the only thing that changes it.
The companion audit in scope_audit.py catches anything that reaches the field by
some other route, because a chokepoint you can bypass is a convention, not a
constraint.
"""

# Who is speaking, most authoritative first. A writer may only lower a rating
# that was set by an authority at or below its own level.
AUTHORITY = {
    "client":       100,   # the client's own word about his own customers
    "hand":          80,   # a human read this and wrote an opening angle
    "web-research":  60,   # someone read the company's own pages and wrote it up
    "rubric":        50,   # a dimension the written criteria settle outright
    "site-read":     30,   # machine signals parsed from the company's site
    "profile":       20,   # a search-model profile with no page to cite
    "permit":        10,   # credential structure alone
}

BANDS = ["No", "Conditional", "Possible", "Promising", "Strong"]
RANK = {b: i for i, b in enumerate(BANDS)}


def apply_rating(c, fit, confidence, rationale, by, log=None):
    """Write a fit onto a company record. THE ONLY sanctioned way to do so.

    `by` must be a key of AUTHORITY. Returns the fit actually written, which is
    not necessarily the fit proposed.
    """
    if by not in AUTHORITY:
        raise ValueError(f"apply_rating: unknown authority {by!r}. "
                         f"Declare who is speaking: {sorted(AUTHORITY)}")
    a = c.setdefault("assessment", {})
    prev, prev_by = a.get("fit"), a.get("rated_by")

    # 1. A lower authority may not overwrite a higher one's rating at all.
    if prev and prev_by and AUTHORITY.get(prev_by, 0) > AUTHORITY[by]:
        if log is not None:
            log[f"refused_{by}_under_{prev_by}"] += 1
        a.setdefault("rating_refusals", []).append(
            f"{by} proposed {fit}; kept {prev} set by {prev_by} (higher authority).")
        return prev

    # 2. Nobody may drop below a settled floor. A floor comes from a credential
    #    that PROVES the qualifying fact on its own, independent of any reading
    #    of the company's website. Item 5 above is what happens without this.
    fl, why = floor_for(c)
    if fl and fit and RANK.get(fit, 99) < RANK[fl]:
        if log is not None:
            log[f"floored_{by}"] += 1
        a["fit"] = fl
        a["confidence"] = confidence or a.get("confidence")
        a["rationale"] = (rationale or "") + f"  [Raised to {fl}: {why}]"
        a["rated_by"] = by
        a["rating_floor"] = {"band": fl, "why": why, "proposed": fit}
        return fl

    a["fit"] = fit
    if confidence:
        a["confidence"] = confidence
    if rationale:
        a["rationale"] = rationale
    a["rated_by"] = by
    return fit

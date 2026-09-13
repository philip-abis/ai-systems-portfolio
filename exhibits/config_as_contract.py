"""Ranking whose rules live in a config file, not in a model's head.

Excerpted from a travel-search skill. Personal constraints have been replaced
with neutral equivalents; the mechanics are unmodified.

WHY THIS EXISTS
===============
The skill has two halves and they are deliberately separated. An agent fetches
the candidates, because that needs the web. This file ranks them, and it runs
offline on the standard library with no network at all.

That split is the point. A model asked to pick "the best flight" from prose will
produce a defensible answer every time and a DIFFERENT defensible answer next
Tuesday, because nothing pins it. Here every rule and every dollar value lives in
a JSON file, so the same inputs always produce the same ranking, and changing the
ranking means editing a value someone can see and argue with rather than
rephrasing a prompt.

THE THREE MECHANICS WORTH STEALING
==================================

**Hard rules eliminate; eliminated options are reported, not dropped.** Anything
ruled out appears under "Ruled out" with the specific rule that killed it. A
shortlist that silently omits things cannot be checked. This is the same
principle as recording a refusal on a record rather than swallowing it.

**Soft penalties are denominated in dollars per person.** Not arbitrary weights
between zero and one - actual money, because that is how the trade-off is really
made. A connection is worth taking if it saves more than the connection costs
you. It also scales correctly with party size without a special case: a late
arrival that costs one traveller $40 costs a family of six $240, so large parties
rule those options out on their own arithmetic rather than on a separate rule.

**Both numbers are always shown.** The cash you actually pay AND the adjusted
score, side by side, so it is always visible why a more expensive itinerary
ranked first. A single blended number hides the adjustment; two numbers make it
arguable.

WHY THIS DOES NOT CONTRADICT "NEVER BLEND INTO A SCORE"
=======================================================
Elsewhere in this portfolio there is a rule against collapsing signals into one
number, learned from a shortlist that came out at 85 because a threshold had been
tuned until it did. This file scores. The difference is not hypocrisy, it is the
three conditions above:

  - the unit is meaningful (money), not an invented weight
  - the raw number is reported next to the adjusted one
  - the coefficients live in config, visible and editable

A score fails when its unit is arbitrary, its inputs are buried, and the only
thing anyone can tune is the threshold. It is legitimate when the adjustment is
denominated in something real and shown alongside what it adjusted.

A RULE CORRECT IN ONE CONTEXT CAN EMPTY THE RESULT SET IN ANOTHER
=================================================================
The arrival caps here were set for short domestic routes, where a same-day
arrival before midnight is always available, so they cost nothing but the worst
options. Applied to an intercontinental route they are catastrophic: the
eastbound leg lands the next morning on every carrier and every date, so the
rules do not tighten the search, they empty it. A long run once ruled out every
transatlantic itinerary that could possibly exist and would have ended in
"nothing cleared the rules" whatever it found, after spending the whole budget
finding it.

The fix was to scope those rules to domestic routes. The important half of the
fix was that the renderer states which rules were relaxed and why, because
dropping a rule quietly is worse than the bug it works around.
"""


def evaluate(option, profile, party_size, domestic=True):
    """Apply hard rules and soft penalties. Returns a Ruling, never a bare bool."""
    r = Ruling(option)
    hard = profile["hard_rules"]
    soft = profile["soft_penalties_per_person_usd"]

    blocked_from = to_minutes(hard["weekly_commitment"]["depart_after"])
    blocked_to = to_minutes(hard["weekly_commitment"]["depart_before"])
    latest_arrival = to_minutes(hard["latest_arrival"])

    late_tiers = sorted(
        ((to_minutes(t["from"]), t["value"]) for t in soft["late_arrival"]["tiers"]),
        reverse=True,
    )

    for leg in option["legs"]:
        dep_min, _ = parse_time(leg["depart"])
        arr_min, arr_next_day = parse_time(leg["arrive"])
        role = leg.get("role", "leg")

        # A hard rule ELIMINATES, and says which rule did it.
        if is_blocked_day(leg) and blocked_from <= dep_min < blocked_to:
            r.fail("Weekly commitment window",
                   f"{role} leg departs {pretty(dep_min)}, inside the blocked window")

        # A soft rule PRICES. Per person, so party size needs no special case.
        elif is_blocked_day(leg) and dep_min < blocked_from:
            p = soft["early_departure"]
            r.penalise("Early departure", p["value"],
                       f"{role} leg departs {pretty(dep_min)}. {p['reason']}")

        # Scoped to the context the rule was written for. Applying these to a
        # long-haul route does not tighten the search, it empties it.
        if domestic:
            if arr_next_day:
                r.fail("Next-day arrival", f"{role} leg lands the following day")
            elif arr_min > latest_arrival:
                for threshold, value in late_tiers:
                    if arr_min >= threshold:
                        r.penalise("Late arrival", value,
                                   f"{role} leg lands {pretty(arr_min)}")
                        break

    return r


# The config this reads, in outline. Every number here is a decision someone made
# and can revisit; none of it is buried in the code above.
EXAMPLE_PROFILE = {
    "hard_rules": {
        "weekly_commitment": {"depart_after": "08:00", "depart_before": "12:30"},
        "latest_arrival": "23:59",
    },
    "soft_penalties_per_person_usd": {
        "early_departure": {"value": 25, "reason": "commitment met at the destination instead"},
        "late_arrival": {"tiers": [{"from": "22:00", "value": 40},
                                   {"from": "23:00", "value": 70}]},
        "connection": {"value": 60, "reason": "risk and time, per connection"},
    },
    "airports": {
        "rules": {
            "PRIMARY":   {"status": "preferred", "penalty_per_person": 0},
            "SECONDARY": {"status": "allowed",   "penalty_per_person": 35,
                          "reason": "ground transfer time and cost"},
        }
    },
}

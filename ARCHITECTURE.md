# Eleven rules, and what each one cost to learn

These are the decisions that recur across the systems in this repository. They
were not designed up front. Each one is the residue of a specific failure on real
data, and each is stated here with that failure attached, because a rule without
its incident is just an opinion.

The systems they come from are prospect research pipelines, a vision-based
grading tool, a field sales app, and the reliability layer that keeps all of them
honest. Different domains, same decisions.

---

## 1. Scripts own facts. The model owns judgment. A schema sits between them.

Anything a script can settle deterministically is settled by a script and never
re-litigated by a model: registry fetches, merges, dedupe, qualification gates,
scope definitions, statistics. What is left is genuinely a judgment call, and in
the largest of these pipelines it is exactly two questions.

The boundary is stated in the docstring of every module that sits on it, because
the boundary erodes silently. A model asked to "just also check" a mechanical
fact will answer, plausibly, and now the fact has two sources.

**The failure it prevents:** a fluent, confident answer where a lookup was
available.

---

## 2. One writer per field, and every writer declares its authority.

A fit rating can only be written through a single function. Each caller names who
is speaking. A lower authority may raise a rating but may never push it below a
floor a higher authority established, and refusals are recorded on the record
rather than swallowed.

**What it cost:** in one working day, six separate code paths each silently
overrode a judgment that had already been made. Each was individually sensible.
One deleted a company the client was actively selling to, along with 141 other
qualified dealers. Comments did not stop it - two of the six were written
directly beneath the comment describing the first.

**The general shape:** when a defect recurs in different files with different
authors, it is not a bug, it is a shape. Fixing it where you find it leaves every
other place free to reproduce it.

→ `exhibits/single_writer_rating.py`

---

## 3. Define scope once. Audit it. Require the leak count to be zero.

A company is in scope if the qualification gate passed and nothing evidenced
rules it out. Not whether anyone has researched it, and not how confident anyone
is - those describe our knowledge, not the company.

**What it cost:** the same bug, filtering on a bookkeeping field instead of on a
judgment, appeared in four different files. It cut three companies the client had
already sold to, hid 291 qualifying records, left 175 rated companies invisible
to export, and pushed 528 below the line on a base-rate guess written into a
field that ranking read as evidence.

The audit does not produce a category to investigate later. It produces a number
required to be zero.

→ `exhibits/scope_audit.py`

---

## 4. State the invariant as an executable assertion.

Dedupe is only correct if each cluster of duplicates leaves exactly one row
standing. Nothing was checking that.

**What it cost:** eleven of 73 clusters were mutually flagged, so both rows were
excluded and seven of the highest-rated companies in the dataset vanished from
the top band. It survived a full run because every individual step was correct. The failure lived in the gap between them, and produced no error, no
exception and no log line.

The check now runs at session start, so a broken graph is reported before any
work is done rather than discovered afterwards by someone asking where a company
went.

→ `exhibits/dedupe_integrity.py`

---

## 5. Prove the page loaded before believing anything extracted from it.

Every extraction schema carries a field asserting the page returned. The
HTTP status is checked separately. Either one failing invalidates the whole
extraction, not just the fields that look wrong.

**What it cost:** an extractor was handed the text of a "page not found" and
returned three confidently wrong figures and a complete, fluent policy summary.
Nothing errored, because from the extractor's side nothing failed - it was given
text and produced the requested shape.

**The consequence:** a load-bearing number never rests on a model-parsed
extraction alone. It needs a raw-text cross-check or a second source. Raw markdown
is preferred over parsed JSON wherever completeness matters, because a page that
did not load is obvious in raw text and invisible in a well-formed object.

---

## 6. Author in one place, deploy to another, and make the difference converge.

Everything here is built with Claude Code, mostly in VS Code and sometimes
straight from the terminal — a real editor, version control, a diff for every
change. Almost none of it is *operated* there. The people who use these
systems work in a chat surface, so a skill is written as project files and
deployed to that surface, and the two have to behave identically.

They cannot behave identically for free, because they differ in one specific way:
a script running in the hosted sandbox has no outbound network, while that same
environment's own tool calls run server-side and reach the web fine. Tools fetch,
scripts compute.

The design that survives that is narrow on purpose.

**One skill, not two.** The alternative — a local version and a hosted version —
means two codebases that drift, and the drift is invisible until they disagree
about the same company.

**The branch is confined to fetching, and nothing else.** Both paths hand the
same page text to the same extraction code. Two paths that extracted differently
would produce different judgments about identical input, which is the single way
this design goes wrong.

**Then they converge.** After the fetch, there is one path again: the same
schema, the same validator, the same ledger. The environment shows up once, at
the top, and never again.

**And the choice is announced.** One sentence before anything is fetched, naming
the path, what it costs per item, and what it cannot do at all. The hosted path
is usually slower and dearer, because the local one fetches in parallel inside a
single process while the hosted one spends a model turn per call. That is a real
difference at scale and invisible in the output, so the operator is told rather
than left to infer it from a thin result.

**What it prevents:** a run that fetched half one way and half the other and
cannot be read afterwards, and worse, a quietly thinner result that looks like an
honest empty one.

---

## 7. Branch on a measured capability, never on an assumed environment.

The same skill runs where a script can open a socket and where it cannot but the
agent's own tool calls can. "Which environment am I in" is a label. "Can this
process reach the API" is the thing that decides and the thing that breaks.

The probe runs once, before any URL is fetched, and the chosen path is announced
in one sentence including what it costs and what it cannot do. Never a per-URL
fallback: a run that fetched half one way and half the other cannot be read
afterwards, because nothing in the output says which half is which.

→ `exhibits/capability_preflight.py`

---

## 8. Bands with stated criteria, never a blended score.

Ratings are named bands whose criteria are written down. There is no combined
number anywhere, and there must never be one.

**What it cost:** I specified the size of the answer instead of the criteria for
it. Early on I gave the system a rough target for how many prospects the
shortlist should contain, which sounds like useful direction and is actually an
inversion: a count is an OUTPUT of a qualification process, and supplying it as
an input means the gates get adjusted until they produce the number requested.
Several signals had been blended into one score, the score had a threshold, and
the threshold moved until the list was the requested size. What comes out of that
is not a shortlist. It is the number you asked for, wearing evidence.

The correct instruction is about the gate, never about the count: state what
qualifies a company and let the total be whatever the data yields, including
uncomfortably small.

The moment two signals collapse into a number, the number gets a threshold, and
the threshold gets tuned. In a later pipeline two dimensions are kept
deliberately separate and reported side by side for exactly this reason.

**When a score IS legitimate.** A travel-ranking skill in this same collection
scores openly, and the difference is worth stating rather than glossing. Three
conditions make it honest. The unit is real money per person, not an invented
weight — a connection is worth taking if it saves more than the connection costs
you, and that scales correctly with party size without a special case. The raw
cash figure is reported next to the adjusted score, so it is always visible why a
more expensive option ranked first. And every coefficient lives in a config file
where it can be seen and argued with rather than buried in the ranking code.

A score fails when its unit is arbitrary, its inputs are hidden, and the only
adjustable thing is the threshold. It works when the adjustment is denominated in
something real and shown alongside what it adjusted.

→ `exhibits/config_as_contract.py`

---

## 9. Separate what prepares an update from what sends it.

Building an export payload and pushing it to a live system are separate scripts.
There is no `--push` flag on the export command, so there is no flag that can be
passed by accident.

The same principle governs writes generally: no delete policy on the call
records table, because a wrong value is fixable in seconds and a vanished record
is not. Where two systems hold the same field, one owns it and the other is a
one-way mirror carrying a `last_synced` stamp, so a stale copy reports itself as
stale rather than as agreement.

---

## 10. Design for the environment the software is used in, not developed in.

The call sheet is worked from a dock and a truck. So a capture is written to the
phone before the network is touched, and the network write is allowed to fail.
Unsent work is retried on the next save, on sign-in, and when the browser reports
it is back online. The header names where the data is rather than reassuring
anyone that it is safe, and signing out with unsent records asks first.

On load, the newer of the local and server record wins on timestamp. Server-wins
is the obvious rule and it is wrong: a capture from a phone that has been offline
is the freshest record that exists.

→ `exhibits/offline_first_capture.js`

---

## 11. A rule correct in one context can empty the result set in another

Arrival caps written for short domestic routes cost nothing there, because a
same-day arrival is always available. Applied to intercontinental routes the same
caps are catastrophic: every carrier's eastbound leg lands the next morning, so
the rules do not tighten the search, they eliminate every itinerary that could
exist.

**What it cost:** a long run ruled out every transatlantic option and would have
finished with "nothing cleared the rules" whatever it found, after spending the
entire budget finding it.

The fix was scoping those rules to the context they were written for. The
important half of the fix was that the renderer now states which rules were
relaxed and why, because a rule dropped quietly is worse than the bug it works
around — it turns a visible constraint into an invisible one.

**The same mistake, in a different medium.** The transfer-to-human tool on a voice
agent originally required the caller to know the founder's first name, as a spam
filter. That is sound reasoning about cold callers and useless as a gate, because
almost nobody phoning a business for the first time knows the founder's first
name — including the people you most want to reach you. The rule did not separate
real callers from noise. It separated people who had already met me from everyone
else, and everyone else is the reason the number exists. Removed.

The diagnostic in both cases is the same question: not what is this rule intended
to exclude, but what does it actually exclude.

→ `case-studies/voice-and-chat-agent.md`

---

## The layer underneath eleven rules

None of the above survives contact with time unless something checks it. A
session-start preflight runs three deterministic checks against the live data and
stays silent when they pass. A post-landing debrief refuses to let a session end
with uncommitted machinery, documentation that has drifted from its code, or
source material that has crept into version control - and it checks both the
project repository and the global configuration repository separately, because
they have different remotes and a commit in one does not carry the other. A
pre-commit hook blocks credentials and private names. A claims guard reads Word
documents as well as markdown, because the file that once got out was a `.docx`
and a markdown-only scan would not have seen it.

That layer is not the interesting part of the work. It is the part that decides
whether the interesting part is still true in six months.

→ `exhibits/session_debrief.py`

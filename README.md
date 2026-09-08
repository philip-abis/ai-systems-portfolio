# AI systems, and why they are shaped the way they are

Philip Garrison. Twenty-five years in commercial operations across logistics,
wine importing and AgTech. What follows is what I have built with Claude over the
last several months, and more importantly, the reasoning underneath it.

I am not a software engineer and this is not an engineering portfolio. I do not
write production code by hand; I design these systems, direct their construction,
and operate them against real data with real users. The judgment is the part
worth reading.

---

## The short version

**Four prospect research pipelines.** One finds wholesale distributors across the
United States for a Long Island oyster farm with no sales force. Another maps the
drone-services market for a start-up opening eight countries in North and South
America: Argentina, Brazil, Canada, Chile, Colombia, Mexico, Peru and the United
States. Both ingest public government registries
and the open web, qualify against a deterministic gate, and hand a human a ranked
call list with the evidence behind every judgment attached to it.

At that scope the numbers mean something. The two working ledgers hold 4,702 and
2,341 companies, of which 1,960 have been individually rated, and 384 survive
qualification to reach the call list itself: 99 rated Strong, 285
Promising, every one of them a distributor rather than a restaurant or a retailer.

Most of the funnel is discarding, and that is the design rather than a shortfall.
One national register alone returns 6,912 companies for a sector where 55 are
material. The filter that drops the other 6,857 runs at fetch time rather than
downstream, because passing them along would look like thoroughness while moving
the judgment somewhere nobody can inspect it.

**A vision-based grading tool** that reads photographed workbook pages, grades
them against an answer key, tracks per-concept accuracy across a chapter and
rolls the result up to a database. It is the only system here with verifiable
ground truth, and it carries an eval suite.

**A field sales app** deployed to a non-technical user who works it from his
phone: one company at a time, tap to dial, four fields after the call. Static
page, Postgres behind it, row-level security, offline-first so a dead signal on a
dock loses nothing.

**A travel-search skill** whose entire ranking lives in a config file rather than
in a model's judgment, so the same inputs always produce the same answer. It is
the one place here where a numeric score is legitimate, and the architecture
document explains why that is not a contradiction.

**An assistant reachable two ways.** Abby answers my consulting practice's phone
and its website chat. On the phone she runs on `gpt-4.1` with Deepgram
transcription, books a fifteen-minute call against a live calendar through custom
tools, and transfers to a human on request; on the site she is a widget that
answers questions and routes people to the same booking. Two builds on two
platforms, one persona, live since March. Most of the interesting design is about
failure modes that only exist on a call: never guess at a bad transcription, and
acknowledge out loud before a silent tool call, because silence during one reads
as a dropped line and the caller hangs up.

**A reliability layer** underneath all of it, which is the part I would defend
before the rest. Three deterministic checks run against the live data before a
session starts and stay silent when they pass. A second pass at the end refuses to
let a session close with machinery uncommitted, documentation that has drifted
from its code, or source material that has crept into version control. Neither
depends on anyone remembering to run it, which is the only reason either still
works months later.

Roughly 24,000 lines of working machinery across eleven skills, connected to
Notion, Gmail, Google Workspace, Slack and two web-data providers over MCP, with
Supabase for Postgres and auth and Netlify for hosting where something has to be
a real web app. All of it built with Claude Code, mostly in VS Code, sometimes
straight from the terminal, and deployed to a chat surface a non-technical
operator uses. That
split between where it is written and where it is run shows up in nearly every
design decision here.

---

## Start here

**[ARCHITECTURE.md](ARCHITECTURE.md)** is the document I would want read. Eleven
decisions that recur across every system, each stated with the specific failure
that produced it. About ten minutes.

Then whichever case study fits what you care about:

- **[Prospect research at scale](case-studies/prospect-pipelines.md)**: the
  largest system, the government registries underneath it, and the day six
  separate code paths each silently overrode a human judgment.
- **[Grading, with ground truth](case-studies/workbook-grading.md)**: the only
  system here that can be scored, including the pass where fixing the ambiguous
  items made the accuracy number go *down* and it was reported anyway.
- **[A tool someone else uses](case-studies/call-sheet.md)**: the app, the
  security model, and why the data is not in the page.
- **[An assistant that answers the phone and the website](case-studies/voice-and-chat-agent.md)**: the voice agent, the decisions that only matter on a call, and the access control
  I built and then removed once I worked out what it was actually filtering.

The `exhibits/` directory holds seven files chosen because each one demonstrates a
rule, not because it is large. Every one is excerpted from a system in production
use. Client identities have been removed from the commentary; the logic is
unmodified, and where a docstring was rewritten the file says so at the top.

---

## Three mistakes that changed the design

Each cost something real, and each produced a structural change rather than a
resolution to be more careful.

**Specifying the size of the answer instead of the criteria for it.** I told the
system roughly how many prospects the shortlist should hold. That sounds like
direction and is really an inversion: a count is an output of qualification, so
supplying it as an input means the gates get tuned until they produce it. What
fixed it was not a better score. It was removing the ability to have one, and
never stating a target again.

**Trusting the pipeline instead of testing it.** I asked the client to name the
companies he was already selling to, then went looking for them in my own output.
Four of the six were in the data and had been thrown out, not ranked low,
discarded, for the crime of not having been researched yet. Those six are now a
permanent regression test that runs at the start of every working session.

**Believing an extraction without checking the page loaded.** It returned three
confident figures and a complete policy summary, read off a page that did not
exist. Nothing errored, because from the extractor's side nothing failed: it was
handed text and produced the requested shape. Every schema here now carries a
field asserting the page came back.

---

## What this is not

I do not write agent frameworks and I have not shipped a production LLM
application. This is system design, orchestration and operation, at the level
where the questions are which work belongs to a script and which to a model,
where the boundary between them is enforced, who is allowed to write which field,
and what happens when a step fails silently.

Nothing in this repository is anyone else's work. Third-party skill catalogues I
use are excluded on purpose.

See [NOTICE](NOTICE) for terms.

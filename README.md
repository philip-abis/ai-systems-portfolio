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

**Four prospect research pipelines.** Their working ledgers hold 4,702 and 2,341
companies; 1,960 have been individually rated. The registries feeding them are
larger still — one national register alone returns 6,912 companies, of which 55
are material, and the filter that discards the rest is part of the design rather
than an afterthought. They qualify against a deterministic gate and hand a human
a ranked call list with the evidence attached. Built for a Long Island oyster
farm and for a drone-services start-up.

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

**A reliability layer** underneath all of it: session-start data checks, an
end-of-session audit that blocks a close on drifted documentation or leaked
material, and a guard that reads Word documents because the file that once got
out was a `.docx`.

Roughly 24,000 lines of working machinery across eleven skills, connected to
Notion, Gmail, Google Workspace, Slack and two web-data providers over MCP. All
of it authored in code and deployed to a chat surface a non-technical operator
uses, which is a constraint that shows up in nearly every design decision here.

---

## Start here

**[ARCHITECTURE.md](ARCHITECTURE.md)** is the document I would want read. Eleven
decisions that recur across every system, each stated with the specific failure
that produced it. About ten minutes.

Then whichever case study fits what you care about:

- **[Prospect research at scale](case-studies/prospect-pipelines.md)** — the
  largest system, the government registries underneath it, and the day six
  separate code paths each silently overrode a human judgment.
- **[Grading, with ground truth](case-studies/workbook-grading.md)** — the only
  system here that can be scored, including the pass where fixing the ambiguous
  items made the accuracy number go *down* and it was reported anyway.
- **[A tool someone else uses](case-studies/call-sheet.md)** — the app, the
  security model, and why the data is not in the page.

The `exhibits/` directory holds seven files chosen because each one demonstrates a
rule, not because it is large. Every one is excerpted from a system in production
use. Client identities have been removed from the commentary; the logic is
unmodified, and where a docstring was rewritten the file says so at the top.

---

## What I would want asked about

The failures, because they are the only part that cannot be faked.

Specifying the size of the answer instead of the criteria for it. I once told the
system roughly how many prospects the shortlist should hold, which sounds like
direction and is really an inversion — a count is an output of qualification, so
supplying it as an input just means the gates get tuned until they produce it.
What fixed it was not a better score. It was removing the ability to have one, and
never stating a target again.

The day I stopped trusting the pipeline and asked the client to name the
companies he was already selling to. Four of the six were in my data and had been
thrown out — not ranked low, discarded, for the crime of not having been
researched yet. Those six are now a permanent regression test that runs at the
start of every working session.

The extraction that returned three confident figures and a complete policy
summary read off a page that did not exist. Nothing errored. That is why every
schema here carries a field asserting the page actually loaded.

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

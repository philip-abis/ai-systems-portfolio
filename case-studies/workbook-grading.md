# Grading, with ground truth

Three chained skills that take photographs of completed workbook pages and
produce a graded chapter, a per-concept accuracy breakdown, a review brief, a
printable quiz and a database rollup.

It is the only system in this repository whose output can be scored. Every other
system produces judgments nobody can check. A graded page has a right answer.

## What it does

Photographs of student work land in a chapter folder. The pipeline preprocesses
them, reads each page, grades every exercise against the answer key where one
exists, and where none does, solves independently and verifies. Results go into a
chapter ledger. When the chapter closes, statistics roll up, weak concepts are
identified by threshold, and the result is written to a database and handed to
the next skill, which produces the review brief, the quiz PDF and prompts for
further study.

Judgment lives in the skill definition. All bookkeeping, hashing, dedupe,
merging, statistics, image preprocessing, lives in scripts that take arguments,
print JSON to stdout, and never call a model or an API. Human-readable progress
goes to stderr so stdout always parses as a single JSON document.

## The design decisions worth naming

**Pages are classified by content at read time, not by filename or folder.** A
page with handwriting is student work and gets graded. A print-only page is
reference material, logged as such, and skipped. Filenames are not a schema.

**A teacher's mark is never overruled.** Where the grader disagrees with a mark
already on the page, it records a discrepancy rather than substituting its own
verdict. The teacher outranks the model, and the disagreement is surfaced rather
than resolved silently.

**Identity is derived, not stored.** Subject, grade and chapter come from the
path, and grade identifies which student this is, so there is no separate student
field anywhere in the schema. That was a convenience decision that turned out to
be a privacy one.

**Ambiguity is a verdict, not a fallback.** An unclear read is recorded as
ambiguous and flagged, never guessed. That escape hatch was originally written
for unclear teacher marks and had to be extended to the grader's own uncertain
reads of small handwritten fractions, where independent arithmetic did not
reconcile cleanly with the image.

## The number that went down

On a second pass over one chapter, six items previously flagged ambiguous turned
out to be resolvable from the existing photographs by cropping the unclear region
and magnifying it. One of them was a student's own annotation next to her answer,
misread as an illegible teacher mark at page scale.

Resolving all six moved chapter accuracy from 79.4% to **75.0%** and changed the
diagnosis of one weak concept from a method gap to a single denominator slip.

The number got worse. That is the correct outcome, the earlier figure was
higher because four wrong answers were sitting in a bucket that did not count
against it, and it is recorded in the skill's improvements log with the date. A
system that only reports numbers when they improve is not measuring anything.

The lasting change was procedural: crop and magnify is now a required step before
escalating to ambiguous, and escalation is reserved for photographs too
low-resolution to resolve even magnified.

## Other things the log records

A glob fixed at exactly two directory levels silently never surfaced pending work
in a chapter nested three levels deep. It raised no error; it simply returned
nothing, which is indistinguishable from having nothing to do. Fixed with a
recursive glob, verified against both directory shapes at once.

Two skills built to run in sequence were never wired together, so the
review package had to be requested by name every time. Nobody noticed until a
chapter was closed and the quiz that was supposed to follow never arrived. The
handoff is now automatic and announced rather than confirmed, because closing the
chapter is already the decision.

An API required a date to be set through an expanded key rather than a plain
value, the kind of detail that costs an hour and is worth a line in a log so it
costs nobody an hour again.

## Evaluation

Seven scripted evals with fixtures, including one that resubmits a page already
processed to confirm the ledger is idempotent rather than double-counting. That
is the same discipline as the duplicate-cluster assertion in the prospect
pipelines, applied to a completely different problem: state an invariant, then
make something check it.

## Tooling

Claude with vision for the reading and grading. Python standard library for the
ledger, Pillow for image preprocessing, ReportLab for the quiz PDF, a database
over MCP for the rollup. Degrades gracefully without the database by writing the
summary locally and flagging that the sync is pending, rather than failing the
whole chapter close.

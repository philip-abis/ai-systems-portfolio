# Prospect research at scale

Four pipelines, one architecture. The largest read 1,221 companies for a Long
Island oyster farm looking for wholesale buyers outside its home market. The same
shape was then applied to a drone-services start-up, to a country-level market
sizing exercise, and to a contact-research skill shared across all of them.

## The problem the architecture is answering

A prospect list is easy to generate and almost impossible to trust. Anyone can
produce 500 companies. The questions that decide whether it is worth anything
are: does this company actually buy the thing, who says so, and what happens when
two sources disagree.

So the design puts a hard, legally grounded gate at the front and confines the
model to the two questions that genuinely require judgment.

## Inputs

Two public government registries provide the spine: a state shellfish dealer
roster and the federal Interstate Certified Shellfish Shippers List. Between them
they enumerate every business permitted to buy and resell shellfish, and they
carry the permit class.

Permit class matters more than anything a website says, because it settles a
question no amount of reading can: whether a company **must** buy from someone
rather than harvesting its own. Certain credentials prove the holder cannot
harvest. That is a fact, not an inference, and the pipeline treats it as one.

From there the system finds and reads each company's own site. Directories,
aggregators and data brokers are excluded by an explicit list, because a
directory listing is never evidence about a business, only evidence that a
directory exists.

## What is a script and what is a model

Scripts do the registry fetches, the merge, the dedupe, the permit gate, the
scope definition, the statistics, and the export payload. All deterministic, all
re-runnable, all inspectable.

The model answers two questions. Does this company grow its own product, making
it a competitor as well as a buyer? And how good a fit is it, expressed as a band
with written criteria rather than a score.

A schema sits between the two so a failure on one side cannot silently corrupt
the other. Discovery appends to a JSONL as each company completes and skips ids
already present, so a crash at company 700 costs 700 fetches rather than 1,400.

## The day it went wrong six times

In a single working day, six separate functions each silently overrode a judgment
that had already been made. Each was individually reasonable.

A roster flag was treated as fatal, deleting a company the client was actively
selling to plus 141 other qualified dealers. Absence from a federal list was
treated as disqualifying, which would have erased every buyer in seven states
that run no such certification. Absence from one roster snapshot was read as "not
certified", marking 160 live businesses uncertified — all 160 clustered on nine
state renewal dates, which is renewal lag, not closure. A directory's "Market"
category was read as retail-only, downgrading a wholesaler supplying 200-plus
restaurants. And twice, a decision function ignored a credential that had already
settled the question, demoting 76 companies because their own sites confirmed the
qualifying fact without using the expected word.

The second of those two was found only because the band totals moved and someone
asked why.

Comments had not prevented it. Two of the six were written directly beneath the
comment describing the first. The defect was structural: six code paths wrote the
same field independently, and none could see what authority had already settled
it.

## What changed

One chokepoint. Every writer declares who is speaking, ordered from the client's
own word about his own customers down to credential structure alone. A lower
authority may raise a rating but never push it below a floor a higher one
established, and refusals are recorded on the record rather than swallowed.

Scope moved into a single definition with an audit that requires the count of
unaccounted companies to be zero. A separate check asserts that every duplicate
cluster leaves exactly one row standing, after a mutual-flagging bug hid seven of
the highest-rated companies for an entire run without raising an error anywhere.

## The falsification test

None of that proves the list is good. So I asked the client to name the companies
he was already selling to, and went looking for them in my own output.

Four of the six were in the data and had been thrown out. Not ranked low —
discarded, for the crime of not having been researched yet. The list was not
merely padded. It was missing the answer.

Those six are now a permanent regression test. A validation script re-scores the
ranking against them and runs automatically at the start of every working
session, so the specific way this system was once wrong cannot come back without
someone being told.

## Output and ownership

A ranked call list in Notion, banded, every rating carrying its evidence and a
written rationale. The ownership line is explicit and recorded in the database's
own column descriptions so a rebuild cannot lose it: the research owns the
research fields and overwrites them on every push, the CRM owns the five fields a
caller fills in, and the two are joined on a stable id rather than on company
name, because registry names, trade names and CRM display names diverge in every
dataset and a name join breaks silently.

## Tooling

Claude, mostly Opus, orchestrated in Claude Code with the same skills packaged to
run in Claude Cowork so a non-technical operator can use them without a terminal.
Firecrawl for fetching. Notion over MCP as CRM and system of record. Python
standard library, no framework — nothing an orchestration framework would have
done here was not done more legibly by a JSON file and a schema.

## Honest assessment

The top band is small and I have left it small. Nothing in the rating code can be
tuned to hit a count, which was a deliberate response to having done exactly that
once. A low hit rate on a qualified list is a better outcome than a long list
nobody trusts, and the client works it in call order rather than by volume.

# An assistant that answers the phone and the website

Abby is the assistant for my consulting practice. She answers the company phone
and she answers the chat widget on the site, and to anyone contacting the business
she is one assistant reachable two ways. Underneath she is two builds on two
platforms, which is a real distinction and one I would rather state than blur.

Both went live in the same week in March and have run since.

## What she does

**On the phone.** Answers with "ABI Solutions, this is Abby. How can I help you
today?" Answers questions about the business. Books a fifteen-minute intro call
against a live calendar, which requires a name and an email address, then confirms
it. Transfers to a human on request, in any phrasing. Logs the interaction.

**On the website.** A persistent widget, described in its own configuration as
available around the clock to answer questions, schedule consultations, and help a
visitor work out whether AI is worth doing in their business. Styled to the site
rather than left on defaults, brand colour, custom avatar, a composer prompt in
her own voice. Proactive pop-ups are switched off deliberately; a bubble that
interrupts a reader after ten seconds is a tactic that annoys more people than it
converts.

Both channels book, and both can reach a person. What differs is the shape of the
conversation rather than the capability: a caller expects to finish in one turn-
taking exchange, where a visitor can be given options to click and can leave the
window open.

## The build

| | |
|---|---|
| Voice | VAPI, `gpt-4.1`, Deepgram `nova-3` transcription, fallback voice configured |
| Chat | Botpress webchat v2, deployed, embedded on the site |
| Booking | Cal.com, through two separate custom tools |
| Logging | Google Sheets row append |
| Transfer | VAPI `transferCall` to a real number |

Four tools are attached to the voice assistant: check availability, create a
booking, transfer to a human, append a log row. Availability and booking are
separate on purpose, the model checks what exists before it offers anything,
rather than proposing a time and discovering it is taken.

Voice created 7 March, chat 11 March, both last modified 12 March. Unchanged
since, which is its own kind of evidence.

## The design decisions that only matter on a phone

Voice has failure modes text does not, and most of the prompt is about them.

**Do not guess at a bad transcription.** The instruction is explicit: if the
assistant is not confident it understood, it must not guess, and it must say one
exact sentence asking the caller to repeat. This is the same rule as the
`ambiguous` verdict in the grading pipeline and the recorded refusal in the rating
chokepoint, arrived at independently in a third modality. An agent that produces a
plausible answer to something it did not hear is worse than one that asks again,
because the caller cannot see that it misheard.

**Acknowledge before transferring.** The prompt requires a specific spoken line,
"just a minute, I'll connect you now", *before* the transfer tool fires. Without
it there is a silent gap while the tool runs, and on a phone call silence is
indistinguishable from a dropped call. The caller hangs up. This costs one
sentence and prevents the most likely abandonment in the whole flow.

**Say the timezone once. Do not say the weekday.** All offered times are announced
as Eastern, once, at the top, because a call gives you no place to put a timezone
label. Options are given as month and day only.

The second half of that is a mitigation and I would rather name it than dress it
up. The honest reason the weekday is omitted is that I did not want to depend on
the model getting it right, and the real fix is an assistant that knows the 12th
is a Tuesday, which I have not built. There is a genuine argument underneath it,
which is that "Tuesday the 12th" asserts two facts where the booking needs one,
and the spare fact is something a caller can stop and check. That holds even for a
model that computes dates perfectly. But it is the argument I found afterwards,
not the reason I made the choice.

**One question per turn.** Obvious in text, essential in voice, where a caller
answering two questions at once produces a transcript nobody can parse
deterministically.

## The control I built and then removed

Originally the transfer-to-human tool had a gate: the caller had to know my first
name. The reasoning was ordinary spam filtering, someone who knows the founder by
name is a real contact, and someone cold-calling the company number is not.

It was the wrong control, and the reason is worth stating precisely. The gate
tested the wrong thing. Almost nobody calling a business for the first time knows
the founder's first name, including people you very much want to speak to. So the
filter did not separate real callers from noise; it separated people who had met
me from everyone else, and everyone else is the entire point of having a phone
number.

I removed it. The assistant now transfers whenever a human is asked for, in any
phrasing, person, agent, representative, owner, someone else.

This is the same failure as the arrival caps elsewhere in this portfolio, which
were correct for short domestic routes and eliminated every intercontinental
itinerary that could exist. A rule that is right in one context can, unchanged, do
something entirely different in another. Both were found the same way, by asking
what the rule actually excludes rather than what it was intended to exclude.

## Honest limits

The two builds do not share a brain. Same persona, same purpose, separate
configurations on separate platforms with their own knowledge, and keeping them
consistent is manual work nobody is doing. Unifying them behind one knowledge
source is the obvious next move and has not been done.

The chat side's knowledge base is out of date. I know, and it is on the list.

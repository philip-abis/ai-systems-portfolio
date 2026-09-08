# An assistant that answers the phone

Abby is the assistant on my consulting practice's website. She exists twice: as a
voice agent that answers the company phone, and as a chat widget on the site.
Two separate builds on two platforms, deliberately presented as one persona,
because to the person contacting the business it is the same assistant whether
they type or call.

You can use the chat one. The voice one answers a real number.

## What she does

Answers questions about the business. Books a fifteen-minute intro call against a
live calendar, which requires collecting a name and an email address, and sends a
confirmation. Transfers the call to a human on request. Logs the interaction.

## The build

| | |
|---|---|
| Voice | VAPI, `gpt-4.1`, Deepgram `nova-3` for transcription, with a fallback voice configured |
| Chat | Botpress webchat, embedded on the site |
| Booking | Cal.com, through two custom tools |
| Logging | Google Sheets row append |
| Transfer | VAPI `transferCall` to a real number |

Four tools are attached to the voice assistant: check availability, create a
booking, transfer to a human, and append a log row. Availability and booking are
separate tools on purpose — the model checks what exists before it offers
anything, rather than proposing a time and discovering it is taken.

In production since March, unchanged since March, which is its own kind of
evidence.

## The design decisions that only matter on a phone

Voice has failure modes text does not, and most of the prompt is about them.

**Do not guess at a bad transcription.** The instruction is explicit: if the
assistant is not confident it understood, it must not guess, and it must say one
exact sentence asking the caller to repeat. This is the same rule as the
`ambiguous` verdict in the grading pipeline and the recorded refusal in the rating
chokepoint, arrived at independently in a third modality. An agent that produces a
plausible answer to something it did not hear is worse than one that asks again,
because the caller cannot see that it misheard.

**Acknowledge before transferring.** The prompt requires a specific spoken line —
"just a minute, I'll connect you now" — *before* the transfer tool fires. Without
it there is a silent gap while the tool runs, and on a phone call silence is
indistinguishable from a dropped call. The caller hangs up. This costs one
sentence and prevents the most likely abandonment in the whole flow.

**Say the timezone once, and never say the weekday.** All offered times are
announced as Eastern, once, at the top. Options are given as month and day only.
Saying "Tuesday the 12th" on a call invites the caller to check whether the 12th
really is a Tuesday, and now you are arguing about a calendar instead of booking
a meeting. Removing the weekday removes an entire class of conversational
derailment.

**One question per turn.** Obvious in text, essential in voice, where a caller
answering two questions at once produces a transcript nobody can parse
deterministically.

## The control I built and then removed

Originally the transfer-to-human tool had a gate: the caller had to know my first
name. The reasoning was ordinary spam filtering — someone who knows the founder by
name is a real contact, and someone cold-calling the company number is not.

It was the wrong control, and the reason is worth stating precisely. The gate
tested the wrong thing. Almost nobody calling a business for the first time knows
the founder's first name, including people you very much want to speak to. So the
filter did not separate real callers from noise; it separated people who had met
me from everyone else, and everyone else is the entire point of having a phone
number.

I removed it. The assistant now transfers whenever a human is asked for, in any
phrasing — person, agent, representative, owner, someone else.

This is the same failure as the arrival caps elsewhere in this portfolio, which
were correct for short domestic routes and eliminated every intercontinental
itinerary that could exist. A rule that is right in one context can, unchanged, do
something entirely different in another. Both were found the same way, by asking
what the rule actually excludes rather than what it was intended to exclude.

## Honest limits

The two builds do not share a brain. The chat agent and the voice agent are
separate configurations on separate platforms with their own knowledge, and
keeping them consistent is manual. Unifying them behind one knowledge source is
the obvious next move and has not been done.

The chat agent's knowledge base is out of date. I know, and it is on the list.

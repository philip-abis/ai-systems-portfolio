# A tool someone else uses

A phone-first call sheet for the operator working the prospect list produced by
the research pipelines. Static page, Postgres behind it, deployed to a URL. The
user is not technical, has no account with any AI vendor, and works it from a
dock.

## Why it exists

The prospect list already lived in a database with a good web interface. That
interface was the wrong tool for the job in a specific way: the call-order view
displays 32 properties, opening a record on a phone means scrolling past all of
them to reach the five the caller owns, and a table has no concept of "next
company". Working a queue meant returning to the list and finding the place
again after every call.

A call sheet is not a table you edit. It is a queue: show me the next company,
here is the number, four questions, next.

## What it does

Opens on the first company with no capture against it, so the queue resumes
rather than restarting. Rank and fit badges, company, location, business type.
Call, Email and Website as thumb-sized targets. Who to ask for and their title.
The opening angle — the specific reason to phone this company rather than any
other. Longer research folded away until wanted.

Then four fields: stage as chips rather than a dropdown, next step, notes, and an
optional relationship marker. The contact date is stamped automatically rather
than typed.

## The three decisions that mattered

**The data is not in the page.** An earlier version embedded the company list in
the HTML, which was fine for a private artifact and unacceptable on a public
host: it would have put a client's ranked prospect list, opening angles and
contact names on the open internet. Companies live in the database and the page
is an empty shell until someone signs in. That is also what makes the source safe
to publish.

**Row-level security, not obscurity.** The public API key ships in the page
source, because that is what it is for. What protects the data is a policy layer
that grants nothing to anonymous requests and select, insert and update to
authenticated ones. There is deliberately no delete policy: a wrong stage is
fixable in seconds, a vanished call record is not.

The correct way to verify that is to load the deployed page signed out and
confirm it returns nothing, which I did, twice, once before the data was loaded
and once after. A comment claiming a system is secure is not evidence that it is.

**Offline-first, because of where it is used.** A capture is written to the phone
*before* the network is touched, and the network write is allowed to fail.
Anything unsent retries on the next save, on sign-in, and when the browser
reports it is back online. The header shows a count of unsent records rather than
a generic "saved", and signing out with pending work asks first.

The merge rule on load is the subtle part. The obvious rule is server-wins, and
it is wrong here: a capture made on a phone that has been offline for an hour is
the freshest record that exists. Newer wins on timestamp, and an unsynced local
record is never overwritten by an older server copy.

→ `exhibits/offline_first_capture.js`

## The constraint that shaped the architecture

The system of record is reachable only through the AI agent's own tool calls, not
through a server-side API. Nothing deployed can write to it directly.

Rather than route around that, the write path is inverted. The app becomes the
only writer for the five caller-owned fields and the system of record becomes a
one-way downstream display, updated by a session that reads the app's database
and pushes through the tools it does have. The alternative — two writable copies
of the same field with no reconciliation — produces loops, duplicates and silent
divergence as the normal case rather than the edge case.

The mirror carries a `last_synced` stamp, and a screen showing unsynced captures
says so rather than implying the board is current.

## Tooling

Plain HTML, CSS and JavaScript. No build step, no framework. Supabase for
Postgres, auth and row-level security. Netlify for static hosting. Accounts are
created by hand in the dashboard; there is no sign-up in the app, because an app
with a public URL and open registration is an app anyone can join.

## Honest status

The push back to the system of record is not written yet, so calls captured in
the app do not yet appear on the main board automatically. That is the next piece, and its two rules are already
written down: per-field, and only for companies that have a capture, so
it can never write an empty value over something a human typed.

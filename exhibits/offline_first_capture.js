/* Offline-first capture, from a call-sheet web app used in the field.
 *
 * WHY THE ORDER OF OPERATIONS IS THE WHOLE DESIGN
 * ===============================================
 * The user of this app makes sales calls from a dock and from a truck. The
 * obvious implementation - write to the server, then update the UI - loses a
 * call every time the signal drops, and loses it silently, because the failure
 * arrives after the user has already moved on to the next company.
 *
 * So a capture is written to localStorage BEFORE the network is touched, and the
 * network write is allowed to fail. Anything unsent is retried on the next save,
 * on the next sign-in, and on the browser's `online` event. The header shows a
 * count of unsent records rather than a generic "saved", and signing out with
 * unsent work asks first.
 *
 * THE MERGE RULE IS THE SUBTLE PART
 * ==================================
 * On load, the app has two sets of records: what the server holds and what this
 * phone holds. The naive rule is server-wins, and it is wrong here. A capture
 * made on a phone that has been offline for an hour is the freshest record that
 * exists; server-wins would silently discard it in the name of consistency. So
 * the newer of the two wins on `captured_at`, and local records that have never
 * synced are never overwritten by an older server copy.
 *
 * WHAT IT IS EVIDENCE OF
 * ======================
 * Designing for the environment the software is actually used in rather than the
 * one it is developed in. Every failure mode here - dead signal, backgrounded
 * tab, sign-out with pending work - produces a visible state rather than silent
 * loss, and the labels say where the data is rather than reassuring the user
 * that it is safe.
 */

async function commit() {
  const c = LIST[i];
  if (!c) return;
  if (!draft.stage && !draft.next && !draft.notes && !draft.confirmed) {
    toast("Nothing to save");
    return;
  }

  caps[c.ledger_id] = {
    ledger_id: c.ledger_id, company: c.company, rank: c.rank,
    stage: draft.stage || null, next_step: draft.next || null,
    notes: draft.notes || null, confirmed: draft.confirmed || null,
    last_contacted: new Date().toISOString().slice(0, 10),
    captured_at: new Date().toISOString(),
    synced: false,
  };

  writeLS(LS_CAP, caps);   // on the phone BEFORE the network is tried
  toast("Logged");
  next();                  // the user moves on immediately; sync is not in their way
  flush();                 // fire and forget, may fail, will be retried
}

async function flush() {
  const pending = Object.keys(caps).filter((k) => !caps[k].synced);
  if (!pending.length || !navigator.onLine) { chrome(); return; }

  for (const id of pending) {
    const rec = caps[id];
    const r = await sb.from("captures").upsert({
      ledger_id: rec.ledger_id, company: rec.company, rank: rec.rank,
      stage: rec.stage, next_step: rec.next_step, notes: rec.notes,
      confirmed: rec.confirmed, last_contacted: rec.last_contacted,
      captured_at: rec.captured_at,
    }, { onConflict: "ledger_id" });

    // Stop on the FIRST failure rather than pressing on. If the network just
    // died, the remaining calls will fail too, and burning through them turns
    // one retry into fifty.
    if (r.error) break;
    rec.synced = true;
  }
  writeLS(LS_CAP, caps);
  chrome();                // repaint the unsent counter, whatever happened
}

// On load: merge server records into local ones, newest wins.
async function mergeFromServer() {
  const cp = await sb.from("captures").select("*");
  if (cp.error) return;                       // offline: keep working from local
  (cp.data || []).forEach((row) => {
    const local = caps[row.ledger_id];
    if (!local || (row.captured_at || "") > (local.captured_at || "")) {
      caps[row.ledger_id] = toLocal(row, true);
    }
  });
  writeLS(LS_CAP, caps);
}

window.addEventListener("online", flush);

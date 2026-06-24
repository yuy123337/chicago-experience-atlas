// ============================================================
// Chicago Feedback — Google Apps Script Web App
// ------------------------------------------------------------
// HOW TO USE:
//   1. Open the "Chicago_feedbacks" Google Sheet → Extensions → Apps Script
//   2. Delete the stub, paste THIS file, Save.
//   3. Deploy → Manage deployments → ✎ edit → Version: "New version" → Deploy.
//      (Re-using the SAME deployment keeps your /exec URL unchanged — no re-wiring.)
//
// The website POSTs each contribution here. This script ONLY appends rows
// (write-only — visitors can't read/export). Rows route into 3 tabs:
//   been       one row per VISITED place — all 3 ratings + emotions + free text
//   curious    one row per place a visitor is curious about — expectation + emotions
//   explorers  de-duplicated emails of people who opted in
// `construct` is kept as a COLUMN (the map lens the visitor had open), not a tab split,
// so you can filter/group by it without fragmenting identical rows.
// Each row carries place_id (gmap_id) so it joins back to chicago_eligible_master.csv.
//
// EMOTIONS are dummy-coded: the site sends a pipe-string ("pleasant|interesting"),
// and this script expands it into one 0/1 column per option (Qualtrics "select all"
// style) so analysis needs no string parsing. The raw string is kept as emotions_raw.
// The 6 options pair to constructs: pleasant/enjoyable→happy, interesting/surprising→rich,
// fulfilling/purposeful→meaning.
// ============================================================

// Canonical emotion options, in fixed column order. Must match EMOS keys in index.html.
// 6 positive (2/construct) + 3 reverse-keyed negatives: stressful↔happy, boring↔rich, shallow↔meaning.
var EMO_KEYS = ['pleasant', 'enjoyable', 'interesting', 'surprising', 'fulfilling', 'purposeful', 'stressful', 'boring', 'shallow'];

// Add profanity / slurs here (lowercase). Rows that match are FLAGGED, not deleted
// (we preserve research data; the lab decides, and public views can hide flagged rows).
var BADWORDS = ['examplebadword'];

function flagText(t) {
  t = (t || '').toLowerCase();
  for (var i = 0; i < BADWORDS.length; i++) {
    if (t.indexOf(BADWORDS[i]) >= 0) return BADWORDS[i];
  }
  return '';
}

// "pleasant|interesting" -> {emo_pleasant:1, emo_interesting:1, ...} (0 for the rest), in EMO_KEYS order
function emoDict(raw) {
  var picked = (raw || '').toLowerCase().split('|');  // split the pipe-string the site sends
  var o = {}; EMO_KEYS.forEach(function (k) { o['emo_' + k] = picked.indexOf(k) >= 0 ? 1 : 0; }); return o;
}

// Append a row from a {field:value} object, SELF-HEALING the header so schema changes never need a tab wipe:
//   • empty tab        → write the canonical header, then the row
//   • missing a column → add that field as a NEW trailing column (no shifting; existing rows stay aligned)
//   • always           → write values in the CURRENT header's order
// This is why adding emotions / ratings / zip no longer requires clearing the Sheet.
function appendObj(sh, obj, order) {
  if (sh.getLastRow() === 0) sh.appendRow(order);
  var header = sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0];
  Object.keys(obj).forEach(function (k) {
    if (header.indexOf(k) < 0) { header.push(k); sh.getRange(1, header.length, 1, 1).setValue(k); }
  });
  sh.appendRow(header.map(function (col) { return obj.hasOwnProperty(col) ? obj[col] : ''; }));
}

// Idempotency: has this cid already been written to this tab? (so a client retry never duplicates a row)
function cidExists(sh, cid) {
  if (sh.getLastRow() < 2) return false;
  var header = sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0];
  var ci = header.indexOf('cid');
  if (ci < 0) return false;
  var col = sh.getRange(2, ci + 1, sh.getLastRow() - 1, 1).getValues();
  for (var i = 0; i < col.length; i++) { if (col[i][0] === cid) return true; }
  return false;
}

function doPost(e) {
  var lock = LockService.getScriptLock();   // serialize concurrent writes so simultaneous submissions never collide
  try { lock.waitLock(20000); } catch (e2) { return out({ ok: false, error: 'busy' }); }
  try {
    var d = JSON.parse(e.postData.contents);
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    if (d.relation === 'signup') { if (d.email) logSignup(ss, d); return out({ ok: true }); }  // email-only sign-up
    if (!d.relation || !d.place_id) return out({ ok: false, error: 'missing fields' }); // basic validation

    var been = d.relation === 'been';
    var tab = been ? 'been' : 'curious';                 // 2 data tabs — construct is a column, not a split
    var sh = ss.getSheetByName(tab) || ss.insertSheet(tab);

    var reason  = flagText(d.text || d.expectation || '');
    var flagged = reason ? 1 : 0;
    var emoCols = EMO_KEYS.map(function (k) { return 'emo_' + k; });  // header names

    if (d.cid && cidExists(sh, d.cid)) return out({ ok: true, dup: true });  // idempotent: a client retry — ack, don't re-write

    // Build the row as a field→value object so appendObj can self-heal the header.
    var obj = { ts:d.ts, ts_local:d.ts_local||'', cid:d.cid||'', place_id:d.place_id, passport_id:d.passport_id||'', construct:d.construct,
                name:d.name, cat:d.cat, grp:d.grp, lat:d.lat, lon:d.lon };
    var ed = emoDict(d.emotions); for (var k in ed) obj[k] = ed[k];     // emo_* dummies (incl. stressful/boring/shallow)
    obj.emotions_raw = d.emotions || ''; obj.email = d.email || ''; obj.flagged = flagged; obj.flag_reason = reason;

    var order;
    if (been) {
      obj.rich_1to5 = d.rich_1to5; obj.meaning_1to5 = d.meaning_1to5; obj.happy_1to5 = d.happy_1to5;
      obj.frequency = d.frequency; obj.endorse = d.endorse; obj.text = d.text;
      order = ['ts','ts_local','cid','place_id','passport_id','construct','name','cat','grp','lat','lon','rich_1to5','meaning_1to5','happy_1to5','frequency','endorse'].concat(emoCols).concat(['emotions_raw','text','email','flagged','flag_reason']);
    } else {
      obj.expectation = d.expectation;
      obj.exp_rich_1to5 = d.rich_1to5; obj.exp_meaning_1to5 = d.meaning_1to5; obj.exp_happy_1to5 = d.happy_1to5;  // curious sliders = EXPECTED ratings
      order = ['ts','ts_local','cid','place_id','passport_id','construct','name','cat','grp','lat','lon','expectation','exp_rich_1to5','exp_meaning_1to5','exp_happy_1to5'].concat(emoCols).concat(['emotions_raw','email','flagged','flag_reason']);
    }
    appendObj(sh, obj, order);

    if (d.email) logSignup(ss, d);   // also collect the email as a "become an Explorer" sign-up
    return out({ ok: true });
  } catch (err) {
    return out({ ok: false, error: String(err) });
  } finally {
    lock.releaseLock();
  }
}

// Clean, de-duplicated email list of people who opted in ("become a City Explorer").
function logSignup(ss, d) {
  var sh = ss.getSheetByName('explorers') || ss.insertSheet('explorers');
  if (sh.getLastRow() > 1) {  // dedup on email (column 2)
    var emails = sh.getRange(2, 2, sh.getLastRow() - 1, 1).getValues().map(function (r) { return r[0]; });
    if (emails.indexOf(d.email) >= 0) return;  // already signed up — skip
  }
  appendObj(sh, { ts:d.ts, ts_local:d.ts_local||'', email:d.email, home_zip:d.home_zip||'', passport_id:d.passport_id||'', first_construct:d.construct, cid:d.cid||'' },
            ['ts', 'ts_local', 'email', 'home_zip', 'passport_id', 'first_construct', 'cid']);
}

function out(o) {
  return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
}

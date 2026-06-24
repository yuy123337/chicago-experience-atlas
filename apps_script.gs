// ============================================================
// Chicago Feedback — Google Apps Script Web App
// ------------------------------------------------------------
// HOW TO USE:
//   1. Open the "Chicago Feedback" Google Sheet → Extensions → Apps Script
//   2. Delete the stub, paste THIS file, Save.
//   3. Deploy → New deployment → Web app
//        Execute as:        Me
//        Who has access:    Anyone
//      Deploy → authorize → copy the .../exec URL → send it to Claude to wire the site.
//
// The website POSTs each contribution here. This script ONLY appends rows
// (write-only — visitors can't read/export). Rows route into 3 tabs:
//   been_here  (the rich, experienced data — what we care about most)
//   want_to_go (intention + expectation)
//   curious    (intention + expectation, relation = explore)
// Each row carries place_id (gmap_id) so it joins back to chicago_eligible_master.csv.
// ============================================================

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

function doPost(e) {
  try {
    var d = JSON.parse(e.postData.contents);
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    if (d.relation === 'signup') { if (d.email) logSignup(ss, d); return out({ ok: true }); }  // email-only sign-up
    if (!d.relation || !d.place_id) return out({ ok: false, error: 'missing fields' }); // basic validation
    var been = d.relation === 'been';
    var tab = (d.construct || 'other') + (been ? '_been' : '_curious');  // e.g. rich_been, happy_curious, meaning_curious
    var sh = ss.getSheetByName(tab) || ss.insertSheet(tab);

    var reason  = flagText(d.text || d.expectation || '');
    var flagged = reason ? 1 : 0;

    if (sh.getLastRow() === 0) {
      sh.appendRow(been
        ? ['ts','place_id','construct','name','cat','grp','lat','lon','rich_1to5','meaning_1to5','happy_1to5','frequency','endorse','emotions','text','email','flagged','flag_reason']
        : ['ts','place_id','construct','name','cat','grp','lat','lon','expectation','email','flagged','flag_reason']);
    }

    sh.appendRow(been
      ? [d.ts,d.place_id,d.construct,d.name,d.cat,d.grp,d.lat,d.lon,d.rich_1to5,d.meaning_1to5,d.happy_1to5,d.frequency,d.endorse,d.emotions,d.text,d.email,flagged,reason]
      : [d.ts,d.place_id,d.construct,d.name,d.cat,d.grp,d.lat,d.lon,d.expectation,d.email,flagged,reason]);

    if (d.email) logSignup(ss, d);   // also collect the email as a "become an Explorer" sign-up
    return out({ ok: true });
  } catch (err) {
    return out({ ok: false, error: String(err) });
  }
}

// Clean, de-duplicated email list of people who opted in ("become a City Explorer").
function logSignup(ss, d) {
  var sh = ss.getSheetByName('explorers') || ss.insertSheet('explorers');
  if (sh.getLastRow() === 0) sh.appendRow(['ts', 'email', 'first_construct']);
  var existing = sh.getLastRow() > 1
    ? sh.getRange(2, 2, sh.getLastRow() - 1, 1).getValues().map(function (r) { return r[0]; })
    : [];
  if (existing.indexOf(d.email) < 0) sh.appendRow([d.ts, d.email, d.construct]);  // skip duplicates
}

function out(o) {
  return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
}

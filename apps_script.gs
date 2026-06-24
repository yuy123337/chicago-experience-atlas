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
var EMO_KEYS = ['pleasant', 'enjoyable', 'interesting', 'surprising', 'fulfilling', 'purposeful'];

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

// "pleasant|interesting" -> [1,0,1,0,0,0] in EMO_KEYS order
function emoBinaries(raw) {
  var picked = (raw || '').toLowerCase().split('|');  // split the pipe-string the site sends
  return EMO_KEYS.map(function (k) { return picked.indexOf(k) >= 0 ? 1 : 0; });
}

function doPost(e) {
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
    var emoVals = emoBinaries(d.emotions);                            // 0/1 values

    if (sh.getLastRow() === 0) {
      sh.appendRow(been
        ? ['ts','place_id','construct','name','cat','grp','lat','lon','rich_1to5','meaning_1to5','happy_1to5','frequency','endorse'].concat(emoCols).concat(['emotions_raw','text','email','flagged','flag_reason'])
        : ['ts','place_id','construct','name','cat','grp','lat','lon','expectation'].concat(emoCols).concat(['emotions_raw','email','flagged','flag_reason']));
    }

    sh.appendRow(been
      ? [d.ts,d.place_id,d.construct,d.name,d.cat,d.grp,d.lat,d.lon,d.rich_1to5,d.meaning_1to5,d.happy_1to5,d.frequency,d.endorse].concat(emoVals).concat([d.emotions||'',d.text,d.email,flagged,reason])
      : [d.ts,d.place_id,d.construct,d.name,d.cat,d.grp,d.lat,d.lon,d.expectation].concat(emoVals).concat([d.emotions||'',d.email,flagged,reason]));

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

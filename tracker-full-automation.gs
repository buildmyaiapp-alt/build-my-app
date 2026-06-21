/****************************************************************
 *  BUILD MY APP — FULL DAILY TRACKER AUTOMATION
 *  Runs entirely on Google's servers (no Mac needed).
 *  Every day it:
 *    1. Pulls yesterday's Meta Ads data
 *    2. Counts yesterday's ₹99 / ₹199 leads from the leads sheet
 *    3. Writes the complete row into the Campaign Tracker sheet
 *
 *  ── HOW TO INSTALL (one time) ──
 *  1. Open your Campaign Tracker Google Sheet
 *  2. Extensions → Apps Script
 *  3. Add a new script file, paste ALL of this in, Save
 *  4. Run the function  setup  (top toolbar ▶)  → Authorize when asked
 *     - This installs the daily 9 AM trigger AND backfills the last 7 days
 *  Done. It now runs by itself every morning.
 ****************************************************************/

// ── CONFIG ────────────────────────────────────────────────
var META_TOKEN   = "EAAjhqiQfnU0BRaFyWEc0Xe691JYQdP1fshF7QszbQFOlQZAAlvLttZAJML04HP7UzSVQEmZCDWZBBFMYHmaOXX8NKrjZCZCw1WRwKRw8GY682fIJoNfYqf2FviwpZAgMuIdgHu3ZA5jzuyG2BwjPPHtPs300KZBCvegH7qCmZBZCZC9IY5RCXNTNqMNcJ7aq78aDKQZDZD";
var AD_ACCOUNT   = "act_1186360290155097";
var META_VER     = "v19.0";

var TRACKER_SHEET_ID = "1l19zWjcmYxJ5EWda_uHDdMPJsjYqbxiHY9bzRG-ugWg";
var TRACKER_TAB      = "Tracker";

var LEADS_SHEET_ID   = "18c0VazYcBZtgdFDzJK6baFb4ZQieb0_mhfWzzkIcKRA";
var LEADS_TAB        = "Batch 28 June";   // ← change when a new batch starts
var LEADS_DATE_COL   = 1;           // column A = date/timestamp
var LEADS_AMOUNT_COL = 6;           // column F = "₹99" / "₹199"

var TZ = "Asia/Kolkata";
var DAYS = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"];
var MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];

// ── ENTRY POINTS ──────────────────────────────────────────

// Run this ONCE to install the daily trigger + backfill recent days.
function setup() {
  // remove any old triggers for this function
  ScriptApp.getProjectTriggers().forEach(function(t){
    if (t.getHandlerFunction() === "runDaily") ScriptApp.deleteTrigger(t);
  });
  // create daily 9 AM trigger
  ScriptApp.newTrigger("runDaily").timeBased().everyDays(1).atHour(9).create();
  Logger.log("✅ Daily 9 AM trigger installed.");
  // backfill last 7 days
  backfillDays(7);
  Logger.log("✅ Setup complete.");
}

// The daily trigger target — updates yesterday.
function runDaily() {
  var y = new Date();
  y.setDate(y.getDate() - 1);
  updateForDate(y);
}

// Backfill the last N days (today not included).
function backfillDays(n) {
  for (var i = n; i >= 1; i--) {
    var d = new Date();
    d.setDate(d.getDate() - i);
    try { updateForDate(d); } catch (e) { Logger.log("Error " + fmtISO(d) + ": " + e); }
  }
}

// ── CORE ──────────────────────────────────────────────────
function updateForDate(dateObj) {
  var iso = fmtISO(dateObj);                 // 2026-06-10
  var disp = dateObj.getDate() + " " + MONTHS[dateObj.getMonth()]; // "10 Jun"
  var day = DAYS[dateObj.getDay()];

  var meta = getMeta(iso);
  var leads = countLeads(iso);               // {l99, l199}
  var total = leads.l99 + leads.l199;
  var revenue = leads.l99 * 99 + leads.l199 * 199;
  var cpa = total ? round2(meta.spend / total) : "";
  var eff = round2(meta.spend - revenue);
  var recover = meta.spend ? round2(revenue / meta.spend * 100) : 0;
  var clpv = meta.lpv ? round2(meta.spend / meta.lpv) : 0;

  // Tracker columns D..R
  var newData = [
    meta.spend, leads.l99, leads.l199, total,
    cpa, meta.link_clicks, meta.lpv, meta.cpm,
    meta.ctr + "%", meta.cpc, clpv,
    revenue, eff, recover + "%", cpa
  ];

  writeRow(disp, day, newData);
  Logger.log(disp + ": spend ₹" + meta.spend + " | " + leads.l99 + "×99 + " + leads.l199 + "×199 = " + total + " leads | rev ₹" + revenue);
}

// ── META ──────────────────────────────────────────────────
function getMeta(iso) {
  var url = "https://graph.facebook.com/" + META_VER + "/" + AD_ACCOUNT + "/insights"
    + "?level=account&fields=spend,clicks,ctr,cpm,actions"
    + "&time_range=" + encodeURIComponent(JSON.stringify({ since: iso, until: iso }))
    + "&access_token=" + META_TOKEN;
  var res = JSON.parse(UrlFetchApp.fetch(url, { muteHttpExceptions: true }).getContentText());
  var d = (res.data && res.data[0]) ? res.data[0] : {};
  var acts = d.actions || [];
  function ga(t) { for (var i = 0; i < acts.length; i++) if (acts[i].action_type === t) return Math.round(parseFloat(acts[i].value)); return 0; }
  var spend = parseFloat(d.spend || 0);
  var clicks = parseInt(d.clicks || 0, 10);
  return {
    spend: spend, link_clicks: ga("link_click"), lpv: ga("landing_page_view"),
    cpm: round2(parseFloat(d.cpm || 0)), ctr: round2(parseFloat(d.ctr || 0)),
    cpc: clicks ? round2(spend / clicks) : 0
  };
}

// ── LEADS COUNT ───────────────────────────────────────────
function countLeads(iso) {
  var ss = SpreadsheetApp.openById(LEADS_SHEET_ID);
  var sh = ss.getSheetByName(LEADS_TAB);
  if (!sh) throw new Error("Leads tab not found: " + LEADS_TAB);
  var values = sh.getDataRange().getValues();
  var l99 = 0, l199 = 0;
  for (var i = 1; i < values.length; i++) {        // skip header
    var dateCell = values[i][LEADS_DATE_COL - 1];
    if (!dateCell) continue;
    if (cellToISO(dateCell) !== iso) continue;
    var amt = String(values[i][LEADS_AMOUNT_COL - 1]);
    if (amt.indexOf("199") !== -1) l199++;
    else if (amt.indexOf("99") !== -1) l99++;
  }
  return { l99: l99, l199: l199 };
}

// Convert a leads-sheet date cell (Date object OR "DD/MM/YYYY ..." text) to yyyy-MM-dd
function cellToISO(cell) {
  if (cell instanceof Date) return Utilities.formatDate(cell, TZ, "yyyy-MM-dd");
  var s = String(cell).trim();
  var m = s.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})/);   // DD/MM/YYYY
  if (m) return m[3] + "-" + pad(m[2]) + "-" + pad(m[1]);
  m = s.match(/^(\d{4})-(\d{2})-(\d{2})/);             // already ISO
  if (m) return m[1] + "-" + m[2] + "-" + m[3];
  return s;
}

// ── WRITE TO TRACKER ──────────────────────────────────────
function writeRow(disp, day, newData) {
  var ss = SpreadsheetApp.openById(TRACKER_SHEET_ID);
  var sh = ss.getSheetByName(TRACKER_TAB);
  var dates = sh.getRange("A:A").getValues();
  var rowIndex = -1;
  for (var j = 1; j < dates.length; j++) {
    var v = dates[j][0];
    if (!v) continue;
    var s = (v instanceof Date) ? (v.getDate() + " " + MONTHS[v.getMonth()]) : String(v).trim();
    if (s === disp) { rowIndex = j + 1; break; }   // 1-based row
  }
  if (rowIndex > 0) {
    sh.getRange(rowIndex, 4, 1, newData.length).setValues([newData]);
  } else {
    var last = sh.getLastRow() + 1;
    sh.getRange(last, 1).setValue(disp);
    sh.getRange(last, 2).setValue(day);
    sh.getRange(last, 4, 1, newData.length).setValues([newData]);
  }
}

// ── HELPERS ───────────────────────────────────────────────
function fmtISO(d) { return Utilities.formatDate(d, TZ, "yyyy-MM-dd"); }
function pad(n) { n = String(n); return n.length < 2 ? "0" + n : n; }
function round2(x) { return Math.round(x * 100) / 100; }

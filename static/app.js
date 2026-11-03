/* LockeSmith front end: the run-state form, one-click examples, streaming answers with live
   researcher lanes, cited answers with pick cards and a coverage chart, and the research trace.
   Talks to app.py: /catalog, /examples, /chat/stream (falls back to /chat), /upload_log,
   /clear_log, /run_state, /history, /clear. */

"use strict";

const $ = (sel, el = document) => el.querySelector(sel);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const SESSION_KEY = "lockesmith.session";
const MAX_LOG_BYTES = 4_000_000;

const GAMES = ["emerald", "ruby", "sapphire"];
const GAME_NAMES = { emerald: "Emerald", ruby: "Ruby", sapphire: "Sapphire" };

const ui = {
  game: "emerald",
  catalogs: {}, // game -> /catalog?game=... (badges, battles and places differ by game)
  catalog: null, // the current game's
  examples: [],
  speciesByName: new Map(),
  battleLabel: new Map(),
  sessionId: null,
  badges: new Set(),
  badgesSet: false, // false = "not given" (the agent will ask); true = the list is the answer, even empty
  used: new Set(),
  log: null,
  busy: false,
  entryCount: 0,
  options: {}, // kind -> Map(lowercased id or name -> {id, name}) for the pickers
  pickers: {},
};
const cap = (t) => t[0].toUpperCase() + t.slice(1);

/* ---- API --------------------------------------------------------------------------- */

async function api(path, body) {
  const opts = body === undefined ? {} : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
  const r = await fetch(path, opts);
  if (!r.ok) {
    let detail = r.statusText;
    try { detail = (await r.json()).detail || detail; } catch { /* not JSON */ }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return r.json();
}

function newSessionId() {
  const id = (crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).slice(2) + Date.now().toString(36)).replace(/-/g, "");
  try { localStorage.setItem(SESSION_KEY, id); } catch { /* storage blocked: the id lives for this page only */ }
  ui.sessionId = id;
  $("#session-id").textContent = id.slice(0, 8);
  return id;
}

/* ---- pick-from-list chips ------------------------------------------------------------------ */

function optionMap(items) {
  const map = new Map();
  for (const o of items) { map.set(String(o.id).toLowerCase(), o); map.set(o.name.toLowerCase(), o); }
  return map;
}

/* An input with a datalist that only accepts listed values, each shown as a removable chip.
   Typing filters the list; picking an entry (or Enter on an exact name) adds it. */
let pickerCount = 0;

/* `listId` shares a page-wide datalist (moves: one list for every party row). With `items`, the
   picker keeps its own list, offering only what isn't picked here or taken by `excluded()`. */
function tagPicker({ listId, items, options, max = Infinity, placeholder, more = "Add another", chipClass = () => "",
                     values = [], excluded = () => new Set() }) {
  const el = document.createElement("div");
  el.className = "tagpick";
  const chips = document.createElement("span");
  chips.className = "tagpick-chips";
  chips.style.display = "contents";
  const input = document.createElement("input");
  input.setAttribute("aria-label", placeholder);
  let list = null;
  if (items) {
    list = document.createElement("datalist");
    list.id = `pick-list-${++pickerCount}`;
    el.append(list);
    input.setAttribute("list", list.id);
  } else {
    input.setAttribute("list", listId);
  }
  el.append(chips, input);
  let picked = [];
  const changed = () => el.dispatchEvent(new Event("change", { bubbles: true }));
  const refresh = () => {
    if (!list) return;
    const taken = excluded();
    list.innerHTML = items.filter((o) => !taken.has(o.id) && !picked.some((x) => x.id === o.id))
      .map((o) => `<option value="${esc(o.name)}">`).join("");
  };
  const render = () => {
    chips.innerHTML = picked.map((o, i) => `<span class="tag ${chipClass(o)}">${esc(o.name)}<button type="button" data-i="${i}" aria-label="Remove ${esc(o.name)}">×</button></span>`).join("");
    input.hidden = picked.length >= max;
    input.placeholder = picked.length ? more : placeholder;
    refresh();
  };
  const add = (text) => {
    const o = options.get(text.trim().toLowerCase());
    if (!o || excluded().has(o.id)) { input.classList.toggle("invalid", !!text.trim()); return; }
    if (!picked.some((x) => x.id === o.id) && picked.length < max) picked.push(o);
    input.value = "";
    input.classList.remove("invalid");
    render();
    changed();
  };
  input.addEventListener("input", (e) => {
    input.classList.remove("invalid");
    // A datalist pick arrives as a replacement, not typing
    if (e.inputType === "insertReplacementText" || e.inputType === undefined) add(input.value);
  });
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") { e.preventDefault(); add(input.value); }
    else if (e.key === "Backspace" && !input.value && picked.length) { picked.pop(); render(); changed(); }
  });
  input.addEventListener("change", () => { if (input.value) add(input.value); });
  chips.addEventListener("click", (e) => {
    const b = e.target.closest("button[data-i]");
    if (!b) return;
    picked.splice(Number(b.dataset.i), 1);
    render();
    changed();
    input.focus();
  });
  el.addEventListener("click", (e) => { if (e.target === el) input.focus(); });
  el.getValues = () => picked.map((o) => o.name);
  el.getIds = () => new Set(picked.map((o) => o.id));
  el.refresh = refresh;
  el.setValues = (vals) => {
    picked = [];
    const taken = excluded();
    for (const v of vals || []) {
      const o = options.get(String(v).toLowerCase());
      if (o && !taken.has(o.id) && !picked.some((x) => x.id === o.id) && picked.length < max) picked.push(o);
    }
    input.value = "";
    render();
  };
  el.setValues(values);
  return el;
}

/* ---- the run form ---------------------------------------------------------------------- */

/* The parts of the form that differ by game: badge leaders, the story battles, Nuzlocke places. */
function applyCatalog() {
  const c = ui.catalog;
  ui.battleLabel = new Map(c.battles.map((b) => [b.id, b.label]));
  $("#badges").innerHTML = c.badges.map((b) => {
    const leader = b.label.split(": ")[1] || b.label;
    const name = b.id[0].toUpperCase() + b.id.slice(1);
    return `<button type="button" class="badge-btn" data-badge="${b.id}" aria-pressed="false" title="${esc(b.label)}">
      <span class="b-name">${esc(name)}</span><span class="b-leader">${esc(leader)}</span></button>`;
  }).join("");
  $("#last-battle").innerHTML = `<option value="">From my badges</option>`
    + c.battles.map((b) => `<option value="${b.id}">${esc(b.label)}</option>`).join("");
}

/* Switch the form to another game. Badges keep their names across games; a last battle that
   doesn't exist in the new game (Emerald's Space Center) is cleared. */
function setGame(game) {
  game = GAMES.includes(game) ? game : "emerald";
  for (const el of document.querySelectorAll('input[name="game"]')) el.checked = el.value === game;
  if (game === ui.game && ui.catalog) return;
  const last = $("#last-battle").value;
  ui.game = game;
  ui.catalog = ui.catalogs[game];
  applyCatalog();
  $("#last-battle").value = ui.battleLabel.has(last) ? last : "";
  renderUsedList();
  paintBadges();
}

function buildForm() {
  const c = ui.catalog;
  $("#species-list").innerHTML = c.species.map((s) => `<option value="${esc(s.name)}">`).join("");
  for (const s of c.species) ui.speciesByName.set(s.name.toLowerCase(), s);
  applyCatalog();
  $("#game").addEventListener("change", (e) => { if (e.target.name === "game") { setGame(e.target.value); updateStatus(); } });
  $("#move-list").innerHTML = c.moves.map((m) => `<option value="${esc(m.name)}">`).join("");
  ui.options.species = optionMap(c.species);
  ui.options.moves = optionMap(c.moves);
  ui.options.types = optionMap(c.types.map((t) => ({ id: t, name: cap(t) })));
  const typeChip = (o) => `type ${o.id}`;
  const typeItems = c.types.map((t) => ({ id: t, name: cap(t) }));
  // A type can be allowed or banned, not both: each box hides and refuses the other's types
  ui.pickers.allowedTypes = tagPicker({ items: typeItems, options: ui.options.types, placeholder: "Empty: every type is allowed",
    more: "Add a type", chipClass: typeChip, excluded: () => ui.pickers.bannedTypes?.getIds() ?? new Set() });
  ui.pickers.bannedTypes = tagPicker({ items: typeItems, options: ui.options.types, placeholder: "Empty: no type is banned",
    more: "Add a type", chipClass: typeChip, excluded: () => ui.pickers.allowedTypes.getIds() });
  ui.pickers.allowedTypes.addEventListener("change", () => ui.pickers.bannedTypes.refresh());
  ui.pickers.bannedTypes.addEventListener("change", () => ui.pickers.allowedTypes.refresh());
  ui.pickers.allowedTypes.refresh();
  ui.pickers.bannedSpecies = tagPicker({ listId: "species-list", options: ui.options.species, placeholder: "e.g. Gyarados", more: "Add a Pokémon" });
  $("#r-allowed-types").appendChild(ui.pickers.allowedTypes);
  $("#r-banned-types").appendChild(ui.pickers.bannedTypes);
  $("#r-banned").appendChild(ui.pickers.bannedSpecies);
  renderUsedList();

  $("#badges").addEventListener("click", (e) => {
    const btn = e.target.closest(".badge-btn");
    if (!btn) return;
    const id = btn.dataset.badge;
    ui.badges.has(id) ? ui.badges.delete(id) : ui.badges.add(id);
    ui.badgesSet = true;
    paintBadges();
  });
  $("#no-badges").addEventListener("click", () => { ui.badges.clear(); ui.badgesSet = true; paintBadges(); });
  $("#add-member").addEventListener("click", () => addMember());
  $("#used-filter").addEventListener("input", renderUsedList);
  $("#used-list").addEventListener("change", (e) => {
    if (e.target.name !== "used") return;
    e.target.checked ? ui.used.add(e.target.value) : ui.used.delete(e.target.value);
    updateStatus();
  });
  $("#r-nuzlocke").addEventListener("change", syncRuleVisibility);
  $("#r-caps").addEventListener("change", syncRuleVisibility);
  $("#run-form").addEventListener("input", updateStatus);
  $("#run-form").addEventListener("change", updateStatus);
  $("#log-file").addEventListener("change", onLogFile);
  $("#sample-log").addEventListener("click", () => loadSampleLog("fire-tate-liza.log"));
  $("#new-run").addEventListener("click", startOver);
  syncRuleVisibility();
}

function paintBadges() {
  for (const btn of document.querySelectorAll(".badge-btn")) btn.setAttribute("aria-pressed", String(ui.badges.has(btn.dataset.badge)));
  const hint = $("#badge-hint");
  if (!ui.badgesSet) { hint.textContent = 'Not set yet: pick the badges you hold, or "No badges yet".'; hint.className = "hint"; }
  else { hint.textContent = ui.badges.size ? `${ui.badges.size} badge${ui.badges.size > 1 ? "s" : ""} held.` : "No badges yet."; hint.className = "hint ok"; }
  updateStatus();
}

function renderUsedList() {
  const filter = $("#used-filter").value.trim().toLowerCase();
  const names = ui.catalog.places.map((p) => p.name);
  const custom = [...ui.used].filter((u) => !names.includes(u));
  const all = [...custom, ...names].filter((n) => !filter || n.toLowerCase().includes(filter));
  $("#used-list").innerHTML = all.map((n) =>
    `<label><input type="checkbox" name="used" value="${esc(n)}" ${ui.used.has(n) ? "checked" : ""}>${esc(n)}</label>`).join("")
    || `<span class="hint">No place matches.</span>`;
}

function syncRuleVisibility() {
  $("#nuzlocke-opts").hidden = !$("#r-nuzlocke").checked;
  $("#cap-offset-row").hidden = !$("#r-caps").checked;
  updateStatus();
}

function addMember(m = {}) {
  const rows = document.querySelectorAll(".member");
  if (rows.length >= 6) return;
  const row = document.createElement("div");
  row.className = "member";
  row.innerHTML = `
    <input class="species" list="species-list" placeholder="Species" aria-label="Species" value="${esc(m.species || "")}">
    <input class="level" type="number" min="1" max="100" placeholder="Lv" aria-label="Level" value="${esc(m.level || "")}">
    <button type="button" class="rm" aria-label="Remove">×</button>`;
  const moves = tagPicker({ listId: "move-list", options: ui.options.moves, max: 4, placeholder: "Moves, if you know them (up to 4)",
                            more: "Add a move", values: m.moves || [] });
  moves.classList.add("moves");
  row.appendChild(moves);
  row.querySelector(".rm").addEventListener("click", () => { row.remove(); $("#add-member").hidden = false; updateStatus(); });
  row.querySelector(".species").addEventListener("change", (e) => {
    e.target.style.borderColor = e.target.value && !ui.speciesByName.has(e.target.value.trim().toLowerCase()) ? "var(--rust)" : "";
  });
  $("#party").appendChild(row);
  $("#add-member").hidden = document.querySelectorAll(".member").length >= 6;
}

function readForm() {
  const starter = document.querySelector('input[name="starter"]:checked')?.value || null;
  const rival = document.querySelector('input[name="rival"]:checked')?.value || null;
  const party = [...document.querySelectorAll(".member")].map((row) => ({
    species: row.querySelector(".species").value.trim(),
    level: parseInt(row.querySelector(".level").value, 10),
    moves: row.querySelector(".moves").getValues(),
  })).filter((m) => m.species && m.level >= 1 && m.level <= 100);
  return {
    game: ui.game, starter, rival,
    badges: ui.badgesSet ? ui.catalog.badges.map((b) => b.id).filter((b) => ui.badges.has(b)) : null,
    last_battle: $("#last-battle").value || null,
    party,
    ruleset: {
      nuzlocke: $("#r-nuzlocke").checked,
      encounter_scope: $("#r-scope").value,
      gifts_count_as_encounter: $("#r-gifts").checked,
      dupes_clause: $("#r-dupes").checked,
      used_routes: $("#r-nuzlocke").checked ? [...ui.used] : [],
      level_caps: $("#r-caps").checked,
      level_cap_offset: parseInt($("#r-offset").value, 10) || 0,
      allowed_types: ui.pickers.allowedTypes.getValues(),
      banned_types: ui.pickers.bannedTypes.getValues(),
      no_legendaries: $("#r-nolegends").checked,
      wild_only: $("#r-wild").checked,
      banned_species: ui.pickers.bannedSpecies.getValues(),
      notes: $("#r-notes").value.split("\n").map((s) => s.trim()).filter(Boolean),
    },
  };
}

function fillForm(rs = {}, { highlight = false } = {}) {
  const before = highlight ? JSON.stringify(readForm()) : null;
  setGame(rs.game || "emerald");
  for (const el of document.querySelectorAll('input[name="starter"]')) el.checked = el.value === rs.starter;
  for (const el of document.querySelectorAll('input[name="rival"]')) el.checked = el.value === (rs.rival || "");
  ui.badges = new Set(rs.badges || []);
  ui.badgesSet = Array.isArray(rs.badges);
  $("#last-battle").value = rs.last_battle || "";
  $("#party").innerHTML = "";
  for (const m of rs.party || []) addMember(m);
  if (!(rs.party || []).length) addMember();
  $("#add-member").hidden = (rs.party || []).length >= 6;
  const r = rs.ruleset || {};
  $("#r-nuzlocke").checked = !!r.nuzlocke;
  $("#r-scope").value = r.encounter_scope || "location";
  $("#r-gifts").checked = !!r.gifts_count_as_encounter;
  $("#r-dupes").checked = !!r.dupes_clause;
  ui.used = new Set(r.used_routes || []);
  $("#r-caps").checked = !!r.level_caps;
  $("#r-offset").value = r.level_cap_offset || 0;
  ui.pickers.allowedTypes.setValues(r.allowed_types || (r.monotype ? [r.monotype] : []));
  ui.pickers.bannedTypes.setValues(r.banned_types || []);
  $("#r-nolegends").checked = !!r.no_legendaries;
  $("#r-wild").checked = !!r.wild_only;
  ui.pickers.bannedSpecies.setValues(r.banned_species || []);
  $("#r-notes").value = (r.notes || []).join("\n");
  const anyRule = r.nuzlocke || r.level_caps || r.no_legendaries || r.wild_only
    || [r.allowed_types, r.banned_types, r.banned_species, r.notes].some((xs) => (xs || []).length);
  $("#rules").open = !!anyRule;
  renderUsedList();
  paintBadges();
  syncRuleVisibility();
  if (highlight && before !== JSON.stringify(readForm())) {
    const panel = $(".run-panel");
    panel.classList.remove("flash"); void panel.offsetWidth; panel.classList.add("flash");
    $("#run-status").textContent = "Updated from your message";
  }
}

function updateStatus() {
  const rs = readForm();
  const missing = [!rs.starter && "starter", rs.badges === null && "badges"].filter(Boolean);
  const status = $("#run-status");
  status.textContent = missing.length ? `Needs: ${missing.join(", ")}` : `${rs.badges.length} badge${rs.badges.length === 1 ? "" : "s"} · ${rs.party.length || "no"} party`;
  status.className = "run-status" + (missing.length ? "" : " ready");
  const r = rs.ruleset;
  const n = [r.nuzlocke, r.level_caps, r.no_legendaries, r.wild_only, r.allowed_types.length, r.banned_types.length].filter(Boolean).length
    + r.banned_species.length + r.notes.length;
  $("#rules-count").textContent = n ? `${n} on` : "";
}

/* ---- randomizer log ------------------------------------------------------------------ */

const SHADOW_WORDS = {
  encounters: "wild and static Pokémon", trainer_mons: "trainer teams", species: "stats, types and abilities",
  evolutions: "evolutions", machines: "TM moves", move_tutors: "tutor moves", learnsets: "TM and tutor learnsets",
};

async function uploadLog(text, name) {
  if (text.length > MAX_LOG_BYTES) throw new Error("That file is too big for a randomizer log (over 4 MB).");
  const summary = await api("/upload_log", { log_text: text, name, session_id: ui.sessionId });
  ui.log = summary;
  if (summary.game && summary.game !== ui.game) { // the server read the log's game from its footer
    setGame(summary.game);
    $("#run-status").textContent = `Switched to ${GAME_NAMES[summary.game]} (the log's game)`;
  }
  renderLog();
  return summary;
}

async function onLogFile(e) {
  const file = e.target.files[0];
  if (!file) return;
  $("#log-summary").innerHTML = `<span class="hint">Reading ${esc(file.name)}…</span>`;
  try { await uploadLog(await file.text(), file.name); }
  catch (err) { $("#log-summary").innerHTML = `<span class="warn">Couldn't load that log: ${esc(err.message)}</span>`; }
  e.target.value = "";
}

async function loadSampleLog(file) {
  const text = await (await fetch(`/static/samples/${file}`)).text();
  await uploadLog(text, file);
  $("#randomizer").open = true;
}

function renderLog() {
  const s = ui.log;
  $("#log-pill").textContent = s ? "log loaded" : "";
  if (!s) { $("#log-summary").innerHTML = ""; return; }
  const reads = s.shadowed.map((t) => SHADOW_WORDS[t] || t);
  const unread = Object.values(s.unread || {});
  $("#log-summary").innerHTML = `
    <p class="ok">Loaded ${esc(s.log_id)}${s.seed ? ` (seed ${esc(s.seed)})` : ""}.</p>
    <p>Answers now use this log for: ${reads.length ? esc(reads.join(", ")) : "nothing (it only lists unchanged data)"}. Everything else is vanilla.</p>
    ${unread.length ? `<p class="warn">Changed but not readable yet, so it won't guess: ${esc(unread.join(", "))}.</p>` : ""}
    ${s.warning_count ? `<p class="hint">${s.warning_count} line(s) couldn't be placed; see the trace for details.</p>` : ""}
    <button type="button" class="link-btn" id="remove-log">Remove log</button>`;
  $("#remove-log").addEventListener("click", async () => {
    await api("/clear_log", { session_id: ui.sessionId });
    ui.log = null;
    renderLog();
  });
}

/* ---- examples ------------------------------------------------------------------------ */

function renderExamples() {
  // Small bubbles under the question box; hovering (or focusing) one shows what it is
  $("#examples").insertAdjacentHTML("beforeend", ui.examples.map((ex, i) => `
    <button type="button" class="ex-bubble${ex.readme ? " featured" : ""}" data-id="${esc(ex.id)}" aria-describedby="tip-${esc(ex.id)}">Example ${i + 1}<span class="ex-tip" role="tooltip" id="tip-${esc(ex.id)}">
      <span class="ex-tag">${esc(ex.tag)}</span>
      <span class="ex-title">${esc(ex.title)}</span>
      <span class="ex-blurb">${esc(ex.blurb)}</span>
      <span class="ex-q">“${esc(ex.message)}”</span>
      ${ex.readme ? `<span class="ex-readme">★ README sample</span>` : ""}</span></button>`).join(""));
  $("#examples").addEventListener("click", (e) => {
    const btn = e.target.closest(".ex-bubble");
    if (btn) useExample(ui.examples.find((x) => x.id === btn.dataset.id), btn);
  });
}

async function useExample(ex, btn) {
  if (ui.busy) return;
  for (const b of document.querySelectorAll(".ex-bubble")) b.classList.toggle("active", b === btn);
  if (ui.entryCount) resetConversation(); // each example is its own fresh run
  ui.log = null;
  renderLog();
  fillForm(ex.run_state);
  $("#run-status").textContent = `Filled in for “${ex.title}”`;
  if (ex.sample_log) {
    try { await loadSampleLog(ex.sample_log); }
    catch (err) { $("#log-summary").innerHTML = `<span class="warn">Couldn't load the sample log: ${esc(err.message)}</span>`; }
  }
  const q = $("#question");
  q.value = ex.message;
  const ask = $("#ask");
  ask.classList.remove("pulse"); void ask.offsetWidth; ask.classList.add("pulse");
  $("#composer").scrollIntoView({ behavior: "smooth", block: "nearest" });
  q.focus({ preventScroll: true });
}

/* ---- describing agents and tools in plain words ----------------------------------------- */

const AGENT_NAMES = {
  clarifier: "Gatekeeper", lead: "Lead", battle_researcher: "Battle researcher", catch_researcher: "Catch researcher",
  moves_researcher: "Moves researcher", story_researcher: "Story researcher", verifier: "Verifier", writer: "Writer", pipeline: "Pipeline",
};
const agentName = (a) => AGENT_NAMES[a] || a.replace(/_/g, " ");
const battleName = (id) => ui.battleLabel.get(id) || id;
const list = (xs) => (Array.isArray(xs) ? xs.join(", ") : xs);

function describeTool(name, a = {}) {
  const before = a.before_battle ? ` before ${battleName(a.before_battle)}` : "";
  switch (name) {
    case "decide": return "read the question and run state";
    case "dispatch_researchers": return `sent out ${(a.tasks || []).length || "the"} researcher${(a.tasks || []).length === 1 ? "" : "s"} in parallel`;
    case "scout_battle": case "get_trainer_team": case "threat_matrix": return `scouted ${battleName(a.battle || a.battle_ref || "the next battle")}`;
    case "gauntlet_overview": return "profiled every battle left in the run";
    case "get_remaining_battles": return "listed the battles ahead";
    case "get_catchable": return `checked what's catchable${a.types?.length ? ` (${list(a.types)})` : a.species ? ` (${a.species})` : ""}${before}`;
    case "assess_candidates": return `weighed ${list(a.species || [])} for the long run`;
    case "encounter_odds": return `checked encounter odds at ${a.location}`;
    case "species_info": return `read up on ${a.name}`;
    case "move_info": return `looked up ${a.name}`;
    case "moves_outlook": return `checked moves and evolutions for ${list(a.species || [])}${before}`;
    case "get_learnset": return `read ${a.species}'s learnset`;
    case "get_tm_availability": return `listed TMs obtainable${before}${a.species ? ` for ${a.species}` : ""}`;
    case "get_next_steps": return "worked out the next story steps";
    case "get_story_outline": return "outlined the road to the Champion";
    case "search_guide": return `searched the walkthrough for “${a.query}”`;
    case "query_db": return "queried the database";
    case "verify": return a.after === "repair" ? "re-checked the repaired picks" : `checked ${(a.picks || []).length} pick${(a.picks || []).length === 1 ? "" : "s"} against the data`;
    case "promote_backups": return "swapped failing picks for their backups";
    case "correct_where": return "corrected where to catch a pick, from the encounter data";
    case "citation_check": return a.after === "retry" ? "re-checked the citations" : "checked every citation";
    case "turn_limit_wrap_up": return "hit its tool budget and wrapped up";
    case "error": return "ran into an error";
    case "chart_error": return "couldn't draw the chart";
    default: return name.replace(/_/g, " ");
  }
}

/* ---- live progress ---------------------------------------------------------------------- */

class Progress {
  constructor(host) {
    this.started = performance.now();
    this.lanes = new Map();
    host.innerHTML = `<div class="progress-box" aria-live="polite">
      <div class="progress-now"><span class="now">Reading your question… <span class="cursor">▼</span></span><span class="progress-time">0 s</span></div>
      <div class="lanes"></div></div>`;
    this.box = host.firstElementChild;
    this.timer = setInterval(() => { $(".progress-time", this.box).textContent = `${Math.round((performance.now() - this.started) / 1000)} s`; }, 500);
  }
  now(text) { $(".now", this.box).innerHTML = `${esc(text)} <span class="cursor">▼</span>`; }
  lane(agent) {
    if (!this.lanes.has(agent)) {
      const el = document.createElement("div");
      el.className = "lane";
      el.innerHTML = `<h4>${esc(agentName(agent))}<span class="done"></span></h4><ol></ol>`;
      $(".lanes", this.box).appendChild(el);
      this.lanes.set(agent, el);
    }
    return this.lanes.get(agent);
  }
  event(ev) {
    if (ev.type === "agent_start") {
      const lane = this.lane(ev.agent);
      lane.classList.remove("idle");
      const label = { clarifier: "Reading your question…", lead: "The Lead is planning the research…", writer: "Writing it up…" }[ev.agent];
      this.now(label || `${agentName(ev.agent)} is digging in…`);
    } else if (ev.type === "tool_start") {
      if (ev.name === "dispatch_researchers") {
        const kinds = (ev.args.tasks || []).map((t) => agentName(`${t.researcher}_researcher`).replace(" researcher", ""));
        this.now(`Sending ${kinds.length} researchers out in parallel: ${kinds.join(", ").toLowerCase()}`);
      }
      const li = document.createElement("li");
      li.className = "running";
      li.dataset.name = ev.name;
      li.textContent = describeTool(ev.name, ev.args) + "…";
      $("ol", this.lane(ev.agent)).appendChild(li);
    } else if (ev.type === "tool_call") {
      const ol = $("ol", this.lane(ev.agent));
      let li = [...ol.querySelectorAll("li.running")].find((x) => x.dataset.name === ev.name);
      if (!li) { li = document.createElement("li"); ol.appendChild(li); }
      li.className = "";
      li.innerHTML = `<span class="t">${Math.round(ev.t)}s</span>${esc(describeTool(ev.name, ev.args))}`;
      if (ev.agent === "verifier") this.now(`Verifier ${describeTool(ev.name, ev.args)}`);
    }
  }
  stop() { clearInterval(this.timer); }
}

/* ---- asking ------------------------------------------------------------------------------- */

async function ask(message) {
  if (ui.busy || !message.trim()) return;
  ui.busy = true;
  $("#ask").disabled = true;
  $("#question").value = "";
  $("#empty")?.remove();
  const entry = newEntry(message);
  const progress = new Progress($(".entry-body", entry));
  const runState = readForm();
  const started = performance.now();
  try {
    const result = await streamChat({ message, session_id: ui.sessionId, run_state: runState }, progress);
    progress.stop();
    renderAnswer(entry, result.body, result.usage, (performance.now() - started) / 1000);
  } catch (err) {
    progress.stop();
    $(".entry-body", entry).innerHTML = `<p class="error-note">Sorry, that didn't come back: ${esc(err.message)}. Please try again.</p>`;
  } finally {
    ui.busy = false;
    $("#ask").disabled = false;
    syncRunState();
  }
}

async function streamChat(payload, progress) {
  let response;
  try {
    response = await fetch("/chat/stream", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
  } catch { response = null; }
  if (!response || !response.ok || !response.body) {
    progress.now("Researching… (this takes about a minute)");
    return { body: await api("/chat", payload), usage: [] };
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    let chunk;
    try { chunk = await reader.read(); }
    catch { return await waitForHistory(payload, progress); }
    if (chunk.done) break;
    buffer += decoder.decode(chunk.value, { stream: true });
    let cut;
    while ((cut = buffer.indexOf("\n\n")) >= 0) {
      const block = buffer.slice(0, cut);
      buffer = buffer.slice(cut + 2);
      const data = block.split("\n").filter((l) => l.startsWith("data: ")).map((l) => l.slice(6)).join("\n");
      if (!data) continue;
      const ev = JSON.parse(data);
      if (ev.type === "done") return { body: ev.body, usage: ev.usage || [] };
      if (ev.type === "error") throw new Error(ev.detail);
      progress.event(ev);
    }
  }
  return await waitForHistory(payload, progress);
}

async function waitForHistory(payload, progress) {
  // The stream dropped mid-answer; the server keeps working, so wait for the turn to land.
  progress.now("The live feed dropped; still waiting for the answer…");
  const startLen = (await api(`/history?session_id=${encodeURIComponent(payload.session_id)}`)).history.length;
  for (let i = 0; i < 60; i++) {
    await new Promise((r) => setTimeout(r, 5000));
    const h = (await api(`/history?session_id=${encodeURIComponent(payload.session_id)}`)).history;
    if (h.length > startLen) return { body: { response: h[h.length - 1].content, tool_calls: [], citations: [], plan: null, chart: null }, usage: [] };
  }
  throw new Error("timed out waiting for the answer");
}

async function syncRunState() {
  try {
    const s = await api(`/run_state?session_id=${encodeURIComponent(ui.sessionId)}`);
    if (s.run_state) fillForm(s.run_state, { highlight: true });
  } catch { /* keep the form as it is */ }
}

/* ---- rendering answers --------------------------------------------------------------------- */

function newEntry(question) {
  ui.entryCount += 1;
  const el = document.createElement("article");
  el.className = "entry";
  el.id = `entry-${ui.entryCount}`;
  el.innerHTML = `<h3 class="entry-q">${esc(question)}</h3><div class="entry-meta"></div><div class="entry-body"></div>`;
  $("#entries").appendChild(el);
  el.scrollIntoView({ behavior: "smooth", block: "start" });
  return el;
}

function markdown(text, citations, entryId) {
  const html = DOMPurify.sanitize(marked.parse(text || ""));
  const known = new Map((citations || []).map((c) => [String(c.n), c]));
  return html.replace(/\[(\d+)\]/g, (m, n) => {
    const c = known.get(n);
    return c ? `<a class="cite" href="#${entryId}-src-${n}" title="${esc(c.label)}">${n}</a>` : m;
  });
}

function typePills(species) {
  const s = ui.speciesByName.get(String(species || "").toLowerCase());
  return s ? s.types.map((t) => `<span class="type ${t}">${t}</span>`).join("") : "";
}

function pickCards(plan) {
  const recs = plan?.recommendations || [];
  if (!recs.length) return "";
  return `<div class="glance">${recs.map((r) => {
    const core = r.horizon !== "situational";
    const evo = r.evolve_to && r.evolve_to.toLowerCase() !== r.species.toLowerCase() ? r.evolve_to : "";
    const backups = (r.alternatives || []).map((a) => a.species).join(", ");
    return `<div class="pick ${core ? "core" : "situational"}">
      <div class="pick-head"><span class="pick-name">${esc(r.species)}${evo ? ` → ${esc(evo)}` : ""}</span>
        <span class="pick-horizon">${core ? "core pick" : "for this fight"}</span></div>
      <div class="pick-types">${typePills(evo || r.species)}</div>
      <dl>
        <dt>Role</dt><dd>${esc(r.role)}</dd>
        <dt>Where</dt><dd>${esc(r.where)}</dd>
        <dt>Ready for</dt><dd>${esc(battleName(r.before_battle))}</dd>
        ${r.key_moves?.length ? `<dt>Moves</dt><dd>${esc(r.key_moves.join(", "))}</dd>` : ""}
        ${backups ? `<dt>Backup</dt><dd>${esc(backups)}</dd>` : ""}
      </dl></div>`;
  }).join("")}</div>`;
}

function sourcesList(citations, entryId) {
  if (!citations?.length) return "";
  return `<details class="box sources"><summary>Sources (${citations.length})</summary><ol>${citations.map((c) => `
    <li id="${entryId}-src-${c.n}">${c.url ? `<a href="${esc(c.url)}" target="_blank" rel="noopener">${esc(c.label)}</a>` : esc(c.label)}
      <code>${esc(c.source_id)}</code></li>`).join("")}</ol></details>`;
}

function parseJSON(text) { try { return JSON.parse(text); } catch { return null; } }

function verifierSection(calls) {
  const v = calls.filter((c) => c.agent === "verifier");
  if (!v.length) return "";
  const items = v.map((c) => {
    const data = parseJSON(c.result);
    let body;
    if (Array.isArray(data) && data.length && typeof data[0] === "object") {
      body = data.map((x) => `<div class="violation"><span class="sev ${x.severity}">${esc(x.severity)}</span><strong>${esc(x.species)}</strong>${x.alt !== null && x.alt !== undefined ? " (backup)" : ""}: ${esc(x.detail)} <code>${esc(x.code)}</code></div>`).join("");
    } else if (Array.isArray(data)) {
      body = data.map((x) => `<div class="violation">${esc(x)}</div>`).join("");
    } else {
      body = `<div class="violation"><span class="sev ok">ok</span>${esc(c.result)}</div>`;
    }
    return `<div><span class="t">${Math.round(c.t)}s</span> <em>${esc(describeTool(c.name, c.args))}</em>${body}</div>`;
  }).join("");
  return `<div class="verifier"><h4>Verifier (code, no model)</h4>${items}</div>`;
}

function callDetails(c) {
  const args = Object.keys(c.args || {}).length ? JSON.stringify(c.args, null, 1) : "";
  return `<details class="call"><summary><span class="t">${Math.round(c.t)}s</span>${esc(describeTool(c.name, c.args))}</summary>
    <pre>${args ? `args: ${esc(args)}\n\n` : ""}result: ${esc(c.result)}</pre></details>`;
}

function traceSection(calls, usage) {
  if (!calls?.length) return "";
  const rounds = new Map();
  for (const c of calls) {
    if (c.agent === "verifier") continue;
    if (!rounds.has(c.round)) rounds.set(c.round, []);
    rounds.get(c.round).push(c);
  }
  const parts = [...rounds.entries()].sort((a, b) => a[0] - b[0]).map(([round, cs]) => {
    const researchers = [...new Set(cs.filter((c) => c.agent.endsWith("_researcher")).map((c) => c.agent))];
    const others = cs.filter((c) => !c.agent.endsWith("_researcher"));
    const dispatch = others.find((c) => c.name === "dispatch_researchers");
    const tasks = (dispatch?.args?.tasks || []).map((t) => `<li><strong>${esc(t.researcher)}:</strong> ${esc(t.task)}</li>`).join("");
    const title = round === 0 ? "Before research" : `Research round ${round}`;
    const note = researchers.length > 1 ? `${researchers.length} researchers ran in parallel, each in a fresh context.` : "";
    return `<div class="round"><h4>${title}</h4>${note ? `<p class="round-note">${note}</p>` : ""}
      ${others.map((c) => `<div><strong>${esc(agentName(c.agent))}</strong> ${callDetails(c)}</div>`).join("")}
      ${tasks ? `<details class="call"><summary>The Lead's tasks</summary><ul>${tasks}</ul></details>` : ""}
      ${researchers.length ? `<div class="lanes">${researchers.map((a) => `<div class="lane"><h4>${esc(agentName(a))}</h4>
        ${cs.filter((c) => c.agent === a).map(callDetails).join("")}</div>`).join("")}</div>` : ""}</div>`;
  }).join("");
  const n = usage?.length || 0;
  const tokens = (usage || []).reduce((s, u) => s + (u.input_tokens || 0) + (u.output_tokens || 0), 0);
  const fallback = (usage || []).filter((u) => u.fallback).length;
  const priced = (usage || []).filter((u) => typeof u.cost_usd === "number");
  const cost = priced.reduce((s, u) => s + u.cost_usd, 0);
  return `<details class="box trace"><summary>Research trace: how it got here (${calls.length} steps)</summary>
    ${parts}${verifierSection(calls)}
    ${n ? `<p class="usage">${n} model calls · ${tokens.toLocaleString()} tokens${priced.length === n ? ` · about $${cost.toFixed(3)} at Vertex AI list prices` : ""}${fallback ? ` · ${fallback} answered by the fallback model (rate limit or a stalled call)` : ""}</p>` : ""}</details>`;
}

function renderAnswer(entry, body, usage, seconds) {
  const calls = body.tool_calls || [];
  const researchers = new Set(calls.filter((c) => c.agent.endsWith("_researcher")).map((c) => `${c.round}:${c.agent}`));
  const rounds = new Set(calls.filter((c) => c.agent.endsWith("_researcher")).map((c) => c.round));
  const meta = [
    `${Math.round(seconds)} s`,
    researchers.size ? `${researchers.size} researcher run${researchers.size === 1 ? "" : "s"} in ${rounds.size} round${rounds.size === 1 ? "" : "s"}` : "",
    body.citations?.length ? `${body.citations.length} sources` : "",
    ui.log ? `<span class="loglabel">randomized: ${esc(ui.log.log_id)}</span>` : "",
  ].filter(Boolean);
  $(".entry-meta", entry).innerHTML = meta.map((m) => `<span>${m}</span>`).join("");
  const id = entry.id;
  $(".entry-body", entry).innerHTML = `
    ${pickCards(body.plan)}
    <div class="answer">${markdown(body.response, body.citations, id)}</div>
    ${body.chart ? `<figure class="chart"><div class="chart-host"></div><figcaption>Built from the trainer teams${ui.log ? " in your log" : ""} and the Gen III type chart; hover a cell for details.</figcaption></figure>` : ""}
    ${sourcesList(body.citations, id)}
    ${traceSection(calls, usage)}
    ${body.plan?.recommendations?.length ? `<div class="followups">
      <button type="button" class="chip" data-q="I don't like those picks. Give me something different.">Different picks, please</button>
      <button type="button" class="chip" data-q="What should I do next in the story?">What do I do next?</button>
      <button type="button" class="chip" data-q="Give me a plan from here to the Champion.">Plan to the Champion</button></div>` : ""}`;
  if (body.chart && window.vegaEmbed) {
    vegaEmbed($(".chart-host", entry), body.chart, { actions: false, renderer: "svg", config: chartTheme() }).catch(() => {
      $(".chart", entry).innerHTML = `<figcaption>The chart couldn't be drawn here.</figcaption>`;
    });
  }
  for (const chip of entry.querySelectorAll(".chip")) chip.addEventListener("click", () => { $("#question").value = chip.dataset.q; $("#question").focus(); });
}

function chartTheme() {
  const css = getComputedStyle(document.documentElement);
  const ink = css.getPropertyValue("--ink").trim(), ink2 = css.getPropertyValue("--ink-2").trim();
  return {
    background: null, font: "Source Sans 3, system-ui, sans-serif",
    title: { color: ink, font: "Fraunces, Georgia, serif", fontSize: 15, subtitleColor: ink2, subtitleFontSize: 11.5, anchor: "start" },
    axis: { labelColor: ink2, titleColor: ink2, labelFontSize: 11.5 },
    legend: { labelColor: ink2, titleColor: ink2 },
  };
}

/* ---- conversation lifecycle ------------------------------------------------------------- */

function resetConversation() {
  const old = ui.sessionId;
  if (old) api("/clear", { session_id: old }).catch(() => {});
  newSessionId();
  ui.entryCount = 0;
  $("#entries").innerHTML = `<div class="empty" id="empty"><p class="empty-title">A fresh page.</p><p>Ask about your run, or pick one of the examples under the question box.</p></div>`;
}

function startOver() {
  resetConversation();
  ui.log = null;
  renderLog();
  fillForm({});
  for (const b of document.querySelectorAll(".ex-bubble")) b.classList.remove("active");
  $("#question").value = "";
}

async function restore() {
  try {
    const [state, hist] = await Promise.all([
      api(`/run_state?session_id=${encodeURIComponent(ui.sessionId)}`),
      api(`/history?session_id=${encodeURIComponent(ui.sessionId)}`),
    ]);
    if (state.run_state) fillForm(state.run_state);
    if (state.randomizer) { ui.log = state.randomizer; renderLog(); }
    const h = hist.history || [];
    if (h.length) $("#empty")?.remove();
    for (let i = 0; i + 1 < h.length; i += 2) {
      const entry = newEntry(h[i].content);
      $(".entry-meta", entry).innerHTML = "<span>earlier in this session</span>";
      $(".entry-body", entry).innerHTML = `<div class="answer">${markdown(h[i + 1].content, [], entry.id)}</div>`;
    }
  } catch { /* a new server: nothing to restore */ }
}

/* ---- banner and about drawer ------------------------------------------------------------------ */

function playBannerVideo() {
  // static/media/banner.mp4, when present, replaces the still banner art (see .hero in style.css)
  const still = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const video = document.createElement("video");
  Object.assign(video, { src: "/static/media/banner.mp4", poster: "/static/media/banner-poster.jpg",
                         muted: true, loop: true, playsInline: true, autoplay: !still, preload: "auto" });
  video.setAttribute("muted", "");
  video.setAttribute("aria-hidden", "true");
  video.className = "hero-video";
  video.addEventListener("loadeddata", () => $("#hero").classList.add("has-video"), { once: true });
  $("img.hero-art").after(video);
}

function setUpAbout() {
  const panel = $("#about"), backdrop = $("#about-backdrop"), opener = $("#about-open");
  const show = (open) => {
    panel.hidden = backdrop.hidden = !open;
    opener.setAttribute("aria-expanded", String(open));
    (open ? $("#about-close") : opener).focus();
  };
  opener.addEventListener("click", () => show(panel.hidden));
  $("#about-close").addEventListener("click", () => show(false));
  backdrop.addEventListener("click", () => show(false));
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !panel.hidden) show(false); });
}

/* ---- start ---------------------------------------------------------------------------------- */

async function init() {
  let stored = null;
  try { stored = localStorage.getItem(SESSION_KEY); } catch { /* storage blocked */ }
  if (stored) { ui.sessionId = stored; $("#session-id").textContent = stored.slice(0, 8); } else newSessionId();

  const [catalogs, examples] = await Promise.all([
    Promise.all(GAMES.map((g) => api(`/catalog?game=${g}`))), api("/examples"),
  ]);
  GAMES.forEach((g, i) => { ui.catalogs[g] = catalogs[i]; });
  ui.examples = examples;
  ui.catalog = ui.catalogs.emerald;
  buildForm();
  renderExamples();
  setUpAbout();
  if (ui.catalog.banner_video) playBannerVideo();
  fillForm({});
  await restore();

  $("#composer").addEventListener("submit", (e) => { e.preventDefault(); ask($("#question").value); });
  $("#question").addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey && !e.isComposing) { e.preventDefault(); ask($("#question").value); }
  });
  $("#clear-chat").addEventListener("click", () => { resetConversation(); ui.log = null; renderLog(); });
}

init().catch((err) => {
  document.body.insertAdjacentHTML("afterbegin", `<p class="error-note" style="padding:12px 24px">LockeSmith couldn't start: ${esc(err.message)}</p>`);
});

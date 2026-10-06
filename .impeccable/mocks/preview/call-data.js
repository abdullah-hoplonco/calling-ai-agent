// Preview data and player shared by the two direction previews.
// Every number is SYNTHETIC. Audio uses the browser's own voices.
(function () {
  const STAGES = [
    { id: "IDENTITY", label: "Identity", mark: "A" },
    { id: "OPENING", label: "Opening", mark: "B" },
    { id: "INFO", label: "Information", mark: "C" },
    { id: "INTENT", label: "Intent", mark: "D" },
    { id: "BOOKING", label: "Booking", mark: "E" },
    { id: "OUTCOME", label: "Outcome", mark: "F" },
  ];

  // parts: [turn end, LLM first token, voice first audio, network + framework] in ms
  const TURNS = [
    { stage: "IDENTITY", lead: "", omar: "Hi, is this Khalifa?", parts: null,
      events: [{ t: "Lead answered", by: "code" }] },
    { stage: "IDENTITY", lead: "Yes, speaking.", tool: true, parts: null,
      omar: "Hi Khalifa, this is Omar from Hoplon and Co. You filled in a form on our website about a mobile app for your laundry shops, so I'm calling with the information you asked for. Just so you know, this call is recorded. Is now a good time for two minutes?",
      events: [{ t: "Identity confirmed", by: "LLM" }] },
    { stage: "OPENING", lead: "Sure, go ahead.", tool: true, parts: [240, 380, 120, 150],
      omar: "Great, thanks. We build iPhone and Android apps end to end, including booking and card payments. What's the main thing your customers struggle with today?",
      events: [{ t: "Agreed to continue", by: "LLM" }] },
    { stage: "INFO", lead: "They phone us to book pickups, and we miss a lot of calls.", cut: true, parts: [280, 210, 110, 150],
      omar: "That's a common one. An app lets them book a pickup slot and pay in a few taps, so nobody waits on the phone.",
      events: [{ t: "Rapport turn 1 of 2", by: "code" }, { t: "Cut off by the Lead", by: "code" }] },
    { stage: "INFO", lead: "Mostly regulars, yes. Families and hotels.", parts: [270, 230, 115, 140],
      omar: "Then repeat bookings and saved cards will matter a lot. It sounds like a solid project. Is this something you'd like to move ahead with soon?",
      events: [{ t: "Rapport turn 2 of 2", by: "code" }] },
    { stage: "INTENT", lead: "Maybe. Roughly how much would it cost?", tool: true, parts: [290, 520, 135, 185],
      omar: "It really depends on what you need, and we can adjust the budget to fit. My manager will go through that with you on a quick 30-minute call. Would earlier or later this week suit you, morning or afternoon?",
      guard: { rule: "No prices on the call", blocked: "A first version usually starts at around AED 40,000." },
      events: [{ t: "Intent to Buy", by: "LLM" }, { t: "Price blocked", by: "code" }, { t: "Qualified Lead", by: "code" }] },
    { stage: "BOOKING", lead: "Later this week, afternoon.", tool: true, parts: [250, 330, 110, 150],
      omar: "I have Wednesday at 3pm or Thursday at 4:30pm. Which suits you better?",
      events: [{ t: "Preference: later, afternoon", by: "LLM" }, { t: "2 slots offered", by: "code" }] },
    { stage: "BOOKING", lead: "Wednesday at three is good.", tool: true, parts: [260, 410, 120, 160],
      omar: "Wednesday at 3pm it is. I'll send the invite to the email on your form, the one at example.com. Is that still best?",
      events: [{ t: "Slot accepted: Wed 3pm", by: "LLM" }] },
    { stage: "OUTCOME", lead: "Yes, that email is fine.", tool: true, parts: null,
      omar: "One moment while I lock that in. You're booked for Wednesday at 3pm with my manager. The invite with the Google Meet link is on its way. Thanks, Khalifa!",
      events: [{ t: "Calendar confirmed", by: "code" }, { t: "Discovery Call booked", by: "code" }] },
  ];

  const est = (s) => (s ? Math.round(s.trim().split(/\s+/).length * 330 + 350) : 0);
  let clock = 0;
  TURNS.forEach((t, i) => {
    t.n = i + 1;
    t.total = t.parts ? t.parts.reduce((a, b) => a + b, 0) : null;
    t.leadMs = t.lead ? est(t.lead) : 1100; // ring + pick-up on turn 1
    t.omarMs = est(t.omar);
    t.gapMs = t.total ?? 450;
    t.leadAt = clock; clock += t.leadMs;
    t.gapAt = clock; clock += t.gapMs;
    t.omarAt = clock; clock += t.cut ? Math.round(t.omarMs * 0.72) : t.omarMs;
    t.endAt = clock; clock += 300;
    t.stageObj = STAGES.find((s) => s.id === t.stage);
  });

  const measured = TURNS.filter((t) => t.total != null).map((t) => t.total).sort((a, b) => a - b);
  const pct = (p) => measured[Math.max(1, Math.ceil((p / 100) * measured.length)) - 1];
  const partP50 = [0, 1, 2, 3].map((k) => {
    const v = TURNS.filter((t) => t.parts).map((t) => t.parts[k]).sort((a, b) => a - b);
    return v[Math.max(1, Math.ceil(0.5 * v.length)) - 1];
  });

  // ---------- audio ----------
  const synth = window.speechSynthesis;
  let V = { omar: null, lead: null };
  function pickVoices() {
    if (!synth) return;
    const en = synth.getVoices().filter((v) => /^en/i.test(v.lang));
    V.omar = en.find((v) => /Daniel|UK English Male|Arthur|Oliver|George|Ryan/i.test(v.name)) || en.find((v) => /GB/i.test(v.lang)) || en[0] || null;
    V.lead = en.find((v) => v !== V.omar && /Rishi|Aaron|Fred|Alex|Tom|Reed|US English|Eddy/i.test(v.name)) || en.find((v) => v !== V.omar && !/GB/i.test(v.lang)) || en.find((v) => v !== V.omar) || V.omar;
  }
  if (synth) { pickVoices(); synth.onvoiceschanged = pickVoices; }

  let token = null;
  const sleep = (ms, tok) => new Promise((r) => { const id = setTimeout(r, ms); tok.timers.push(id); });
  function say(text, who, ms, tok, cutMs, muted) {
    return new Promise((resolve) => {
      let done = false;
      const finish = () => { if (!done) { done = true; resolve(); } };
      if (muted || !synth || !V[who]) { tok.timers.push(setTimeout(finish, cutMs || ms)); return; }
      const u = new SpeechSynthesisUtterance(text);
      u.voice = V[who]; u.lang = V[who].lang; u.rate = who === "omar" ? 1.04 : 1.08; u.pitch = who === "omar" ? 0.95 : 1.05;
      u.onend = finish; u.onerror = finish;
      synth.speak(u);
      tok.timers.push(setTimeout(() => { synth.cancel(); finish(); }, cutMs || ms * 1.8 + 2500));
    });
  }

  async function play(h, opts = {}) {
    stop();
    const tok = { stopped: false, timers: [] };
    token = tok;
    const muted = !!opts.muted;
    for (let i = opts.from || 0; i < TURNS.length; i++) {
      const t = TURNS[i];
      if (tok.stopped) return;
      h.turn && h.turn(t, i);
      h.lead && h.lead(t, i);
      if (t.lead) await say(t.lead, "lead", t.leadMs, tok, null, muted);
      else await sleep(t.leadMs, tok);
      if (tok.stopped) return;
      h.gap && h.gap(t, i);
      await sleep(t.gapMs, tok);
      if (tok.stopped) return;
      h.omar && h.omar(t, i);
      await say(t.omar, "omar", t.omarMs, tok, t.cut ? Math.round(t.omarMs * 0.72) : null, muted);
      if (tok.stopped) return;
      h.done && h.done(t, i);
      await sleep(300, tok);
    }
    if (!tok.stopped) h.end && h.end();
  }
  function stop() {
    if (token) { token.stopped = true; token.timers.forEach(clearTimeout); }
    token = null;
    if (synth) synth.cancel();
  }

  const verdict = (ms) => (ms == null ? null : ms <= 900 ? "good" : ms <= 1500 ? "warn" : "crit");
  const fmt = (ms) => ms.toLocaleString("en-US");

  window.CALL = {
    LEAD: { name: "Khalifa Al Dhaheri", first: "Khalifa", form: "We run a chain of 4 laundry shops in Dubai and want a mobile app where customers book pickups." },
    STAGES, TURNS, P50: pct(50), P95: pct(95), PART_P50: partP50, N: measured.length, LENGTH: clock,
    PARTS: ["Turn end", "LLM first token", "Voice first audio", "Network + framework"],
    play, stop, verdict, fmt, voices: () => V,
  };
})();

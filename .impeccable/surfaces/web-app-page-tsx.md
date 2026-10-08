---
version: 1
slug: "web-app-page-tsx"
primary_target: "web/app/page.tsx"
related_targets: ["web/components/App.tsx","web/components/views/StudioView.tsx","web/components/views/ConsoleView.tsx","web/components/views/EnterpriseView.tsx","web/components/views/ShowcaseView.tsx"]
---

# Surface brief: "Talk to Omar" demo (web/app/page.tsx)

Scope: the whole M1 browser demo page, shipped in four switchable themes (toggle in each theme's chrome; saved per browser; `?ui=studio|console|enterprise|showcase`). Default: Console (changed from Studio by the user on 2026-10-07).
Visitor mode: Operate (Studio, Console, Enterprise); Persuade (Showcase), all running the same live call.
Audience: C-suite on their own MacBooks (impress first, with sound), and engineers who need the measured detail.
Task: pick a Lead, call Omar or hear the spoken sample, and read stage, rules and the wait before every reply.
Content: 3 synthetic Leads; live data from `omar.state` and `omar.latency`; the sample is spoken with browser voices and labelled synthetic.
Constraints: free tiers; no invented numbers; Hoplon logo and name kept, the old house look (navy band, Noto Sans ledger) replaced at the user's request on 2026-10-06.
Decided by the user on 2026-10-06: "Session Timeline" as default with SaaS console as switchable, plus a premium enterprise SaaS theme and a marketing landing-page theme, all in production. The owner said "decide on your own" for the rest.

## Direction contract

THESIS: Hear the call first, then see the wait. Every theme shows the gap between the Lead's last word and Omar's first sound, measured and split into six parts, next to the words. Refuses the old static ledger and the glowing-orb voice-demo cliché.

OWN-WORLD: Studio: dark recording session (Geist / Geist Mono), Lead sky blue, Omar amber, transport LCD, lanes, wait editor. Console (default): the hoplonco.com identity (black, white, electric lime, Epilogue, pill buttons, real wordmark); a black call deck with the recording and stage track, a transcript with a verdict badge per reply, a tabbed side panel. Rebranded at the user's request on 2026-10-07. Enterprise: Hoplon navy band and gold primary action (Manrope), stepper, raised KPI tiles, compliance and pipeline cards. Showcase: navy landing page (Bricolage Grotesque + Figtree), gold CTA, the live call window as the product shot. Six fixed part inks per theme; green/amber/red only for target verdicts.

STORY: The visitor presses one button and hears Omar and the Lead talk; while it plays, each wait draws itself and the totals land against the 0.9 s / 1.5 s targets; the close shows the outcome and the code's state.

FIRST VIEWPORT: Studio: transport (Call, Hear sample, mute, LCD clock, status, p50, p95, theme switch) over the arrangement (Time, Stages, Lead, Omar, Wait, Events lanes) with a centred Lead-picker card when empty; Inspector, Wait editor and Code state panels below.

FORM: user-selected after preview round (Session Timeline was my pick, card 1 of my ordered list; SaaS console was the category standard requested by the user); direction seed key 09e9eeb9.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

---
name: Talk to Omar (Hoplon & Co house world)
description: A working console in the Hoplon house blue on white, where a call reads as a ledger of measured turns.
colors:
  navy: "#0b2e6b"
  navy-2: "#123a80"
  blue: "#1f5fbf"
  sky: "#e8f0fb"
  sky-2: "#d3e2f7"
  tint: "#f5f8fc"
  zebra: "#f6f9fe"
  white: "#ffffff"
  rule: "#d9e1ed"
  rule-soft: "#eaf0f8"
  ink: "#14213d"
  ink-2: "#46526b"
  ink-3: "#5a6577"
  on-navy: "#c9daf5"
  on-navy-2: "#8fa9d6"
  good: "#0e7a3e"
  warn: "#8a5300"
  crit: "#b42318"
  good-bg: "#e6f4ec"
  warn-bg: "#fbf0dc"
  crit-bg: "#fdf1f0"
  seg-end: "#1f5fbf"
  seg-llm: "#0b2e6b"
  seg-tts: "#1baf7a"
  seg-other: "#9fb3cf"
typography:
  title:
    fontFamily: "Noto Sans, system-ui, sans-serif"
    fontSize: "1.25rem"
    fontWeight: 700
    lineHeight: 1.3
    letterSpacing: "0.005em"
  figure:
    fontFamily: "Noto Sans, system-ui, sans-serif"
    fontSize: "1.375rem"
    fontWeight: 600
    lineHeight: 1.25
    fontFeature: "\"tnum\", \"lnum\""
  section:
    fontFamily: "Noto Sans, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 600
    lineHeight: 1.5
  body:
    fontFamily: "Noto Sans, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.5
    fontFeature: "\"tnum\", \"lnum\""
  body-small:
    fontFamily: "Noto Sans, system-ui, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "Noto Sans, system-ui, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 600
    lineHeight: 1.5
  micro:
    fontFamily: "Noto Sans, system-ui, sans-serif"
    fontSize: "0.6875rem"
    fontWeight: 600
    lineHeight: 1.5
rounded:
  hair: "1px"
  bar: "2px"
  chip: "3px"
  pill: "4px"
  box: "6px"
  dot: "50%"
spacing:
  xs: "0.35rem"
  sm: "0.6rem"
  md: "1.25rem"
  lg: "1.5rem"
  xl: "2rem"
  rail: "22rem"
components:
  button-call:
    backgroundColor: "{colors.navy}"
    textColor: "{colors.white}"
    rounded: "{rounded.box}"
    typography: "{typography.body}"
    height: "2.75rem"
  button-call-hover:
    backgroundColor: "{colors.blue}"
  button-link:
    textColor: "{colors.blue}"
    typography: "{typography.body-small}"
    padding: "0.15rem 0"
  lead-option:
    backgroundColor: "{colors.white}"
    textColor: "{colors.ink}"
    rounded: "{rounded.box}"
    padding: "0.7rem 0.8rem"
  lead-option-checked:
    backgroundColor: "{colors.white}"
    textColor: "{colors.ink}"
  step-chip:
    backgroundColor: "{colors.sky}"
    textColor: "{colors.navy}"
    rounded: "{rounded.chip}"
    typography: "{typography.label}"
    padding: "0.05rem 0.45rem"
  stage-flag:
    backgroundColor: "{colors.sky}"
    textColor: "{colors.ink-2}"
    rounded: "{rounded.chip}"
    typography: "{typography.micro}"
    padding: "0 0.35rem"
  target-tag-good:
    backgroundColor: "{colors.good}"
    textColor: "{colors.white}"
    rounded: "{rounded.chip}"
    typography: "{typography.micro}"
    padding: "0 0.4rem"
  target-tag-crit:
    backgroundColor: "{colors.crit}"
    textColor: "{colors.white}"
    rounded: "{rounded.chip}"
    typography: "{typography.micro}"
    padding: "0 0.4rem"
  summary-figure:
    backgroundColor: "{colors.white}"
    textColor: "{colors.navy}"
    typography: "{typography.figure}"
    padding: "0.75rem 1.25rem"
  band:
    backgroundColor: "{colors.navy}"
    textColor: "{colors.white}"
    padding: "1rem 2rem 1.1rem"
  rail:
    backgroundColor: "{colors.tint}"
    textColor: "{colors.ink}"
    padding: "1.5rem 1.5rem 2.5rem"
    width: "{spacing.rail}"
  table-head:
    backgroundColor: "{colors.navy}"
    textColor: "{colors.white}"
    typography: "{typography.label}"
    padding: "0.45rem 0.75rem"
---

# Design System: Talk to Omar (Hoplon & Co house world)

## Overview

**Creative North Star: "The Measured Ledger"**

The Hoplon house world, first set in print for the executive brief and engineer guide, carried onto a working screen. A navy band holds the logo and the call's progress; below it, a cool tint rail holds the controls and the code's state, and a white main column holds the record. Every surface is flat paper divided by hairline rules. Nothing floats, nothing glows, and decoration is close to zero: the only colour that is not blue is there because it measures something.

Density is that of a well-set report, not a dashboard. Body text sits at 14px, secondary text at 13px, and every number uses tabular lining figures so columns of milliseconds align. Hierarchy comes from weight (600 on navy) and from the navy band and navy table heads, not from size jumps; the largest type on the page is the 22px summary figure, because the numbers are the point.

The world rejects the split of chat bubbles on one side and a metrics panel on the other. A conversation turn and its measured delay sit in the same row.

**Key Characteristics:**
- Navy band, tint rail, white work column; one family (Noto Sans) in four weights.
- Hairline rules (1px) instead of shadows to separate everything.
- Tabular numerals globally; values right-aligned in tables and totals.
- Blue family for state; green, amber and red only for pass or fail against a target.
- Four fixed measurement inks for the parts of a delay.

## Colors

A narrow, cool palette of one navy and one blue on white, with three signal colours held in reserve for verdicts.

### Primary
- **Hoplon Navy** (navy): the band, the primary Call button, navy table heads, section headings, stage names, emphasised facts and figure values. It is the voice of the system.
- **Deep Navy** (navy-2): the darker partner to navy, declared for navy surfaces that need a second tone.

### Secondary
- **Signal Blue** (blue): interaction and liveness. Call button hover, link buttons, focus rings, radio and checkbox accent, the checked Lead border, the "Omar" speaker label, the listening pulse and lit microphone bars.

### Tertiary
- **Sky** (sky) and **Sky Deep** (sky-2): quiet fills. Step chips, stage flags, the sample-mode notice strip, the fresh-row flash, text selection, and the hairline under section headings.

### Neutral
- **White** (white): the work column, cards, sticky ledger header.
- **Cool Tint** (tint): the left rail and scrollbar track.
- **Zebra** (zebra): even rows of navy-headed tables (inherited from the print tables).
- **Hairline** (rule): all structural 1px borders: rail edge, cards, summary, ledger header, section dividers.
- **Soft Hairline** (rule-soft): row dividers inside the ledger and tables; the empty delay rail.
- **Ink** (ink), **Ink 2** (ink-2), **Ink 3** (ink-3): primary text, secondary text (Lead's words, Lead message), and tertiary text (labels, hints, captions, units).
- **On-Navy** (on-navy) and **On-Navy Muted** (on-navy-2): text and track lines on the navy band; on-navy-2 also marks idle and completed states (done track dots, idle pulse).

### Signal (verdict only)
- **Pass Green** (good / good-bg), **Near Amber** (warn / warn-bg), **Fail Red** (crit / crit-bg): the p50/p95 tags, the summary verdict, the per-row total, and the over-scale arrow on the delay bar.

### Measurement inks
- **Turn end** (seg-end), **LLM** (seg-llm), **TTS** (seg-tts), **Other** (seg-other): the four segments of a delay bar and their legend keys, always in this order.

### Named Rules
**The Verdict-Only Signal Rule.** Green, amber and red mean pass, near or fail against a stated target (0.9 s typical, 1.5 s slow) and nothing else. Lead status, stage, guard hits, outcome and agent state use the navy/blue family. One exemption, recorded in the surface brief: the control that ends a call (End call, Stop sample, Cancel) and the error box use red, following the destructive-action and error conventions.

**The Fixed Inks Rule.** The four delay inks never change order or hue, and never carry meaning beyond "which part of the wait". The TTS green is a part, not a pass; a pass is shown only in the total and the tags.

## Typography

**Body Font:** Noto Sans (via next/font, with Noto Sans, system-ui, sans-serif fallback)

**Character:** One humanist sans in weights 400 to 700, the same family the print documents use, so the screen and the PDFs read as one house. Global `tabular-nums lining-nums` makes every measurement column align.

### Hierarchy
- **Title** (700, 1.25rem, 1.3): the page title in the band only.
- **Figure** (600, 1.375rem, 1.25): summary readouts (p50, p95, replies measured), in navy.
- **Section** (600, 1rem): headings of main-column sections, with a 1.5px sky-2 underline.
- **Body** (400, 0.875rem, 1.5): conversation text, Lead names (at 600), agent state, button labels at 0.9375rem/600.
- **Body Small** (400, 0.8125rem): rail headings (600, navy), facts lists, hints, Lead messages, table cells, stage names.
- **Label** (400 to 600, 0.75rem): column heads, figure labels, targets, step chips, notes, track sub-labels.
- **Micro** (600 to 700, 0.6875rem): target tags, stage flags, the "cut off" chip, delay-part numbers.

Prose blocks cap at 68 to 72ch (guide list, said lines, section hints).

### Named Rules
**The Weight-Not-Size Rule.** Emphasis is weight 600 in navy at the same size, not a larger size. The scale steps are 11, 12, 13, 14, 15, 16, 20, 22px; nothing exceeds 22px.

**The Tabular Rule.** Every number on screen is tabular and lining; totals and table values right-align.

## Layout

A fixed shell: the navy band spans the top (logo and title on the left, a six-node stage track filling the rest), then a two-column grid of a 22rem tint rail and a fluid main column (`minmax(0, 1fr)`). The main column stacks summary strip, ledger and the stage table with a 2rem gap.

The ledger is a five-column grid shared by its header, rows and pending row: turn number, stage, conversation, delay bar, total (3.5rem / 9.5rem / 1fr / 15rem / 4.5rem, with a 1.25rem column gap). The header sticks to the top on scroll. Rows breathe at 0.9rem vertical padding.

Spacing is rem-based and moderate: 0.35 to 0.6rem inside clusters, 1.25rem between related blocks, 1.5rem rail padding and section gaps, 2rem page-edge padding and main-column gaps.

Responsive behaviour, at 1180px: the band stacks (identity above track) and ledger columns narrow. At 900px: the rail moves above the main column with a bottom rule; the band hides its subtitle and track labels, showing one caption line ("Now: ..." or "Outcome: ...") under the dots; the ledger header hides and each row becomes a three-line card (number, stage and total; conversation; delay bar); the summary figures wrap with the verdict as a full-width footer; part-columns of the stage table hide.

## Elevation & Depth

Flat. Depth comes from three tonal planes (navy band, tint rail, white work column) and 1px hairlines, not from shadows. The few shadows that exist are soft, low and navy-tinted, and each marks a state or a single floating control.

### Shadow Vocabulary
- **Selected lift** (`box-shadow: 0 1px 3px rgb(11 46 107 / 0.1)`): the checked Lead option.
- **Button seat** (`box-shadow: 0 1px 2px rgb(11 46 107 / 0.25)`): the primary Call button.
- **Float** (`box-shadow: 0 6px 18px rgb(11 46 107 / 0.25)`): only the fixed "allow audio" button, which floats over content.
- **Halo ring** (`box-shadow: 0 0 0 4px rgb(255 255 255 / 0.18)` on navy; `0 0 0 3px` sky-2 on white): the current track dot and the speaking pulse.

### Named Rules
**The Hairline Rule.** Separation is a 1px rule (rule or rule-soft); dashed hairlines mark provisional content (the sample row, the pending row).

## Shapes

Small, quiet corners. 6px on boxes the user acts on or reads as a unit (Lead options, buttons, summary strip, outcome box, error box); 3 to 4px on chips, tags and the verdict pill; 1 to 2px on bar segments and legend keys; full circles only for track dots and the agent pulse. The over-scale marker on a delay bar is a small red triangle (clip-path) pointing past the rail's end.

## Components

### Buttons
Solid, compact, unadorned.
- **Shape:** 6px corners, 2.75rem tall, full rail width.
- **Primary (Call):** navy fill, white 15px/600 label, button seat shadow.
- **Hover / Focus / Active:** hover moves the fill to blue over 150ms; active nudges down 1px; focus is the global 2px blue outline at 2px offset.
- **Link button:** blue 13px text with a 35%-opacity underline at 3px offset that goes solid on hover; used for secondary actions such as "Watch a sample call".

### Lead options (radio cards)
- **Style:** white, 1px hairline, 6px corners, 0.7rem 0.8rem padding; native radio in blue accent; name (14px/600), message (13px ink-2, clamped to two lines), note (12px ink-3).
- **States:** hover darkens the border; checked takes a blue border and the selected lift; while a call runs, unchosen options fade to 55%.

### Chips
- **Step chip:** 12px navy on sky, 3px corners. Events reported by code use a transparent fill with an inset sky-2 hairline instead; a muted "by code" or "reported by LLM" suffix follows.
- **Stage flag:** 11px/600 ink-2 on sky ("tool call", "interrupted").
- **Cut chip:** 11px/600 ink-2 with a dashed on-navy-2 border, marking a line the Lead interrupted.

### Summary strip
A single bordered box (hairline, 6px) of figures divided by vertical hairlines: label (12px ink-3), figure value (22px/600 navy) with a pass/fail tag, target line (12px ink-3). A verdict sits at the right end; with a result it becomes a tinted pill in the signal colour.

### Delay bar (signature)
A 10px rail in rule-soft on a fixed 0 to 1.5 s scale, filled left to right by the four inks (turn end, LLM, TTS, other). A 2px ink tick at 55% opacity marks the 0.9 s target; a red triangle appears past the end when the total exceeds 1.5 s. Under it, the part values in milliseconds with 7px keys. When a row lands, each segment draws from scaleX(0) over 260ms, staggered by 90ms.

### Ledger row
Turn number, stage (13px/600 navy), conversation (speaker label in a 3rem column: "Lead" in ink-3, "Omar" in blue; Lead's words in ink-2, Omar's in ink), delay bar, and total (15px/600, right-aligned, coloured by verdict). A new row flashes sky and fades over 1400ms. The sample row is muted with a dashed divider and a blue "Example" marker.

### Stage track (navigation of progress)
Six nodes on the navy band joined by 2px lines. Todo: hollow dot with on-navy-2 ring; done: filled on-navy-2 with a solid line; current: white dot with a white halo and white 600 label. The outcome node turns white when the call ends.

### Agent state
A 10px pulse dot and a navy 600 label. Listening: blue, breathing at 1.6s; thinking: on-navy-2, breathing at 0.6s; speaking: navy with a sky-2 ring. Beside it, a microphone meter of 3px-gapped bars that light blue.

### Data tables
Navy head row with white 12px/600 labels, zebra rows, rule-soft dividers, right-aligned numbers, the first column left-aligned in navy 600; a split body with a hairline top and a bold navy summary row.

## Do's and Don'ts

### Do:
- **Do** keep the three planes: navy band, tint rail, white work column, separated by 1px rule hairlines.
- **Do** use navy for headings, stage names and emphasised facts, and blue for interaction, focus and liveness.
- **Do** reserve good/warn/crit (and their -bg tints) for pass, near or fail against a stated target.
- **Do** draw delay parts in the four fixed inks, in order, on a fixed scale with the target tick.
- **Do** set every number in tabular lining figures and right-align totals and table values.
- **Do** use the house ease (cubic-bezier(0.16, 1, 0.3, 1)) at 150 to 260ms for state changes, and honour reduced motion.

### Don't:
- **Don't** colour status, stage, guard hits, outcome or agent state green, amber or red.
- **Don't** separate surfaces with shadows; the only shadows are the four listed in Elevation & Depth.
- **Don't** set type larger than 22px or add a second family.
- **Don't** split a turn into chat bubbles apart from its measurements; a turn and its delay share one row.

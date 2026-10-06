// The call stages from core/omar_core/state_machine.py, in plain words.

export const STAGE_NAME: Record<string, string> = {
  DIALING: "Dialing",
  IDENTITY: "Identity check",
  OPENING: "Legal opening",
  ARABIC_CHECK: "English check",
  INFO: "Information",
  INTENT: "Intent probe",
  CALLBACK: "Callback time",
  BOOKING_PREF: "Booking: preference",
  BOOKING_OFFER: "Booking: two slots",
  EMAIL_CONFIRM: "Booking: email",
  BOOKING_PENDING: "Booking: calendar",
  ENDED: "Ended",
};

export const TRACK: { id: string; label: string; stages: string[] }[] = [
  { id: "identity", label: "Identity", stages: ["DIALING", "IDENTITY"] },
  { id: "opening", label: "Opening", stages: ["OPENING", "ARABIC_CHECK"] },
  { id: "info", label: "Information", stages: ["INFO"] },
  { id: "intent", label: "Intent", stages: ["INTENT", "CALLBACK"] },
  {
    id: "booking",
    label: "Booking",
    stages: ["BOOKING_PREF", "BOOKING_OFFER", "EMAIL_CONFIRM", "BOOKING_PENDING"],
  },
  { id: "outcome", label: "Outcome", stages: ["ENDED"] },
];

export function trackIndex(stage: string | undefined): number {
  if (!stage) return -1;
  return TRACK.findIndex((t) => t.stages.includes(stage));
}

export function shortStatus(status: string): string {
  if (status.includes("Discovery Call booked")) return "Call booked";
  if (status.includes("booking link")) return "Booking link sent";
  if (status === "Qualified Lead") return "Qualified";
  if (status.startsWith("Opted-out")) return "Opted out";
  if (status.includes("declined recording")) return "Parked, no recording";
  if (status.includes("needs Arabic")) return "Parked, needs Arabic";
  if (status.startsWith("Parked")) return "Parked";
  if (status.includes("callback")) return "Callback booked";
  if (status.includes("retry")) return "Retry scheduled";
  if (status.startsWith("Wrong")) return "Wrong number";
  return status;
}

export const EVENT_WORDS: Record<string, string> = {
  answered: "Lead answered",
  confirm_identity: "Identity confirmed",
  wrong_person: "Wrong person",
  good_time: "Agreed to continue",
  objects_recording: "Declined recording",
  speaks_arabic: "Spoke Arabic",
  english_ok: "English is fine",
  english_no: "Needs Arabic",
  lead_turn: "Rapport turn",
  intent_yes: "Intent to Buy",
  objection: "Objection",
  no_intent: "No intent now",
  ask_manager: "Asked for someone",
  ask_price: "Asked about price",
  ask_timeline: "Asked about timeline",
  ask_bot: "Asked if AI",
  not_now: "Busy now",
  not_interested: "Not interested",
  callback_in_window: "Callback agreed",
  callback_outside: "Callback outside hours",
  give_preference: "Gave a preference",
  slots_found: "Calendar: slots found",
  accept_slot: "Picked a slot",
  neither_slot: "Neither slot",
  email_ok: "Email confirmed",
  new_email: "New email",
  calendar_confirms: "Calendar: confirmed",
  calendar_slot_taken: "Calendar: slot taken",
  calendar_error: "Calendar: error",
  line_drops: "Line dropped",
};

export const RULE_WORDS: Record<string, string> = {
  no_budget: "No budget figures",
  no_timeline: "No durations",
  no_booked_before_calendar: "No 'booked' before the calendar",
  never_deny_ai: "Never deny being an AI",
  say_my_manager: "Say 'my manager'",
};

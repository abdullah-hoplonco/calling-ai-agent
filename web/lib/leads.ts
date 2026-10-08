// Synthetic Leads from .scratch/calling-agent/assets/dummy-leads. No real people.

export type DemoLead = {
  id: string;
  name: string;
  email: string;
  message: string;
  topic: string | null;
  note: string;
  label?: string; // shown in the picker when several Leads share a name
};

export const LEADS: DemoLead[] = [
  {
    id: "omair",
    name: "Omair",
    label: "Omair · catering business",
    email: "omair@example.com",
    message:
      "Hi, I run a small business in Dubai and I'm thinking about a proper website and maybe an app. Can someone call me to talk it through?",
    topic: "a website and maybe an app for your business",
    note: "Open brief. The agent gets to know him first; orders come in on WhatsApp.",
  },
  {
    id: "omair-realestate",
    name: "Omair",
    label: "Omair · real estate brokerage",
    email: "omair.homes@example.com",
    message:
      "Hi, I run a small real estate brokerage in Dubai Marina. Our listings get views but very few serious enquiries. Looking for help with ads and lead generation.",
    topic: "ads and lead generation for your brokerage",
    note: "Marketing brief. A little sceptical after a bad agency; asks what makes Hoplon different.",
  },
  {
    id: "omair-startup",
    name: "Omair",
    label: "Omair · fintech founder",
    email: "omair@savewise.example.com",
    message:
      "Hey, I'm building a savings app and need an MVP for iOS and Android before an investor meeting. Please call me.",
    topic: "an iOS and Android MVP for your savings app",
    note: "Founder in a hurry. Pushes on timeline and price; tests the no-numbers rules.",
  },
  {
    id: "khalifa",
    name: "Khalifa Al Dhaheri",
    email: "khalifa.dhaheri@example.com",
    message:
      "We run a chain of 4 laundry shops in Dubai and want a mobile app where customers can schedule pickup and delivery and pay by card. iOS and Android.",
    topic: "a mobile app for your laundry shops",
    note: "Clear project. Good for the booking path.",
  },
  {
    id: "rhea",
    name: "Rhea Fernandes",
    email: "rhea.f@example.com",
    message: "please call me",
    topic: null,
    note: "No topic. Nimra must find out what she needs.",
  },
  {
    id: "salma",
    name: "Salma Al Hammadi",
    email: "salma.hammadi@example.com",
    message:
      "السلام عليكم، عندي متجر عطور على انستغرام وأبغى حملة إعلانية على تيك توك وسناب شات، وكمان موقع إلكتروني بسيط للطلبات.",
    topic: "a TikTok and Snapchat campaign and a simple ordering website",
    note: "Wrote in Arabic. Tests the English check.",
  },
];

export const OLD_LEAD_MONTH = "March";

// Which LLM speaks on the call. The worker builds it per call (voice/src/omar_voice/agent.py).
export type LlmChoice = "groq" | "deepseek" | "auto";

export const LLM_CHOICES: { id: LlmChoice; label: string; note: string }[] = [
  { id: "auto", label: "Auto", note: "DeepSeek first; Groq takes over when DeepSeek fails." },
  { id: "groq", label: "Groq", note: "Qwen3.8-27B. Fastest, but the free tier runs out after about 2 minutes of talk." },
  { id: "deepseek", label: "DeepSeek", note: "V4.1 Flash, thinking off. No per-minute limit; slower to start." },
];

export function leadMetadata(
  lead: DemoLead,
  old: boolean,
  llm: LlmChoice = "auto",
  voice?: string,
  stability?: number,
  lang: "en" | "hi" = "en",
) {
  return {
    llm,
    lang,
    voice,
    stability,
    lead: {
      name: lead.name,
      email: lead.email,
      message: lead.message,
      topic: lead.topic,
      leadType: old ? "old" : "new",
      submittedMonth: old ? OLD_LEAD_MONTH : null,
    },
  };
}

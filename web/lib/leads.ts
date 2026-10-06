// Synthetic Leads from .scratch/calling-agent/assets/dummy-leads. No real people.

export type DemoLead = {
  id: string;
  name: string;
  email: string;
  message: string;
  topic: string | null;
  note: string;
};

export const LEADS: DemoLead[] = [
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
    note: "No topic. Omar must find out what she needs.",
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

export function leadMetadata(lead: DemoLead, old: boolean) {
  return {
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

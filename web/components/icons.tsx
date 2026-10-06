// One icon family: 24px grid, 1.75 stroke, round caps. Sized by CSS (.ic).

type P = { className?: string };
const S = ({ children, className = "" }: { children: React.ReactNode; className?: string }) => (
  <svg
    className={`ic ${className}`}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.75"
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden="true"
  >
    {children}
  </svg>
);

export const IconPhone = (p: P) => (
  <S {...p}>
    <path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2" />
  </S>
);
export const IconPhoneOff = (p: P) => (
  <S {...p}>
    <path d="M10.7 13.3a11 11 0 0 0 2.8 2.2L15 13l5 2v4a2 2 0 0 1-2 2 16 16 0 0 1-8.6-3.4M6.6 14.9A16 16 0 0 1 3 6a2 2 0 0 1 2-2h4l2 5-2.5 1.5" />
    <path d="M3 21 21 3" />
  </S>
);
export const IconPlay = (p: P) => (
  <S {...p}>
    <path d="M7 4.5v15l12-7.5z" fill="currentColor" stroke="none" />
  </S>
);
export const IconStop = (p: P) => (
  <S {...p}>
    <rect x="6" y="6" width="12" height="12" rx="1.5" fill="currentColor" stroke="none" />
  </S>
);
export const IconSpeaker = (p: P) => (
  <S {...p}>
    <path d="M11 5 6 9H3v6h3l5 4zM15.5 8.5a5 5 0 0 1 0 7M18.5 5.5a9 9 0 0 1 0 13" />
  </S>
);
export const IconMute = (p: P) => (
  <S {...p}>
    <path d="M11 5 6 9H3v6h3l5 4zM22 9l-6 6M16 9l6 6" />
  </S>
);
export const IconCheck = (p: P) => (
  <S {...p}>
    <path d="m5 12.5 4.5 4.5L19 7.5" />
  </S>
);
export const IconShield = (p: P) => (
  <S {...p}>
    <path d="M12 3 20 7v5c0 5-3.5 8-8 9-4.5-1-8-4-8-9V7z" />
    <path d="m9 12 2 2 4-4" />
  </S>
);
export const IconCalendar = (p: P) => (
  <S {...p}>
    <rect x="3.5" y="5" width="17" height="15" rx="2" />
    <path d="M8 3v4M16 3v4M3.5 10h17" />
  </S>
);
export const IconClock = (p: P) => (
  <S {...p}>
    <circle cx="12" cy="12" r="8.5" />
    <path d="M12 7.5V12l3 2" />
  </S>
);
export const IconUser = (p: P) => (
  <S {...p}>
    <circle cx="12" cy="8" r="3.5" />
    <path d="M5 20a7 7 0 0 1 14 0" />
  </S>
);
export const IconBolt = (p: P) => (
  <S {...p}>
    <path d="M13 3 5 13.5h6L10 21l8-10.5h-6z" />
  </S>
);
export const IconWave = (p: P) => (
  <S {...p}>
    <path d="M3 12h2M7 8v8M11 5v14M15 9v6M19 7v10M21 12h0" />
  </S>
);
export const IconChat = (p: P) => (
  <S {...p}>
    <path d="M20 12a8 8 0 0 1-11.6 7.1L4 20l1-4.2A8 8 0 1 1 20 12" />
  </S>
);
export const IconCode = (p: P) => (
  <S {...p}>
    <path d="m8 7-5 5 5 5M16 7l5 5-5 5" />
  </S>
);
export const IconArrow = (p: P) => (
  <S {...p}>
    <path d="M5 12h14M13 6l6 6-6 6" />
  </S>
);
export const IconAlert = (p: P) => (
  <S {...p}>
    <path d="M12 4 2.5 20h19z" />
    <path d="M12 10v4M12 17h0" />
  </S>
);

"use client";

import { RoomAudioRenderer, RoomContext, StartAudio } from "@livekit/components-react";
import { useCallback, useEffect, useState } from "react";

import { LiveBridge } from "@/components/LiveBridge";
import { THEMES, ThemeSwitch, type Ui } from "@/components/shared";
import { ConsoleView } from "@/components/views/ConsoleView";
import { EnterpriseView } from "@/components/views/EnterpriseView";
import { ShowcaseView } from "@/components/views/ShowcaseView";
import { StudioView } from "@/components/views/StudioView";
import { useCall } from "@/lib/useCall";

const KEY = "omar-ui";
const isUi = (v: string | null): v is Ui => THEMES.some((t) => t.id === v);

export function App() {
  const c = useCall();
  const [ui, setUiState] = useState<Ui>("console");

  useEffect(() => {
    const q = new URLSearchParams(window.location.search).get("ui");
    let saved: string | null = null;
    try {
      saved = window.localStorage.getItem(KEY);
    } catch {}
    const next = isUi(q) ? q : isUi(saved) ? saved : null;
    if (next) setUiState(next);
  }, []);

  const setUi = useCallback((u: Ui) => {
    setUiState(u);
    try {
      window.localStorage.setItem(KEY, u);
    } catch {}
    const url = new URL(window.location.href);
    url.searchParams.set("ui", u);
    window.history.replaceState(null, "", url);
  }, []);

  const sw = <ThemeSwitch ui={ui} setUi={setUi} />;

  return (
    <RoomContext.Provider value={c.room}>
      <div className={`ui ui-${ui}`} data-ui={ui}>
        {ui === "studio" && <StudioView c={c} switcher={sw} />}
        {ui === "console" && <ConsoleView c={c} switcher={sw} />}
        {ui === "enterprise" && <EnterpriseView c={c} switcher={sw} />}
        {ui === "showcase" && <ShowcaseView c={c} switcher={sw} />}
      </div>
      {c.source === "live" && <LiveBridge c={c} />}
      <RoomAudioRenderer />
      <StartAudio label="Allow audio to hear Nimra" className="start-audio" />
    </RoomContext.Provider>
  );
}

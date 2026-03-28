"use client";
import { useEffect, useState } from "react";
import type { SessionState } from "@/lib/types";

const INITIAL: SessionState = {
  bot_status: "waiting",
  transcript: [],
  summary: "",
  word_count: 0,
  start_time: null,
};

export function useMeetingSocket() {
  const [session, setSession] = useState<SessionState>(INITIAL);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const wsUrl = process.env.NEXT_PUBLIC_BACKEND_WS_URL ?? "ws://localhost:8001/ws";
    const ws = new WebSocket(wsUrl);

    ws.onopen  = () => setConnected(true);
    ws.onclose = () => setConnected(false);

    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data);
      if (msg.type === "init") {
        setSession(msg.data);
      } else if (msg.type === "transcript") {
        setSession((prev) => ({
          ...prev,
          transcript: [...prev.transcript, msg.entry],
          word_count: msg.word_count,
          bot_status: "inmeeting",
        }));
      } else if (msg.type === "summary") {
        setSession((prev) => ({ ...prev, summary: msg.summary }));
      }
    };

    return () => ws.close();
  }, []);

  return { session, connected };
}
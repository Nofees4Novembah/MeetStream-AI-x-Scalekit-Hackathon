"use client";
import { useEffect, useRef, useState } from "react";
import type { SessionState } from "@/lib/types";

const INITIAL: SessionState = {
  bot_status: "waiting",
  transcript: [],
  summary: "",
  word_count: 0,
  start_time: null,
};

export function useMeetingSocket() {
  const [session,     setSession]     = useState<SessionState>(INITIAL);
  const [connected,   setConnected]   = useState(false);
  const [emailSentWs, setEmailSentWs] = useState<{to: string; at: string} | null>(null);

  const wsRef      = useRef<WebSocket | null>(null);
  const retryDelay = useRef(1000);
  const unmounted  = useRef(false);
  const timerRef   = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    unmounted.current = false;
    const wsUrl = process.env.NEXT_PUBLIC_BACKEND_WS_URL ?? "ws://localhost:3000/ws";

    function connect() {
      if (unmounted.current) return;

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        retryDelay.current = 1000;
      };

      ws.onclose = () => {
        setConnected(false);
        if (!unmounted.current) {
          timerRef.current = setTimeout(connect, retryDelay.current);
          retryDelay.current = Math.min(retryDelay.current * 2, 10000);
        }
      };

      ws.onmessage = (e) => {
        const msg = JSON.parse(e.data);
        if (msg.type === "init") {
          setSession(msg.data);
          if (msg.data.email_sent) setEmailSentWs(msg.data.email_sent);
        } else if (msg.type === "transcript") {
          setSession((prev) => ({
            ...prev,
            transcript: [...prev.transcript, msg.entry],
            word_count: msg.word_count,
            bot_status: "inmeeting",
          }));
        } else if (msg.type === "summary") {
          setSession((prev) => ({ ...prev, summary: msg.summary }));
        } else if (msg.type === "bot_status") {
          setSession((prev) => ({ ...prev, bot_status: msg.status }));
        } else if (msg.type === "email_sent") {
          setEmailSentWs(msg.email_sent);
        }
      };
    }

    connect();

    return () => {
      unmounted.current = true;
      if (timerRef.current) clearTimeout(timerRef.current);
      wsRef.current?.close();
    };
  }, []);

  return { session, connected, emailSentWs };
}

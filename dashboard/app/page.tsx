"use client";
import { useState, useRef, useEffect } from "react";
import { useMeetingSocket } from "@/hooks/useMeetingSocket";
import type { TranscriptEntry } from "@/lib/types";

const API = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8001";

function ConfidenceBar({ c }: { c: number }) {
  const pct  = Math.round(c * 100);
  const color = c >= 0.85 ? "bg-green-500" : c >= 0.70 ? "bg-amber-400" : "bg-red-400";
  return (
    <div className="flex items-center gap-2 mt-2">
      <div className="h-1.5 w-20 rounded-full bg-gray-100">
        <div className={`h-1.5 rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-gray-400">{pct}%</span>
    </div>
  );
}

function TranscriptRow({ entry }: { entry: TranscriptEntry }) {
  const initials = entry.speaker.split(" ").map((w) => w[0]).join("").slice(0, 2).toUpperCase();
  const time     = new Date(entry.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  return (
    <div className={`rounded-xl border p-3 space-y-1.5 text-sm transition-colors
      ${entry.flag_for_review ? "border-red-200 bg-red-50" : "border-gray-100 bg-white"}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-full bg-violet-100 text-violet-800 text-xs font-medium
            flex items-center justify-center">{initials}</div>
          <span className="font-medium text-gray-900">{entry.speaker}</span>
          {entry.flag_for_review && (
            <span className="text-xs bg-red-100 text-red-600 px-2 py-0.5 rounded-full">
              Review needed
            </span>
          )}
        </div>
        <span className="text-xs text-gray-400">{time}</span>
      </div>
      <p className="text-gray-700 leading-relaxed pl-9">{entry.text}</p>
      <div className="pl-9"><ConfidenceBar c={entry.confidence} /></div>
    </div>
  );
}

export default function Dashboard() {
  const { session, connected } = useMeetingSocket();
  const [summary,       setSummary]       = useState("");
  const [brief,         setBrief]         = useState("");
  const [lateJoiner,    setLateJoiner]    = useState("");
  const [loadingSummary, setLoadingSummary] = useState(false);
  const [loadingBrief,   setLoadingBrief]   = useState(false);
  const feedRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (feedRef.current) feedRef.current.scrollTop = feedRef.current.scrollHeight;
  }, [session.transcript]);

  useEffect(() => {
    if (session.summary) setSummary(session.summary);
  }, [session.summary]);

  async function getSummary() {
    setLoadingSummary(true);
    const res  = await fetch(`${API}/api/summarize`, { method: "POST" });
    const data = await res.json();
    setSummary(data.summary);
    setLoadingSummary(false);
  }

  async function getBrief() {
    setLoadingBrief(true);
    const res  = await fetch(`${API}/api/late-joiner-brief`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: lateJoiner || "New participant" }),
    });
    const data = await res.json();
    setBrief(data.brief);
    setLoadingBrief(false);
  }

  const flaggedCount = session.transcript.filter((e) => e.flag_for_review).length;

  const statusStyle: Record<string, string> = {
    waiting:   "bg-gray-100 text-gray-500",
    joining:   "bg-amber-100 text-amber-700",
    inmeeting: "bg-green-100 text-green-700",
    stopped:   "bg-red-100 text-red-600",
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto space-y-5">

        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold text-gray-900">Meeting Dashboard</h1>
            <p className="text-sm text-gray-400 mt-0.5">Live transcript · summaries · late joiner briefs</p>
          </div>
          <div className="flex items-center gap-2">
            <span className={`text-xs px-2.5 py-1 rounded-full font-medium
              ${statusStyle[session.bot_status] ?? statusStyle.waiting}`}>
              {session.bot_status}
            </span>
            <span className={`text-xs px-2.5 py-1 rounded-full
              ${connected ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-400"}`}>
              {connected ? "connected" : "disconnected"}
            </span>
          </div>
        </div>

        {/* Metrics */}
        <div className="grid grid-cols-3 gap-4">
          {[
            { label: "Words spoken",        value: session.word_count.toLocaleString() },
            { label: "Transcript segments", value: session.transcript.length },
            { label: "Flagged for review",  value: flaggedCount },
          ].map((m) => (
            <div key={m.label} className="bg-white rounded-2xl border border-gray-100 p-4">
              <p className="text-2xl font-semibold text-gray-900">{m.value}</p>
              <p className="text-sm text-gray-400 mt-1">{m.label}</p>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-3 gap-4 items-start">

          {/* Transcript feed */}
          <div className="col-span-2 bg-white rounded-2xl border border-gray-100 p-5">
            <div className="flex items-center justify-between mb-3">
              <p className="text-sm font-medium text-gray-700">Live transcript</p>
              {session.bot_status === "inmeeting" && (
                <span className="flex items-center gap-1.5 text-xs text-red-500">
                  <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" /> Live
                </span>
              )}
            </div>
            <div ref={feedRef} className="space-y-2 overflow-y-auto max-h-[480px]">
              {session.transcript.length === 0 ? (
                <p className="text-sm text-gray-400 py-12 text-center">
                  Waiting for the bot to join the meeting...
                </p>
              ) : (
                session.transcript.map((entry, i) => (
                  <TranscriptRow key={i} entry={entry} />
                ))
              )}
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-4">

            {/* Summary */}
            <div className="bg-white rounded-2xl border border-gray-100 p-4 space-y-3">
              <p className="text-sm font-medium text-gray-700">Summary</p>
              {summary
                ? <p className="text-sm text-gray-600 leading-relaxed whitespace-pre-wrap">{summary}</p>
                : <p className="text-sm text-gray-400">No summary yet</p>
              }
              <button onClick={getSummary} disabled={loadingSummary}
                className="w-full text-xs border border-gray-200 rounded-lg px-3 py-2
                  hover:bg-gray-50 disabled:opacity-40 transition-colors">
                {loadingSummary ? "Generating..." : "Generate summary"}
              </button>
            </div>

            {/* Late joiner */}
            <div className="bg-white rounded-2xl border border-gray-100 p-4 space-y-3">
              <p className="text-sm font-medium text-gray-700">Late joiner brief</p>
              <input
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm
                  outline-none focus:ring-2 focus:ring-violet-300"
                placeholder="Participant name"
                value={lateJoiner}
                onChange={(e) => setLateJoiner(e.target.value)}
              />
              {brief && (
                <div className="bg-violet-50 rounded-lg p-3 text-sm text-gray-700 leading-relaxed">
                  {brief}
                </div>
              )}
              <button onClick={getBrief} disabled={loadingBrief}
                className="w-full text-xs border border-gray-200 rounded-lg px-3 py-2
                  hover:bg-gray-50 disabled:opacity-40 transition-colors">
                {loadingBrief ? "Generating..." : "Generate brief"}
              </button>
            </div>

            {/* Flagged */}
            {flaggedCount > 0 && (
              <div className="bg-white rounded-2xl border border-red-100 p-4 space-y-2">
                <p className="text-sm font-medium text-gray-700">
                  Flagged for review
                  <span className="ml-2 bg-red-100 text-red-600 text-xs px-2 py-0.5 rounded-full">
                    {flaggedCount}
                  </span>
                </p>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {session.transcript
                    .filter((e) => e.flag_for_review)
                    .map((e, i) => (
                      <div key={i} className="text-xs text-gray-600 bg-red-50 rounded-lg p-2.5 leading-relaxed">
                        <span className="font-medium">{e.speaker}:</span> {e.text}
                        <div className="text-red-400 mt-1">{Math.round(e.confidence * 100)}% confidence</div>
                      </div>
                    ))}
                </div>
              </div>
            )}

          </div>
        </div>
      </div>
    </div>
  );
}
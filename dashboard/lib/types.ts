export type TranscriptEntry = {
  speaker: string;
  timestamp: string;
  text: string;
  confidence: number;
  flag_for_review: boolean;
};

export type SessionState = {
  bot_status: string;
  transcript: TranscriptEntry[];
  summary: string;
  word_count: number;
  start_time: string | null;
};
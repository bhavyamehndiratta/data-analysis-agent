// Shapes of the data exchanged with the FastAPI backend.

/** Returned by POST /api/upload after a dataset is ingested. */
export interface SessionInfo {
  session_id: string;
  filename: string;
  rows: number;
  columns: number;
  column_names: string[];
  /** Column name -> count of missing values in that column. */
  missing_values: Record<string, number>;
  duplicate_rows: number;
}

/** A follow-up question the agent investigated on its own. */
export interface DrillDownItem {
  question: string;
  answer: string;
}

export type MessageRole = 'user' | 'assistant';

/** One entry in the chat transcript. */
export interface ChatMessage {
  id?: number;
  role: MessageRole;
  content: string;
  streaming?: boolean;
  code_executed?: string[];
  drill_down?: DrillDownItem[];
  iterations?: number;
}

/** One server-sent event emitted by POST /api/stream. */
export interface StreamEvent {
  type: string;
  content?: string;
}

/** Error body FastAPI returns on a failed request. */
export interface ApiErrorBody {
  detail?: string;
}

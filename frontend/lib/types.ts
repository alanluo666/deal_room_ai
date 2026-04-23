export interface User {
  id: number;
  email: string;
  created_at: string;
}

export interface DealRoom {
  id: number;
  owner_id: number;
  name: string;
  target_company: string | null;
  created_at: string;
}

export interface DealRoomCreateInput {
  name: string;
  target_company?: string | null;
}

export interface AuthCredentials {
  email: string;
  password: string;
}

export type DocumentStatus =
  | "pending"
  | "processing"
  | "ready"
  | "failed";

export interface DealRoomDocument {
  id: number;
  deal_room_id: number;
  filename: string;
  mime_type: string;
  size_bytes: number;
  status: DocumentStatus;
  error_message: string | null;
  chunk_count: number;
  created_at: string;
}

export interface Citation {
  document_id: number;
  filename: string;
  chunk_index: number;
  snippet: string;
}

export interface AskRequestInput {
  question: string;
  top_k?: number;
}

export interface AskResponse {
  question_id: number;
  answer: string;
  citations: Citation[];
  model: string;
  chunks_used: number;
}

export type AnalyzeTask = "summary" | "risks";

export interface AnalyzeRequestInput {
  task: AnalyzeTask;
  top_k?: number;
}

export interface AnalyzeResponse {
  task: AnalyzeTask;
  answer: string;
  citations: Citation[];
  model: string;
  chunks_used: number;
}

export interface QuestionRead {
  id: number;
  deal_room_id: number;
  user_id: number;
  question: string;
  answer: string;
  citations: Citation[];
  created_at: string;
}

// ---------------------------------------------------------------------------
// Chat (Person C slice)
//
// Mirrors the Pydantic ChatRequest/ChatResponse in api/schemas.py. Shapes are
// forward-compatible with Person A's ADK agent (message history, optional
// session_id, reserved steps[] for agent traces) without taking any ADK
// dependency now.
// ---------------------------------------------------------------------------

export type ChatRole = "user" | "assistant" | "system";

export interface ChatMessage {
  role: ChatRole;
  content: string;
}

export interface ChatRequest {
  messages: ChatMessage[];
  top_k?: number;
  session_id?: string | null;
}

export interface ChatStep {
  name: string;
  detail?: string | null;
}

export interface ChatResponse {
  message: ChatMessage;
  citations: Citation[];
  model: string;
  chunks_used: number;
  session_id: string | null;
  steps: ChatStep[];
}

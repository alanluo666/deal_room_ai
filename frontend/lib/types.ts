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

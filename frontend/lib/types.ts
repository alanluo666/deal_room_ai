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

export interface User {
  id: number;
  email: string;
  username: string;
  role: 'user' | 'admin';
  is_active: boolean;
  created_at: string;
}

export interface Wish {
  id: number;
  title: string;
  link: string | null;
  price_estimate: string | null;
  notes: string | null;
  owner_id: number;
  created_at: string;
  updated_at: string;
}

export interface WishCreate {
  title: string;
  link?: string;
  price_estimate?: number;
  notes?: string;
}

export interface WishUpdate {
  title?: string;
  link?: string;
  price_estimate?: number;
  notes?: string;
}

export interface WishListResponse {
  items: Wish[];
  total: number;
  limit: number;
  offset: number;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterData {
  email: string;
  username: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export interface ApiError {
  code: string;
  message: string;
  details: Record<string, unknown>;
}

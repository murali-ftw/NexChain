/**
 * Mirrors backend-api's LoginRequest/LoginResponse/UserSummary
 * (com.nexchain.backend.auth.dto) field-for-field — see docs/api_contracts.md
 * POST /api/auth/login.
 */

export interface LoginRequest {
  email: string;
  password: string;
}

export interface AuthUser {
  id: number;
  username: string;
  email: string;
  role: string;
}

export interface LoginResponse {
  accessToken: string;
  refreshToken: string | null;
  tokenType: string;
  expiresIn: number;
  user: AuthUser;
}

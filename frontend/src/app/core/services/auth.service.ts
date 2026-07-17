import { Injectable, signal } from '@angular/core';
import { Router } from '@angular/router';
import { Observable } from 'rxjs';
import { map, tap } from 'rxjs/operators';
import { LoginApiService } from '../../features/auth/services/login-api.service';
import { AuthUser } from '../models/auth.model';

const TOKEN_KEY = 'nexchain.auth.token';
const USER_KEY = 'nexchain.auth.user';

/**
 * Day 6 (P1.6): authentication state — JWT storage, current user, and session
 * restoration on page refresh. `LoginApiService` owns the HTTP call; this owns
 * what happens with the result. No JWT expiry parsing on the client: an
 * expired/invalid token is caught the same way as any other bad token, by the
 * backend returning 401 (see the interceptor's 401 handling).
 */
@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly token = signal<string | null>(localStorage.getItem(TOKEN_KEY));
  readonly currentUser = signal<AuthUser | null>(this.readStoredUser());

  constructor(
    private readonly loginApiService: LoginApiService,
    private readonly router: Router,
  ) {}

  isAuthenticated(): boolean {
    return this.token() !== null;
  }

  getToken(): string | null {
    return this.token();
  }

  login(email: string, password: string): Observable<AuthUser> {
    return this.loginApiService.login({ email, password }).pipe(
      tap((response) => {
        localStorage.setItem(TOKEN_KEY, response.accessToken);
        localStorage.setItem(USER_KEY, JSON.stringify(response.user));
        this.token.set(response.accessToken);
        this.currentUser.set(response.user);
      }),
      map((response) => response.user),
    );
  }

  logout(): void {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    this.token.set(null);
    this.currentUser.set(null);
    this.router.navigate(['/login']);
  }

  private readStoredUser(): AuthUser | null {
    const raw = localStorage.getItem(USER_KEY);
    if (!raw) {
      return null;
    }
    try {
      return JSON.parse(raw) as AuthUser;
    } catch {
      return null;
    }
  }
}

import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { environment } from '../../../../environments/environment';
import { LoginRequest, LoginResponse } from '../../../core/models/auth.model';

/**
 * Day 6 (P1.6): the real Angular -> Spring Boot transport for login — see
 * docs/api_contracts.md for the POST /api/auth/login contract. Pure HTTP
 * boundary; session state (token storage, current user) lives in AuthService.
 */
@Injectable({ providedIn: 'root' })
export class LoginApiService {
  constructor(private readonly http: HttpClient) {}

  login(request: LoginRequest): Observable<LoginResponse> {
    return this.http
      .post<LoginResponse>(`${environment.apiBaseUrl}/api/auth/login`, request)
      .pipe(catchError((err: HttpErrorResponse) => throwError(() => new Error(this.toFriendlyMessage(err)))));
  }

  private toFriendlyMessage(err: HttpErrorResponse): string {
    const backendMessage = err.error?.message;
    return typeof backendMessage === 'string' && backendMessage.length > 0
      ? backendMessage
      : 'Unable to sign in. Please try again.';
  }
}

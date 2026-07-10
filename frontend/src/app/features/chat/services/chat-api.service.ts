import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { environment } from '../../../../environments/environment';
import { ChatResponse } from '../models/chat.model';

/**
 * Day 4 (P1.4): the real Angular -> Spring Boot transport for chat. Replaces the
 * Day 3 frontend-only ChatMockService as the primary success path — see
 * docs/api_contracts.md for the current POST /api/chat contract and mock status.
 */
@Injectable({ providedIn: 'root' })
export class ChatApiService {
  constructor(private readonly http: HttpClient) {}

  sendMessage(query: string, sessionId: string): Observable<ChatResponse> {
    return this.http
      .post<ChatResponse>(`${environment.apiBaseUrl}/api/chat`, { query, sessionId })
      .pipe(catchError((err: HttpErrorResponse) => throwError(() => new Error(this.toFriendlyMessage(err)))));
  }

  /** Backend validation errors carry a real message (ErrorResponse.message); anything
   * else (network down, 5xx) falls back to a generic, user-safe message. */
  private toFriendlyMessage(err: HttpErrorResponse): string {
    const backendMessage = err.error?.message;
    return typeof backendMessage === 'string' && backendMessage.length > 0
      ? backendMessage
      : 'Unable to retrieve the response. Please try again.';
  }
}

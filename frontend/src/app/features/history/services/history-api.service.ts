import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { environment } from '../../../../environments/environment';
import { HistoryItem } from '../models/history.model';

/**
 * Day 5 (P1.5): the real Angular -> Spring Boot transport for query history — see
 * docs/api_contracts.md for the current GET /api/chat/history contract and mock status.
 */
@Injectable({ providedIn: 'root' })
export class HistoryApiService {
  constructor(private readonly http: HttpClient) {}

  getHistory(): Observable<HistoryItem[]> {
    return this.http
      .get<HistoryItem[]>(`${environment.apiBaseUrl}/api/chat/history`)
      .pipe(catchError((err: HttpErrorResponse) => throwError(() => new Error(this.toFriendlyMessage(err)))));
  }

  private toFriendlyMessage(err: HttpErrorResponse): string {
    const backendMessage = err.error?.message;
    return typeof backendMessage === 'string' && backendMessage.length > 0
      ? backendMessage
      : 'Unable to load query history. Please try again.';
  }
}

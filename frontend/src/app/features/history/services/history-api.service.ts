import { HttpClient, HttpErrorResponse, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, throwError } from 'rxjs';
import { catchError, map } from 'rxjs/operators';
import { environment } from '../../../../environments/environment';
import { HistoryDetail, HistoryItem } from '../models/history.model';

/** One page of conversations, plus the total count across all of the user's history —
 * the backend reports the total via the `X-Total-Count` header, not the body, so the
 * body shape stays a plain array either way (see docs/api_contracts.md). */
export interface HistoryPage {
  items: HistoryItem[];
  totalCount: number;
}

/**
 * Day 7 (P1.7): the real Angular -> Spring Boot transport for query history — list,
 * restore-detail, and delete. See docs/api_contracts.md for the GET /api/chat/history
 * contract; the /{id} and DELETE routes are this day's addition, nested under the same
 * frozen /api/chat/history path.
 */
@Injectable({ providedIn: 'root' })
export class HistoryApiService {
  constructor(private readonly http: HttpClient) {}

  /** Every conversation, unbounded — used by the History page's search, which needs the
   * full set to filter over. */
  getHistory(): Observable<HistoryItem[]> {
    return this.http
      .get<HistoryItem[]>(`${environment.apiBaseUrl}/api/chat/history`)
      .pipe(catchError((err: HttpErrorResponse) => throwError(() => new Error(this.toFriendlyMessage(err)))));
  }

  /** One page of conversations (P1.7 rectification) — for callers with enough history
   * that loading everything up front stops being practical. */
  getHistoryPage(page: number, size: number): Observable<HistoryPage> {
    const params = new HttpParams().set('page', page).set('size', size);
    return this.http
      .get<HistoryItem[]>(`${environment.apiBaseUrl}/api/chat/history`, { params, observe: 'response' })
      .pipe(
        map((response) => ({
          items: response.body ?? [],
          totalCount: Number(response.headers.get('X-Total-Count') ?? response.body?.length ?? 0),
        })),
        catchError((err: HttpErrorResponse) => throwError(() => new Error(this.toFriendlyMessage(err)))),
      );
  }

  /** Fetches every turn of one conversation, for restoring it into the chat page. */
  getHistoryDetail(id: string): Observable<HistoryDetail> {
    return this.http
      .get<HistoryDetail>(`${environment.apiBaseUrl}/api/chat/history/${encodeURIComponent(id)}`)
      .pipe(catchError((err: HttpErrorResponse) => throwError(() => new Error(this.toFriendlyMessage(err)))));
  }

  deleteHistory(id: string): Observable<void> {
    return this.http
      .delete<void>(`${environment.apiBaseUrl}/api/chat/history/${encodeURIComponent(id)}`)
      .pipe(catchError((err: HttpErrorResponse) => throwError(() => new Error(this.toFriendlyMessage(err)))));
  }

  private toFriendlyMessage(err: HttpErrorResponse): string {
    const backendMessage = err.error?.message;
    if (typeof backendMessage === 'string' && backendMessage.length > 0) {
      return backendMessage;
    }
    return err.status === 404
      ? 'That conversation could not be found.'
      : 'Unable to load query history. Please try again.';
  }
}

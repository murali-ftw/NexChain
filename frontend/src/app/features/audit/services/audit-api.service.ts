import { HttpClient, HttpErrorResponse, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, throwError } from 'rxjs';
import { catchError, map } from 'rxjs/operators';
import { environment } from '../../../../environments/environment';
import { AuditEntry } from '../models/audit.model';

/** One page of audit entries, plus the total count across the whole log — the backend
 * reports the total via the `X-Total-Count` header, not the body, so the body shape
 * stays a plain array either way (see docs/api_contracts.md). */
export interface AuditPage {
  items: AuditEntry[];
  totalCount: number;
}

/**
 * Day 8 (P1.8): the real Angular -> Spring Boot transport for the audit log — list and
 * per-entry detail. See docs/api_contracts.md for the GET /api/audit contract; the /{id}
 * route is this day's addition, nested under the same frozen /api/audit path.
 */
@Injectable({ providedIn: 'root' })
export class AuditApiService {
  constructor(private readonly http: HttpClient) {}

  /** Every audit entry, unbounded — used by the Audit page's search/filters, which need
   * the full set to filter over. */
  getAuditLog(): Observable<AuditEntry[]> {
    return this.http
      .get<AuditEntry[]>(`${environment.apiBaseUrl}/api/audit`)
      .pipe(catchError((err: HttpErrorResponse) => throwError(() => new Error(this.toFriendlyMessage(err)))));
  }

  /** One page of the audit log — for callers with enough history that loading
   * everything up front stops being practical. */
  getAuditLogPage(page: number, size: number): Observable<AuditPage> {
    const params = new HttpParams().set('page', page).set('size', size);
    return this.http
      .get<AuditEntry[]>(`${environment.apiBaseUrl}/api/audit`, { params, observe: 'response' })
      .pipe(
        map((response) => ({
          items: response.body ?? [],
          totalCount: Number(response.headers.get('X-Total-Count') ?? response.body?.length ?? 0),
        })),
        catchError((err: HttpErrorResponse) => throwError(() => new Error(this.toFriendlyMessage(err)))),
      );
  }

  /** Fetches one entry in full — backs the audit page's detail drawer. */
  getAuditEntry(auditId: number): Observable<AuditEntry> {
    return this.http
      .get<AuditEntry>(`${environment.apiBaseUrl}/api/audit/${auditId}`)
      .pipe(catchError((err: HttpErrorResponse) => throwError(() => new Error(this.toFriendlyMessage(err)))));
  }

  private toFriendlyMessage(err: HttpErrorResponse): string {
    const backendMessage = err.error?.message;
    if (typeof backendMessage === 'string' && backendMessage.length > 0) {
      return backendMessage;
    }
    return err.status === 404
      ? 'That audit entry could not be found.'
      : 'Unable to load the audit log. Please try again.';
  }
}

import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { environment } from '../../../../environments/environment';
import { AuditEntry } from '../models/audit.model';

/**
 * Day 5 (P1.5): the real Angular -> Spring Boot transport for the audit log — see
 * docs/api_contracts.md for the current GET /api/audit contract and mock status.
 */
@Injectable({ providedIn: 'root' })
export class AuditApiService {
  constructor(private readonly http: HttpClient) {}

  getAuditLog(): Observable<AuditEntry[]> {
    return this.http
      .get<AuditEntry[]>(`${environment.apiBaseUrl}/api/audit`)
      .pipe(catchError((err: HttpErrorResponse) => throwError(() => new Error(this.toFriendlyMessage(err)))));
  }

  private toFriendlyMessage(err: HttpErrorResponse): string {
    const backendMessage = err.error?.message;
    return typeof backendMessage === 'string' && backendMessage.length > 0
      ? backendMessage
      : 'Unable to load the audit log. Please try again.';
  }
}

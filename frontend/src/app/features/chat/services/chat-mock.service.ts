import { Injectable } from '@angular/core';
import { Observable, throwError, timer } from 'rxjs';
import { map, switchMap } from 'rxjs/operators';
import {
  DEGRADED_RESPONSE,
  FLAGSHIP_RESPONSE,
  INVENTORY_RESPONSE,
  REPORTING_RESPONSE,
  SLA_POLICY_RESPONSE,
  genericResponse,
} from '../data/chat-fixtures';
import { ChatResponse } from '../models/chat.model';

const MOCK_DELAY_MS = 900;

/**
 * Day 3 stub: resolves a typed query to a fixture response purely by keyword match.
 * No real intent classification — that is Person 3's work (P3.7, LangGraph Supervisor).
 *
 * Manual test triggers (not shown in the UI, for exercising error/degraded states):
 * a query containing "simulate error" rejects; a query containing "simulate degraded"
 * returns the partial/warned fixture.
 */
@Injectable({ providedIn: 'root' })
export class ChatMockService {
  getResponse(query: string, sessionId: string): Observable<ChatResponse> {
    const normalized = query.toLowerCase();

    if (normalized.includes('simulate error')) {
      return timer(MOCK_DELAY_MS).pipe(
        switchMap(() => throwError(() => new Error('Unable to retrieve the response. Please try again.'))),
      );
    }

    const fixture = this.resolveFixture(normalized, query);
    return timer(MOCK_DELAY_MS).pipe(
      map(() => ({
        ...fixture,
        traceId: crypto.randomUUID(),
        sessionId,
        timestamp: new Date().toISOString(),
      })),
    );
  }

  /** Context-specific loading text, shown while getResponse()'s delay is in flight. */
  getLoadingMessage(query: string): string {
    const normalized = query.toLowerCase();
    if (normalized.includes('simulate error') || normalized.includes('simulate degraded')) {
      return 'Checking shipment status...';
    }
    if (normalized.includes('45892')) {
      return 'Checking order and shipment status...';
    }
    if (normalized.includes('sku') || normalized.includes('stock')) {
      return 'Checking inventory...';
    }
    if (normalized.includes('sla') || normalized.includes('escalation')) {
      return 'Searching knowledge base...';
    }
    if (normalized.includes('warehouse') || normalized.includes('report')) {
      return 'Running report query...';
    }
    return 'Thinking...';
  }

  private resolveFixture(normalized: string, originalQuery: string) {
    if (normalized.includes('simulate degraded')) {
      return DEGRADED_RESPONSE;
    }
    if (normalized.includes('45892')) {
      return FLAGSHIP_RESPONSE;
    }
    if (normalized.includes('sku') || normalized.includes('stock')) {
      return INVENTORY_RESPONSE;
    }
    if (normalized.includes('sla') || normalized.includes('escalation')) {
      return SLA_POLICY_RESPONSE;
    }
    if (normalized.includes('warehouse') || normalized.includes('report')) {
      return REPORTING_RESPONSE;
    }
    return genericResponse(originalQuery);
  }
}

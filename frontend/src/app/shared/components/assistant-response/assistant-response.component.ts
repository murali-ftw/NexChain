import { Component, Input, computed, signal } from '@angular/core';
import { ChatResponse } from '../../../features/chat/models/chat.model';

type SourceBadge = 'DB' | 'API' | 'KB';

@Component({
  selector: 'app-assistant-response',
  standalone: true,
  imports: [],
  templateUrl: './assistant-response.component.html',
  styleUrl: './assistant-response.component.scss',
})
export class AssistantResponseComponent {
  private readonly _response = signal<ChatResponse | null>(null);

  @Input({ required: true })
  set response(value: ChatResponse) {
    this._response.set(value);
  }
  get response(): ChatResponse {
    return this._response()!;
  }

  /** Current-status line composed from structured fields — there is no separate
   * "current status" string in the agreed schema (see docs/api_contracts.md), so this
   * is assembled from whichever of orderStatus/shipmentStatus/currentLocation are present. */
  readonly currentStatusLine = computed(() => {
    const r = this._response();
    if (!r) return null;
    const parts = [r.orderStatus, r.shipmentStatus, r.currentLocation].filter(
      (part): part is string => !!part,
    );
    return parts.length > 0 ? parts.join(' · ') : null;
  });

  readonly hasImpact = computed(() => {
    const r = this._response();
    if (!r) return false;
    return (
      r.promisedDeliveryDate != null ||
      r.revisedDeliveryDate != null ||
      r.delayDays != null ||
      r.slaStatus !== 'N/A'
    );
  });

  /** Source badges are derived from `intent` (RoutingCategory) — the schema has no
   * separate DB/API/KB tag on individual sources, see docs/api_contracts.md. */
  readonly sourceBadges = computed<SourceBadge[]>(() => {
    const r = this._response();
    if (!r) return [];
    switch (r.intent) {
      case 'KNOWLEDGE_QUERY':
        return ['KB'];
      case 'DATABASE_QUERY':
        return ['DB'];
      case 'API_QUERY':
        return ['API'];
      case 'MULTI_TOOL_QUERY':
        return r.sources.length > 0 ? ['DB', 'API', 'KB'] : ['DB', 'API'];
    }
  });

  readonly slaBadgeClass = computed(() => {
    const r = this._response();
    if (!r) return '';
    switch (r.slaStatus) {
      case 'Breached':
        return 'impact__sla-badge--breached';
      case 'At Risk':
        return 'impact__sla-badge--at-risk';
      case 'On Time':
        return 'impact__sla-badge--on-time';
      default:
        return 'impact__sla-badge--na';
    }
  });
}

import { Component, Input, computed, signal } from '@angular/core';
import { RoutingCategory, Source } from '../../../../features/chat/models/chat.model';

type SourceBadge = 'DB' | 'API' | 'KB';

/** Renders Tool Sources (DB/API/KB badges, derived from `intent` — the schema has
 * no per-source DB/API/KB tag, see docs/api_contracts.md) and Knowledge Sources
 * (individual KB document citations). Always shows the intent badges since
 * `intent` is always present on the wire contract; the document list is empty
 * for non-KB answers, which is expected, not an error (P1.9). */
@Component({
  selector: 'app-sources-card',
  standalone: true,
  imports: [],
  templateUrl: './sources-card.component.html',
  styleUrl: './sources-card.component.scss',
})
export class SourcesCardComponent {
  private readonly _intent = signal<RoutingCategory>('DATABASE_QUERY');
  private readonly _sources = signal<Source[]>([]);

  @Input({ required: true }) set intent(value: RoutingCategory) {
    this._intent.set(value);
  }
  get intent(): RoutingCategory {
    return this._intent();
  }

  @Input() set sources(value: Source[]) {
    this._sources.set(value ?? []);
  }
  get sources(): Source[] {
    return this._sources();
  }

  readonly toolBadges = computed<SourceBadge[]>(() => {
    switch (this._intent()) {
      case 'KNOWLEDGE_QUERY':
        return ['KB'];
      case 'DATABASE_QUERY':
        return ['DB'];
      case 'API_QUERY':
        return ['API'];
      case 'MULTI_TOOL_QUERY':
        return this._sources().length > 0 ? ['DB', 'API', 'KB'] : ['DB', 'API'];
    }
  });
}

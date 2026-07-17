import { Component, Input, computed, signal } from '@angular/core';
import { SlaStatus } from '../../../../features/chat/models/chat.model';

/** Renders ETA/Promised Date, Revised ETA, and the SLA Status badge. Self-hides
 * only when there is truly nothing to show (`slaStatus` is required on the wire
 * contract, so 'N/A' with no dates still renders a badge — P1.9). */
@Component({
  selector: 'app-sla-card',
  standalone: true,
  imports: [],
  templateUrl: './sla-card.component.html',
  styleUrl: './sla-card.component.scss',
})
export class SlaCardComponent {
  private readonly _slaStatus = signal<SlaStatus>('N/A');
  private readonly _promisedDeliveryDate = signal<string | null>(null);
  private readonly _revisedDeliveryDate = signal<string | null>(null);

  @Input({ required: true }) set slaStatus(value: SlaStatus) {
    this._slaStatus.set(value);
  }
  get slaStatus(): SlaStatus {
    return this._slaStatus();
  }

  @Input() set promisedDeliveryDate(value: string | null) {
    this._promisedDeliveryDate.set(value);
  }
  get promisedDeliveryDate(): string | null {
    return this._promisedDeliveryDate();
  }

  @Input() set revisedDeliveryDate(value: string | null) {
    this._revisedDeliveryDate.set(value);
  }
  get revisedDeliveryDate(): string | null {
    return this._revisedDeliveryDate();
  }

  readonly hasContent = computed(
    () =>
      this._promisedDeliveryDate() != null ||
      this._revisedDeliveryDate() != null ||
      this._slaStatus() !== 'N/A',
  );

  readonly badgeClass = computed(() => {
    switch (this._slaStatus()) {
      case 'Breached':
        return 'sla-badge--breached';
      case 'At Risk':
        return 'sla-badge--at-risk';
      case 'On Time':
        return 'sla-badge--on-time';
      default:
        return 'sla-badge--na';
    }
  });
}

import { Component, Input, computed, signal } from '@angular/core';

/** Renders Delay Reason + Delay Days. Self-hides when both are absent
 * (P1.9, see docs/api_contracts.md). */
@Component({
  selector: 'app-delay-card',
  standalone: true,
  imports: [],
  templateUrl: './delay-card.component.html',
  styleUrl: './delay-card.component.scss',
})
export class DelayCardComponent {
  private readonly _delayReason = signal<string | null>(null);
  private readonly _delayDays = signal<number | null>(null);

  @Input() set delayReason(value: string | null) {
    this._delayReason.set(value);
  }
  get delayReason(): string | null {
    return this._delayReason();
  }

  @Input() set delayDays(value: number | null) {
    this._delayDays.set(value);
  }
  get delayDays(): number | null {
    return this._delayDays();
  }

  readonly hasContent = computed(() => this._delayReason() != null || this._delayDays() != null);
}

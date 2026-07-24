import { Component, Input, computed, signal } from '@angular/core';
import { ChatResponse } from '../../../features/chat/models/chat.model';
import { StatusCardComponent } from '../response-cards/status-card/status-card.component';
import { ShipmentCardComponent } from '../response-cards/shipment-card/shipment-card.component';
import { DelayCardComponent } from '../response-cards/delay-card/delay-card.component';
import { SlaCardComponent } from '../response-cards/sla-card/sla-card.component';
import { RecommendationsCardComponent } from '../response-cards/recommendations-card/recommendations-card.component';
import { SourcesCardComponent } from '../response-cards/sources-card/sources-card.component';
import { MetadataFooterComponent } from '../response-cards/metadata-footer/metadata-footer.component';
import { MarkdownLitePipe } from '../../pipes/markdown-lite.pipe';

/** Container for the P1.9 structured response. Composes the reusable card
 * components below; each card self-hides when its own fields are absent, so
 * this component never needs to know which fields a given intent populates. */
@Component({
  selector: 'app-assistant-response',
  standalone: true,
  imports: [
    StatusCardComponent,
    ShipmentCardComponent,
    DelayCardComponent,
    SlaCardComponent,
    RecommendationsCardComponent,
    SourcesCardComponent,
    MetadataFooterComponent,
    MarkdownLitePipe,
  ],
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

  /** Which copy button most recently succeeded, so only that one shows "Copied". */
  readonly copiedKey = signal<string | null>(null);

  /** Whether the status/shipment/delay/SLA card grid has anything to show at all —
   * governs whether the grid wrapper renders, since every card inside self-hides
   * individually but an all-hidden grid would still show empty padding. */
  readonly hasCardContent = computed(() => {
    const r = this._response();
    if (!r) return false;
    return (
      r.orderStatus != null ||
      r.shipmentStatus != null ||
      r.currentLocation != null ||
      r.delayReason != null ||
      r.delayDays != null ||
      r.promisedDeliveryDate != null ||
      r.revisedDeliveryDate != null ||
      r.slaStatus !== 'N/A'
    );
  });

  /** Copies raw source text (not rendered markup). No-ops where the Clipboard
   * API is unavailable or permission is refused — never throws at the user. */
  copy(key: string, text: string | null): void {
    if (!text) {
      return;
    }
    void navigator.clipboard?.writeText(text).then(
      () => {
        this.copiedKey.set(key);
        setTimeout(() => this.copiedKey.set(null), 1600);
      },
      () => {},
    );
  }
}

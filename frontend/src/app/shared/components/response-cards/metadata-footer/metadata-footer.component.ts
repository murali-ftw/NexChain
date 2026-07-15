import { Component, Input } from '@angular/core';
import { DatePipe } from '@angular/common';

/** Renders the response envelope: warnings, partial-response indicator, timestamp,
 * and trace ID. `traceId`/`timestamp` are always present on the wire contract
 * (Spring Boot's application-layer envelope — see docs/api_contracts.md), so those
 * two rows always render; `warnings`/`partial` only render when applicable (P1.9). */
@Component({
  selector: 'app-metadata-footer',
  standalone: true,
  imports: [DatePipe],
  templateUrl: './metadata-footer.component.html',
  styleUrl: './metadata-footer.component.scss',
})
export class MetadataFooterComponent {
  @Input({ required: true }) traceId!: string;
  @Input({ required: true }) timestamp!: string;
  @Input() warnings: string[] = [];
  @Input() partial = false;
}

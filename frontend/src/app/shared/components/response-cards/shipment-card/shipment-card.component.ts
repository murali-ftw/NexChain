import { Component, Input, computed, signal } from '@angular/core';

/** Renders Shipment Status + Current Location. Self-hides when both are absent
 * (e.g. a pure inventory/KB query — P1.9, see docs/api_contracts.md). */
@Component({
  selector: 'app-shipment-card',
  standalone: true,
  imports: [],
  templateUrl: './shipment-card.component.html',
  styleUrl: './shipment-card.component.scss',
})
export class ShipmentCardComponent {
  private readonly _shipmentStatus = signal<string | null>(null);
  private readonly _currentLocation = signal<string | null>(null);

  @Input() set shipmentStatus(value: string | null) {
    this._shipmentStatus.set(value);
  }
  get shipmentStatus(): string | null {
    return this._shipmentStatus();
  }

  @Input() set currentLocation(value: string | null) {
    this._currentLocation.set(value);
  }
  get currentLocation(): string | null {
    return this._currentLocation();
  }

  readonly hasContent = computed(() => this._shipmentStatus() != null || this._currentLocation() != null);
}

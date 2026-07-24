import { Component, ViewEncapsulation } from '@angular/core';

/**
 * Glass wrapper for a projected native <table>. Deliberately not a
 * data-driven grid — plain <table>/<thead>/<tbody> markup stays the most
 * accessible, flexible way to render tabular data; this component only
 * supplies the Aetheria wrapper/header/row treatment around it.
 */
@Component({
  selector: 'app-table',
  standalone: true,
  imports: [],
  templateUrl: './table.component.html',
  styleUrl: './table.component.scss',
  encapsulation: ViewEncapsulation.None,
  host: { class: 'app-table' },
})
export class TableComponent {}

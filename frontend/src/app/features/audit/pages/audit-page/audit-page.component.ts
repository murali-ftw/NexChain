import { Component } from '@angular/core';

@Component({
  selector: 'app-audit-page',
  standalone: true,
  imports: [],
  templateUrl: './audit-page.component.html',
  styleUrl: './audit-page.component.scss',
})
export class AuditPageComponent {
  readonly columns = ['Timestamp', 'User', 'Question', 'Intent', 'Agents Invoked', 'SLA Result'];
}

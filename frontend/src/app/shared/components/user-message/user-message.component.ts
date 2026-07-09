import { Component, Input } from '@angular/core';
import { DatePipe } from '@angular/common';

@Component({
  selector: 'app-user-message',
  standalone: true,
  imports: [DatePipe],
  templateUrl: './user-message.component.html',
  styleUrl: './user-message.component.scss',
})
export class UserMessageComponent {
  @Input({ required: true }) text!: string;
  @Input() timestamp?: Date;
}

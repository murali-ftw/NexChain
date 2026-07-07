import { Component, EventEmitter, Output } from '@angular/core';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-chat-input',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './chat-input.component.html',
  styleUrl: './chat-input.component.scss',
})
export class ChatInputComponent {
  @Output() send = new EventEmitter<string>();

  message = '';

  submit(): void {
    const trimmed = this.message.trim();
    if (!trimmed) {
      return;
    }
    this.send.emit(trimmed);
    this.message = '';
  }
}

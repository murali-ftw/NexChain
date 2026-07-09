import { Component, EventEmitter, Input, Output } from '@angular/core';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-chat-input',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './chat-input.component.html',
  styleUrl: './chat-input.component.scss',
})
export class ChatInputComponent {
  /** True while the assistant is "thinking" — greys out input and blocks duplicate sends. */
  @Input() disabled = false;

  @Output() send = new EventEmitter<string>();

  message = '';

  get isBlank(): boolean {
    return this.message.trim().length === 0;
  }

  /** Enter sends; Shift+Enter inserts a newline (default textarea behavior). */
  onEnter(event: Event): void {
    const keyboardEvent = event as KeyboardEvent;
    if (keyboardEvent.shiftKey) {
      return;
    }
    keyboardEvent.preventDefault();
    this.submit();
  }

  submit(): void {
    if (this.disabled) {
      return;
    }
    const trimmed = this.message.trim();
    if (!trimmed) {
      return;
    }
    this.send.emit(trimmed);
    this.message = '';
  }
}

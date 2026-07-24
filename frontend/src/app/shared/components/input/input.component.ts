import { Component, EventEmitter, Input, Output } from '@angular/core';

export type InputFieldType = 'text' | 'search' | 'date' | 'email';

let nextInputId = 0;

@Component({
  selector: 'app-input',
  standalone: true,
  imports: [],
  templateUrl: './input.component.html',
  styleUrl: './input.component.scss',
})
export class InputComponent {
  @Input() label?: string;
  @Input() type: InputFieldType = 'text';
  @Input() placeholder = '';
  @Input() value = '';
  @Input() disabled = false;
  @Input() ariaLabel?: string;
  @Output() valueChange = new EventEmitter<string>();

  readonly inputId = `app-input-${nextInputId++}`;

  onInput(event: Event): void {
    this.valueChange.emit((event.target as HTMLInputElement).value);
  }
}

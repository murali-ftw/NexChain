import { Component, ElementRef, EventEmitter, Input, Output, ViewChild, signal } from '@angular/core';
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

  /** ponytail: display-only. There is no upload endpoint in the API contract
   * (chat-api.service posts {message, sessionId} and nothing else), so attached
   * files are never read, encoded, or transmitted — they are a visual context
   * affordance only. Wire these into a multipart request here if an upload
   * endpoint ever lands; until then sending is deliberately unchanged. */
  readonly attachments = signal<string[]>([]);
  readonly isDragging = signal(false);

  @ViewChild('field') private field?: ElementRef<HTMLTextAreaElement>;
  @ViewChild('filePicker') private filePicker?: ElementRef<HTMLInputElement>;

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
    this.attachments.set([]);
    this.resetHeight();
  }

  /** Grows the pod with the message instead of scrolling a fixed-height box. */
  autoGrow(event: Event): void {
    const el = event.target as HTMLTextAreaElement;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 168)}px`;
  }

  private resetHeight(): void {
    const el = this.field?.nativeElement;
    if (el) {
      el.style.height = 'auto';
    }
  }

  openFilePicker(): void {
    if (this.disabled) {
      return;
    }
    this.filePicker?.nativeElement.click();
  }

  onFilesPicked(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.addFiles(input.files);
    input.value = ''; // let the same file be re-picked
  }

  onDragOver(event: DragEvent): void {
    if (this.disabled) {
      return;
    }
    event.preventDefault();
    this.isDragging.set(true);
  }

  onDragLeave(event: DragEvent): void {
    // Ignore bubbling from children — only clear when the pointer truly leaves the pod.
    if (event.currentTarget instanceof Node && event.relatedTarget instanceof Node) {
      if (event.currentTarget.contains(event.relatedTarget)) {
        return;
      }
    }
    this.isDragging.set(false);
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    this.isDragging.set(false);
    if (this.disabled) {
      return;
    }
    this.addFiles(event.dataTransfer?.files ?? null);
  }

  removeAttachment(name: string): void {
    this.attachments.update((names) => names.filter((n) => n !== name));
  }

  private addFiles(files: FileList | null): void {
    if (!files?.length) {
      return;
    }
    const incoming = Array.from(files).map((f) => f.name);
    this.attachments.update((names) => [...new Set([...names, ...incoming])]);
  }
}

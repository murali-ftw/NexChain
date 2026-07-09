import { Component, ElementRef, ViewChild, signal } from '@angular/core';
import { ChatInputComponent } from '../../../../shared/components/chat-input/chat-input.component';
import { UserMessageComponent } from '../../../../shared/components/user-message/user-message.component';
import { AssistantResponseComponent } from '../../../../shared/components/assistant-response/assistant-response.component';
import { SuggestedQuestionsComponent } from '../../components/suggested-questions/suggested-questions.component';
import { ChatMockService } from '../../services/chat-mock.service';
import { ChatMessage } from '../../models/chat.model';

@Component({
  selector: 'app-chat-page',
  standalone: true,
  imports: [ChatInputComponent, UserMessageComponent, AssistantResponseComponent, SuggestedQuestionsComponent],
  templateUrl: './chat-page.component.html',
  styleUrl: './chat-page.component.scss',
})
export class ChatPageComponent {
  readonly messages = signal<ChatMessage[]>([]);
  readonly isLoading = signal(false);
  readonly loadingText = signal('Thinking...');

  @ViewChild('scrollAnchor') private scrollAnchor?: ElementRef<HTMLDivElement>;

  /** Groups this conversation's turns for the mock backend — mirrors what a real
   * session id would do once wired to /api/chat (P1.5+). Not persisted (see P1.7). */
  private readonly sessionId = crypto.randomUUID();

  constructor(private readonly chatMock: ChatMockService) {}

  onSend(text: string): void {
    if (this.isLoading()) {
      return;
    }
    const trimmed = text.trim();
    if (!trimmed) {
      return;
    }

    this.messages.update((msgs) => [
      ...msgs,
      { kind: 'user', id: crypto.randomUUID(), text: trimmed, timestamp: new Date() },
    ]);
    this.scrollToBottom();

    this.isLoading.set(true);
    this.loadingText.set(this.chatMock.getLoadingMessage(trimmed));

    this.chatMock.getResponse(trimmed, this.sessionId).subscribe({
      next: (response) => {
        this.isLoading.set(false);
        this.messages.update((msgs) => [
          ...msgs,
          { kind: 'assistant', id: crypto.randomUUID(), response, timestamp: new Date() },
        ]);
        this.scrollToBottom();
      },
      error: (err: unknown) => {
        this.isLoading.set(false);
        const message = err instanceof Error ? err.message : 'Unable to retrieve the response. Please try again.';
        this.messages.update((msgs) => [
          ...msgs,
          { kind: 'error', id: crypto.randomUUID(), message, retryText: trimmed, timestamp: new Date() },
        ]);
        this.scrollToBottom();
      },
    });
  }

  retry(text: string): void {
    this.onSend(text);
  }

  private scrollToBottom(): void {
    setTimeout(() => {
      this.scrollAnchor?.nativeElement.scrollIntoView({ behavior: 'smooth', block: 'end' });
    });
  }
}

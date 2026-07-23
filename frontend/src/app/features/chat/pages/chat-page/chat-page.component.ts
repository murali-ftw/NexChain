import { Component, ElementRef, OnInit, ViewChild, signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { timer } from 'rxjs';
import { ChatInputComponent } from '../../../../shared/components/chat-input/chat-input.component';
import { UserMessageComponent } from '../../../../shared/components/user-message/user-message.component';
import { AssistantResponseComponent } from '../../../../shared/components/assistant-response/assistant-response.component';
import { SuggestedQuestionsComponent } from '../../components/suggested-questions/suggested-questions.component';
import { ChatApiService } from '../../services/chat-api.service';
import { HistoryApiService } from '../../../history/services/history-api.service';
import { DEGRADED_RESPONSE } from '../../data/chat-fixtures';
import { ChatMessage, ChatResponse } from '../../models/chat.model';
import { environment } from '../../../../../environments/environment';

@Component({
  selector: 'app-chat-page',
  standalone: true,
  imports: [ChatInputComponent, UserMessageComponent, AssistantResponseComponent, SuggestedQuestionsComponent],
  templateUrl: './chat-page.component.html',
  styleUrl: './chat-page.component.scss',
})
export class ChatPageComponent implements OnInit {
  readonly messages = signal<ChatMessage[]>([]);
  readonly isLoading = signal(false);
  readonly loadingText = signal('Thinking...');
  readonly isRestoring = signal(false);

  @ViewChild('scrollAnchor') private scrollAnchor?: ElementRef<HTMLDivElement>;

  /** Groups this conversation's turns for the backend. Starts as a fresh id; ngOnInit
   * overwrites it with the restored conversation's id when reopened from History
   * (P1.7), so new messages continue that session instead of starting a new one. */
  private sessionId: string = crypto.randomUUID();

  constructor(
    private readonly chatApi: ChatApiService,
    private readonly historyApi: HistoryApiService,
    private readonly route: ActivatedRoute,
    private readonly router: Router,
  ) {}

  ngOnInit(): void {
    const restoreId = this.route.snapshot.queryParamMap.get('sessionId');
    if (!restoreId) {
      return;
    }
    this.restoreConversation(restoreId);
  }

  private restoreConversation(restoreId: string): void {
    this.isRestoring.set(true);
    this.historyApi.getHistoryDetail(restoreId).subscribe({
      next: (detail) => {
        this.sessionId = detail.sessionId;
        this.messages.set(
          detail.turns.flatMap((turn) => {
            const timestamp = new Date(turn.timestamp);
            return [
              { kind: 'user' as const, id: crypto.randomUUID(), text: turn.question, timestamp },
              { kind: 'assistant' as const, id: crypto.randomUUID(), response: turn.response, timestamp },
            ];
          }),
        );
        this.isRestoring.set(false);
        this.scrollToBottom();
      },
      error: (err: unknown) => {
        this.isRestoring.set(false);
        const message = err instanceof Error ? err.message : 'That conversation could not be restored.';
        this.messages.set([
          { kind: 'error', id: crypto.randomUUID(), message, retryText: '', restoreId, timestamp: new Date() },
        ]);
      },
    });
  }

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
    this.loadingText.set(this.getLoadingMessage(trimmed));

    const normalized = trimmed.toLowerCase();

    // Day 4 (P1.4): explicit local test triggers only — Spring Boot has no reason to
    // simulate its own failure, and a real "stop the backend" test covers the
    // unavailable-backend case more realistically. Every other query — including every
    // suggested question — goes through the real POST /api/chat round trip below.
    // Disabled in production builds (environment.production) so a real end user can
    // never trigger a fake response by typing these phrases.
    if (!environment.production && normalized.includes('simulate error')) {
      timer(600).subscribe(() =>
        this.handleError(new Error('Unable to retrieve the response. Please try again.'), trimmed),
      );
      return;
    }
    if (!environment.production && normalized.includes('simulate degraded')) {
      timer(600).subscribe(() =>
        this.handleSuccess({
          ...DEGRADED_RESPONSE,
          traceId: crypto.randomUUID(),
          sessionId: this.sessionId,
          timestamp: new Date().toISOString(),
        }),
      );
      return;
    }

    this.chatApi.sendMessage(trimmed, this.sessionId).subscribe({
      next: (response) => this.handleSuccess(response),
      error: (err: unknown) => this.handleError(err, trimmed),
    });
  }

  retry(text: string, restoreId?: string): void {
    if (restoreId) {
      this.restoreConversation(restoreId);
      return;
    }
    this.onSend(text);
  }

  private handleSuccess(response: ChatResponse): void {
    this.isLoading.set(false);
    this.messages.update((msgs) => [
      ...msgs,
      { kind: 'assistant', id: crypto.randomUUID(), response, timestamp: new Date() },
    ]);
    this.scrollToBottom();
    this.syncSessionIdToUrl();
  }

  /** Puts the active sessionId in the URL once a real turn has round-tripped, so a
   * mid-conversation page refresh restores it via the same query-param path History
   * links already use, instead of silently dropping the conversation (Day 13 QA). */
  private syncSessionIdToUrl(): void {
    if (this.route.snapshot.queryParamMap.get('sessionId') === this.sessionId) {
      return;
    }
    this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { sessionId: this.sessionId },
      queryParamsHandling: 'merge',
      replaceUrl: true,
    });
  }

  private handleError(err: unknown, retryText: string): void {
    this.isLoading.set(false);
    const message = err instanceof Error ? err.message : 'Unable to retrieve the response. Please try again.';
    this.messages.update((msgs) => [
      ...msgs,
      { kind: 'error', id: crypto.randomUUID(), message, retryText, timestamp: new Date() },
    ]);
    this.scrollToBottom();
  }

  /** Context-specific loading text — purely cosmetic, doesn't mock any response content. */
  private getLoadingMessage(query: string): string {
    const normalized = query.toLowerCase();
    if (normalized.includes('simulate error') || normalized.includes('simulate degraded')) {
      return 'Checking shipment status...';
    }
    if (normalized.includes('45892')) {
      return 'Checking order and shipment status...';
    }
    if (normalized.includes('sku') || normalized.includes('stock')) {
      return 'Checking inventory...';
    }
    if (normalized.includes('sla') || normalized.includes('escalation')) {
      return 'Searching knowledge base...';
    }
    if (normalized.includes('warehouse') || normalized.includes('report')) {
      return 'Running report query...';
    }
    return 'Thinking...';
  }

  private scrollToBottom(): void {
    setTimeout(() => {
      this.scrollAnchor?.nativeElement.scrollIntoView({ behavior: 'smooth', block: 'end' });
    });
  }
}

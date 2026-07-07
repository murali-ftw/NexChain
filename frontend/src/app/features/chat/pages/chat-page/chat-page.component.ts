import { Component } from '@angular/core';
import { ChatInputComponent } from '../../../../shared/components/chat-input/chat-input.component';
import { SuggestedQuestionsComponent } from '../../components/suggested-questions/suggested-questions.component';

interface ChatMessage {
  role: 'user' | 'assistant';
  text: string;
}

@Component({
  selector: 'app-chat-page',
  standalone: true,
  imports: [ChatInputComponent, SuggestedQuestionsComponent],
  templateUrl: './chat-page.component.html',
  styleUrl: './chat-page.component.scss',
})
export class ChatPageComponent {
  messages: ChatMessage[] = [];

  onSend(text: string): void {
    this.messages.push({ role: 'user', text });
  }
}

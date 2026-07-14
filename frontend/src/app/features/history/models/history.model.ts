import { ChatResponse } from '../../chat/models/chat.model';

/**
 * Mirrors backend-api's HistoryItemDto (GET /api/chat/history) field-for-field —
 * see docs/api_contracts.md. Day 7 (P1.7): real per-user, per-session persistence.
 */
export interface HistoryItem {
  id: string;
  question: string;
  answerSummary: string;
  timestamp: string;
  sessionId: string;
}

/** Mirrors backend-api's ConversationTurnDto — one question/answer turn in a conversation. */
export interface ConversationTurn {
  question: string;
  response: ChatResponse;
  timestamp: string;
}

/** Mirrors backend-api's HistoryDetailDto (GET /api/chat/history/{id}) — every turn in a
 * conversation, in order, so it can be replayed and continued under the same session id. */
export interface HistoryDetail {
  id: string;
  sessionId: string;
  turns: ConversationTurn[];
}

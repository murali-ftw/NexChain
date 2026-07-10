/**
 * Mirrors backend-api's HistoryItemDto (GET /api/chat/history) field-for-field —
 * see docs/api_contracts.md. Day 5 (P1.5): backend returns fixed mock records today,
 * no persistence until P1.7 (Day 7).
 */
export interface HistoryItem {
  id: string;
  question: string;
  answerSummary: string;
  timestamp: string;
  sessionId: string;
}

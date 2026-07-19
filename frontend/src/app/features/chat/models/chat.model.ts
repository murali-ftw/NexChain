/**
 * Mirrors backend-api's ChatResponse (com.nexchain.backend.chat.dto.ChatResponse),
 * which itself mirrors CoPilotResponse in ai/contracts.py (Person 3, P3.1) field-for-field,
 * plus two provisional fields and the app-layer envelope — see docs/api_contracts.md.
 * Field names here are deliberately identical so a real HTTP response can be assigned
 * to this type with zero mapping once P1.10 lands.
 */

export type RoutingCategory = 'KNOWLEDGE_QUERY' | 'DATABASE_QUERY' | 'API_QUERY' | 'MULTI_TOOL_QUERY';

export type SlaStatus = 'On Time' | 'At Risk' | 'Breached' | 'N/A';

export interface Source {
  documentName: string;
  snippet: string | null;
  docId: number | null;
  score: number | null;
}

export interface ChatResponse {
  traceId: string;
  sessionId: string;
  timestamp: string;
  answerText: string;
  intent: RoutingCategory;
  orderStatus: string | null;
  shipmentStatus: string | null;
  currentLocation: string | null;
  delayReason: string | null;
  promisedDeliveryDate: string | null;
  revisedDeliveryDate: string | null;
  delayDays: number | null;
  slaStatus: SlaStatus;
  recommendedActions: string[];
  sources: Source[];
  partial: boolean;
  warnings: string[];
  error: string | null;
  agentsInvoked: string[];
  generatedSql: string | null;
}

/**
 * One entry in the local, in-memory conversation. Day 3 scope — not persisted (see P1.7).
 * The in-flight "thinking" state is tracked separately (ChatPageComponent.isLoading),
 * not as a message-array entry, so there's no variant for it here.
 */
export type ChatMessage =
  | { kind: 'user'; id: string; text: string; timestamp: Date }
  | { kind: 'assistant'; id: string; response: ChatResponse; timestamp: Date }
  | { kind: 'error'; id: string; message: string; retryText: string; timestamp: Date };

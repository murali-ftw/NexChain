import { SlaStatus, Source } from '../../chat/models/chat.model';

/**
 * Mirrors backend-api's AuditEntryDto / ApiCallDto (GET /api/audit) field-for-field —
 * see docs/api_contracts.md. `kbSources` and `slaResult` reuse the same wire types as
 * the chat response (`Source` / `SlaStatus`) since they are the identical shape.
 * `sessionId` and `warnings` are Day 8 (P1.8) additions to the DTO.
 */
export interface AuditApiCall {
  endpoint: string;
  statusCode: number;
  latencyMs: number;
}

export interface AuditEntry {
  auditId: number;
  traceId: string;
  sessionId: string;
  timestamp: string;
  user: string;
  rawQuestion: string;
  detectedIntent: string[];
  agentsInvoked: string[];
  generatedSql: string | null;
  apiCalls: AuditApiCall[];
  kbSources: Source[];
  slaResult: SlaStatus;
  status: string;
  warnings: string[];
}

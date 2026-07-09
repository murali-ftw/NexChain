import { ChatResponse } from '../models/chat.model';

/** Fixture content only — traceId/sessionId/timestamp are filled in per-request by ChatMockService. */
export type ChatResponseFixture = Omit<ChatResponse, 'traceId' | 'sessionId' | 'timestamp'>;

/** Scenario A (mandatory): the project's flagship delay scenario — problem_statement.md Section 7. */
export const FLAGSHIP_RESPONSE: ChatResponseFixture = {
  answerText: 'Order SO-45892 has been dispatched from the warehouse.',
  intent: 'MULTI_TOOL_QUERY',
  orderStatus: 'Dispatched',
  shipmentStatus: 'Customs Hold',
  currentLocation: 'Chennai Port',
  delayReason: 'HS code mismatch during customs validation.',
  promisedDeliveryDate: '2026-07-03',
  revisedDeliveryDate: '2026-07-09',
  delayDays: 6,
  slaStatus: 'Breached',
  recommendedActions: [
    'Verify the HS code in the commercial invoice.',
    'Send the corrected document to the customs broker.',
    'Escalate to the logistics manager.',
    'Notify the customer with the revised ETA.',
  ],
  sources: [
    {
      documentName: 'Customs Hold SOP',
      snippet: 'Covers HS code mismatch during customs validation and other customs hold causes.',
      docId: 3,
      score: 0.93,
    },
  ],
  partial: false,
  warnings: [],
  error: null,
};

/** Scenario B: inventory lookup — no order/shipment fields apply. */
export const INVENTORY_RESPONSE: ChatResponseFixture = {
  answerText: 'SKU-1001 has 240 units available at the Chennai warehouse.',
  intent: 'DATABASE_QUERY',
  orderStatus: null,
  shipmentStatus: null,
  currentLocation: 'Chennai Warehouse',
  delayReason: null,
  promisedDeliveryDate: null,
  revisedDeliveryDate: null,
  delayDays: null,
  slaStatus: 'N/A',
  recommendedActions: [],
  sources: [],
  partial: false,
  warnings: [],
  error: null,
};

/** Scenario C: SOP/policy lookup — no order/shipment/impact fields apply. */
export const SLA_POLICY_RESPONSE: ChatResponseFixture = {
  answerText:
    "SLA breaches are escalated based on the customer's tier — STANDARD, GOLD, or PLATINUM — " +
    'each mapped to a specific escalation role and response-time target.',
  intent: 'KNOWLEDGE_QUERY',
  orderStatus: null,
  shipmentStatus: null,
  currentLocation: null,
  delayReason: null,
  promisedDeliveryDate: null,
  revisedDeliveryDate: null,
  delayDays: null,
  slaStatus: 'N/A',
  recommendedActions: [
    "Identify the customer's SLA tier and the breach severity.",
    'Route the case to the escalation role mapped to that tier.',
    'Notify the customer with a revised resolution timeline.',
  ],
  sources: [
    {
      documentName: 'Escalation Matrix',
      snippet: 'Maps delay severity and SLA tier to escalation role and expected response time.',
      docId: 5,
      score: 0.88,
    },
    {
      documentName: 'SLA Policy',
      snippet: 'Defines STANDARD/GOLD/PLATINUM tiers, max_delay_days thresholds, and escalation roles.',
      docId: 1,
      score: 0.81,
    },
  ],
  partial: false,
  warnings: [],
  error: null,
};

/**
 * Scenario D: reporting. The agreed schema has no tabular/report-row field, so the
 * result is represented as prose in answerText rather than inventing a new field —
 * see docs/api_contracts.md provisional-extension notes for the same pattern.
 */
export const REPORTING_RESPONSE: ChatResponseFixture = {
  answerText:
    '4 orders from the Chennai warehouse are currently delayed: SO-10241 (2 days), ' +
    'SO-10288 (5 days), SO-10299 (1 day), SO-10310 (3 days).',
  intent: 'DATABASE_QUERY',
  orderStatus: null,
  shipmentStatus: null,
  currentLocation: 'Chennai Warehouse',
  delayReason: null,
  promisedDeliveryDate: null,
  revisedDeliveryDate: null,
  delayDays: null,
  slaStatus: 'N/A',
  recommendedActions: [],
  sources: [],
  partial: false,
  warnings: [],
  error: null,
};

/**
 * Degraded variant of the flagship scenario: shipment API unavailable, DB data still
 * returned. Demonstrates `partial`/`warnings` per tech-req Section 3.4's retry/fallback policy.
 */
export const DEGRADED_RESPONSE: ChatResponseFixture = {
  answerText: 'Order SO-45892 has been dispatched from the warehouse.',
  intent: 'MULTI_TOOL_QUERY',
  orderStatus: 'Dispatched',
  shipmentStatus: null,
  currentLocation: null,
  delayReason: null,
  promisedDeliveryDate: '2026-07-03',
  revisedDeliveryDate: null,
  delayDays: null,
  slaStatus: 'At Risk',
  recommendedActions: ['Retry the shipment lookup once the tracking API is back online.'],
  sources: [],
  partial: true,
  warnings: ['Shipment API unavailable. This answer is based on database records only.'],
  error: null,
};

/** Fallback for anything that doesn't match a known scenario — mirrors backend-api's own generic mock. */
export function genericResponse(query: string): ChatResponseFixture {
  return {
    answerText: `Mock response for: "${query}"`,
    intent: 'DATABASE_QUERY',
    orderStatus: null,
    shipmentStatus: null,
    currentLocation: null,
    delayReason: null,
    promisedDeliveryDate: null,
    revisedDeliveryDate: null,
    delayDays: null,
    slaStatus: 'N/A',
    recommendedActions: [],
    sources: [],
    partial: false,
    warnings: [],
    error: null,
  };
}

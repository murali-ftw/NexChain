package com.nexchain.backend.chat.service;

import com.nexchain.backend.chat.dto.ChatRequest;
import com.nexchain.backend.chat.dto.ChatResponse;
import com.nexchain.backend.chat.dto.RoutingCategory;
import com.nexchain.backend.common.dto.SlaStatus;
import com.nexchain.backend.common.dto.SourceDto;
import java.time.Instant;
import java.util.List;
import java.util.UUID;
import org.springframework.stereotype.Service;

/**
 * Day 4 contract stub. No FastAPI call, no LangGraph, no real intent classification —
 * that is Person 2/3's work and lands via P1.10 (Day 11). Every response is a
 * controlled, deterministic mock keyed off simple keyword matching; the {@code warnings}
 * field always discloses this.
 *
 * Content mirrors the scenario set already built in Angular's chat-fixtures.ts (Day 3)
 * so both layers agree on substance, not just shape, now that Angular calls this
 * endpoint directly instead of generating its own local mock (P1.4, Day 4).
 */
@Service
public class ChatService {

    private static final String MOCK_DISCLAIMER =
            "Day 4 mock response — no real AI pipeline yet (see P1.10, Day 11).";

    public ChatResponse getMockResponse(ChatRequest request) {
        String traceId = UUID.randomUUID().toString();
        String sessionId = request.sessionId() != null ? request.sessionId() : UUID.randomUUID().toString();
        Instant now = Instant.now();
        String normalized = request.query().toLowerCase();

        if (normalized.contains("45892")) {
            return flagshipResponse(traceId, sessionId, now);
        }
        if (normalized.contains("sku") || normalized.contains("stock")) {
            return inventoryResponse(traceId, sessionId, now);
        }
        if (normalized.contains("sla") || normalized.contains("escalation")) {
            return slaPolicyResponse(traceId, sessionId, now);
        }
        if (normalized.contains("warehouse") || normalized.contains("report")) {
            return reportingResponse(traceId, sessionId, now);
        }
        return genericResponse(traceId, sessionId, now, request.query());
    }

    /** Scenario A (mandatory): problem_statement.md Section 7's flagship delay scenario. */
    private ChatResponse flagshipResponse(String traceId, String sessionId, Instant now) {
        return new ChatResponse(
                traceId,
                sessionId,
                now,
                "Order SO-45892 has been dispatched from the warehouse.",
                RoutingCategory.MULTI_TOOL_QUERY,
                "Dispatched",
                "Customs Hold",
                "Chennai Port",
                "HS code mismatch during customs validation.",
                "2026-07-03",
                "2026-07-09",
                6,
                SlaStatus.BREACHED,
                List.of(
                        "Verify the HS code in the commercial invoice.",
                        "Send the corrected document to the customs broker.",
                        "Escalate to the logistics manager.",
                        "Notify the customer with the revised ETA."),
                List.of(new SourceDto(
                        "Customs Hold SOP",
                        "Covers HS code mismatch during customs validation and other customs hold causes.",
                        3,
                        0.93)),
                false,
                List.of(MOCK_DISCLAIMER),
                null);
    }

    /** Scenario B: inventory lookup — no order/shipment fields apply. */
    private ChatResponse inventoryResponse(String traceId, String sessionId, Instant now) {
        return new ChatResponse(
                traceId,
                sessionId,
                now,
                "SKU-1001 has 240 units available at the Chennai warehouse.",
                RoutingCategory.DATABASE_QUERY,
                null,
                null,
                "Chennai Warehouse",
                null,
                null,
                null,
                null,
                SlaStatus.NOT_APPLICABLE,
                List.of(),
                List.of(),
                false,
                List.of(MOCK_DISCLAIMER),
                null);
    }

    /** Scenario C: SOP/policy lookup — no order/shipment/impact fields apply. */
    private ChatResponse slaPolicyResponse(String traceId, String sessionId, Instant now) {
        return new ChatResponse(
                traceId,
                sessionId,
                now,
                "SLA breaches are escalated based on the customer's tier — STANDARD, GOLD, or PLATINUM"
                        + " — each mapped to a specific escalation role and response-time target.",
                RoutingCategory.KNOWLEDGE_QUERY,
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                SlaStatus.NOT_APPLICABLE,
                List.of(
                        "Identify the customer's SLA tier and the breach severity.",
                        "Route the case to the escalation role mapped to that tier.",
                        "Notify the customer with a revised resolution timeline."),
                List.of(
                        new SourceDto(
                                "Escalation Matrix",
                                "Maps delay severity and SLA tier to escalation role and expected response time.",
                                5,
                                0.88),
                        new SourceDto(
                                "SLA Policy",
                                "Defines STANDARD/GOLD/PLATINUM tiers, max_delay_days thresholds, and escalation"
                                        + " roles.",
                                1,
                                0.81)),
                false,
                List.of(MOCK_DISCLAIMER),
                null);
    }

    /**
     * Scenario D: reporting. The agreed schema has no tabular/report-row field, so the
     * result is prose in answerText rather than an invented field — see docs/api_contracts.md.
     */
    private ChatResponse reportingResponse(String traceId, String sessionId, Instant now) {
        return new ChatResponse(
                traceId,
                sessionId,
                now,
                "4 orders from the Chennai warehouse are currently delayed: SO-10241 (2 days), "
                        + "SO-10288 (5 days), SO-10299 (1 day), SO-10310 (3 days).",
                RoutingCategory.DATABASE_QUERY,
                null,
                null,
                "Chennai Warehouse",
                null,
                null,
                null,
                null,
                SlaStatus.NOT_APPLICABLE,
                List.of(),
                List.of(),
                false,
                List.of(MOCK_DISCLAIMER),
                null);
    }

    private ChatResponse genericResponse(String traceId, String sessionId, Instant now, String query) {
        return new ChatResponse(
                traceId,
                sessionId,
                now,
                "Mock response for: \"%s\"".formatted(query),
                RoutingCategory.DATABASE_QUERY,
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                SlaStatus.NOT_APPLICABLE,
                List.of(),
                List.of(),
                false,
                List.of(MOCK_DISCLAIMER),
                null);
    }
}

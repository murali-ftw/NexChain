package com.nexchain.backend.chat.client;

import com.nexchain.backend.chat.dto.RoutingCategory;
import com.nexchain.backend.common.dto.SlaStatus;
import com.nexchain.backend.common.dto.SourceDto;
import java.util.List;

/**
 * Test double standing in for Person 2's real FastAPI service, so
 * ApplicationSmokeTests can exercise the whole /api/chat -> history -> audit
 * pipeline without a live ai_service + Postgres + LLM key. Content mirrors
 * the deterministic Day 4 scenario set the previous in-process ChatService
 * mock used, keyed off the same keywords, so every existing assertion in
 * ApplicationSmokeTests keeps meaning what it always meant.
 *
 * <p>The real integration (ChatService -> RestClientAiQueryClient -> FastAPI
 * -> LangGraph -> MCP -> Postgres) is exercised separately, end-to-end,
 * against the live stack — not by this fake.
 */
public class FakeAiQueryClient implements AiQueryClient {

    @Override
    public AiQueryResult query(String query, String sessionId, String traceId, String userId) {
        String normalized = query.toLowerCase();

        if (normalized.contains("45892")) {
            return flagship();
        }
        if (normalized.contains("sku") || normalized.contains("stock")) {
            return inventory();
        }
        if (normalized.contains("sla") || normalized.contains("escalation")) {
            return slaPolicy();
        }
        if (normalized.contains("warehouse") || normalized.contains("report")) {
            return reporting();
        }
        return generic(query);
    }

    private AiQueryResult flagship() {
        return new AiQueryResult(
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
                null);
    }

    private AiQueryResult inventory() {
        return new AiQueryResult(
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
                null);
    }

    private AiQueryResult slaPolicy() {
        return new AiQueryResult(
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
                null);
    }

    private AiQueryResult reporting() {
        return new AiQueryResult(
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
                null);
    }

    private AiQueryResult generic(String query) {
        return new AiQueryResult(
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
                null);
    }
}

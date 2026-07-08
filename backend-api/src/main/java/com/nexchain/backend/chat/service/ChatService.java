package com.nexchain.backend.chat.service;

import com.nexchain.backend.chat.dto.ChatRequest;
import com.nexchain.backend.chat.dto.ChatResponse;
import com.nexchain.backend.chat.dto.RoutingCategory;
import com.nexchain.backend.common.dto.SlaStatus;
import java.time.Instant;
import java.util.List;
import java.util.UUID;
import org.springframework.stereotype.Service;

/**
 * Day 2 contract stub. No FastAPI call, no LangGraph, no real intent classification —
 * that is Person 2/3's work and lands via P1.10 (Day 11). Every response is a
 * controlled mock; the {@code warnings} field always says so.
 *
 * The one exception is the SO-45892 flagship scenario from docs/problem_statement.md
 * Section 7: if the query mentions it, this returns the fully-populated shape so
 * Person 1 can build/verify the Response Card UI against realistic data before the
 * real pipeline exists.
 */
@Service
public class ChatService {

    private static final String MOCK_DISCLAIMER =
            "Day 2 mock response — no real AI pipeline yet (see P1.10, Day 11).";

    public ChatResponse getMockResponse(ChatRequest request) {
        String traceId = UUID.randomUUID().toString();
        String sessionId = request.sessionId() != null ? request.sessionId() : UUID.randomUUID().toString();
        Instant now = Instant.now();

        if (request.query().toLowerCase().contains("45892")) {
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
                    List.of(),
                    false,
                    List.of(MOCK_DISCLAIMER),
                    null);
        }

        return new ChatResponse(
                traceId,
                sessionId,
                now,
                "Mock response for: \"%s\"".formatted(request.query()),
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

package com.nexchain.backend.chat.service;

import com.nexchain.backend.chat.client.AiQueryClient;
import com.nexchain.backend.chat.client.AiQueryResult;
import com.nexchain.backend.chat.dto.ChatRequest;
import com.nexchain.backend.chat.dto.ChatResponse;
import java.time.Instant;
import java.util.List;
import java.util.UUID;
import org.springframework.stereotype.Service;

/**
 * P1.10: the real AI execution pipeline. Every question is forwarded to
 * Person 2's FastAPI service (POST /ai/query), which runs it through the
 * LangGraph pipeline (intent classification -> KB/SQL/API branches ->
 * business rules -> final response) and returns the CoPilotResponse shape.
 *
 * <p>{@code traceId} is minted here, at the start of every request, and
 * threaded through FastAPI -> LangGraph -> MCP unchanged (tech-req §9) so
 * audit_log.trace_id can correlate the full request across every layer.
 * {@link AiQueryClient} never throws — success, timeout, and failure all
 * come back as a plain {@link AiQueryResult}, so the only job left here is
 * building Spring Boot's own envelope around it.
 */
@Service
public class ChatService {

    private final AiQueryClient aiQueryClient;

    public ChatService(AiQueryClient aiQueryClient) {
        this.aiQueryClient = aiQueryClient;
    }

    public ChatResponse getResponse(ChatRequest request, String username) {
        String traceId = UUID.randomUUID().toString();
        String sessionId = request.sessionId() != null ? request.sessionId() : UUID.randomUUID().toString();
        Instant now = Instant.now();

        AiQueryResult result = aiQueryClient.query(request.query(), sessionId, traceId, username);
        List<String> warnings = result.error() != null ? List.of(result.error()) : List.of();

        return new ChatResponse(
                traceId,
                sessionId,
                now,
                result.answerText(),
                result.intent(),
                result.orderStatus(),
                result.shipmentStatus(),
                result.currentLocation(),
                result.delayReason(),
                result.promisedDeliveryDate(),
                result.revisedDeliveryDate(),
                result.delayDays(),
                result.slaStatus(),
                result.recommendedActions(),
                result.sources(),
                result.partial(),
                warnings,
                result.error());
    }
}

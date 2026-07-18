package com.nexchain.backend.chat.client;

import com.nexchain.backend.chat.dto.RoutingCategory;
import com.nexchain.backend.common.dto.SlaStatus;
import com.nexchain.backend.common.dto.SourceDto;
import java.util.List;

/**
 * The AI service's answer, already trimmed to exactly the fields {@link
 * com.nexchain.backend.chat.service.ChatService} needs to build a {@code
 * ChatResponse} — everything except the traceId/sessionId/timestamp envelope,
 * which Spring Boot owns regardless of which {@link AiQueryClient} answered.
 *
 * <p>{@code error} carries a human-readable degradation/failure reason
 * whenever {@code partial} is true (a source was unavailable, or the whole
 * pipeline failed) — {@link RestClientAiQueryClient} builds one of these for
 * every failure mode itself, so {@code ChatService} never has to branch on
 * exceptions.
 */
public record AiQueryResult(
        String answerText,
        RoutingCategory intent,
        String orderStatus,
        String shipmentStatus,
        String currentLocation,
        String delayReason,
        String promisedDeliveryDate,
        String revisedDeliveryDate,
        Integer delayDays,
        SlaStatus slaStatus,
        List<String> recommendedActions,
        List<SourceDto> sources,
        boolean partial,
        String error,
        List<String> agentsInvoked,
        String generatedSql) {}

package com.nexchain.backend.chat.client;

import com.nexchain.backend.chat.dto.RoutingCategory;
import com.nexchain.backend.common.dto.SlaStatus;
import com.nexchain.backend.common.dto.SourceDto;
import java.util.List;

/**
 * The raw JSON body of Person 2's {@code POST /ai/query} response
 * (ai_service/schemas.py AiQueryResponse) — camelCase on the wire, so Jackson
 * deserializes it with no custom naming strategy. Kept separate from {@link
 * AiQueryResult} because this shape is the external contract (Person 2 owns
 * it) while {@code AiQueryResult} is this service's own internal value type.
 */
public record AiServiceResponse(
        String traceId,
        String sessionId,
        String answerText,
        RoutingCategory intent,
        String orderStatus,
        String shipmentStatus,
        String currentLocation,
        String delayReason,
        Integer delayDays,
        SlaStatus slaStatus,
        List<String> recommendedActions,
        List<SourceDto> sources,
        boolean partial,
        String error,
        String promisedDeliveryDate,
        String revisedDeliveryDate) {}

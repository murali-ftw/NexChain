package com.nexchain.backend.chat.dto;

import com.nexchain.backend.common.dto.SlaStatus;
import com.nexchain.backend.common.dto.SourceDto;
import java.time.Instant;
import java.util.List;

/**
 * Application-facing chat response. {@code answerText} through {@code generatedSql} mirror
 * {@code CoPilotResponse} in ai/contracts.py (Person 3, P3.1, frozen Day 1) field-for-field
 * — that part is NOT to be changed without Person 3's sign-off. {@code promisedDeliveryDate}
 * / {@code revisedDeliveryDate} and {@code agentsInvoked} / {@code generatedSql} were
 * originally provisional Spring Boot-only extensions but are now part of the frozen
 * contract too (ai/contracts.py CoPilotResponse, ai/CONTRACTS.md §8 changelog).
 *
 * {@code traceId}/{@code sessionId}/{@code timestamp}/{@code warnings} are Spring Boot's
 * own application-layer envelope, added here since Person 1 owns the app-facing contract.
 *
 * {@code agentsInvoked}/{@code generatedSql} exist on this DTO (not just AuditEntryDto)
 * because {@link com.nexchain.backend.audit.service.AuditService#record} builds the audit
 * entry from the same ChatResponse instance ChatController already has in hand — see that
 * class's docstring.
 */
public record ChatResponse(
        String traceId,
        String sessionId,
        Instant timestamp,
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
        List<String> warnings,
        String error,
        List<String> agentsInvoked,
        String generatedSql) {}

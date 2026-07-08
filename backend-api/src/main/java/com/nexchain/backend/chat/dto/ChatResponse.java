package com.nexchain.backend.chat.dto;

import com.nexchain.backend.common.dto.SlaStatus;
import com.nexchain.backend.common.dto.SourceDto;
import java.time.Instant;
import java.util.List;

/**
 * Application-facing chat response. {@code answerText} through {@code error} mirror
 * {@code CoPilotResponse} in ai/contracts.py (Person 3, P3.1, frozen Day 1) field-for-field
 * — that part is NOT to be changed without Person 3's sign-off.
 *
 * {@code traceId}/{@code sessionId}/{@code timestamp}/{@code warnings} are Spring Boot's
 * own application-layer envelope, added here since Person 1 owns the app-facing contract.
 *
 * PROVISIONAL EXTENSION (requires Person 3 approval — see docs/api_contracts.md):
 * {@code promisedDeliveryDate} and {@code revisedDeliveryDate} are NOT present in the
 * current ai/contracts.py CoPilotResponse, but docs/04_ui_ux_design.md Section 3.2's
 * Impact table and the flagship sample in docs/problem_statement.md Section 7 both
 * require them. Added here so Angular has somewhere to render them; flagged for the
 * team to fold back into the frozen Python contract.
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
        String error) {}

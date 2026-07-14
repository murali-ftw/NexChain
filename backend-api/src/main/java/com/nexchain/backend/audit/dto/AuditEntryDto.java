package com.nexchain.backend.audit.dto;

import com.nexchain.backend.common.dto.SlaStatus;
import com.nexchain.backend.common.dto.SourceDto;
import java.time.Instant;
import java.util.List;

/**
 * Mirrors the audit_log table columns in docs/06_backend_schema.md Section 2.14, plus
 * {@code warnings} (P1.8) — Spring Boot's own envelope field (same as {@code ChatResponse
 * .warnings()}, not part of Person 2's schema), surfaced here because it's already real
 * data available at record time and the Day 8 task explicitly asks the audit view to show
 * warnings when available.
 */
public record AuditEntryDto(
        long auditId,
        String traceId,
        String sessionId,
        Instant timestamp,
        String user,
        String rawQuestion,
        List<String> detectedIntent,
        List<String> agentsInvoked,
        String generatedSql,
        List<ApiCallDto> apiCalls,
        List<SourceDto> kbSources,
        SlaStatus slaResult,
        String status,
        List<String> warnings) {}

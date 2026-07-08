package com.nexchain.backend.audit.dto;

import com.nexchain.backend.common.dto.SlaStatus;
import com.nexchain.backend.common.dto.SourceDto;
import java.time.Instant;
import java.util.List;

/** Mirrors the audit_log table columns in docs/06_backend_schema.md Section 2.14. */
public record AuditEntryDto(
        long auditId,
        String traceId,
        Instant timestamp,
        String user,
        String rawQuestion,
        List<String> detectedIntent,
        List<String> agentsInvoked,
        String generatedSql,
        List<ApiCallDto> apiCalls,
        List<SourceDto> kbSources,
        SlaStatus slaResult,
        String status) {}

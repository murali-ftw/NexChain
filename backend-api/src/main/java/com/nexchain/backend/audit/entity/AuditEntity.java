package com.nexchain.backend.audit.entity;

import com.nexchain.backend.audit.dto.ApiCallDto;
import com.nexchain.backend.common.dto.SlaStatus;
import com.nexchain.backend.common.dto.SourceDto;
import jakarta.persistence.Column;
import jakarta.persistence.Convert;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Lob;
import jakarta.persistence.Table;
import java.time.Instant;
import java.util.List;

/**
 * JPA-persisted audit entry (P1.8), field-for-field matching {@code AuditEntryDto} /
 * Person 2's {@code audit_log} table shape (docs/06_backend_schema.md §2.14). Lives in
 * backend-api's own H2 database (the same one Query History already uses, P1.7) rather
 * than the real Postgres {@code audit_log} table: that table's {@code user_id} column has
 * a hard foreign key to {@code users}, and Spring Boot's auth still runs on
 * {@link com.nexchain.backend.auth.user.InMemoryUserStore} rather than real rows in
 * Postgres's {@code users} table — so nothing today could satisfy that constraint without
 * duplicating the real source of truth. This entity is a drop-in swap once auth itself
 * moves to real persistence.
 *
 * Unlike conversation history, every chat call inserts one independent new row here — there
 * is no shared mutable row to race on, so (unlike {@code ConversationHistoryStore}) no
 * per-key locking is needed for correctness under concurrency.
 */
@Entity
@Table(name = "audit_entries")
public class AuditEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long auditId;

    @Column(nullable = false)
    private String traceId;

    @Column(nullable = false)
    private String userEmail;

    @Column(nullable = false)
    private String sessionId;

    @Lob
    @Column(nullable = false)
    private String rawQuestion;

    @Lob
    @Column(nullable = false)
    @Convert(converter = StringListConverter.class)
    private List<String> detectedIntent;

    @Lob
    @Column(nullable = false)
    @Convert(converter = StringListConverter.class)
    private List<String> agentsInvoked;

    @Lob
    private String generatedSql;

    @Lob
    @Column(nullable = false)
    @Convert(converter = ApiCallListConverter.class)
    private List<ApiCallDto> apiCalls;

    @Lob
    @Column(nullable = false)
    @Convert(converter = SourceListConverter.class)
    private List<SourceDto> kbSources;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private SlaStatus slaResult;

    @Column(nullable = false)
    private String status;

    @Lob
    @Column(nullable = false)
    @Convert(converter = StringListConverter.class)
    private List<String> warnings;

    @Column(nullable = false)
    private Instant createdAt;

    protected AuditEntity() {
        // JPA
    }

    public AuditEntity(
            String traceId,
            String userEmail,
            String sessionId,
            String rawQuestion,
            List<String> detectedIntent,
            List<String> agentsInvoked,
            String generatedSql,
            List<ApiCallDto> apiCalls,
            List<SourceDto> kbSources,
            SlaStatus slaResult,
            String status,
            List<String> warnings,
            Instant createdAt) {
        this.traceId = traceId;
        this.userEmail = userEmail;
        this.sessionId = sessionId;
        this.rawQuestion = rawQuestion;
        this.detectedIntent = detectedIntent;
        this.agentsInvoked = agentsInvoked;
        this.generatedSql = generatedSql;
        this.apiCalls = apiCalls;
        this.kbSources = kbSources;
        this.slaResult = slaResult;
        this.status = status;
        this.warnings = warnings;
        this.createdAt = createdAt;
    }

    public Long getAuditId() {
        return auditId;
    }

    public String getTraceId() {
        return traceId;
    }

    public String getUserEmail() {
        return userEmail;
    }

    public String getSessionId() {
        return sessionId;
    }

    public String getRawQuestion() {
        return rawQuestion;
    }

    public List<String> getDetectedIntent() {
        return detectedIntent;
    }

    public List<String> getAgentsInvoked() {
        return agentsInvoked;
    }

    public String getGeneratedSql() {
        return generatedSql;
    }

    public List<ApiCallDto> getApiCalls() {
        return apiCalls;
    }

    public List<SourceDto> getKbSources() {
        return kbSources;
    }

    public SlaStatus getSlaResult() {
        return slaResult;
    }

    public String getStatus() {
        return status;
    }

    public List<String> getWarnings() {
        return warnings;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }
}

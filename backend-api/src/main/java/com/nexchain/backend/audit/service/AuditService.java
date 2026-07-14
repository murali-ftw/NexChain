package com.nexchain.backend.audit.service;

import com.nexchain.backend.audit.dto.AuditEntryDto;
import com.nexchain.backend.audit.entity.AuditEntity;
import com.nexchain.backend.audit.exception.AuditEntryNotFoundException;
import com.nexchain.backend.audit.store.AuditRepository;
import com.nexchain.backend.auth.user.UserStore;
import com.nexchain.backend.chat.dto.ChatResponse;
import java.time.Instant;
import java.util.List;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;

/** P1.8: real audit persistence, backed by {@link AuditRepository}. Replaces the Day 4
 * fixed 2-record mock. */
@Service
public class AuditService {

    private final AuditRepository repository;
    private final UserStore userStore;

    public AuditService(AuditRepository repository, UserStore userStore) {
        this.repository = repository;
        this.userStore = userStore;
    }

    /** Called by {@code ChatController} after every successful /api/chat response — the
     * chat pipeline is still a Day 4 mock (no real intent classifier, agents, SQL
     * generation, or tool calls — that's P2.10/P3), so {@code agentsInvoked},
     * {@code generatedSql}, and {@code apiCalls} are empty/null: there is nothing real
     * to report there yet. {@code detectedIntent} and {@code kbSources} are populated
     * from what the response actually carries. */
    public void record(String userEmail, String sessionId, String rawQuestion, ChatResponse response) {
        String displayUser = userStore.findByEmail(userEmail).map(u -> u.username()).orElse(userEmail);
        AuditEntity entity =
                new AuditEntity(
                        response.traceId(),
                        displayUser,
                        sessionId,
                        rawQuestion,
                        List.of(response.intent().name()),
                        List.of(),
                        null,
                        List.of(),
                        response.sources(),
                        response.slaStatus(),
                        deriveStatus(response),
                        response.warnings(),
                        Instant.now());
        repository.save(entity);
    }

    /** Global audit view — see {@code AuditRepository}: not scoped per requesting user. */
    public List<AuditEntryDto> getAuditLog() {
        return repository.findAllByOrderByCreatedAtDesc().stream().map(this::toDto).toList();
    }

    /** One page of the global audit log, most recently created first. */
    public List<AuditEntryDto> getAuditLog(int page, int size) {
        return repository.findAllByOrderByCreatedAtDesc(PageRequest.of(page, size)).stream()
                .map(this::toDto)
                .toList();
    }

    public long countAuditLog() {
        return repository.count();
    }

    public AuditEntryDto getAuditEntry(long auditId) {
        AuditEntity entity = repository.findById(auditId).orElseThrow(() -> new AuditEntryNotFoundException(auditId));
        return toDto(entity);
    }

    private String deriveStatus(ChatResponse response) {
        if (response.error() != null) {
            return "ERROR";
        }
        if (response.partial()) {
            return "PARTIAL";
        }
        return "SUCCESS";
    }

    private AuditEntryDto toDto(AuditEntity entity) {
        return new AuditEntryDto(
                entity.getAuditId(),
                entity.getTraceId(),
                entity.getSessionId(),
                entity.getCreatedAt(),
                entity.getUserEmail(),
                entity.getRawQuestion(),
                entity.getDetectedIntent(),
                entity.getAgentsInvoked(),
                entity.getGeneratedSql(),
                entity.getApiCalls(),
                entity.getKbSources(),
                entity.getSlaResult(),
                entity.getStatus(),
                entity.getWarnings());
    }
}

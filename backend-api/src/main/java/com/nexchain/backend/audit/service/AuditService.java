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

    /** Called by {@code ChatController} after every successful /api/chat response.
     * {@code agentsInvoked} and {@code generatedSql} come straight from the response
     * (ai/contracts.py CoPilotResponse carries both — see ChatResponse's docstring);
     * {@code apiCalls} stays empty because no wire field for it exists anywhere
     * upstream yet, unlike those two. {@code detectedIntent} and {@code kbSources}
     * are populated from what the response actually carries. */
    public void record(String userEmail, String sessionId, String rawQuestion, ChatResponse response) {
        String displayUser = userStore.findByEmail(userEmail).map(u -> u.username()).orElse(userEmail);
        AuditEntity entity =
                new AuditEntity(
                        response.traceId(),
                        displayUser,
                        sessionId,
                        rawQuestion,
                        List.of(response.intent().name()),
                        response.agentsInvoked(),
                        response.generatedSql(),
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

package com.nexchain.backend.history.store;

import com.nexchain.backend.chat.dto.ChatResponse;
import com.nexchain.backend.history.dto.ConversationTurnDto;
import com.nexchain.backend.history.entity.ConversationEntity;
import com.nexchain.backend.history.model.ConversationRecord;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Component;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.transaction.support.TransactionTemplate;

/**
 * Per-user conversation history (P1.7), backed by {@link ConversationHistoryRepository} —
 * a file-based H2 database owned entirely by backend-api, so history now survives a
 * restart. Person 2's frozen schema (docs/06_backend_schema.md) still has no
 * conversation/session table of its own; this doesn't touch it or the shared
 * `nexchain` Postgres database at all.
 *
 * Keyed by session id so a conversation grows in place across turns rather than
 * creating a new history entry per message ("no duplicate sessions").
 */
@Component
public class ConversationHistoryStore {

    private final ConversationHistoryRepository repository;
    private final TransactionTemplate transactionTemplate;

    /**
     * One monitor per session id, so concurrent turns for the same session serialize
     * instead of racing on find-then-save (a bug found during audit: two concurrent
     * requests to the same session could each read the row before the other's write
     * committed, and the second save silently overwrote the first's turn — 9 of 10
     * concurrent messages to one session were lost before this fix). Turns for
     * different sessions still run fully in parallel. This is a single-JVM, in-process
     * lock — correct because this store backs one H2 file owned by one backend-api
     * instance, not a clustered deployment; the map only grows (one entry per session
     * ever created), an acceptable tradeoff at this project's scale.
     */
    private final ConcurrentHashMap<String, Object> sessionLocks = new ConcurrentHashMap<>();

    public ConversationHistoryStore(ConversationHistoryRepository repository, PlatformTransactionManager transactionManager) {
        this.repository = repository;
        // A plain @Transactional method commits only after the method returns (the AOP
        // proxy commits around the call) — a `synchronized` block *inside* the method
        // releases before that commit happens, so a second thread can still read stale
        // data. TransactionTemplate commits synchronously inside the call, so wrapping it
        // in the synchronized block below means the lock isn't released until the write
        // is actually durable — this is what actually closed the race, verified live
        // (10/10 concurrent turns to one session now persist; the @Transactional-only
        // version still lost turns under load).
        this.transactionTemplate = new TransactionTemplate(transactionManager);
    }

    public void recordTurn(String userEmail, String sessionId, String question, ChatResponse response) {
        Object lock = sessionLocks.computeIfAbsent(sessionId, id -> new Object());
        synchronized (lock) {
            transactionTemplate.executeWithoutResult(status -> {
                var turn = new ConversationTurnDto(question, response, Instant.now());
                ConversationEntity entity =
                        repository.findById(sessionId).orElseGet(() -> new ConversationEntity(sessionId, userEmail));
                entity.addTurn(turn);
                repository.save(entity);
            });
        }
    }

    /** Every one of the user's conversations, most recently updated first — unbounded, for
     * callers (like the frontend's client-side search) that need the full set. */
    public List<ConversationRecord> forUser(String userEmail) {
        return repository.findByUserEmailOrderByLastUpdatedDesc(userEmail).stream().map(this::toRecord).toList();
    }

    /** One page of the user's conversations, most recently updated first (P1.7 rectification). */
    public List<ConversationRecord> forUser(String userEmail, int page, int size) {
        return repository.findByUserEmailOrderByLastUpdatedDesc(userEmail, PageRequest.of(page, size)).stream()
                .map(this::toRecord)
                .toList();
    }

    public long countForUser(String userEmail) {
        return repository.countByUserEmail(userEmail);
    }

    /**
     * Empty if the id doesn't exist OR belongs to a different user — the caller (see
     * {@code HistoryService}) can't tell those two cases apart, so a request for someone
     * else's conversation 404s exactly like a request for a nonexistent one.
     */
    public Optional<ConversationRecord> get(String userEmail, String sessionId) {
        return repository.findById(sessionId).filter(e -> e.getUserEmail().equals(userEmail)).map(this::toRecord);
    }

    @Transactional
    public boolean delete(String userEmail, String sessionId) {
        return repository
                .findById(sessionId)
                .filter(e -> e.getUserEmail().equals(userEmail))
                .map(e -> {
                    repository.delete(e);
                    return true;
                })
                .orElse(false);
    }

    /** Test-only hygiene: each smoke-test method should see a clean store, not another test's history. */
    @Transactional
    public void clear() {
        repository.deleteAll();
    }

    private ConversationRecord toRecord(ConversationEntity entity) {
        return new ConversationRecord(entity.getSessionId(), entity.getUserEmail(), entity.getTurns());
    }
}

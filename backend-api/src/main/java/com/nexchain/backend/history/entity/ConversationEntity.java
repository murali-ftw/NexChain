package com.nexchain.backend.history.entity;

import com.nexchain.backend.history.dto.ConversationTurnDto;
import jakarta.persistence.Column;
import jakarta.persistence.Convert;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Lob;
import jakarta.persistence.Table;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;

/**
 * JPA-persisted conversation thread, keyed by session id (P1.7 rectification — replaces
 * the process-local {@code ConcurrentHashMap} store so history survives a restart).
 * Lives in backend-api's own file-backed H2 database, not Person 2's shared Postgres.
 */
@Entity
@Table(name = "conversation_history")
public class ConversationEntity {

    @Id
    private String sessionId;

    @Column(nullable = false)
    private String userEmail;

    @Lob
    @Column(nullable = false)
    @Convert(converter = ConversationTurnsConverter.class)
    private List<ConversationTurnDto> turns = new ArrayList<>();

    @Column(nullable = false)
    private Instant lastUpdated;

    protected ConversationEntity() {
        // JPA
    }

    public ConversationEntity(String sessionId, String userEmail) {
        this.sessionId = sessionId;
        this.userEmail = userEmail;
    }

    public void addTurn(ConversationTurnDto turn) {
        turns.add(turn);
        lastUpdated = turn.timestamp();
    }

    public String getSessionId() {
        return sessionId;
    }

    public String getUserEmail() {
        return userEmail;
    }

    public List<ConversationTurnDto> getTurns() {
        return turns;
    }

    public Instant getLastUpdated() {
        return lastUpdated;
    }
}

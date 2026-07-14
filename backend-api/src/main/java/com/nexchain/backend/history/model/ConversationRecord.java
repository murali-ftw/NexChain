package com.nexchain.backend.history.model;

import com.nexchain.backend.history.dto.ConversationTurnDto;
import java.time.Instant;
import java.util.List;

/**
 * One authenticated user's conversation thread, keyed by session id. Internal only —
 * never serialized directly; {@code HistoryService} maps this to {@code HistoryItemDto}
 * / {@code HistoryDetailDto} for the wire.
 */
public record ConversationRecord(String sessionId, String userEmail, List<ConversationTurnDto> turns) {

    public String firstQuestion() {
        return turns.get(0).question();
    }

    public ConversationTurnDto lastTurn() {
        return turns.get(turns.size() - 1);
    }

    public Instant lastUpdated() {
        return lastTurn().timestamp();
    }
}

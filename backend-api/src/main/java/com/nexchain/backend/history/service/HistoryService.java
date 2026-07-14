package com.nexchain.backend.history.service;

import com.nexchain.backend.chat.dto.ChatResponse;
import com.nexchain.backend.history.dto.HistoryDetailDto;
import com.nexchain.backend.history.dto.HistoryItemDto;
import com.nexchain.backend.history.exception.HistoryNotFoundException;
import com.nexchain.backend.history.model.ConversationRecord;
import com.nexchain.backend.history.store.ConversationHistoryStore;
import java.util.List;
import org.springframework.stereotype.Service;

/** P1.7: real per-user conversation history, backed by {@link ConversationHistoryStore}. */
@Service
public class HistoryService {

    private final ConversationHistoryStore store;

    public HistoryService(ConversationHistoryStore store) {
        this.store = store;
    }

    /** Called by {@code ChatController} after every successful /api/chat response — the
     * "automatic" part of automatic history updates. Same session id twice updates the
     * same conversation instead of creating a second one. */
    public void record(String userEmail, String sessionId, String question, ChatResponse response) {
        store.recordTurn(userEmail, sessionId, question, response);
    }

    public List<HistoryItemDto> getHistory(String userEmail) {
        return store.forUser(userEmail).stream().map(this::toItemDto).toList();
    }

    /** P1.7 rectification: one page of the user's conversations, most recently updated first. */
    public List<HistoryItemDto> getHistory(String userEmail, int page, int size) {
        return store.forUser(userEmail, page, size).stream().map(this::toItemDto).toList();
    }

    public long countHistory(String userEmail) {
        return store.countForUser(userEmail);
    }

    public HistoryDetailDto getDetail(String userEmail, String sessionId) {
        ConversationRecord record =
                store.get(userEmail, sessionId).orElseThrow(() -> new HistoryNotFoundException(sessionId));
        return new HistoryDetailDto(record.sessionId(), record.sessionId(), record.turns());
    }

    public void delete(String userEmail, String sessionId) {
        if (!store.delete(userEmail, sessionId)) {
            throw new HistoryNotFoundException(sessionId);
        }
    }

    private HistoryItemDto toItemDto(ConversationRecord record) {
        return new HistoryItemDto(
                record.sessionId(),
                record.firstQuestion(),
                record.lastTurn().response().answerText(),
                record.lastUpdated(),
                record.sessionId());
    }
}

package com.nexchain.backend.history.dto;

import java.util.List;

/**
 * Full conversation thread for restoring a history item — every turn in order, so the
 * frontend can replay the whole thread and continue it under the same session id.
 */
public record HistoryDetailDto(String id, String sessionId, List<ConversationTurnDto> turns) {}

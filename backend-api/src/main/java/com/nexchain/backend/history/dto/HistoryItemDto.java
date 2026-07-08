package com.nexchain.backend.history.dto;

import java.time.Instant;

public record HistoryItemDto(String id, String question, String answerSummary, Instant timestamp, String sessionId) {}

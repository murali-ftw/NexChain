package com.nexchain.backend.history.dto;

import com.nexchain.backend.chat.dto.ChatResponse;
import java.time.Instant;

/** One question/answer turn within a conversation — the unit persisted per successful /api/chat call. */
public record ConversationTurnDto(String question, ChatResponse response, Instant timestamp) {}

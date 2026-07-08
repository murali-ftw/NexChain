package com.nexchain.backend.chat.dto;

import jakarta.validation.constraints.NotBlank;

public record ChatRequest(@NotBlank(message = "query must not be blank") String query, String sessionId) {}

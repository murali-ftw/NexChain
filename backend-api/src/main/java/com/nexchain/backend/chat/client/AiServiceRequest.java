package com.nexchain.backend.chat.client;

/**
 * Body of {@code POST /ai/query} (ai_service/schemas.py AiQueryRequest) —
 * camelCase on the wire, matching Person 2's Pydantic alias generator.
 */
public record AiServiceRequest(String query, String sessionId, String traceId, String userId) {}

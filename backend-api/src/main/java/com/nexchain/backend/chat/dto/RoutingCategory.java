package com.nexchain.backend.chat.dto;

/**
 * Mirrors {@code RoutingCategory} in ai/contracts.py (Person 3, P3.1, frozen Day 1)
 * exactly — same four values, same names. Enum constant names already match the
 * wire strings Person 3 uses, so no custom Jackson (de)serializer is needed.
 */
public enum RoutingCategory {
    KNOWLEDGE_QUERY,
    DATABASE_QUERY,
    API_QUERY,
    MULTI_TOOL_QUERY
}

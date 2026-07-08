package com.nexchain.backend.common.dto;

/**
 * A citation surfaced to the user. Mirrors {@code Source} in ai/contracts.py
 * (Person 3, P3.1, frozen Day 1) so the same shape can flow straight through
 * once Spring Boot forwards to Person 2/3's real AI service.
 */
public record SourceDto(String documentName, String snippet, Integer docId, Double score) {}

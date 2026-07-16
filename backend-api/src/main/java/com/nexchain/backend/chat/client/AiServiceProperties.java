package com.nexchain.backend.chat.client;

import org.springframework.boot.context.properties.ConfigurationProperties;

/**
 * Binds {@code ai.service.*} (application.yml) — the base URL and timeouts
 * for calling Person 2's FastAPI service. Connect/read timeouts are split
 * because a slow-to-establish connection (service down/unreachable) and a
 * slow-to-answer one (graph mid-run) are different failure shapes worth
 * different budgets — read has to cover a full LangGraph invocation
 * (several sequential LLM/tool calls), connect does not.
 */
@ConfigurationProperties(prefix = "ai.service")
public record AiServiceProperties(String baseUrl, int connectTimeoutMs, int readTimeoutMs) {

    public AiServiceProperties {
        if (baseUrl == null || baseUrl.isBlank()) {
            baseUrl = "http://localhost:8001";
        }
        if (connectTimeoutMs <= 0) {
            connectTimeoutMs = 3000;
        }
        if (readTimeoutMs <= 0) {
            readTimeoutMs = 35000;
        }
    }
}

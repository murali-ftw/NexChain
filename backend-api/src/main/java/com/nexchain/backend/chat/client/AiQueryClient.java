package com.nexchain.backend.chat.client;

/**
 * Spring Boot's side of the {@code POST /ai/query} contract with Person 2's
 * FastAPI service (docs/api_contracts.md "Spring Boot → FastAPI"). An
 * interface, not a concrete class, so tests can substitute a fake without a
 * live ai_service + Postgres + LLM key — see {@code FakeAiQueryClient} in
 * the test sources.
 */
public interface AiQueryClient {

    /**
     * @param query the user's natural-language question
     * @param sessionId conversation session id, threaded through unchanged
     * @param traceId correlation id, threaded through unchanged (tech-req §9)
     * @param userId authenticated caller's username (Authentication#getName())
     * @return never null; failures are reported via {@link AiQueryResult#partial()}
     *     and {@link AiQueryResult#error()}, never a thrown exception — this method
     *     is the one place that translates "FastAPI is down/slow/erroring" into a
     *     value ChatService can hand straight to the user.
     */
    AiQueryResult query(String query, String sessionId, String traceId, String userId);
}

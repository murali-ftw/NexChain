package com.nexchain.backend.chat.client;

import com.nexchain.backend.chat.dto.RoutingCategory;
import com.nexchain.backend.common.dto.SlaStatus;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.client.HttpStatusCodeException;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestClient;

/**
 * The real {@link AiQueryClient}: {@code POST /ai/query} against Person 2's
 * FastAPI service (docs/api_contracts.md "Spring Boot → FastAPI").
 *
 * <p>Per that contract, FastAPI returns a non-200 on failure and Spring Boot
 * "maps that to a ChatResponse with partial: true and a populated warnings
 * entry, never a raw 5xx passthrough to Angular" — every failure mode below
 * (unreachable service, timeout, non-2xx, malformed body) is caught here and
 * turned into a degraded {@link AiQueryResult} rather than a thrown
 * exception, so {@code ChatService} never needs its own try/catch.
 */
public class RestClientAiQueryClient implements AiQueryClient {

    private static final Logger log = LoggerFactory.getLogger(RestClientAiQueryClient.class);

    private static final String UNAVAILABLE_ANSWER =
            "The AI service is temporarily unavailable. Please try again in a moment.";

    private final RestClient restClient;

    public RestClientAiQueryClient(RestClient restClient) {
        this.restClient = restClient;
    }

    @Override
    public AiQueryResult query(String query, String sessionId, String traceId, String userId) {
        long startedAtMs = System.currentTimeMillis();
        try {
            AiServiceResponse body = restClient
                    .post()
                    .uri("/ai/query")
                    .body(new AiServiceRequest(query, sessionId, traceId, userId))
                    .retrieve()
                    .body(AiServiceResponse.class);
            long durationMs = System.currentTimeMillis() - startedAtMs;
            if (body == null) {
                log.warn("ai_service traceId={} duration_ms={} returned an empty body", traceId, durationMs);
                return degraded("AI service returned an empty response");
            }
            log.info(
                    "dependency_call dependency=ai_service traceId={} duration_ms={} outcome=success partial={}",
                    traceId,
                    durationMs,
                    body.partial());
            return new AiQueryResult(
                    body.answerText(),
                    body.intent(),
                    body.orderStatus(),
                    body.shipmentStatus(),
                    body.currentLocation(),
                    body.delayReason(),
                    body.promisedDeliveryDate(),
                    body.revisedDeliveryDate(),
                    body.delayDays(),
                    body.slaStatus(),
                    body.recommendedActions() != null ? body.recommendedActions() : List.of(),
                    body.sources() != null ? body.sources() : List.of(),
                    body.partial(),
                    body.error(),
                    body.agentsInvoked() != null ? body.agentsInvoked() : List.of(),
                    body.generatedSql());
        } catch (HttpStatusCodeException ex) {
            long durationMs = System.currentTimeMillis() - startedAtMs;
            log.warn(
                    "dependency_call dependency=ai_service traceId={} duration_ms={} outcome=failure "
                            + "status={} error_type={} detail={}",
                    traceId,
                    durationMs,
                    ex.getStatusCode().value(),
                    ex.getClass().getSimpleName(),
                    ex.getResponseBodyAsString());
            return degraded("AI service error (%s): %s".formatted(ex.getStatusCode().value(), detailFrom(ex)));
        } catch (ResourceAccessException ex) {
            // Connection refused, DNS failure, or a read that exceeded readTimeoutMs
            // (AiServiceProperties) — the service is down, unreachable, or too slow.
            // ex.getMessage() (internal hostnames/ports) is logged, not returned to the
            // client — the warnings field is user-facing (Day 13 QA hardening).
            long durationMs = System.currentTimeMillis() - startedAtMs;
            log.warn(
                    "dependency_call dependency=ai_service traceId={} duration_ms={} outcome=failure "
                            + "error_type={} detail={}",
                    traceId,
                    durationMs,
                    ex.getClass().getSimpleName(),
                    ex.getMessage());
            return degraded("AI service is unreachable or timed out.");
        } catch (Exception ex) {
            long durationMs = System.currentTimeMillis() - startedAtMs;
            log.error(
                    "dependency_call dependency=ai_service traceId={} duration_ms={} outcome=failure "
                            + "error_type={} unexpected failure",
                    traceId,
                    durationMs,
                    ex.getClass().getSimpleName(),
                    ex);
            return degraded("AI service call failed.");
        }
    }

    private String detailFrom(HttpStatusCodeException ex) {
        String body = ex.getResponseBodyAsString();
        return (body == null || body.isBlank()) ? ex.getStatusText() : body;
    }

    private AiQueryResult degraded(String error) {
        return new AiQueryResult(
                UNAVAILABLE_ANSWER,
                RoutingCategory.DATABASE_QUERY,
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                SlaStatus.NOT_APPLICABLE,
                List.of(),
                List.of(),
                true,
                error,
                List.of(),
                null);
    }
}

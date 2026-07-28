package com.nexchain.backend.config;

import com.nexchain.backend.chat.client.AiQueryClient;
import com.nexchain.backend.chat.client.AiServiceProperties;
import com.nexchain.backend.chat.client.RestClientAiQueryClient;
import com.nexchain.backend.common.logging.RequestCorrelationFilter;
import org.slf4j.MDC;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.client.RestClient;

/**
 * Wires the real {@link AiQueryClient} — a {@link RestClient} pointed at
 * Person 2's FastAPI service, with the connect/read timeouts from {@code
 * ai.service.*} (application.yml). Read timeout is generous (default 35s)
 * because a full LangGraph invocation can chain several sequential LLM/tool
 * calls (P1.10 flagship: text-to-sql + api-status + knowledge-base +
 * business-rule, each with its own retry budget).
 *
 * <p>Every outbound call also carries the current request's {@code
 * X-Request-ID} (set by {@link RequestCorrelationFilter}), so ai_service's
 * own logs and Spring Boot's logs for the same request share one id even
 * before either side reads the {@code traceId} JSON field.
 */
@Configuration
@EnableConfigurationProperties(AiServiceProperties.class)
public class AiServiceConfig {

    @Bean
    public AiQueryClient aiQueryClient(AiServiceProperties properties) {
        SimpleClientHttpRequestFactory requestFactory = new SimpleClientHttpRequestFactory();
        requestFactory.setConnectTimeout(properties.connectTimeoutMs());
        requestFactory.setReadTimeout(properties.readTimeoutMs());

        RestClient restClient =
                RestClient.builder()
                        .baseUrl(properties.baseUrl())
                        .requestFactory(requestFactory)
                        .requestInterceptor((request, body, execution) -> {
                            String requestId = MDC.get(RequestCorrelationFilter.MDC_REQUEST_ID);
                            if (requestId != null) {
                                request.getHeaders().set(RequestCorrelationFilter.REQUEST_ID_HEADER, requestId);
                            }
                            return execution.execute(request, body);
                        })
                        .build();
        return new RestClientAiQueryClient(restClient);
    }
}

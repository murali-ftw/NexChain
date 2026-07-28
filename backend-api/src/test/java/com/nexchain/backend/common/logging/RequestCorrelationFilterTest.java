package com.nexchain.backend.common.logging;

import static org.assertj.core.api.Assertions.assertThat;

import jakarta.servlet.FilterChain;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;

/**
 * Unit-level coverage for the filter that resolves and echoes back the
 * request's correlation id (RC logging hardening) — no Spring context needed,
 * same lightweight style as {@code RestClientAiQueryClientTest}.
 */
class RequestCorrelationFilterTest {

    private final RequestCorrelationFilter filter = new RequestCorrelationFilter();

    @Test
    void missingRequestIdIsMintedAndReturnedInResponseHeader() throws Exception {
        MockHttpServletRequest request = new MockHttpServletRequest("GET", "/api/health");
        MockHttpServletResponse response = new MockHttpServletResponse();
        FilterChain chain = (req, res) -> {};

        filter.doFilter(request, response, chain);

        String requestId = response.getHeader(RequestCorrelationFilter.REQUEST_ID_HEADER);
        assertThat(requestId).isNotBlank();
    }

    @Test
    void suppliedXRequestIdIsEchoedBackUnchanged() throws Exception {
        MockHttpServletRequest request = new MockHttpServletRequest("GET", "/api/health");
        request.addHeader(RequestCorrelationFilter.REQUEST_ID_HEADER, "caller-supplied-id-123");
        MockHttpServletResponse response = new MockHttpServletResponse();
        FilterChain chain = (req, res) -> {};

        filter.doFilter(request, response, chain);

        assertThat(response.getHeader(RequestCorrelationFilter.REQUEST_ID_HEADER))
                .isEqualTo("caller-supplied-id-123");
    }

    @Test
    void suppliedXCorrelationIdIsAcceptedWhenXRequestIdIsAbsent() throws Exception {
        MockHttpServletRequest request = new MockHttpServletRequest("GET", "/api/health");
        request.addHeader("X-Correlation-ID", "correlation-id-456");
        MockHttpServletResponse response = new MockHttpServletResponse();
        FilterChain chain = (req, res) -> {};

        filter.doFilter(request, response, chain);

        assertThat(response.getHeader(RequestCorrelationFilter.REQUEST_ID_HEADER))
                .isEqualTo("correlation-id-456");
    }

    @Test
    void mdcIsClearedAfterTheRequestCompletes() throws Exception {
        MockHttpServletRequest request = new MockHttpServletRequest("GET", "/api/health");
        MockHttpServletResponse response = new MockHttpServletResponse();
        FilterChain chain = (req, res) -> assertThat(org.slf4j.MDC.get(RequestCorrelationFilter.MDC_REQUEST_ID))
                .isNotBlank();

        filter.doFilter(request, response, chain);

        assertThat(org.slf4j.MDC.get(RequestCorrelationFilter.MDC_REQUEST_ID)).isNull();
    }
}

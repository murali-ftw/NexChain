package com.nexchain.backend.common.logging;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.UUID;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

/**
 * First filter in the chain (see SecurityConfig): resolves the correlation id for this
 * request, makes it available to every log statement for the rest of the request via
 * MDC, echoes it back as a response header, and logs one request-summary line per call.
 *
 * <p>Accepts an inbound {@code X-Request-ID} or {@code X-Correlation-ID} header —
 * whichever a caller (Angular, a gateway, a test) supplies — or mints a fresh UUID when
 * neither is present, so every request is correlatable end to end even from an
 * unmodified client. The same value becomes {@code ChatService}'s {@code traceId}
 * (rather than a second, independent id) so the HTTP-level correlation id and the
 * AI-pipeline trace id sent to FastAPI/MCP are one and the same across the whole stack.
 *
 * <p>{@code userId} is only resolvable after the security filters below this one have
 * run, so it's read from {@link SecurityContextHolder} in the {@code finally} block
 * (after {@code chain.doFilter} returns) rather than up front.
 */
@Component
public class RequestCorrelationFilter extends OncePerRequestFilter {

    private static final Logger log = LoggerFactory.getLogger(RequestCorrelationFilter.class);

    public static final String REQUEST_ID_HEADER = "X-Request-ID";
    private static final String CORRELATION_ID_HEADER = "X-Correlation-ID";
    public static final String MDC_REQUEST_ID = "requestId";
    public static final String MDC_USER_ID = "userId";

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
            throws ServletException, IOException {
        String requestId = resolveRequestId(request);
        MDC.put(MDC_REQUEST_ID, requestId);
        response.setHeader(REQUEST_ID_HEADER, requestId);

        long startedAtMs = System.currentTimeMillis();
        try {
            filterChain.doFilter(request, response);
        } finally {
            MDC.put(MDC_USER_ID, resolveUserId());
            long durationMs = System.currentTimeMillis() - startedAtMs;
            log.info(
                    "http_request method={} path={} status={} duration_ms={}",
                    request.getMethod(),
                    request.getRequestURI(),
                    response.getStatus(),
                    durationMs);
            MDC.clear();
        }
    }

    private String resolveRequestId(HttpServletRequest request) {
        String requestId = firstNonBlank(request.getHeader(REQUEST_ID_HEADER), request.getHeader(CORRELATION_ID_HEADER));
        return requestId != null ? requestId : UUID.randomUUID().toString();
    }

    private String firstNonBlank(String... values) {
        for (String value : values) {
            if (value != null && !value.isBlank()) {
                return value;
            }
        }
        return null;
    }

    private String resolveUserId() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        return authentication != null && authentication.isAuthenticated() ? authentication.getName() : "-";
    }
}

package com.nexchain.backend.chat.client;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.method;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withServerError;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;

import java.io.IOException;
import java.net.ServerSocket;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.RestClient;

/**
 * P1.10: RestClientAiQueryClient must never let Spring Boot ChatService see a
 * thrown exception — every failure mode (non-2xx, unreachable, timeout) has
 * to come back as a degraded {@link AiQueryResult} (partial=true, error set),
 * per docs/api_contracts.md's "Spring Boot → FastAPI" error-behavior contract.
 */
class RestClientAiQueryClientTest {

    private ServerSocket blackHole;

    @AfterEach
    void closeBlackHole() throws IOException {
        if (blackHole != null && !blackHole.isClosed()) {
            blackHole.close();
        }
    }

    private RestClientAiQueryClient clientFor(RestClient.Builder builder) {
        return new RestClientAiQueryClient(builder.build());
    }

    @Test
    void successfulResponseMapsStraightThrough() {
        RestClient.Builder builder = RestClient.builder().baseUrl("http://localhost:8001");
        MockRestServiceServer server = MockRestServiceServer.bindTo(builder).build();
        server.expect(requestTo("http://localhost:8001/ai/query"))
                .andExpect(method(HttpMethod.POST))
                .andRespond(withSuccess(
                        """
                        {
                          "traceId": "t-1", "sessionId": "s-1",
                          "answerText": "Order SO-45892 is Delayed.",
                          "intent": "MULTI_TOOL_QUERY",
                          "orderStatus": "Delayed", "shipmentStatus": null,
                          "currentLocation": null, "delayReason": null,
                          "delayDays": 6, "slaStatus": "Breached",
                          "recommendedActions": ["Escalate to the Logistics Manager."],
                          "sources": [], "partial": false, "error": null,
                          "promisedDeliveryDate": "2026-07-03", "revisedDeliveryDate": "2026-07-09"
                        }
                        """,
                        MediaType.APPLICATION_JSON));

        AiQueryResult result = clientFor(builder).query("Where is SO-45892?", "s-1", "t-1", "demo-user");

        assertThat(result.answerText()).isEqualTo("Order SO-45892 is Delayed.");
        assertThat(result.delayDays()).isEqualTo(6);
        assertThat(result.partial()).isFalse();
        assertThat(result.error()).isNull();
        server.verify();
    }

    @Test
    void non200ResponseDegradesInsteadOfThrowing() {
        RestClient.Builder builder = RestClient.builder().baseUrl("http://localhost:8001");
        MockRestServiceServer server = MockRestServiceServer.bindTo(builder).build();
        server.expect(requestTo("http://localhost:8001/ai/query"))
                .andRespond(withServerError().body("{\"detail\": \"AI service error: boom\"}"));

        AiQueryResult result = clientFor(builder).query("anything", "s-1", "t-1", "demo-user");

        assertThat(result.partial()).isTrue();
        assertThat(result.error()).contains("boom");
        assertThat(result.slaStatus().wireValue()).isEqualTo("N/A");
    }

    @Test
    void unreachableServiceDegradesInsteadOfThrowing() {
        // Nothing listens on this port — connection refused.
        RestClient restClient = RestClient.builder().baseUrl("http://localhost:1").build();
        AiQueryResult result = new RestClientAiQueryClient(restClient).query("anything", "s-1", "t-1", "demo-user");

        assertThat(result.partial()).isTrue();
        assertThat(result.error()).isNotBlank();
    }

    @Test
    void slowResponseTimesOutAndDegradesInsteadOfThrowing() throws IOException, InterruptedException {
        blackHole = new ServerSocket(0);
        Thread acceptorThread = new Thread(() -> {
            try {
                // Accept the connection but never write a response — the client's
                // read timeout, not this thread, is what ends the test.
                blackHole.accept();
            } catch (IOException ignored) {
                // Expected once the test closes blackHole in @AfterEach.
            }
        });
        acceptorThread.setDaemon(true);
        acceptorThread.start();

        SimpleClientHttpRequestFactory requestFactory = new SimpleClientHttpRequestFactory();
        requestFactory.setConnectTimeout(2000);
        requestFactory.setReadTimeout(300);
        RestClient restClient = RestClient.builder()
                .baseUrl("http://localhost:" + blackHole.getLocalPort())
                .requestFactory(requestFactory)
                .build();

        AiQueryResult result = new RestClientAiQueryClient(restClient).query("anything", "s-1", "t-1", "demo-user");

        assertThat(result.partial()).isTrue();
        assertThat(result.error()).isNotBlank();
        acceptorThread.join(TimeUnit.SECONDS.toMillis(2));
    }
}

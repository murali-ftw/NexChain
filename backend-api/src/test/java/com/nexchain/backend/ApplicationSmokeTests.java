package com.nexchain.backend;

import static org.hamcrest.Matchers.hasSize;
import static org.hamcrest.Matchers.matchesPattern;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.nexchain.backend.audit.store.AuditRepository;
import com.nexchain.backend.chat.client.AiQueryClient;
import com.nexchain.backend.chat.client.FakeAiQueryClient;
import com.nexchain.backend.history.store.ConversationHistoryStore;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Import;
import org.springframework.context.annotation.Primary;
import org.springframework.http.MediaType;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;

/**
 * Day 4 completion-gate coverage (contract endpoints, chat mock scenarios, validation
 * errors) plus Day 6 (P1.6) authentication coverage: login issues a real JWT, protected
 * endpoints (/api/chat/**, /api/audit/**) reject anonymous/invalid callers and accept
 * valid ones, and public endpoints (/api/health, /api/auth/login) stay open. Plus Day 7
 * (P1.7) coverage: automatic per-user conversation history. Plus RC-stabilization
 * coverage: /api/audit/** requires the ADMIN role, not just any authenticated user.
 *
 * <p>P1.10: the chat pipeline now calls out to Person 2's real FastAPI service via
 * {@link AiQueryClient}. This class swaps in {@link FakeAiQueryClient} (same scenario
 * content the old in-process mock produced) so the full /api/chat -> history -> audit
 * pipeline is still testable without a live ai_service + Postgres + LLM key. The real
 * {@code RestClientAiQueryClient} wiring is verified separately.
 */
@SpringBootTest
@AutoConfigureMockMvc
@TestPropertySource(properties = "spring.datasource.url=jdbc:h2:mem:history-test;DB_CLOSE_DELAY=-1")
@Import(ApplicationSmokeTests.FakeAiQueryClientConfig.class)
class ApplicationSmokeTests {

    @TestConfiguration
    static class FakeAiQueryClientConfig {
        // Deliberately not named aiQueryClient(): Spring rejects two bean
        // definitions with the same name (allow-bean-definition-overriding
        // defaults to false) even with @Primary, which only breaks ties
        // between differently-named candidates of the same type.
        @Bean
        @Primary
        AiQueryClient fakeAiQueryClient() {
            return new FakeAiQueryClient();
        }
    }

    private static final String DEMO_EMAIL = "user@example.com";
    private static final String DEMO_PASSWORD = "password";
    private static final String SECOND_EMAIL = "second-user@example.com";
    private static final String SECOND_PASSWORD = "password";
    private static final String ADMIN_EMAIL = "admin@example.com";
    private static final String ADMIN_PASSWORD = "password";

    @Autowired private MockMvc mockMvc;
    @Autowired private ObjectMapper objectMapper;
    @Autowired private ConversationHistoryStore conversationHistoryStore;
    @Autowired private AuditRepository auditRepository;

    private String token;
    private String adminToken;

    @BeforeEach
    void obtainToken() throws Exception {
        // Both stores are singletons shared across every test method in this class (Spring
        // caches the context) — clear them so one test's chat calls don't leak into
        // another's history/audit assertions.
        conversationHistoryStore.clear();
        auditRepository.deleteAll();
        token = login(DEMO_EMAIL, DEMO_PASSWORD);
        adminToken = login(ADMIN_EMAIL, ADMIN_PASSWORD);
    }

    private String login(String email, String password) throws Exception {
        MvcResult result =
                mockMvc.perform(
                                post("/api/auth/login")
                                        .contentType(MediaType.APPLICATION_JSON)
                                        .content(
                                                """
                                                {"email": "%s", "password": "%s"}
                                                """
                                                        .formatted(email, password)))
                        .andExpect(status().isOk())
                        .andReturn();
        return objectMapper.readTree(result.getResponse().getContentAsString()).get("accessToken").asText();
    }

    @Test
    void healthReturnsUp() throws Exception {
        mockMvc.perform(get("/api/health"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("UP"))
                .andExpect(jsonPath("$.service").value("backend-api"));
    }

    @Test
    void chatWithFlagshipOrderReturnsFullMockScenario() throws Exception {
        mockMvc.perform(
                        post("/api/chat")
                                .header("Authorization", "Bearer " + token)
                                .contentType(MediaType.APPLICATION_JSON)
                                .content(
                                        """
                                        {"query": "Where is order SO-45892? Why is it delayed?"}
                                        """))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.intent").value("MULTI_TOOL_QUERY"))
                .andExpect(jsonPath("$.slaStatus").value("Breached"))
                .andExpect(jsonPath("$.delayDays").value(6))
                .andExpect(jsonPath("$.promisedDeliveryDate").value("2026-07-03"))
                .andExpect(jsonPath("$.revisedDeliveryDate").value("2026-07-09"))
                .andExpect(jsonPath("$.recommendedActions", hasSize(4)))
                .andExpect(jsonPath("$.sources", hasSize(1)));
    }

    @Test
    void chatWithInventoryQueryReturnsInventoryMock() throws Exception {
        mockMvc.perform(
                        post("/api/chat")
                                .header("Authorization", "Bearer " + token)
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("""
                                        {"query": "Is SKU-1001 in stock?"}
                                        """))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.intent").value("DATABASE_QUERY"))
                .andExpect(jsonPath("$.slaStatus").value("N/A"))
                .andExpect(jsonPath("$.answerText").value("SKU-1001 has 240 units available at the Chennai warehouse."));
    }

    @Test
    void chatWithSlaQueryReturnsSlaPolicyMock() throws Exception {
        mockMvc.perform(
                        post("/api/chat")
                                .header("Authorization", "Bearer " + token)
                                .contentType(MediaType.APPLICATION_JSON)
                                .content(
                                        """
                                        {"query": "What is the SLA breach escalation process?"}
                                        """))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.intent").value("KNOWLEDGE_QUERY"))
                .andExpect(jsonPath("$.sources", hasSize(2)))
                .andExpect(jsonPath("$.recommendedActions", hasSize(3)));
    }

    @Test
    void chatWithReportingQueryReturnsReportingMock() throws Exception {
        mockMvc.perform(
                        post("/api/chat")
                                .header("Authorization", "Bearer " + token)
                                .contentType(MediaType.APPLICATION_JSON)
                                .content(
                                        """
                                        {"query": "Show delayed orders from Chennai warehouse."}
                                        """))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.intent").value("DATABASE_QUERY"))
                .andExpect(jsonPath("$.answerText").value(org.hamcrest.Matchers.containsString("Chennai warehouse")));
    }

    @Test
    void chatWithUnrecognizedQueryReturnsGenericMock() throws Exception {
        mockMvc.perform(
                        post("/api/chat")
                                .header("Authorization", "Bearer " + token)
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("""
                                        {"query": "What time is it?"}
                                        """))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.slaStatus").value("N/A"))
                .andExpect(jsonPath("$.answerText").value("Mock response for: \"What time is it?\""));
    }

    @Test
    void chatRejectsBlankQuery() throws Exception {
        mockMvc.perform(
                        post("/api/chat")
                                .header("Authorization", "Bearer " + token)
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("""
                                        {"query": ""}
                                        """))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.status").value(400))
                .andExpect(jsonPath("$.path").value("/api/chat"));
    }

    @Test
    void chatRejectsMissingQuery() throws Exception {
        mockMvc.perform(
                        post("/api/chat")
                                .header("Authorization", "Bearer " + token)
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("{}"))
                .andExpect(status().isBadRequest());
    }

    @Test
    void chatRejectsMalformedJson() throws Exception {
        mockMvc.perform(
                        post("/api/chat")
                                .header("Authorization", "Bearer " + token)
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("not-json"))
                .andExpect(status().isBadRequest());
    }

    @Test
    void loginReturnsValidJwt() throws Exception {
        mockMvc.perform(
                        post("/api/auth/login")
                                .contentType(MediaType.APPLICATION_JSON)
                                .content(
                                        """
                                        {"email": "user@example.com", "password": "password"}
                                        """))
                .andExpect(status().isOk())
                // 3 base64url segments separated by dots: header.payload.signature.
                .andExpect(jsonPath("$.accessToken").value(matchesPattern("^[\\w-]+\\.[\\w-]+\\.[\\w-]+$")))
                .andExpect(jsonPath("$.tokenType").value("Bearer"))
                .andExpect(jsonPath("$.expiresIn").value(3600))
                .andExpect(jsonPath("$.user.email").value("user@example.com"))
                .andExpect(jsonPath("$.user.role").value("USER"));
    }

    @Test
    void loginRejectsInvalidEmail() throws Exception {
        mockMvc.perform(
                        post("/api/auth/login")
                                .contentType(MediaType.APPLICATION_JSON)
                                .content(
                                        """
                                        {"email": "not-an-email", "password": "password"}
                                        """))
                .andExpect(status().isBadRequest());
    }

    @Test
    void loginRejectsWrongPassword() throws Exception {
        mockMvc.perform(
                        post("/api/auth/login")
                                .contentType(MediaType.APPLICATION_JSON)
                                .content(
                                        """
                                        {"email": "user@example.com", "password": "wrong-password"}
                                        """))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.status").value(401))
                .andExpect(jsonPath("$.message").value("Invalid email or password"));
    }

    @Test
    void loginRejectsUnknownUser() throws Exception {
        mockMvc.perform(
                        post("/api/auth/login")
                                .contentType(MediaType.APPLICATION_JSON)
                                .content(
                                        """
                                        {"email": "nobody@example.com", "password": "password"}
                                        """))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.message").value("Invalid email or password"));
    }

    @Test
    void chatRejectsAnonymousRequest() throws Exception {
        mockMvc.perform(
                        post("/api/chat")
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("""
                                        {"query": "Where is order SO-45892?"}
                                        """))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.status").value(401));
    }

    @Test
    void chatRejectsInvalidToken() throws Exception {
        mockMvc.perform(
                        post("/api/chat")
                                .header("Authorization", "Bearer not-a-real-token")
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("""
                                        {"query": "Where is order SO-45892?"}
                                        """))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void historyRejectsAnonymousRequest() throws Exception {
        mockMvc.perform(get("/api/chat/history")).andExpect(status().isUnauthorized());
    }

    @Test
    void unmappedRouteReturnsCleanNotFoundForAuthenticatedCaller() throws Exception {
        mockMvc.perform(get("/api/nonexistent").header("Authorization", "Bearer " + token))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.status").value(404));
    }

    @Test
    void unmappedRouteReturnsUnauthorizedForAnonymousCaller() throws Exception {
        // Security's authorization check runs before route resolution, so an anonymous
        // caller never learns whether the path exists — same as any other protected route.
        mockMvc.perform(get("/api/nonexistent")).andExpect(status().isUnauthorized());
    }

    @Test
    void historyIsEmptyWhenUserHasNotChattedYet() throws Exception {
        mockMvc.perform(get("/api/chat/history").header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(0)))
                .andExpect(header().string("X-Total-Count", "0"));
    }

    @Test
    void historySupportsPaginationWithoutChangingTheUnpaginatedResponseShape() throws Exception {
        for (int i = 1; i <= 3; i++) {
            mockMvc.perform(
                            post("/api/chat")
                                    .header("Authorization", "Bearer " + token)
                                    .contentType(MediaType.APPLICATION_JSON)
                                    .content(
                                            """
                                            {"query": "Is SKU-1001 in stock?", "sessionId": "sess-%d"}
                                            """
                                                    .formatted(i)))
                    .andExpect(status().isOk());
        }

        // No page/size: unbounded, exactly like before pagination existed.
        mockMvc.perform(get("/api/chat/history").header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(3)))
                .andExpect(header().string("X-Total-Count", "3"));

        // page/size supplied: only that page comes back, but X-Total-Count still reports all 3.
        mockMvc.perform(
                        get("/api/chat/history")
                                .param("page", "0")
                                .param("size", "2")
                                .header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(2)))
                .andExpect(header().string("X-Total-Count", "3"));

        mockMvc.perform(
                        get("/api/chat/history")
                                .param("page", "1")
                                .param("size", "2")
                                .header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(1)));
    }

    @Test
    void historySurvivesFullTurnRoundTripThroughRealPersistence() throws Exception {
        // P1.7 rectification: this is no longer a ConcurrentHashMap — every read here goes
        // through the JPA repository and the JSON converter, proving turns actually
        // serialize/deserialize correctly through the H2-backed store, not just an
        // in-memory object reference.
        mockMvc.perform(
                        post("/api/chat")
                                .header("Authorization", "Bearer " + token)
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("""
                                        {"query": "Where is order SO-45892?", "sessionId": "sess-durable"}
                                        """))
                .andExpect(status().isOk());

        mockMvc.perform(get("/api/chat/history/sess-durable").header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.turns", hasSize(1)))
                .andExpect(jsonPath("$.turns[0].response.slaStatus").value("Breached"))
                .andExpect(jsonPath("$.turns[0].response.delayDays").value(6))
                .andExpect(jsonPath("$.turns[0].response.sources", hasSize(1)));
    }

    /** Audit fix: negative/zero/non-numeric page or size used to leak through as an
     * unhandled exception -> 500, instead of the documented 400 ErrorResponse shape. */
    @Test
    void historyRejectsInvalidPaginationParamsAsBadRequestNotServerError() throws Exception {
        mockMvc.perform(
                        get("/api/chat/history")
                                .param("page", "-1")
                                .param("size", "10")
                                .header("Authorization", "Bearer " + token))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.status").value(400));

        mockMvc.perform(
                        get("/api/chat/history")
                                .param("page", "0")
                                .param("size", "0")
                                .header("Authorization", "Bearer " + token))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.status").value(400));

        mockMvc.perform(
                        get("/api/chat/history")
                                .param("page", "abc")
                                .param("size", "10")
                                .header("Authorization", "Bearer " + token))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.status").value(400));
    }

    /** Audit fix: concurrent turns to the same session used to race on a read-then-save
     * that wasn't atomic — 9 of 10 concurrent messages were silently lost before the
     * per-session lock in ConversationHistoryStore. */
    @Test
    void concurrentTurnsToTheSameSessionAreNotLost() throws Exception {
        int turnCount = 10;
        var executor = java.util.concurrent.Executors.newFixedThreadPool(turnCount);
        var latch = new java.util.concurrent.CountDownLatch(turnCount);
        for (int i = 0; i < turnCount; i++) {
            int n = i;
            executor.submit(() -> {
                try {
                    mockMvc.perform(
                            post("/api/chat")
                                    .header("Authorization", "Bearer " + token)
                                    .contentType(MediaType.APPLICATION_JSON)
                                    .content(
                                            """
                                            {"query": "Is SKU-1001 in stock? turn-%d", "sessionId": "race-test-sess"}
                                            """
                                                    .formatted(n)));
                } catch (Exception e) {
                    throw new RuntimeException(e);
                } finally {
                    latch.countDown();
                }
            });
        }
        latch.await();
        executor.shutdown();

        mockMvc.perform(get("/api/chat/history/race-test-sess").header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.turns", hasSize(turnCount)));
    }

    @Test
    void chatAutomaticallyCreatesHistoryEntry() throws Exception {
        mockMvc.perform(
                        post("/api/chat")
                                .header("Authorization", "Bearer " + token)
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("""
                                        {"query": "Is SKU-1001 in stock?", "sessionId": "sess-1"}
                                        """))
                .andExpect(status().isOk());

        mockMvc.perform(get("/api/chat/history").header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(1)))
                .andExpect(jsonPath("$[0].id").value("sess-1"))
                .andExpect(jsonPath("$[0].sessionId").value("sess-1"))
                .andExpect(jsonPath("$[0].question").value("Is SKU-1001 in stock?"))
                .andExpect(
                        jsonPath("$[0].answerSummary")
                                .value("SKU-1001 has 240 units available at the Chennai warehouse."));
    }

    @Test
    void secondMessageInSameSessionUpdatesTheSameHistoryEntryInsteadOfDuplicating() throws Exception {
        mockMvc.perform(
                        post("/api/chat")
                                .header("Authorization", "Bearer " + token)
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("""
                                        {"query": "Is SKU-1001 in stock?", "sessionId": "sess-1"}
                                        """))
                .andExpect(status().isOk());
        mockMvc.perform(
                        post("/api/chat")
                                .header("Authorization", "Bearer " + token)
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("""
                                        {"query": "What about the SLA policy?", "sessionId": "sess-1"}
                                        """))
                .andExpect(status().isOk());

        mockMvc.perform(get("/api/chat/history").header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(1)))
                .andExpect(jsonPath("$[0].question").value("Is SKU-1001 in stock?"))
                .andExpect(
                        jsonPath("$[0].answerSummary")
                                .value(org.hamcrest.Matchers.containsString("SLA breaches are escalated")));
    }

    @Test
    void historyDetailReturnsEveryTurnForRestoration() throws Exception {
        mockMvc.perform(
                        post("/api/chat")
                                .header("Authorization", "Bearer " + token)
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("""
                                        {"query": "Is SKU-1001 in stock?", "sessionId": "sess-1"}
                                        """))
                .andExpect(status().isOk());
        mockMvc.perform(
                        post("/api/chat")
                                .header("Authorization", "Bearer " + token)
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("""
                                        {"query": "What about the SLA policy?", "sessionId": "sess-1"}
                                        """))
                .andExpect(status().isOk());

        mockMvc.perform(get("/api/chat/history/sess-1").header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.sessionId").value("sess-1"))
                .andExpect(jsonPath("$.turns", hasSize(2)))
                .andExpect(jsonPath("$.turns[0].question").value("Is SKU-1001 in stock?"))
                .andExpect(jsonPath("$.turns[1].question").value("What about the SLA policy?"))
                .andExpect(jsonPath("$.turns[1].response.intent").value("KNOWLEDGE_QUERY"));
    }

    @Test
    void historyDetailRejectsUnknownId() throws Exception {
        mockMvc.perform(get("/api/chat/history/no-such-session").header("Authorization", "Bearer " + token))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.status").value(404));
    }

    @Test
    void historyDetailRejectsAnotherUsersConversation() throws Exception {
        mockMvc.perform(
                        post("/api/chat")
                                .header("Authorization", "Bearer " + token)
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("""
                                        {"query": "Is SKU-1001 in stock?", "sessionId": "sess-1"}
                                        """))
                .andExpect(status().isOk());

        String otherToken = login(SECOND_EMAIL, SECOND_PASSWORD);
        mockMvc.perform(get("/api/chat/history/sess-1").header("Authorization", "Bearer " + otherToken))
                .andExpect(status().isNotFound());
        mockMvc.perform(get("/api/chat/history").header("Authorization", "Bearer " + otherToken))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(0)));
    }

    @Test
    void deleteHistoryRemovesTheConversation() throws Exception {
        mockMvc.perform(
                        post("/api/chat")
                                .header("Authorization", "Bearer " + token)
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("""
                                        {"query": "Is SKU-1001 in stock?", "sessionId": "sess-1"}
                                        """))
                .andExpect(status().isOk());

        mockMvc.perform(delete("/api/chat/history/sess-1").header("Authorization", "Bearer " + token))
                .andExpect(status().isNoContent());
        mockMvc.perform(get("/api/chat/history").header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(0)));
    }

    @Test
    void deleteHistoryRejectsUnknownId() throws Exception {
        mockMvc.perform(delete("/api/chat/history/no-such-session").header("Authorization", "Bearer " + token))
                .andExpect(status().isNotFound());
    }

    @Test
    void historyDetailRejectsAnonymousRequest() throws Exception {
        mockMvc.perform(get("/api/chat/history/sess-1")).andExpect(status().isUnauthorized());
    }

    @Test
    void auditIsEmptyWhenNoOneHasChattedYet() throws Exception {
        mockMvc.perform(get("/api/audit").header("Authorization", "Bearer " + adminToken))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(0)));
    }

    @Test
    void chatAutomaticallyCreatesAnAuditEntry() throws Exception {
        mockMvc.perform(
                        post("/api/chat")
                                .header("Authorization", "Bearer " + token)
                                .contentType(MediaType.APPLICATION_JSON)
                                .content(
                                        """
                                        {"query": "Where is order SO-45892? Why is it delayed?", "sessionId": "sess-1"}
                                        """))
                .andExpect(status().isOk());

        mockMvc.perform(get("/api/audit").header("Authorization", "Bearer " + adminToken))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(1)))
                .andExpect(jsonPath("$[0].user").value("demo-user"))
                .andExpect(jsonPath("$[0].sessionId").value("sess-1"))
                .andExpect(jsonPath("$[0].rawQuestion").value("Where is order SO-45892? Why is it delayed?"))
                .andExpect(jsonPath("$[0].detectedIntent[0]").value("MULTI_TOOL_QUERY"))
                .andExpect(jsonPath("$[0].slaResult").value("Breached"))
                .andExpect(jsonPath("$[0].status").value("SUCCESS"))
                .andExpect(jsonPath("$[0].kbSources", hasSize(1)))
                .andExpect(jsonPath("$[0].traceId").exists())
                // P1.10: a clean success carries no warnings (the Day 4 mock disclaimer this
                // used to assert on is gone — see FakeAiQueryClient/ChatService).
                .andExpect(jsonPath("$[0].warnings", hasSize(0)))
                // Nothing real generates these yet (P2.10/P3's graph doesn't report per-agent
                // invocation lists or raw SQL back through the wire contract) — reported as
                // empty/null rather than fabricated.
                .andExpect(jsonPath("$[0].agentsInvoked", hasSize(0)))
                .andExpect(jsonPath("$[0].generatedSql").doesNotExist());
    }

    @Test
    void everyChatMessageCreatesItsOwnAuditEntryUnlikeHistoryWhichUpdatesInPlace() throws Exception {
        for (int i = 0; i < 2; i++) {
            mockMvc.perform(
                            post("/api/chat")
                                    .header("Authorization", "Bearer " + token)
                                    .contentType(MediaType.APPLICATION_JSON)
                                    .content("""
                                            {"query": "Is SKU-1001 in stock?", "sessionId": "sess-1"}
                                            """))
                    .andExpect(status().isOk());
        }

        mockMvc.perform(get("/api/audit").header("Authorization", "Bearer " + adminToken))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(2)));
    }

    @Test
    void auditDetailReturnsTheFullEntryById() throws Exception {
        mockMvc.perform(
                        post("/api/chat")
                                .header("Authorization", "Bearer " + token)
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("""
                                        {"query": "Is SKU-1001 in stock?", "sessionId": "sess-1"}
                                        """))
                .andExpect(status().isOk());

        long auditId =
                objectMapper
                        .readTree(
                                mockMvc.perform(get("/api/audit").header("Authorization", "Bearer " + adminToken))
                                        .andReturn()
                                        .getResponse()
                                        .getContentAsString())
                        .get(0)
                        .get("auditId")
                        .asLong();

        mockMvc.perform(get("/api/audit/" + auditId).header("Authorization", "Bearer " + adminToken))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.auditId").value(auditId))
                .andExpect(jsonPath("$.rawQuestion").value("Is SKU-1001 in stock?"));
    }

    @Test
    void auditDetailRejectsUnknownId() throws Exception {
        mockMvc.perform(get("/api/audit/999999").header("Authorization", "Bearer " + adminToken))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.status").value(404));
    }

    @Test
    void auditIsVisibleAcrossUsersUnlikeHistory() throws Exception {
        // Audit is a global admin-facing log, unlike per-user-isolated Query History: an
        // admin sees every user's entries, not just their own — proven here by having
        // demo-user create the entry and admin-user (a third, uninvolved account) read it.
        mockMvc.perform(
                        post("/api/chat")
                                .header("Authorization", "Bearer " + token)
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("""
                                        {"query": "Is SKU-1001 in stock?", "sessionId": "sess-1"}
                                        """))
                .andExpect(status().isOk());

        mockMvc.perform(get("/api/audit").header("Authorization", "Bearer " + adminToken))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(1)))
                .andExpect(jsonPath("$[0].user").value("demo-user"));
    }

    @Test
    void auditRejectsNonAdminUser() throws Exception {
        // RBAC (RC stabilization): the audit log is admin-only. A regular authenticated
        // user — even one who generated the very entry being requested — gets 403, not the
        // data. SecurityConfig's hasRole("ADMIN") check runs before the controller, so this
        // also covers /api/audit/{id}.
        String otherToken = login(SECOND_EMAIL, SECOND_PASSWORD);
        mockMvc.perform(get("/api/audit").header("Authorization", "Bearer " + token))
                .andExpect(status().isForbidden())
                .andExpect(jsonPath("$.status").value(403));
        mockMvc.perform(get("/api/audit").header("Authorization", "Bearer " + otherToken))
                .andExpect(status().isForbidden());
        mockMvc.perform(get("/api/audit/1").header("Authorization", "Bearer " + token))
                .andExpect(status().isForbidden());
    }

    @Test
    void auditRejectsAnonymousRequest() throws Exception {
        mockMvc.perform(get("/api/audit")).andExpect(status().isUnauthorized());
        mockMvc.perform(get("/api/audit/1")).andExpect(status().isUnauthorized());
    }

    @Test
    void auditDetailRejectsNonNumericId() throws Exception {
        mockMvc.perform(get("/api/audit/abc").header("Authorization", "Bearer " + adminToken))
                .andExpect(status().isBadRequest());
    }

    @Test
    void auditSupportsPaginationWithoutChangingTheUnpaginatedResponseShape() throws Exception {
        for (int i = 1; i <= 3; i++) {
            mockMvc.perform(
                            post("/api/chat")
                                    .header("Authorization", "Bearer " + token)
                                    .contentType(MediaType.APPLICATION_JSON)
                                    .content(
                                            """
                                            {"query": "Is SKU-1001 in stock?", "sessionId": "sess-%d"}
                                            """
                                                    .formatted(i)))
                    .andExpect(status().isOk());
        }

        // No page/size: unbounded, exactly like before pagination existed.
        mockMvc.perform(get("/api/audit").header("Authorization", "Bearer " + adminToken))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(3)))
                .andExpect(header().string("X-Total-Count", "3"));

        // page/size supplied: only that page comes back, but X-Total-Count still reports all 3.
        mockMvc.perform(
                        get("/api/audit").param("page", "0").param("size", "2").header("Authorization", "Bearer " + adminToken))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(2)))
                .andExpect(header().string("X-Total-Count", "3"));

        mockMvc.perform(
                        get("/api/audit").param("page", "1").param("size", "2").header("Authorization", "Bearer " + adminToken))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(1)));
    }

    @Test
    void auditRejectsInvalidPaginationParamsAsBadRequestNotServerError() throws Exception {
        mockMvc.perform(
                        get("/api/audit").param("page", "-1").param("size", "10").header("Authorization", "Bearer " + adminToken))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.status").value(400));

        mockMvc.perform(
                        get("/api/audit").param("page", "0").param("size", "0").header("Authorization", "Bearer " + adminToken))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.status").value(400));

        mockMvc.perform(
                        get("/api/audit").param("page", "abc").param("size", "10").header("Authorization", "Bearer " + adminToken))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.status").value(400));
    }

    /** Unlike ConversationHistoryStore's append-to-a-shared-row pattern, every chat call
     * inserts an independent new audit row, so there is no read-modify-write race to lose
     * — verifying that empirically rather than just by reasoning about it, the same way
     * the history race was actually caught (by testing, not by inspection). */
    @Test
    void concurrentChatCallsEachCreateTheirOwnAuditEntry() throws Exception {
        int callCount = 10;
        var executor = java.util.concurrent.Executors.newFixedThreadPool(callCount);
        var latch = new java.util.concurrent.CountDownLatch(callCount);
        for (int i = 0; i < callCount; i++) {
            int n = i;
            executor.submit(() -> {
                try {
                    mockMvc.perform(
                            post("/api/chat")
                                    .header("Authorization", "Bearer " + token)
                                    .contentType(MediaType.APPLICATION_JSON)
                                    .content(
                                            """
                                            {"query": "Is SKU-1001 in stock? call-%d", "sessionId": "concurrent-sess-%d"}
                                            """
                                                    .formatted(n, n)));
                } catch (Exception e) {
                    throw new RuntimeException(e);
                } finally {
                    latch.countDown();
                }
            });
        }
        latch.await();
        executor.shutdown();

        mockMvc.perform(get("/api/audit").header("Authorization", "Bearer " + adminToken))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(callCount)));
    }
}

package com.nexchain.backend;

import static org.hamcrest.Matchers.hasSize;
import static org.hamcrest.Matchers.matchesPattern;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;

/**
 * Day 4 completion-gate coverage (contract endpoints, chat mock scenarios, validation
 * errors) plus Day 6 (P1.6) authentication coverage: login issues a real JWT, protected
 * endpoints (/api/chat/**, /api/audit/**) reject anonymous/invalid callers and accept
 * valid ones, and public endpoints (/api/health, /api/auth/login) stay open.
 */
@SpringBootTest
@AutoConfigureMockMvc
class ApplicationSmokeTests {

    private static final String DEMO_EMAIL = "user@example.com";
    private static final String DEMO_PASSWORD = "password";

    @Autowired private MockMvc mockMvc;
    @Autowired private ObjectMapper objectMapper;

    private String token;

    @BeforeEach
    void obtainToken() throws Exception {
        token = login(DEMO_EMAIL, DEMO_PASSWORD);
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
    void auditRejectsAnonymousRequest() throws Exception {
        mockMvc.perform(get("/api/audit")).andExpect(status().isUnauthorized());
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
    void historyReturnsMockRecords() throws Exception {
        mockMvc.perform(get("/api/chat/history").header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(3)))
                .andExpect(jsonPath("$[0].question").exists())
                .andExpect(jsonPath("$[0].answerSummary").exists())
                .andExpect(jsonPath("$[0].sessionId").exists());
    }

    @Test
    void auditReturnsMockRecords() throws Exception {
        mockMvc.perform(get("/api/audit").header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(2)))
                .andExpect(jsonPath("$[0].traceId").exists())
                .andExpect(jsonPath("$[0].detectedIntent", hasSize(2)))
                .andExpect(jsonPath("$[0].slaResult").value("Breached"))
                .andExpect(jsonPath("$[1].generatedSql").exists());
    }
}

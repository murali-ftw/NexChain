package com.nexchain.backend;

import static org.hamcrest.Matchers.hasSize;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

/**
 * Day 4 completion-gate coverage: every contract endpoint returns valid JSON, the chat
 * endpoint resolves each deterministic mock scenario correctly, and Angular's primary
 * round trip (POST /api/chat) rejects a blank/missing query with a clean 4xx body.
 */
@SpringBootTest
@AutoConfigureMockMvc
class ApplicationSmokeTests {

    @Autowired private MockMvc mockMvc;

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
        mockMvc.perform(post("/api/chat").contentType(MediaType.APPLICATION_JSON).content("{}"))
                .andExpect(status().isBadRequest());
    }

    @Test
    void chatRejectsMalformedJson() throws Exception {
        mockMvc.perform(post("/api/chat").contentType(MediaType.APPLICATION_JSON).content("not-json"))
                .andExpect(status().isBadRequest());
    }

    @Test
    void loginReturnsMockToken() throws Exception {
        mockMvc.perform(
                        post("/api/auth/login")
                                .contentType(MediaType.APPLICATION_JSON)
                                .content(
                                        """
                                        {"email": "user@example.com", "password": "password"}
                                        """))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.accessToken").value("mock-token"))
                .andExpect(jsonPath("$.user.email").value("user@example.com"));
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
    void unmappedRouteReturnsCleanNotFound() throws Exception {
        mockMvc.perform(get("/api/nonexistent"))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.status").value(404));
    }

    @Test
    void historyReturnsMockRecords() throws Exception {
        mockMvc.perform(get("/api/chat/history"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(3)))
                .andExpect(jsonPath("$[0].question").exists())
                .andExpect(jsonPath("$[0].answerSummary").exists())
                .andExpect(jsonPath("$[0].sessionId").exists());
    }

    @Test
    void auditReturnsMockRecords() throws Exception {
        mockMvc.perform(get("/api/audit"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(2)))
                .andExpect(jsonPath("$[0].traceId").exists())
                .andExpect(jsonPath("$[0].detectedIntent", hasSize(2)))
                .andExpect(jsonPath("$[0].slaResult").value("Breached"))
                .andExpect(jsonPath("$[1].generatedSql").exists());
    }
}

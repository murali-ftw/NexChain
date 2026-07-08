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
 * Day 2 completion-gate coverage: every contract endpoint returns valid JSON,
 * and the chat endpoint rejects a blank/missing query with a clean 4xx body.
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
                .andExpect(jsonPath("$.slaStatus").value("Breached"))
                .andExpect(jsonPath("$.delayDays").value(6))
                .andExpect(jsonPath("$.recommendedActions", hasSize(4)));
    }

    @Test
    void chatWithGenericQueryReturnsGenericMock() throws Exception {
        mockMvc.perform(
                        post("/api/chat")
                                .contentType(MediaType.APPLICATION_JSON)
                                .content(
                                        """
                                        {"query": "Is SKU-1001 in stock?"}
                                        """))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.slaStatus").value("N/A"))
                .andExpect(jsonPath("$.answerText").value("Mock response for: \"Is SKU-1001 in stock?\""));
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
    void historyReturnsEmptyList() throws Exception {
        mockMvc.perform(get("/api/chat/history")).andExpect(status().isOk()).andExpect(jsonPath("$").isArray());
    }

    @Test
    void auditReturnsEmptyList() throws Exception {
        mockMvc.perform(get("/api/audit")).andExpect(status().isOk()).andExpect(jsonPath("$").isArray());
    }
}

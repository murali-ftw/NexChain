package com.nexchain.backend;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.doThrow;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.nexchain.backend.audit.store.AuditRepository;
import com.nexchain.backend.chat.client.AiQueryClient;
import com.nexchain.backend.chat.client.FakeAiQueryClient;
import com.nexchain.backend.history.store.ConversationHistoryRepository;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Import;
import org.springframework.context.annotation.Primary;
import org.springframework.http.MediaType;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;

/**
 * Day 12 hardening: a chat answer is already fully built before history/audit
 * persistence runs (ChatController). A write failure in either one used to
 * propagate uncaught, turning a successful AI answer into a 500 for the caller.
 * These tests force each repository to throw and confirm /api/chat still returns
 * the real answer with a 200 — the fix is best-effort + log, not fail the request.
 */
@SpringBootTest
@AutoConfigureMockMvc
@TestPropertySource(properties = "spring.datasource.url=jdbc:h2:mem:chat-side-effect-test;DB_CLOSE_DELAY=-1")
@Import(ChatSideEffectFailureTests.FakeAiQueryClientConfig.class)
class ChatSideEffectFailureTests {

    @TestConfiguration
    static class FakeAiQueryClientConfig {
        @Bean
        @Primary
        AiQueryClient fakeAiQueryClient() {
            return new FakeAiQueryClient();
        }
    }

    @Autowired private MockMvc mockMvc;
    @Autowired private ObjectMapper objectMapper;
    @MockBean private AuditRepository auditRepository;
    @MockBean private ConversationHistoryRepository conversationHistoryRepository;

    private String login() throws Exception {
        MvcResult result =
                mockMvc.perform(
                                post("/api/auth/login")
                                        .contentType(MediaType.APPLICATION_JSON)
                                        .content(
                                                """
                                                {"email": "user@example.com", "password": "password"}
                                                """))
                        .andExpect(status().isOk())
                        .andReturn();
        return objectMapper.readTree(result.getResponse().getContentAsString()).get("accessToken").asText();
    }

    @Test
    void chat_survives_an_audit_write_failure() throws Exception {
        doThrow(new RuntimeException("simulated audit write failure")).when(auditRepository).save(any());
        String token = login();

        mockMvc.perform(
                        post("/api/chat")
                                .header("Authorization", "Bearer " + token)
                                .contentType(MediaType.APPLICATION_JSON)
                                .content(
                                        """
                                        {"query": "Where is order SO-45892?"}
                                        """))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.answerText").exists());
    }

    @Test
    void chat_survives_a_history_write_failure() throws Exception {
        doThrow(new RuntimeException("simulated history write failure"))
                .when(conversationHistoryRepository)
                .save(any());
        String token = login();

        mockMvc.perform(
                        post("/api/chat")
                                .header("Authorization", "Bearer " + token)
                                .contentType(MediaType.APPLICATION_JSON)
                                .content(
                                        """
                                        {"query": "Where is order SO-45892?"}
                                        """))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.answerText").exists());
    }
}

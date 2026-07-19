package com.nexchain.backend.chat.controller;

import com.nexchain.backend.audit.service.AuditService;
import com.nexchain.backend.chat.dto.ChatRequest;
import com.nexchain.backend.chat.dto.ChatResponse;
import com.nexchain.backend.chat.service.ChatService;
import com.nexchain.backend.history.service.HistoryService;
import jakarta.validation.Valid;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/chat")
public class ChatController {

    private static final Logger log = LoggerFactory.getLogger(ChatController.class);

    private final ChatService chatService;
    private final HistoryService historyService;
    private final AuditService auditService;

    public ChatController(ChatService chatService, HistoryService historyService, AuditService auditService) {
        this.chatService = chatService;
        this.historyService = historyService;
        this.auditService = auditService;
    }

    /** Every successful response automatically creates/updates the caller's history
     * (P1.7) — same session id updates the existing conversation in place — and
     * automatically records an audit entry (P1.8). Both are side effects of an
     * already-successful AI answer: a write failure in either one (H2 I/O error,
     * constraint violation) must not turn that answer into a 500 for the caller, so
     * each is best-effort and logged rather than left to propagate to
     * GlobalExceptionHandler's catch-all. */
    @PostMapping
    public ChatResponse chat(@Valid @RequestBody ChatRequest request, Authentication authentication) {
        ChatResponse response = chatService.getResponse(request, authentication.getName());
        try {
            historyService.record(authentication.getName(), response.sessionId(), request.query(), response);
        } catch (RuntimeException ex) {
            log.error("history record failed for session {}", response.sessionId(), ex);
        }
        try {
            auditService.record(authentication.getName(), response.sessionId(), request.query(), response);
        } catch (RuntimeException ex) {
            log.error("audit record failed for session {}", response.sessionId(), ex);
        }
        return response;
    }
}

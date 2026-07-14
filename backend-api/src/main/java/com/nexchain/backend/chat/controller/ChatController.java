package com.nexchain.backend.chat.controller;

import com.nexchain.backend.chat.dto.ChatRequest;
import com.nexchain.backend.chat.dto.ChatResponse;
import com.nexchain.backend.chat.service.ChatService;
import com.nexchain.backend.history.service.HistoryService;
import jakarta.validation.Valid;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/chat")
public class ChatController {

    private final ChatService chatService;
    private final HistoryService historyService;

    public ChatController(ChatService chatService, HistoryService historyService) {
        this.chatService = chatService;
        this.historyService = historyService;
    }

    /** Every successful response automatically creates/updates the caller's history
     * (P1.7) — same session id updates the existing conversation in place. */
    @PostMapping
    public ChatResponse chat(@Valid @RequestBody ChatRequest request, Authentication authentication) {
        ChatResponse response = chatService.getMockResponse(request);
        historyService.record(authentication.getName(), response.sessionId(), request.query(), response);
        return response;
    }
}

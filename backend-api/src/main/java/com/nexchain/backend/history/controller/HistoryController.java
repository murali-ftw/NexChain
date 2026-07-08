package com.nexchain.backend.history.controller;

import com.nexchain.backend.history.dto.HistoryItemDto;
import com.nexchain.backend.history.service.HistoryService;
import java.util.List;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/** Contributes GET /api/chat/history — nested under the chat path per the frozen contract. */
@RestController
@RequestMapping("/api/chat")
public class HistoryController {

    private final HistoryService historyService;

    public HistoryController(HistoryService historyService) {
        this.historyService = historyService;
    }

    @GetMapping("/history")
    public List<HistoryItemDto> getHistory() {
        return historyService.getMockHistory();
    }
}

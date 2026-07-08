package com.nexchain.backend.history.service;

import com.nexchain.backend.history.dto.HistoryItemDto;
import java.util.List;
import org.springframework.stereotype.Service;

/** Day 2 contract stub — no persistence yet. Real persistence is P1.7 (Day 7). */
@Service
public class HistoryService {

    public List<HistoryItemDto> getMockHistory() {
        return List.of();
    }
}

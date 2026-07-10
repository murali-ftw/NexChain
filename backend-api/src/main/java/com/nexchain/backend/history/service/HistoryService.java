package com.nexchain.backend.history.service;

import com.nexchain.backend.history.dto.HistoryItemDto;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.List;
import java.util.UUID;
import org.springframework.stereotype.Service;

/** Day 4 contract stub — no persistence yet. Real persistence is P1.7 (Day 7). */
@Service
public class HistoryService {

    public List<HistoryItemDto> getMockHistory() {
        Instant now = Instant.now();
        return List.of(
                new HistoryItemDto(
                        UUID.randomUUID().toString(),
                        "Where is customer order SO-45892? Why is it delayed and what action should we take?",
                        "Customs hold at Chennai Port — SLA breached, 6-day delay.",
                        now.minus(2, ChronoUnit.HOURS),
                        "session-demo-1"),
                new HistoryItemDto(
                        UUID.randomUUID().toString(),
                        "Is SKU-1001 in stock?",
                        "240 units available at the Chennai warehouse.",
                        now.minus(1, ChronoUnit.DAYS),
                        "session-demo-2"),
                new HistoryItemDto(
                        UUID.randomUUID().toString(),
                        "Show delayed orders from Chennai warehouse.",
                        "4 orders currently delayed.",
                        now.minus(2, ChronoUnit.DAYS),
                        "session-demo-3"));
    }
}

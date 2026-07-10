package com.nexchain.backend.audit.service;

import com.nexchain.backend.audit.dto.ApiCallDto;
import com.nexchain.backend.audit.dto.AuditEntryDto;
import com.nexchain.backend.common.dto.SlaStatus;
import com.nexchain.backend.common.dto.SourceDto;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.List;
import java.util.UUID;
import org.springframework.stereotype.Service;

/** Day 4 contract stub — no persistence yet. Real persistence is P1.8 (Day 8). */
@Service
public class AuditService {

    public List<AuditEntryDto> getMockAuditLog() {
        Instant now = Instant.now();
        return List.of(
                new AuditEntryDto(
                        1L,
                        UUID.randomUUID().toString(),
                        now.minus(2, ChronoUnit.HOURS),
                        "demo-user",
                        "Where is customer order SO-45892? Why is it delayed and what action should we take?",
                        List.of("order_status", "delay_analysis"),
                        List.of("text_to_sql_agent", "api_status_agent", "business_rule_agent"),
                        null,
                        List.of(new ApiCallDto("/api/shipment/status/SO-45892", 200, 340)),
                        List.of(new SourceDto(
                                "Customs Hold SOP",
                                "Covers HS code mismatch during customs validation and other customs hold causes.",
                                3,
                                0.93)),
                        SlaStatus.BREACHED,
                        "SUCCESS"),
                new AuditEntryDto(
                        2L,
                        UUID.randomUUID().toString(),
                        now.minus(1, ChronoUnit.DAYS),
                        "demo-user",
                        "Is SKU-1001 in stock?",
                        List.of("inventory"),
                        List.of("text_to_sql_agent"),
                        "SELECT sku, quantity_on_hand FROM inventory WHERE sku = 'SKU-1001'",
                        List.of(),
                        List.of(),
                        SlaStatus.NOT_APPLICABLE,
                        "SUCCESS"));
    }
}

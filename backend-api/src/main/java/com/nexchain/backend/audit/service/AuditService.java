package com.nexchain.backend.audit.service;

import com.nexchain.backend.audit.dto.AuditEntryDto;
import java.util.List;
import org.springframework.stereotype.Service;

/** Day 2 contract stub — no persistence yet. Real persistence is P1.8 (Day 8). */
@Service
public class AuditService {

    public List<AuditEntryDto> getMockAuditLog() {
        return List.of();
    }
}

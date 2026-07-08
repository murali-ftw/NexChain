package com.nexchain.backend.audit.controller;

import com.nexchain.backend.audit.dto.AuditEntryDto;
import com.nexchain.backend.audit.service.AuditService;
import java.util.List;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/audit")
public class AuditController {

    private final AuditService auditService;

    public AuditController(AuditService auditService) {
        this.auditService = auditService;
    }

    @GetMapping
    public List<AuditEntryDto> getAuditLog() {
        return auditService.getMockAuditLog();
    }
}

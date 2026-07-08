package com.nexchain.backend.audit.dto;

public record ApiCallDto(String endpoint, int statusCode, long latencyMs) {}

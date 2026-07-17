package com.nexchain.backend.audit.entity;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.nexchain.backend.audit.dto.ApiCallDto;
import jakarta.persistence.AttributeConverter;
import jakarta.persistence.Converter;
import java.util.List;

/** Stores the {@code apiCalls} list as one JSON column — matches {@code AuditEntryDto.apiCalls}. */
@Converter
public class ApiCallListConverter implements AttributeConverter<List<ApiCallDto>, String> {

    private static final ObjectMapper MAPPER = new ObjectMapper();
    private static final TypeReference<List<ApiCallDto>> TYPE = new TypeReference<>() {};

    @Override
    public String convertToDatabaseColumn(List<ApiCallDto> value) {
        try {
            return MAPPER.writeValueAsString(value);
        } catch (JsonProcessingException e) {
            throw new IllegalStateException("Failed to serialize api call list", e);
        }
    }

    @Override
    public List<ApiCallDto> convertToEntityAttribute(String dbData) {
        try {
            return MAPPER.readValue(dbData, TYPE);
        } catch (JsonProcessingException e) {
            throw new IllegalStateException("Failed to deserialize api call list", e);
        }
    }
}

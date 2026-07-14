package com.nexchain.backend.audit.entity;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.nexchain.backend.common.dto.SourceDto;
import jakarta.persistence.AttributeConverter;
import jakarta.persistence.Converter;
import java.util.List;

/** Stores the {@code kbSources} list as one JSON column — reuses the same {@code SourceDto}
 * as {@code ChatResponse.sources()}, since it's the identical shape. */
@Converter
public class SourceListConverter implements AttributeConverter<List<SourceDto>, String> {

    private static final ObjectMapper MAPPER = new ObjectMapper();
    private static final TypeReference<List<SourceDto>> TYPE = new TypeReference<>() {};

    @Override
    public String convertToDatabaseColumn(List<SourceDto> value) {
        try {
            return MAPPER.writeValueAsString(value);
        } catch (JsonProcessingException e) {
            throw new IllegalStateException("Failed to serialize source list", e);
        }
    }

    @Override
    public List<SourceDto> convertToEntityAttribute(String dbData) {
        try {
            return MAPPER.readValue(dbData, TYPE);
        } catch (JsonProcessingException e) {
            throw new IllegalStateException("Failed to deserialize source list", e);
        }
    }
}

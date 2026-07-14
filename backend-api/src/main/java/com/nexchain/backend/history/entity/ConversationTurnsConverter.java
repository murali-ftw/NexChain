package com.nexchain.backend.history.entity;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import com.nexchain.backend.history.dto.ConversationTurnDto;
import jakarta.persistence.AttributeConverter;
import jakarta.persistence.Converter;
import java.util.List;

/**
 * Serializes a conversation's turns (each one a full {@code ChatResponse}) to a single
 * JSON column. A turn is always read/written as a whole unit, so a JSON blob is simpler
 * here than normalizing every {@code ChatResponse} field into its own set of columns.
 */
@Converter
public class ConversationTurnsConverter implements AttributeConverter<List<ConversationTurnDto>, String> {

    private static final ObjectMapper MAPPER =
            new ObjectMapper().registerModule(new JavaTimeModule()).disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);
    private static final TypeReference<List<ConversationTurnDto>> TURNS_TYPE = new TypeReference<>() {};

    @Override
    public String convertToDatabaseColumn(List<ConversationTurnDto> turns) {
        try {
            return MAPPER.writeValueAsString(turns);
        } catch (JsonProcessingException e) {
            throw new IllegalStateException("Failed to serialize conversation turns", e);
        }
    }

    @Override
    public List<ConversationTurnDto> convertToEntityAttribute(String dbData) {
        try {
            return MAPPER.readValue(dbData, TURNS_TYPE);
        } catch (JsonProcessingException e) {
            throw new IllegalStateException("Failed to deserialize conversation turns", e);
        }
    }
}

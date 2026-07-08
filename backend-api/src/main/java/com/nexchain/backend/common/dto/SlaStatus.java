package com.nexchain.backend.common.dto;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonValue;

/**
 * Mirrors {@code SLAStatus} in ai/contracts.py (Person 3, P3.1, frozen Day 1)
 * field-for-field, including the exact wire strings, so both services agree
 * on SLA wording without a translation layer.
 */
public enum SlaStatus {
    ON_TIME("On Time"),
    AT_RISK("At Risk"),
    BREACHED("Breached"),
    NOT_APPLICABLE("N/A");

    private final String wireValue;

    SlaStatus(String wireValue) {
        this.wireValue = wireValue;
    }

    @JsonValue
    public String wireValue() {
        return wireValue;
    }

    @JsonCreator
    public static SlaStatus fromWireValue(String value) {
        for (SlaStatus status : values()) {
            if (status.wireValue.equalsIgnoreCase(value)) {
                return status;
            }
        }
        throw new IllegalArgumentException("Unknown SLA status: " + value);
    }
}

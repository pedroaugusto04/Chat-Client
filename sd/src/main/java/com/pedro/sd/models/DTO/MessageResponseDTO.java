package com.pedro.sd.models.DTO;

import java.time.OffsetDateTime;

public record MessageResponseDTO(String idemKey, String text, Integer userId, String userNickname, OffsetDateTime timestampClient,
                                 OffsetDateTime timestampServer) {
}

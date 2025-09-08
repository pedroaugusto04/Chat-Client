package com.pedro.sd.models.DTO;

import java.time.LocalDateTime;

public record MessageResponseDTO(String text, Integer userId, LocalDateTime timestamp_client) {
}

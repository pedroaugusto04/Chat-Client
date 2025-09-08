package com.models.DTO;

import java.time.LocalDateTime;

public record MessageSendDTO(String idemKey, String text, Integer userId,LocalDateTime timestamp_client) {
}

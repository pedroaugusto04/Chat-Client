package com.pedro.sd.models.DTO;

import java.time.LocalDateTime;

public record MessageSendDTO(String idemKey, String text, String userNickname,LocalDateTime timestampClient) {
}

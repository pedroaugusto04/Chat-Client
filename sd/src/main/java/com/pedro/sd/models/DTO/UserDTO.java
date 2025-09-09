package com.pedro.sd.models.DTO;

import java.time.LocalDateTime;

public record UserDTO(String nickname, LocalDateTime timestampClient) {
}

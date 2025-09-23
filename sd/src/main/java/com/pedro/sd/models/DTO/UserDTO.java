package com.pedro.sd.models.DTO;

import java.time.OffsetDateTime;

public record UserDTO(String nickname, OffsetDateTime timestampClient) {
}

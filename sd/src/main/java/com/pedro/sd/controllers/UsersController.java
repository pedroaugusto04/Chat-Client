package com.pedro.sd.controllers;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import com.pedro.sd.models.DTO.UserDTO;
import com.pedro.sd.services.UsersService;
import com.pedro.sd.services.LogsService;


@RestController
public class UsersController {

    private UsersService userService;
    private LogsService logsService;

    UsersController(UsersService userService, LogsService logsService){
        this.userService = userService;
        this.logsService = logsService;
    }


    @PostMapping("/nick")
    public ResponseEntity<Void> createUser(@RequestBody UserDTO userDTO) {

        long startTime = System.currentTimeMillis();

        this.logsService.log(userDTO, "CREATE_USER", "Entrou no endpoint para criacao de usuario");

        this.userService.createUser(userDTO);

        long latency = System.currentTimeMillis() - startTime;

        this.logsService.log(userDTO, "CREATE_USER", "Usuario criado com sucesso" + " em" + latency + " ms");

        return ResponseEntity.ok().build();
    }
}
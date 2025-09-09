package com.pedro.sd.controllers;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import com.pedro.sd.models.DTO.UserDTO;
import com.pedro.sd.services.UsersService;

@RestController
public class UsersController {

    private UsersService userService;

    UsersController(UsersService userService){
        this.userService = userService;
    }


    @PostMapping("/nick")
    public ResponseEntity<Void> createUser(@RequestBody UserDTO userDTO) {

        this.logsService.log(userDTO, "CREATE_USER", "Entrou no endpoint para criacao de usuario");

        this.userService.createUser(userDTO);

        this.logsService.log(userDTO, "CREATE_USER", "Usuario criado com sucesso");

        return ResponseEntity.ok().build();
    }
}
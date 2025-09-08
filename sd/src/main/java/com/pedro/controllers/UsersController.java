package com.pedro.controllers;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;

import com.models.DTO.UserDTO;
import com.pedro.services.UsersService;

public class UsersController {

    private UsersService userService;

    UsersController(UsersService userService){
        this.userService = userService;
    }


    @PostMapping("/nick")
    public ResponseEntity<Void> createUser(@RequestBody UserDTO userDTO) {

        this.userService.createUser(userDTO);

        return ResponseEntity.ok().build();
    }
}
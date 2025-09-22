package com.pedro.sd.config.database;

import com.pedro.sd.models.DTO.UserDTO;
import com.pedro.sd.services.GroupsService;
import com.pedro.sd.services.UsersService;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;

@Component
public class DatabaseInitializer implements CommandLineRunner {

    private final GroupsService groupsService;
    private final UsersService usersService;

    public DatabaseInitializer(GroupsService groupsService, UsersService usersService) {
        this.groupsService = groupsService;
        this.usersService = usersService;
    }

    @Override
    public void run(String... args) throws Exception {
        groupsService.createIfNotExists("Grupo_1");
        groupsService.createIfNotExists("teste_vazao");

        usersService.createUser(new UserDTO("admin", LocalDateTime.now()));
    }
}

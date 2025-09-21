package com.pedro.sd.config.database;

import com.pedro.sd.services.GroupsService;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;

@Component
public class DatabaseInitializer implements CommandLineRunner {

    private final GroupsService groupsService;

    public DatabaseInitializer(GroupsService groupsService) {
        this.groupsService = groupsService;
    }

    @Override
    public void run(String... args) throws Exception {
        groupsService.createIfNotExists("Grupo_1");
        groupsService.createIfNotExists("teste_vazao");
    }
}

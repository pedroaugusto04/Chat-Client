package com.pedro.sd.controllers;

import java.util.List;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import com.pedro.sd.models.DTO.GroupDTO;
import com.pedro.sd.models.Entities.Group;
import com.pedro.sd.services.GroupsService;
import com.pedro.sd.services.LogsService;

@RestController
public class GroupsController {

    private GroupsService groupsService;
    private LogsService logsService;

    GroupsController(GroupsService groupsService, LogsService logsService){
        this.groupsService = groupsService;
        this.logsService = logsService;
    }


    @PostMapping("/groups")
    public ResponseEntity<Void> createGroup(@RequestBody GroupDTO groupDTO) {

        long startTime = System.currentTimeMillis();

        this.logsService.log(groupDTO, "CREATE_GROUP", "Entrou no endpoint para criacao de grupo");

        this.groupsService.createGroup(groupDTO);

        long latency = System.currentTimeMillis() - startTime;

        this.logsService.log(groupDTO, "CREATE_GROUP", "Grupo criado com sucesso em " + latency + " ms");

        return ResponseEntity.ok().build();
    }

    @GetMapping("/groups")
    public ResponseEntity<List<Group>> getGroups() {

        long startTime = System.currentTimeMillis();

        this.logsService.log(null, "GET_GROUPS", "Entrou no endpoint para recuperacao de grupos");

        List<Group> groups = this.groupsService.getGroups();

        long latency = System.currentTimeMillis() - startTime;

        this.logsService.log(null, "GET_GROUPS", "Recuperou grupos com sucesso em " + latency + " ms");
        
        return ResponseEntity.ok(groups);
    }
}
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

@RestController
public class GroupsController {

    private GroupsService groupsService;

    GroupsController(GroupsService groupsService){
        this.groupsService = groupsService;
    }


    @PostMapping("/groups")
    public ResponseEntity<Void> createGroup(@RequestBody GroupDTO groupDTO) {

        this.logsService.log(groupDTO, "CREATE_GROUP", "Entrou no endpoint para criacao de grupo");

        this.groupsService.createGroup(groupDTO);

        this.logsService.log(groupDTO, "CREATE_GROUP", "Grupo criado com sucesso");

        return ResponseEntity.ok().build();
    }

    @GetMapping("/groups")
    public ResponseEntity<List<Group>> getGroups() {

        this.logsService.log(null, "GET_GROUPS", "Entrou no endpoint para recuperacao de grupos");

        List<Group> groups = this.groupsService.getGroups();

        this.logsService.log(null, "GET_GROUPS", "Recuperou grupos com sucesso");
        
        return ResponseEntity.ok(groups);
    }
}
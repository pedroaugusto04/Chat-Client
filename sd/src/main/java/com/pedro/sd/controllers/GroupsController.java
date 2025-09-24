package com.pedro.sd.controllers;

import com.pedro.sd.models.DTO.GroupDTO;
import com.pedro.sd.models.DTO.MessageResponseDTO;
import com.pedro.sd.models.Entities.Group;
import com.pedro.sd.services.GroupsService;
import com.pedro.sd.services.LogsService;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Date;
import java.util.List;

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

    @GetMapping("groups/{id}/messages")
    public ResponseEntity<List<MessageResponseDTO>> getLastMessages(

            @PathVariable("id") Integer groupId,
            @RequestParam(value = "since", required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) Date since,
            @RequestParam(value = "limit", defaultValue = "10") Integer limit) {

        long startTime = System.currentTimeMillis();

        this.logsService.log(groupId, "GET_MESSAGES", "Entrou no endpoint para recuperacao de mensagens do grupo");

        List<MessageResponseDTO> messages = groupsService.getMessages(groupId, since, limit);

        long latency = System.currentTimeMillis() - startTime;

        this.logsService.log(messages, "GET_MESSAGES", "Recuperou com sucesso as mensagens do grupo " + groupId + " em " + latency + " ms");

        return ResponseEntity.ok(messages);
    }
}
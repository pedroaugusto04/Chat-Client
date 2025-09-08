package com.pedro.controllers;

import java.util.List;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;

import com.models.DTO.GroupDTO;
import com.models.Entities.Group;
import com.pedro.services.GroupsService;

public class GroupsController {

    private GroupsService groupsService;

    GroupsController(GroupsService groupsService){
        this.groupsService = groupsService;
    }


    @PostMapping("/groups")
    public ResponseEntity<Void> createGroup(@RequestBody GroupDTO groupDTO) {

        this.groupsService.createGroup(groupDTO);
        
        return ResponseEntity.ok().build();
    }

    @GetMapping("/groups")
    public ResponseEntity<List<Group>> getGroups() {

        List<Group> groups = this.groupsService.getGroups();
        
        return ResponseEntity.ok(groups);
    }
}
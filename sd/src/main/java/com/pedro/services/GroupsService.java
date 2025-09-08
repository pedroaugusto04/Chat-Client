package com.pedro.services;

import java.util.List;

import com.models.DTO.GroupDTO;
import com.models.Entities.Group;
import com.pedro.repositories.GroupsRepository;

public class GroupsService {
    
    private GroupsRepository groupsRepository;

    GroupsService(GroupsRepository groupsRepository) {
        this.groupsRepository = groupsRepository;
    }
    
    public void createGroup(GroupDTO groupDTO) {

        Group group = new Group(groupDTO.name());

        this.groupsRepository.save(group);
    }

    public Group getGroup(Integer groupId) {
        return this.groupsRepository.findById(groupId).orElseThrow(() -> new RuntimeException());
    }

    public List<Group> getGroups() {
        return this.groupsRepository.findAll();
    }
}

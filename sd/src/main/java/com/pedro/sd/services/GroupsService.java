package com.pedro.sd.services;

import java.util.List;

import org.springframework.stereotype.Service;

import com.pedro.sd.models.DTO.GroupDTO;
import com.pedro.sd.models.Entities.Group;
import com.pedro.sd.repositories.GroupsRepository;

@Service
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

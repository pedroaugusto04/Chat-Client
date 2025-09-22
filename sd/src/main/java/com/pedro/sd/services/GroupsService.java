package com.pedro.sd.services;

import com.pedro.sd.models.DTO.GroupDTO;
import com.pedro.sd.models.Entities.Group;
import com.pedro.sd.repositories.GroupsRepository;
import org.springframework.stereotype.Service;

import java.util.List;

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

    public void createIfNotExists(String groupName) {
        if (this.groupsRepository.findByName(groupName).orElse(null) == null) {
            this.groupsRepository.save(new Group(groupName));
        }
    }

    public Group getGroup(Integer groupId) {
        return this.groupsRepository.findById(groupId).orElseThrow(() -> new RuntimeException());
    }

    public Group getGroupByName(String groupName) {
        return this.groupsRepository.findByName(groupName).orElseThrow(() -> new RuntimeException());
    }

    public List<Group> getGroups() {
        return this.groupsRepository.findAll();
    }
}

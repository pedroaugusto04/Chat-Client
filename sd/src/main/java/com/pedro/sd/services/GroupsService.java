package com.pedro.sd.services;

import com.pedro.sd.models.DTO.GroupDTO;
import com.pedro.sd.models.DTO.MessageResponseDTO;
import com.pedro.sd.models.Entities.Group;
import com.pedro.sd.models.Entities.Message;
import com.pedro.sd.repositories.GroupsRepository;
import com.pedro.sd.repositories.MessagesRepository;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;

import java.time.OffsetDateTime;
import java.time.ZoneId;
import java.util.Date;
import java.util.List;
import java.util.stream.Collectors;

@Service
public class GroupsService {
    
    private GroupsRepository groupsRepository;
    private MessagesRepository messagesRepository;

    GroupsService(GroupsRepository groupsRepository, MessagesRepository messagesRepository) {
        this.groupsRepository = groupsRepository;
        this.messagesRepository = messagesRepository;
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

    public List<MessageResponseDTO> getMessages(Integer groupId, Date since, Integer limit) {
        Group group = getGroup(groupId);

        List<Message> messages;

        if (since != null) {

            OffsetDateTime sinceDateTime = OffsetDateTime.ofInstant(
                    since.toInstant(),
                    ZoneId.systemDefault()
            );

            messages = messagesRepository.findByGroupAndClientDateAfterOrderByClientDateDesc(
                    group,
                    sinceDateTime,
                    PageRequest.of(0, limit));
        } else {
            messages = messagesRepository.findByGroupOrderByClientDateDesc(
                    group,
                    PageRequest.of(0, limit));
        }

        return messages.stream()
                .map(m -> new MessageResponseDTO(m.getIdemKey(),m.getText(), m.getUser().getId(), m.getUser().getNickname(),m.getClientDate()))
                .collect(Collectors.toList());
    }
}

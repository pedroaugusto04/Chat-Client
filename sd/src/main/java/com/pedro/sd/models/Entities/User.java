package com.pedro.sd.models.Entities;

import jakarta.persistence.*;

import java.time.OffsetDateTime;
import java.util.List;

@Entity
@Table(name = "users")
public class User {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @Column(nullable = false, length = 100)
    private String nickname;

    @OneToMany(mappedBy = "user", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<Message> messages;

    @Column(name="last_activity")
    private OffsetDateTime timestampClient;

    public User() {}

    public User(String nickname, OffsetDateTime timestampClient) {
        this.nickname = nickname;
        this.timestampClient = timestampClient;
    }

    public Integer getId() {
        return id;
    }

    public void setId(Integer id) {
        this.id = id;
    }

    public String getNickname() {
        return nickname;
    }

    public void setNickname(String nickname) {
        this.nickname = nickname;
    }

    public List<Message> getMessages() {
        return messages;
    }

    public void setMessages(List<Message> messages) {
        this.messages = messages;
    }

    public OffsetDateTime getTimestampClient() {
        return timestampClient;
    }

    public void setTimestampClient(OffsetDateTime timestampClient) {
        this.timestampClient = timestampClient;
    }
}

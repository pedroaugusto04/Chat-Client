package com.pedro.sd.models.Entities;

import jakarta.persistence.*;
import org.hibernate.annotations.CreationTimestamp;

import java.time.OffsetDateTime;

@Entity
@Table(name = "messages")
public class Message {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @Column(nullable = false, columnDefinition = "TEXT")
    private String text;

    @Column(name = "idem_key", nullable = false, unique = true)
    private String idemKey;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "fk_user", nullable = false)
    private User user;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "fk_group", nullable = false)
    private Group group;

    @Column(nullable = false)
    private OffsetDateTime clientDate;

    @Column(nullable = false)
    @CreationTimestamp
    private OffsetDateTime serverDate;

    public Message() {}

    public Message(String text, User user, Group group, String idemKey, OffsetDateTime clientDate) {
        this.text = text;
        this.user = user;
        this.group = group;
        this.idemKey = idemKey;
        this.clientDate = clientDate;
    }

    public Integer getId() {
        return id;
    }

    public void setId(Integer id) {
        this.id = id;
    }

    public String getText() {
        return text;
    }

    public void setText(String text) {
        this.text = text;
    }

    public User getUser() {
        return user;
    }

    public void setUser(User user) {
        this.user = user;
    }

    public Group getGroup() {
        return group;
    }

    public void setGroup(Group group) {
        this.group = group;
    }

    public String getIdemKey() {
        return idemKey;
    }

    public void setIdemKey(String idemKey) {
        this.idemKey = idemKey;
    }

    public OffsetDateTime getClientDate() {
        return clientDate;
    }

    public void setClientDate(OffsetDateTime clientDate) {
        this.clientDate = clientDate;
    }

    public OffsetDateTime getServerDate() {
        return serverDate;
    }

    public void setServerDate(OffsetDateTime serverDate) {
        this.serverDate = serverDate;
    }
}

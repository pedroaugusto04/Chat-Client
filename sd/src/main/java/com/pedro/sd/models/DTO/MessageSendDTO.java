package com.pedro.sd.models.DTO;

import java.time.OffsetDateTime;

public class MessageSendDTO {

    private String idemKey;
    private String text;
    private String userNickname;
    private OffsetDateTime timestampClient;
    private boolean isRetry;
    private OffsetDateTime timestampStartServer;
    private OffsetDateTime timestampEndServer;

    public MessageSendDTO(String idemKey, String text, String userNickname,
                          OffsetDateTime timestampClient, boolean isRetry, OffsetDateTime timestampStartServer,OffsetDateTime timestampEndServer) {
        this.idemKey = idemKey;
        this.text = text;
        this.userNickname = userNickname;
        this.timestampClient = timestampClient;
        this.isRetry = isRetry;
        this.timestampStartServer = timestampStartServer;
        this.timestampEndServer = timestampEndServer;
    }

    public MessageSendDTO() {}

    @Override
    public String toString() {
        return "MessageSendDTO{" +
                "idemKey='" + idemKey + '\'' +
                ", text='" + text + '\'' +
                ", userNickname='" + userNickname + '\'' +
                '}';
    }

    public String getIdemKey() { return idemKey; }
    public void setIdemKey(String idemKey) { this.idemKey = idemKey; }

    public String getText() { return text; }
    public void setText(String text) { this.text = text; }

    public String getUserNickname() { return userNickname; }
    public void setUserNickname(String userNickname) { this.userNickname = userNickname; }

    public OffsetDateTime getTimestampClient() { return timestampClient; }
    public void setTimestampClient(OffsetDateTime timestampClient) { this.timestampClient = timestampClient; }

    public boolean isRetry() { return isRetry; }
    public void setRetry(boolean retry) { isRetry = retry; }

    public OffsetDateTime getTimestampStartServer() {
        return timestampStartServer;
    }

    public void setTimestampStartServer(OffsetDateTime timestampStartServer) {
        this.timestampStartServer = timestampStartServer;
    }

    public OffsetDateTime getTimestampEndServer() {
        return timestampEndServer;
    }

    public void setTimestampEndServer(OffsetDateTime timestampEndServer) {
        this.timestampEndServer = timestampEndServer;
    }
}

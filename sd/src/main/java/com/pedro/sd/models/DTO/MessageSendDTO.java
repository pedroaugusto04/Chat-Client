package com.pedro.sd.models.DTO;

import java.time.OffsetDateTime;

public class MessageSendDTO {

    private String idemKey;
    private String text;
    private String userNickname;
    private OffsetDateTime timestampClient;
    private boolean isRetry;
    private OffsetDateTime timestampServer;

    public MessageSendDTO(String idemKey, String text, String userNickname,
                          OffsetDateTime timestampClient, boolean isRetry, OffsetDateTime timestampServer) {
        this.idemKey = idemKey;
        this.text = text;
        this.userNickname = userNickname;
        this.timestampClient = timestampClient;
        this.isRetry = isRetry;
        this.timestampServer = timestampServer;
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

    public OffsetDateTime getTimestampServer() { return timestampServer; }
    public void setTimestampServer(OffsetDateTime timestampServer) { this.timestampServer = timestampServer; }
}

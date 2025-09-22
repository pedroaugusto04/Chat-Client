package com.pedro.sd.models.DTO;

import java.time.LocalDateTime;

public class MessageSendDTO {

    private String idemKey;
    private String text;
    private String userNickname;
    private LocalDateTime timestampClient;
    private boolean isRetry;
    private LocalDateTime sentTime;
    private LocalDateTime timestampServer;

    public MessageSendDTO(String idemKey, String text, String userNickname,
                          LocalDateTime timestampClient, boolean isRetry,
                          LocalDateTime sentTime, LocalDateTime timestampServer) {
        this.idemKey = idemKey;
        this.text = text;
        this.userNickname = userNickname;
        this.timestampClient = timestampClient;
        this.isRetry = isRetry;
        this.sentTime = sentTime;
        this.timestampServer = timestampServer;
    }

    public MessageSendDTO() {}

    public String getIdemKey() { return idemKey; }
    public void setIdemKey(String idemKey) { this.idemKey = idemKey; }

    public String getText() { return text; }
    public void setText(String text) { this.text = text; }

    public String getUserNickname() { return userNickname; }
    public void setUserNickname(String userNickname) { this.userNickname = userNickname; }

    public LocalDateTime getTimestampClient() { return timestampClient; }
    public void setTimestampClient(LocalDateTime timestampClient) { this.timestampClient = timestampClient; }

    public boolean isRetry() { return isRetry; }
    public void setRetry(boolean retry) { isRetry = retry; }

    public LocalDateTime getSentTime() { return sentTime; }
    public void setSentTime(LocalDateTime sentTime) { this.sentTime = sentTime; }

    public LocalDateTime getTimestampServer() { return timestampServer; }
    public void setTimestampServer(LocalDateTime timestampServer) { this.timestampServer = timestampServer; }
}

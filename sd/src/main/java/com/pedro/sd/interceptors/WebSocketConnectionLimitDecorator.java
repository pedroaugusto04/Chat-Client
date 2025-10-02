package com.pedro.sd.interceptors;

import com.pedro.sd.services.LogsService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.WebSocketMessage;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.handler.WebSocketHandlerDecorator;
import org.springframework.web.socket.handler.WebSocketHandlerDecoratorFactory;

import java.io.IOException;
import java.time.Duration;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.Map;

@Component
@EnableScheduling
public class WebSocketConnectionLimitDecorator implements WebSocketHandlerDecoratorFactory {

    // limite de conexoes websocket ( maximo total de 5  ( 4 web socket + 1 http ) )
    private static final int MAX_CONNECTIONS = 4;
    private final LinkedList<WebSocketSession> sessions = new LinkedList<>();
    private static Map<String, LocalDateTime> lastMessagesMap = new HashMap<>();

    @Autowired
    private LogsService logsService;

    @Override
    public WebSocketHandlerDecorator decorate(org.springframework.web.socket.WebSocketHandler handler) {
        return new WebSocketHandlerDecorator(handler) {

            @Override
            public void afterConnectionEstablished(WebSocketSession session) throws Exception {
                synchronized (sessions) {
                    logsService.log(session, "WebSocketDecorator", "Estabeleceu Conexão WebSocket. Numero de conexoes: " + sessions.size());
                    if (sessions.size() >= MAX_CONNECTIONS) {
                        WebSocketSession oldest = sessions.removeFirst();
                        try {
                            logsService.log(oldest, "DISCONNECT", "CONEXAO MAIS ANTIGA FECHADA");
                            oldest.close(); // desconecta a mais antiga
                        } catch (IOException e) {
                            e.printStackTrace();
                        }
                    }
                    // conecta a nova
                    sessions.add(session);
                    logsService.log(session, "CONNECT", "CONEXAO MAIS RECENTE ABERTA");

                    LocalDateTime now = LocalDateTime.now();
                    lastMessagesMap.put(session.getId(), now);
                }
                super.afterConnectionEstablished(session);
            }

            @Override
            public void afterConnectionClosed(WebSocketSession session, org.springframework.web.socket.CloseStatus closeStatus) throws Exception {
                synchronized (sessions) {
                    sessions.remove(session);
                }
                super.afterConnectionClosed(session, closeStatus);
            }

            @Override
            public void handleMessage(WebSocketSession session, WebSocketMessage<?> message) throws Exception {
                String payload = message.getPayload().toString().trim();

                if (payload.startsWith("SEND")) {
                    logsService.log(message, "ON_WEBSOCKET_MSG", "Mensagem SEND recebida no chat");

                    LocalDateTime now = LocalDateTime.now();

                    lastMessagesMap.put(session.getId(), now);

                    super.handleMessage(session, message);
                } else super.handleMessage(session,message);
            }
        };
    }

    @Scheduled(fixedRate = 1000) // roda de segundo em segundo para verificar os clientes que precisam ser desconectados ( >= 5 min sem enviar msg )
    public void checkInactiveSessions() {
        synchronized (sessions) {

            for (WebSocketSession session : new LinkedList<>(sessions)) {
                LocalDateTime lastMessage = lastMessagesMap.get(session.getId());
                if (lastMessage != null &&
                        Duration.between(lastMessage, LocalDateTime.now()).getSeconds() >= 5) {
                    try {
                        logsService.log(session, "TIMEOUT", "Sessão desconectada por inatividade >= 5s");
                        sessions.remove(session);
                        lastMessagesMap.remove(session.getId());
                        session.close();
                    } catch (IOException e) {
                        e.printStackTrace();
                    }
                }
            }
        }
    }
}

package com.pedro.sd.interceptors;

import com.pedro.sd.services.LogsService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.handler.WebSocketHandlerDecorator;
import org.springframework.web.socket.handler.WebSocketHandlerDecoratorFactory;

import java.io.IOException;
import java.util.LinkedList;


@Component
public class WebSocketConnectionLimitDecorator implements WebSocketHandlerDecoratorFactory {

    // limite de conexoes websocket ( maximo total de 5 -> 4 conexoes ws persistentes + 1 http )
    private static final int MAX_CONNECTIONS = 4;
    private final LinkedList<WebSocketSession> sessions = new LinkedList<>();

    @Autowired
    private LogsService logsService;

    @Override
    public WebSocketHandlerDecorator decorate(org.springframework.web.socket.WebSocketHandler handler) {
        return new WebSocketHandlerDecorator(handler) {

            @Override
            public void afterConnectionEstablished(WebSocketSession session) throws Exception {
                synchronized (sessions) {
                    logsService.log(session,"WebSocketDecorator","Estabeleceu Conexão WebSocket. Numero de conexoes: " + sessions.size());
                    if (sessions.size() >= MAX_CONNECTIONS) {
                        WebSocketSession oldest = sessions.removeFirst();
                        try {
                            logsService.log(oldest,"DISCONNECT","CONEXAO MAIS ANTIGA FECHADA");
                            oldest.close(); // desconecta a mais antiga
                        } catch (IOException e) {
                            e.printStackTrace();
                        }
                    }
                    // conecta a nova
                    sessions.add(session);
                    logsService.log(session,"CONNECT","CONEXAO MAIS RECENTE ABERTA");
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
        };
    }
}

import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog
import requests
from datetime import datetime
import uuid
import random
import json
import time
from threading import Thread
import websocket
import logging
from urllib.parse import urlparse

BASE_URL = "http://localhost:8080"


class ChatClient:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.pending_messages = {}
        self.ws_client = None
        self.current_group_sub_id = None
        self.base_interval = 5
        self.gui = None

    def create_user(self, nickname: str):
        url = f"{BASE_URL}/nick"
        payload = {"nickname": nickname, "timestampClient": datetime.now().isoformat()}
        response = self.session.post(url, json=payload)
        response.raise_for_status()

    def create_group(self, name: str):
        url = f"{BASE_URL}/groups"
        payload = {"name": name}
        response = self.session.post(url, json=payload)
        response.raise_for_status()

    def list_groups(self):
        url = f"{BASE_URL}/groups"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def get_messages(self, group_id: int, limit=50):
        url = f"{BASE_URL}/groups/{group_id}/messages"
        params = {"limit": limit}
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def send_message(self, idemKey: str, group_id: int, text: str, nickname: str, isRetry: bool = False, messageInterval: int | None = None):
        if messageInterval is None:
            messageInterval = self.base_interval

        idemKey = idemKey
        payload = {
            "idemKey": idemKey,
            "text": text,
            "userNickname": nickname,
            "timestampClient": datetime.now().isoformat(),
            "isRetry": isRetry
        }

        self.pending_messages[idemKey] = (payload, messageInterval, group_id)
        self.gui.refresh_messages()
        try:
            self.ws_client.send(
                destination=f"/app/chat/{group_id}/send",
                body=json.dumps(payload),
                headers={}
            )
        except Exception:
            raise

    def retry_loop(self):
        def loop():
            self.retry_pending_messages()
            # agenda cada execucao de 10 em 10 segundos
            threading.Timer(10, loop).start()
        loop()

    def retry_pending_messages(self):
        for idemKey in list(self.pending_messages.keys()):
            payload, interval, group_id = self.pending_messages[idemKey]
            text = payload['text']
            nickname = payload['userNickname']
            try:
                if not self.ws_client.connected:
                    self.connect_user_to_group(group_id,nickname)
                self.send_message(idemKey, group_id, text, nickname, True, interval)
            except Exception:
                new_interval = interval * 2
                new_interval = random.uniform(0.5 * new_interval, 1.5 * new_interval)
                new_interval = min(new_interval, 600)
                threading.Timer(new_interval, self.send_message,
                                args=(idemKey, group_id, text, nickname, True, new_interval)).start()

    def connect_user_to_group(self, groupId: int, nickname: str):
        is_not_connected = self.ws_client is None or not self.ws_client.connected
        if is_not_connected:
            self.ws_client = Client("ws://localhost:8080/chat")
            on_connect_callback = lambda frame: self._on_initial_connect(groupId, nickname)
            self.ws_client.connect(connectCallback=on_connect_callback, errorCallback=self._on_ws_error)
        else:
            self._switch_group_subscription(groupId, nickname)

    def _on_initial_connect(self, groupId, nickname):
        # escuta as confirmacoes de mensagem a partir deste usuario
        self.ws_client.subscribe(f"/topic/acks.{nickname}", callback=self._on_ack_message)
        # troca o subscribe pro grupo correspondente
        self._switch_group_subscription(groupId, nickname)

    def _switch_group_subscription(self, groupId, nickname):
        if self.current_group_sub_id:
            self.ws_client.unsubscribe(self.current_group_sub_id)

        # passa a escutar as mensagens do novo grupo
        sub_id, _ = self.ws_client.subscribe(f"/topic/messages.{groupId}", callback=self._on_group_message)
        self.current_group_sub_id = sub_id

        payload = {
            "nickname": nickname,
            "timestampClient": datetime.now().isoformat(),
        }
        self.ws_client.send(
            destination=f"/app/chat/{groupId}",
            body=json.dumps(payload)
        )

    def _on_group_message(self, frame):
        if self.gui:
            self.gui.after(0, self.gui.refresh_messages)

    def _on_ack_message(self, frame):
        data = json.loads(frame.body)
        idemKey = data.get("idemKey")
        if idemKey and idemKey in self.pending_messages:
            del self.pending_messages[idemKey]
        self.gui.refresh_messages()

    def _on_ws_error(self, frame):
        if self.gui:
            self.gui.after(0, lambda: messagebox.showerror("Erro de Conexão"))

class ChatGUI(tk.Tk):
    def __init__(self, client):
        super().__init__()
        self.client = client
        self.title("Chat Client")
        self.geometry("600x500")

        self.group_name = tk.StringVar()
        self.selected_group = None
        self.nickname = None

        self.create_widgets()
        self.groups = []
        self.refresh_groups()

    def create_widgets(self):
        group_frame = ttk.Frame(self)
        group_frame.pack(pady=5)
        ttk.Label(group_frame, text="Nome do grupo:").pack(side=tk.LEFT)
        ttk.Entry(group_frame, textvariable=self.group_name).pack(side=tk.LEFT)
        ttk.Button(group_frame, text="Criar grupo", command=self.create_group).pack(side=tk.LEFT)

        self.groups_list = tk.Listbox(self, height=5)
        self.groups_list.pack(fill=tk.X, padx=10)
        self.groups_list.bind("<<ListboxSelect>>", self.on_group_select)

        self.chat_area = scrolledtext.ScrolledText(self, state='disabled', height=15)
        self.chat_area.pack(fill=tk.BOTH, padx=10, pady=5, expand=True)

        msg_frame = ttk.Frame(self)
        msg_frame.pack(pady=5, fill=tk.X)
        self.msg_entry = ttk.Entry(msg_frame)
        self.msg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(msg_frame, text="Enviar", command=self.send_message).pack(side=tk.LEFT)

    def create_group(self):
        group_name = self.group_name.get().strip()
        if not group_name:
            messagebox.showwarning("Aviso", "Digite um nome para o grupo")
            return
        try:
            self.client.create_group(group_name)
            messagebox.showinfo("Sucesso", f"Grupo criado: {group_name}")
            self.refresh_groups()
        except Exception as e:
            messagebox.showerror("Erro", "Já existe um grupo com o nome informado")

    def refresh_groups(self):
        try:
            self.groups = self.client.list_groups()
            self.groups_list.delete(0, tk.END)
            for g in self.groups:
                self.groups_list.insert(tk.END, f"{g['id']} - {g['name']}")
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def on_group_select(self, event):
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            self.selected_group = self.groups[index]

            if not self.nickname:
                self.nickname = simpledialog.askstring("Nickname", "Digite seu nickname:")
                if not self.nickname:
                    messagebox.showwarning("Aviso", "Você precisa informar um nickname para entrar no grupo")
                    self.selected_group = None
                    return
                try:
                    self.client.create_user(self.nickname)
                except Exception as e:
                    messagebox.showerror("Erro", str(e))
                    self.selected_group = None
                    return

            self.client.connect_user_to_group(self.selected_group['id'], self.nickname)
            self.refresh_messages()

    def send_message(self):
        if not self.selected_group:
            messagebox.showwarning("Aviso", "Selecione um grupo primeiro")
            return
        if not self.nickname:
            messagebox.showwarning("Aviso", "Digite seu nickname antes de enviar mensagens")
            return

        text = self.msg_entry.get()
        if not text:
            return
        try:
            # forma chave de idempotencia com uuid,groupId,text,nickname
            idem_key = str(uuid.uuid4()) + "_" + str(self.selected_group['id']) + "_" + text + "_" + self.nickname
            self.client.send_message(idem_key, self.selected_group['id'], text, self.nickname, False)
            self.msg_entry.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def refresh_messages(self):
        if not self.selected_group:
            return
        try:
            messages = self.client.get_messages(self.selected_group['id'], limit=50)
            idemKeys = {m.get('idemKey') for m in messages}

            self.chat_area.config(state='normal')
            self.chat_area.delete(1.0, tk.END)

            self.chat_area.tag_configure(
                "pending",
                foreground="orange",
                background="#FFF8F0"
            )

            for payload, _, group_id in self.client.pending_messages.values():
                if group_id == self.selected_group['id']:
                    idem = payload['idemKey']
                    if idem not in idemKeys:
                        messages.append(payload)

            messages.sort(key=lambda m: m['timestampClient'])

            self.chat_area.config(state='normal')
            self.chat_area.delete(1.0, tk.END)
            for m in messages:
                ts_raw = m.get('timestampClient', None)
                if ts_raw:
                    try:
                        dt = datetime.fromisoformat(ts_raw)
                        ts = dt.strftime("%d/%m/%Y %H:%M")
                    except Exception:
                        ts = "??"
                else:
                    ts = "??"

                text = m.get('text', '')
                user_nick = m.get('userNickname', 'anonymous')

                if 'idemKey' in m and m['idemKey'] in self.client.pending_messages:
                    self.chat_area.insert(tk.END, f"[{ts}] {user_nick}: {text}   ⏳\n", "pending")
                else:
                    self.chat_area.insert(tk.END, f"[{ts}] {user_nick}: {text}\n")

            self.chat_area.config(state='disabled')
        except Exception as e:
            messagebox.showerror("Erro", str(e))


# classes para conexao WebSocket

class Client:

    def __init__(self, url, headers={}):
        self.url = url
        self.ws = websocket.WebSocketApp(self.url, headers)
        self.ws.on_open = self._on_open
        self.ws.on_message = self._on_message
        self.ws.on_error = self._on_error
        self.ws.on_close = self._on_close
        self.opened = False
        self.connected = False
        self.counter = 0
        self.subscriptions = {}
        self._connectCallback = None
        self.errorCallback = None

    def _connect(self, timeout=0):
        thread = Thread(target=self.ws.run_forever)
        thread.daemon = True
        thread.start()
        total_ms = 0
        while not self.opened:
            time.sleep(.25)
            total_ms += 250
            if 0 < timeout < total_ms:
                raise

    def _on_open(self, ws_app, *args):
        self.opened = True

    def _on_close(self, ws_app, *args):
        self.connected = False
        self._clean_up()

    def _on_error(self, ws_app, error, *args):
        logging.debug(error)

    def _on_message(self, ws_app, message, *args):
        frame = Frame.unmarshall_single(message)
        _results = []
        if frame.command == "CONNECTED":
            self.connected = True
            if self._connectCallback is not None:
                _results.append(self._connectCallback(frame))
        elif frame.command == "MESSAGE":
            subscription = frame.headers['subscription']
            if subscription in self.subscriptions:
                onreceive = self.subscriptions[subscription]
                messageID = frame.headers['message-id']
                def ack(headers):
                    if headers is None: headers = {}
                    return self.ack(messageID, subscription, headers)
                def nack(headers):
                    if headers is None: headers = {}
                    return self.nack(messageID, subscription, headers)
                frame.ack = ack
                frame.nack = nack
                _results.append(onreceive(frame))
            else:
                info = "Unhandled received MESSAGE: " + str(frame)
                logging.debug(info)
                _results.append(info)
        elif frame.command == 'RECEIPT':
            pass
        elif frame.command == 'ERROR':
            if self.errorCallback is not None:
                _results.append(self.errorCallback(frame))
        else:
            info = "Unhandled received MESSAGE: " + frame.command
            logging.debug(info)
            _results.append(info)
        return _results

    def _transmit(self, command, headers, body=None):
        out = Frame.marshall(command, headers, body)
        self.ws.send(out)

    def connect(self, login=None, passcode=None, headers=None, connectCallback=None, errorCallback=None, timeout=0):
        self._connect(timeout)
        headers = headers if headers is not None else {}
        headers['host'] = urlparse(self.url).netloc
        headers['accept-version'] = '1.0,1.1'
        headers['heart-beat'] = '5000,5000'
        if login is not None: headers['login'] = login
        if passcode is not None: headers['passcode'] = passcode
        self._connectCallback = connectCallback
        self.errorCallback = errorCallback
        self._transmit('CONNECT', headers)

    def disconnect(self, disconnectCallback=None, headers=None):
        if headers is None: headers = {}
        self._transmit("DISCONNECT", headers)
        self.ws.on_close = None
        self.ws.close()
        self._clean_up()
        if disconnectCallback is not None:
            disconnectCallback()

    def _clean_up(self):
        self.connected = False

    def send(self, destination, headers=None, body=None):
        if headers is None: headers = {}
        if body is None: body = ''
        headers['destination'] = destination
        return self._transmit("SEND", headers, body)

    def subscribe(self, destination, callback=None, headers=None):
        if headers is None: headers = {}
        if 'id' not in headers:
            headers["id"] = "sub-" + str(self.counter)
            self.counter += 1
        headers['destination'] = destination
        self.subscriptions[headers["id"]] = callback
        self._transmit("SUBSCRIBE", headers)
        def unsubscribe():
            self.unsubscribe(headers["id"])
        return headers["id"], unsubscribe

    def unsubscribe(self, id):
        del self.subscriptions[id]
        return self._transmit("UNSUBSCRIBE", {"id": id})

    def ack(self, message_id, subscription, headers):
        if headers is None: headers = {}
        headers["message-id"] = message_id
        headers['subscription'] = subscription
        return self._transmit("ACK", headers)

    def nack(self, message_id, subscription, headers):
        if headers is None: headers = {}
        headers["message-id"] = message_id
        headers['subscription'] = subscription
        return self._transmit("NACK", headers)

Byte = {
    'LF': '\x0A',
    'NULL': '\x00'
}

class Frame:
    def __init__(self, command, headers, body):
        self.command = command
        self.headers = headers
        self.body = '' if body is None else body

    def __str__(self):
        lines = [self.command]
        skipContentLength = 'content-length' in self.headers
        if skipContentLength:
            del self.headers['content-length']
        for name in self.headers:
            value = self.headers[name]
            lines.append("" + name + ":" + value)
        if self.body is not None and not skipContentLength:
            lines.append("content-length:" + str(len(self.body)))
        lines.append(Byte['LF'] + self.body)
        return Byte['LF'].join(lines)

    @staticmethod
    def unmarshall_single(data):
        lines = data.split(Byte['LF'])
        command = lines[0].strip()
        headers = {}
        i = 1
        while lines[i] != '':
            (key, value) = lines[i].split(':')
            headers[key] = value
            i += 1
        body = None if lines[i + 1] == Byte['NULL'] else lines[i + 1][:-1]
        return Frame(command, headers, body)

    @staticmethod
    def marshall(command, headers, body):
        return str(Frame(command, headers, body)) + Byte['NULL']

if __name__ == "__main__":
    client = ChatClient()
    client.retry_loop()
    app = ChatGUI(client)
    client.gui = app
    app.mainloop()
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog
import requests
from datetime import datetime
import uuid
import random
import json
import websocket


BASE_URL = "http://localhost:8080"
WS_URL = "ws://localhost:8080/chat"

class ChatClient:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.pending_messages = {}
        self.gui = None

        self.ws_client = None
        self.ws_thread = None
        self.connected = False
        self.subscriptions = {}
        self.current_group_sub_id = None
        self.initial_nickname = None
        self.initial_group_id = None

        self.base_interval = 5


    def _on_open(self, ws):
        self.connected = True
        connect_headers = {
            "accept-version": "1.2",
            "heart-beat": "10000,10000",
            "host": "localhost"
        }
        self.stomp_transmit("CONNECT", connect_headers)

    def _on_close(self, ws, close_status_code, close_msg):
        self.connected = False
        self.subscriptions.clear()

    def _on_error(self, ws, error):
        self.connected = False
        self._on_ws_error(str(error))

    def _on_message(self, ws, message):
        lines = message.split('\n')
        command = lines[0].strip()
        headers = {}
        i = 1
        while i < len(lines) and lines[i] != '':
            key, value = lines[i].split(':', 1)
            headers[key.strip()] = value.strip()
            i += 1

        body_start_index = message.find('\n\n')
        body = message[body_start_index + 2:].rstrip('\x00') if body_start_index != -1 else ''

        if command == "CONNECTED":
            if self.gui:
                # carrega as informacoes iniciais dos grupos
                self.gui.refresh_groups()

            self.subscribe(f"/topic/acks.{self.initial_nickname}", self._on_ack_message)
            if self.initial_group_id:
                self._switch_group_subscription(self.initial_group_id, self.initial_nickname)

        elif command == "MESSAGE":
            subscription_id = headers.get('subscription')
            if subscription_id in self.subscriptions:
                callback = self.subscriptions[subscription_id]
                callback(body)

        elif command == "ERROR":
            self._on_ws_error(body)

    def stomp_transmit(self, command, headers, body=None):
        self.connect_user()

        lines = [command]
        for key, value in headers.items():
            lines.append(f"{key}:{value}")

        lines.append('\n')

        frame_string = '\n'.join(lines)
        if body:
            frame_string += body

        frame_string += '\x00'

        if self.connected:
            self.ws_client.send(frame_string)

    def subscribe(self, destination, callback):
        sub_id = f"sub-{uuid.uuid4()}"
        self.subscriptions[sub_id] = callback
        headers = {
            "id": sub_id,
            "destination": destination,
            "ack": "auto"
        }
        self.stomp_transmit("SUBSCRIBE", headers)
        return sub_id

    def unsubscribe(self, sub_id):
        if sub_id in self.subscriptions:
            del self.subscriptions[sub_id]
        headers = {"id": sub_id}
        self.stomp_transmit("UNSUBSCRIBE", headers)


    def connect_user(self):
        # abre conexao websocket caso esteja desligada
        if not self.connected:
            self.ws_client = websocket.WebSocketApp(WS_URL,
                                                    on_open=self._on_open,
                                                    on_message=self._on_message,
                                                    on_error=self._on_error,
                                                    on_close=self._on_close)
            self.ws_thread = threading.Thread(target=self.ws_client.run_forever)
            self.ws_thread.daemon = True
            self.ws_thread.start()

    def _switch_group_subscription(self, groupId, nickname):
        self.connect_user()
        if self.current_group_sub_id:
            self.unsubscribe(self.current_group_sub_id)

        # subscreve no novo grupo
        sub_id = self.subscribe(f"/topic/messages.{groupId}", self._on_group_message)
        self.current_group_sub_id = sub_id

        # notifica entrada do usuario no grupo
        payload = {"nickname": nickname, "timestampClient": datetime.now().isoformat()}
        destination = f"/app/chat/{groupId}"
        headers = {'destination': destination, 'content-type': 'application/json'}
        self.stomp_transmit("SEND", headers, json.dumps(payload))

    def _on_group_message(self, body):

        # atualiza as mensagens assim que um usuario envia uma mensagem no grupo

        data = json.loads(body)
        idemKey = data.get("idemKey")

        msg = {
            "idemKey": idemKey,
            "text": data.get("text"),
            "userId": data.get("userId"),
            "userNickname": data.get("userNickname"),
            "timestampClient": data.get("timestampClient")
        }

        self.gui.messages.append(msg)

        # remove a mensagem da lista de reenvio
        if idemKey and idemKey in self.pending_messages:
            del self.pending_messages[idemKey]

        # atualiza a interface
        self.gui.refresh_messages()

    def _on_ack_message(self,body):
        return

    def _on_ws_error(self, error_message):
        self.gui.after(0, lambda: show_msg_warning(self, self.gui, "Erro", "Falha ao enviar mensagem"))
        # tenta conectar novamente

    def send_message(self, idemKey: str, group_id: int, text: str, nickname: str, isRetry: bool = False,
                     messageInterval: int | None = None):

        # registra a mensagem como pendente
        if messageInterval is None:
            messageInterval = self.base_interval
        payload = {
            "idemKey": idemKey, "text": text, "userNickname": nickname,
            "timestampClient": datetime.now().isoformat(), "isRetry": isRetry
        }
        self.pending_messages[idemKey] = (payload, messageInterval, group_id)

        # tenta conectar e realizar o envio

        self.connect_user()

        self._switch_group_subscription(group_id,nickname)

        self.gui.refresh_messages()

        # envia de forma assincrona pra nao travar o cliente
        def send_async():
            try:
                url = f"http://localhost:8080/chat/{group_id}/messages"
                headers = {'Content-Type': 'application/json'}
                requests.post(url, headers=headers, data=json.dumps(payload))
            except Exception as e:
                self.gui.after(0, lambda: show_msg_warning(self, self.gui, "Erro", "Falha ao enviar mensagem"))

        threading.Thread(target=send_async, daemon=True).start()

    def retry_loop(self):
        # envia periodicamente as mensagens que ainda nao receberam ack do servidor
        def loop():
            self.retry_pending_messages()
            threading.Timer(10, loop).start()
        loop()

    def retry_pending_messages(self):
        self.connect_user()

        print("LOOP RETRY")

        # tentativa de reenvio ( backoff + jitter )
        for idemKey in list(self.pending_messages.keys()):
            payload, interval, group_id = self.pending_messages[idemKey]
            text, nickname = payload['text'], payload['userNickname']
            try:
                self.send_message(idemKey, group_id, text, nickname, True, interval)
            except Exception:
                new_interval = min(interval * 2 * random.uniform(0.5, 1.5), 600)
                threading.Timer(new_interval, self.send_message,
                                args=(idemKey, group_id, text, nickname, True, new_interval)).start()


    def create_user(self, nickname: str):
        url = f"{BASE_URL}/nick"
        payload = {"nickname": nickname, "timestampClient": datetime.now().isoformat()}
        self.session.post(url, json=payload).raise_for_status()

    def create_group(self, name: str):
        url = f"{BASE_URL}/groups"
        payload = {"name": name}
        self.session.post(url, json=payload).raise_for_status()

    def list_groups(self):
        url = f"{BASE_URL}/groups"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def get_messages(self, group_id: int, limit=50):
        url = f"{BASE_URL}/groups/{group_id}/messages"
        response = self.session.get(url, params={"limit": limit})
        response.raise_for_status()
        return response.json()


class ChatGUI(tk.Tk):
    def __init__(self, client: ChatClient):
        super().__init__()
        self.client = client
        self.title("Chat Client")
        self.geometry("600x500")
        self.group_name = tk.StringVar()
        self.selected_group = None
        self.nickname = None
        self.reconnect_popup = None
        self.create_widgets()
        self.groups = []
        self.messages = []

    def create_widgets(self):
        group_frame = ttk.Frame(self)
        group_frame.pack(pady=5)
        ttk.Label(group_frame, text="Group Name:").pack(side=tk.LEFT)
        ttk.Entry(group_frame, textvariable=self.group_name).pack(side=tk.LEFT)
        ttk.Button(group_frame, text="Create Group", command=self.create_group).pack(side=tk.LEFT)

        self.groups_list = tk.Listbox(self, height=5)
        self.groups_list.pack(fill=tk.X, padx=10)
        self.groups_list.bind("<<ListboxSelect>>", self.on_group_select)

        self.chat_area = scrolledtext.ScrolledText(self, state='disabled', height=15)
        self.chat_area.pack(fill=tk.BOTH, padx=10, pady=5, expand=True)

        msg_frame = ttk.Frame(self)
        msg_frame.pack(pady=5, fill=tk.X)
        self.msg_entry = ttk.Entry(msg_frame)
        self.msg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(msg_frame, text="Send", command=self.send_message).pack(side=tk.LEFT)

    def create_group(self):
        group_name = self.group_name.get().strip()
        if not group_name:
            messagebox.showwarning("Aviso", "Digite um nome para o grupo:")
            return
        try:
            self.client.create_group(group_name)
            messagebox.showinfo("Success", f"Grupo criado: {group_name}")
            self.refresh_groups()
        except Exception:
            show_msg_warning(self.client, self, "Erro", "Já existe um grupo com o nome informado.")

    def refresh_groups(self):
        try:
            self.groups = self.client.list_groups()
            self.groups_list.delete(0, tk.END)
            for g in self.groups:
                self.groups_list.insert(tk.END, f"{g['id']} - {g['name']}")
        except Exception:
            show_msg_warning(self.client, self, "Erro", "Não foi possível recuperar os grupos existentes.")

    def on_group_select(self, event):
        selection = event.widget.curselection()
        if not selection: return

        index = selection[0]
        self.selected_group = self.groups[index]

        if not self.nickname:
            self.nickname = simpledialog.askstring("Nickname", "Digite seu nickname:")
        if not self.nickname:
            messagebox.showwarning("Aviso", "Você precisa ter um nickname para entrar em um grupo.")
            self.selected_group = None
            return

        try:
            self.client.create_user(self.nickname)
            self.client._switch_group_subscription(self.selected_group['id'], self.nickname)
            self.refresh_messages(True)
        except Exception as ex:
            show_msg_warning(self.client, self, "Erro", "Não foi possível entrar no grupo selecionado.")
            self.selected_group = None

    def send_message(self):
        if not self.selected_group:
            messagebox.showwarning("Aviso", "Selecione um grupo primeiro.")
            return
        text = self.msg_entry.get().strip()
        if not text: return

        try:
            self.client.send_message(str(uuid.uuid4()), self.selected_group['id'], text, self.nickname)
            self.msg_entry.delete(0, tk.END)
        except Exception:
            show_msg_warning(self.client, self, "Erro", "Não foi possível enviar a mensagem.")

    def refresh_messages(self, initialLoad: bool = False):
        if not self.selected_group: return
        try:
            self.client.connect_user()

            if initialLoad:
                self.messages = self.client.get_messages(self.selected_group['id'], limit=50)


            server_idem_keys = {m.get('idemKey') for m in self.messages}

            all_messages = list(self.messages)

            for payload, _, group_id in self.client.pending_messages.values():
                if group_id == self.selected_group['id'] and payload['idemKey'] not in server_idem_keys:
                    all_messages.append(payload)

            all_messages.sort(key=lambda m: m.get('timestampClient', ''))

            self.chat_area.config(state='normal')
            self.chat_area.delete(1.0, tk.END)
            self.chat_area.tag_configure("pending", foreground="orange")

            for m in all_messages:
                ts_raw = m.get('timestampClient')
                ts = datetime.fromisoformat(ts_raw).strftime("%H:%M:%S") if ts_raw else "??"
                user_nick = m.get('userNickname', 'system')
                text = m.get('text', '')

                if 'idemKey' in m and m['idemKey'] in self.client.pending_messages:
                    self.chat_area.insert(tk.END, f"[{ts}] {user_nick}: {text} ⏳\n", "pending")
                else:
                    self.chat_area.insert(tk.END, f"[{ts}] {user_nick}: {text}\n")

            self.chat_area.config(state='disabled')
            self.chat_area.yview(tk.END)
        except Exception as ex:
            show_msg_warning(self.client, self, "Erro", "Não foi possível recuperar as mensagens.")

    def show_reconnect_modal(self):
        if self.reconnect_popup: return
        self.reconnect_popup = tk.Toplevel(self)
        self.reconnect_popup.title("Aviso")
        self.reconnect_popup.geometry("300x80")
        self.reconnect_popup.transient(self)
        self.reconnect_popup.protocol("WM_DELETE_WINDOW", lambda: None)
        tk.Label(self.reconnect_popup, text="Conexão Perdida. Tentando Reconectar...", fg="white", bg="orange",
                 font=("Arial", 12)).pack(expand=True, fill=tk.BOTH)
        self.check_connection_status()

    def check_connection_status(self):
        if self.client.connected:
            if self.reconnect_popup:
                self.reconnect_popup.destroy()
                self.reconnect_popup = None
        else:
            self.after(500, self.check_connection_status)


def show_msg_warning(client: ChatClient, gui: ChatGUI, title: str, message: str):
    if not client.connected:
        if gui:
            gui.show_reconnect_modal()
        return
    messagebox.showwarning(title, message)


if __name__ == "__main__":
    client = ChatClient()

    app = ChatGUI(client)
    client.gui = app

    client.retry_loop()

    app.mainloop()
import random
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog
import requests
from datetime import datetime, timedelta
import uuid
import json
import websocket
import numpy as np

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
        self.is_connecting = False
        self.subscriptions = {}
        self.current_group_sub_id = None
        self.initial_nickname = None
        self.initial_group_id = None

        self.base_interval = 5

        # mede o tempo de recebimento das mensagens
        self.received_messages_timestamps = []

    def get_throughput(self, interval_seconds=60):
        # calcula a vazao de mensagens no ultimo minuto
        now = datetime.now()
        cutoff = now - timedelta(seconds=interval_seconds)
        recent_msgs = [ts for ts in self.received_messages_timestamps if ts >= cutoff]
        return len(recent_msgs) * (60 / interval_seconds)

    def spam_messages(self):

        # cria grupo teste_vazao e usuario admin para realizar o envio das mensagens automaticamente
        # utilizado pra testar throughput

        group_id = None
        nickname = "admin"

        groups = self.list_groups()
        for g in groups:
            if g['name'] == "teste_vazao":
                group_id = g['id']
                break

        if not group_id:
            self.create_group("teste_vazao")
            groups = self.list_groups()
            for g in groups:
                if g['name'] == "teste_vazao":
                    group_id = g['id']
                    break

        try:
            self.create_user(nickname)
        except:
            pass


        # inicia spam de mensagens
        num_send = 50
        def send_one_message():
            self.send_message(str(uuid.uuid4()), group_id, "TESTE VAZÃO", nickname)
            time.sleep(0.1)
        for _ in range(num_send):
            threading.Thread(target=send_one_message, daemon=True).start()

    def _on_open(self, ws):
        self.connected = True
        self.is_connecting = False
        connect_headers = {
            "accept-version": "1.2",
            "heart-beat": "10000,10000",
            "host": "localhost"
        }
        self.stomp_transmit("CONNECT", connect_headers)

    def _on_close(self, ws, close_status_code, close_msg):
        self.connected = False
        self.subscriptions.clear()
        self.current_group_sub_id = None

    def _on_error(self, ws, error):
        self.connected = False
        self.is_connecting = False
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
                self.gui.after(0,self.gui.refresh_groups)
            if self.initial_nickname:
                self.subscribe(f"/topic/acks.{self.initial_nickname}", self._on_ack_message)
            if self.initial_group_id:
                self._switch_group_subscription(self.initial_group_id, self.initial_nickname)

        elif command == "MESSAGE":
            sub_id = headers.get('subscription')
            if sub_id in self.subscriptions:
                self.subscriptions[sub_id](body)

        elif command == "ERROR":
            self._on_ws_error(body)

    def connect_user(self):
        if self.connected or self.is_connecting:
            return

        self.is_connecting = True

        if self.ws_client:
            try:
                self.ws_client.close()
            except:
                pass

        self.ws_client = websocket.WebSocketApp(
            WS_URL,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close
        )
        self.ws_thread = threading.Thread(target=self._run_ws)
        self.ws_thread.daemon = True
        self.ws_thread.start()

    def _run_ws(self):
        try:
            self.ws_client.run_forever()
        finally:
            self.is_connecting = False
            self.connected = False

    def stomp_transmit(self, command, headers, body=None):
        if not self.connected:
            return
        lines = [command] + [f"{k}:{v}" for k, v in headers.items()] + ['\n']
        frame = '\n'.join(lines) + (body or '') + '\x00'
        self.ws_client.send(frame)

    def subscribe(self, destination, callback):
        sub_id = f"sub-{uuid.uuid4()}"
        self.subscriptions[sub_id] = callback
        headers = {"id": sub_id, "destination": destination, "ack": "auto"}
        self.stomp_transmit("SUBSCRIBE", headers)
        return sub_id

    def unsubscribe(self, sub_id):
        if sub_id in self.subscriptions:
            del self.subscriptions[sub_id]
        headers = {"id": sub_id}
        self.stomp_transmit("UNSUBSCRIBE", headers)

    def _switch_group_subscription(self, group_id, nickname):
        if not self.current_group_sub_id:
            self.current_group_sub_id = self.subscribe(f"/topic/messages.{group_id}", self._on_group_message)
        if self.current_group_sub_id != group_id:
            self.unsubscribe(self.current_group_sub_id)
            self.current_group_sub_id = self.subscribe(f"/topic/messages.{group_id}", self._on_group_message)

        payload = {"nickname": nickname, "timestampClient": datetime.now().isoformat()}
        destination = f"/app/chat/{group_id}"
        headers = {"destination": destination, "content-type": "application/json"}

        self.stomp_transmit("SEND", headers, json.dumps(payload))

    def _on_group_message(self, body):
        data = json.loads(body)
        idemKey = data.get("idemKey")

        msg = {
            "idemKey": idemKey,
            "text": data.get("text"),
            "userId": data.get("userId"),
            "userNickname": data.get("userNickname"),
            "timestampClient": data.get("timestampClient")
        }

        self.received_messages_timestamps.append(datetime.now())

        self.gui.messages.append(msg)
        if idemKey and idemKey in self.pending_messages:
            del self.pending_messages[idemKey]

        if self.gui:
            self.gui.after(0, self.gui.refresh_messages,False)

    def _on_ack_message(self, body):
        pass

    def _on_ws_error(self, error_message):
        self.connected = False
        if self.gui:
            self.gui.after(0, lambda: show_msg_warning(self, self.gui, "Erro", "Falha ao enviar mensagem"))

    def retry_pending_messages(self):
        # tentativa de reenvio com backoff + jitter
        for idemKey in list(self.pending_messages.keys()):
            payload, interval, group_id = self.pending_messages[idemKey]
            text, nickname = payload['text'], payload['userNickname']
            try:
                self.send_message(idemKey, group_id, text, nickname,True, interval, payload['timestampClient'])
            except Exception:
                new_interval = min(interval * 2 * random.uniform(0.5, 1.5), 600)
                threading.Timer(new_interval, self.send_message,
                                args=(idemKey, group_id, text, nickname, True, new_interval, payload['timestampClient'])).start()

    def send_message(self, idemKey, group_id, text, nickname, isRetry=False, messageInterval=None, timestampClient=None):
        if messageInterval is None:
            messageInterval = self.base_interval
        payload = {
            "idemKey": idemKey,
            "text": text,
            "userNickname": nickname,
            "timestampClient": timestampClient if timestampClient else datetime.now().isoformat(),
            "isRetry": isRetry,
            "sentTime": datetime.now().isoformat()
        }
        self.pending_messages[idemKey] = (payload, messageInterval, group_id)
        self._switch_group_subscription(group_id, nickname)

        if self.gui:
            self.gui.after(0, self.gui.refresh_messages,False)

        def send_async():
            try:
                url = f"{BASE_URL}/chat/{group_id}/messages"
                self.session.post(url, json=payload)
            except:
                pass

        threading.Thread(target=send_async, daemon=True).start()

    def retry_loop(self, test_throughput: bool = False):
        def loop():
            nonlocal test_throughput
            if test_throughput:
                spamMessages = True
                test_throughput = False
            else:
                spamMessages = False

            self.connect_user()
            self.retry_pending_messages()

            # calcula e imprime a vazao (mensagens/minuto)

            if spamMessages:
                client.spam_messages()

            throughput = self.get_throughput(60)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Vazão: {throughput:.2f} msg/min")

            threading.Timer(10, loop).start()
        loop()

    def create_user(self, nickname):
        url = f"{BASE_URL}/nick"
        payload = {"nickname": nickname, "timestampClient": datetime.now().isoformat()}
        self.session.post(url, json=payload).raise_for_status()

    def create_group(self, name):
        url = f"{BASE_URL}/groups"
        payload = {"name": name}
        self.session.post(url, json=payload).raise_for_status()

    def list_groups(self):
        url = f"{BASE_URL}/groups"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def get_messages(self, group_id, limit=10):
        url = f"{BASE_URL}/groups/{group_id}/messages"
        response = self.session.get(url, params={"limit": limit})
        response.raise_for_status()
        return response.json()


class ChatGUI(tk.Tk):
    def __init__(self, client):
        super().__init__()
        self.client = client
        self.title("Chat")
        self.geometry("1200x800")
        self.group_name = tk.StringVar()
        self.selected_group = None
        self.nickname = None
        self.reconnect_popup = None
        self.groups = []
        self.messages = []
        self.create_widgets()

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
            messagebox.showwarning("Aviso", "Digite um nome para o grupo")
            return
        try:
            self.client.create_group(group_name)
            messagebox.showinfo("Success", f"Grupo criado: {group_name}")
        except:
            messagebox.showwarning("Erro","Grupo já existe")

        self.after(0, self.refresh_groups)

    def refresh_groups(self):
        try:
            self.groups = self.client.list_groups()
            self.groups_list.delete(0, tk.END)
            for g in self.groups:
                self.groups_list.insert(tk.END, f"{g['id']} - {g['name']}")
        except:
            messagebox.showwarning("Erro","Não foi possível recuperar os grupos")

    def on_group_select(self, event):
        selection = event.widget.curselection()
        if not selection: return
        index = selection[0]
        self.selected_group = self.groups[index]

        if not self.nickname:
            self.nickname = simpledialog.askstring("Nickname", "Digite seu nickname:")
        if not self.nickname:
            messagebox.showwarning("Aviso", "Você precisa de um nickname")
            self.selected_group = None
            return

        try:
            self.client.create_user(self.nickname)
            self.client._switch_group_subscription(self.selected_group['id'], self.nickname)

            self.after(0, self.refresh_messages, True)
        except:
            messagebox.showwarning("Erro","Não foi possível entrar no grupo")
            self.selected_group = None


    def send_message(self):
        if not self.selected_group: return
        text = self.msg_entry.get().strip()
        if not text: return
        try:
            self.client.send_message(str(uuid.uuid4()), self.selected_group['id'], text, self.nickname)
            self.msg_entry.delete(0, tk.END)
        except:
            messagebox.showwarning("Erro","Não foi possível enviar mensagem")

    def refresh_messages(self, initialLoad=False):
        if not self.selected_group: return
        try:
            if initialLoad:
                self.messages = self.client.get_messages(self.selected_group['id'], limit=10)

            server_idem_keys = {m.get('idemKey') for m in self.messages}

            # exibe as 10 ultimas confirmadas pelo servidor + as pendentes

            all_messages = list(self.messages)
            all_messages.sort(key=lambda m: m.get('timestampClient', ''))

            all_messages = all_messages[-10:]

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
        except:
            messagebox.showwarning("Erro","Não foi possível recuperar mensagens")

    def show_reconnect_modal(self):
        if self.reconnect_popup: return
        self.reconnect_popup = tk.Toplevel(self)
        self.reconnect_popup.title("Aviso")
        self.reconnect_popup.geometry("300x80")
        self.reconnect_popup.transient(self)
        self.reconnect_popup.protocol("WM_DELETE_WINDOW", lambda: None)
        tk.Label(self.reconnect_popup, text="Conexão Perdida. Tentando Reconectar...",
                 fg="white", bg="orange", font=("Arial", 12)).pack(expand=True, fill=tk.BOTH)
        self.check_connection_status()

    def check_connection_status(self):
        if self.client.connected:
            if self.reconnect_popup:
                self.reconnect_popup.destroy()
                self.reconnect_popup = None
        else:
            self.after(500, self.check_connection_status)


def show_msg_warning(client, gui, title, message):
    if not client.connected and gui:
        gui.show_reconnect_modal()
        return
    messagebox.showwarning(title, message)


if __name__ == "__main__":
    client = ChatClient()
    app = ChatGUI(client)
    client.gui = app
    client.connect_user()

    def start_test_throughput():
        test_throughput = messagebox.askyesno("Teste de Throughput", "Deseja testar o Throughput (spam automatico de mensagens) ?")
        client.retry_loop(test_throughput)

    app.after(100, start_test_throughput)
    app.mainloop()
import random
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog
import requests
from datetime import datetime, timedelta, timezone
import uuid
import json
import websocket

BASE_URL = "http://127.0.0.1"
WS_URL = "ws://127.0.0.1/chat"


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

    def spam_messages(self):

        # cria grupo teste_vazao e usuario admin para realizar o envio das mensagens automaticamente
        # utilizado pra testar throughput

        if self.gui:
            self.gui.disable_all_controls()
            self.gui.open_stress_test_popup()

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

        def send_messages_loop(numSend):
            for _ in range(numSend):
                self.send_message(str(uuid.uuid4()), group_id, "TESTE VAZÃO", nickname)
                time.sleep(0.05)
            if self.gui:
                self.gui.enable_all_controls()
                self.gui.close_stress_test_popup()

        thread = threading.Thread(target=send_messages_loop, args=(100,), daemon=True)
        thread.start()

    def _on_open(self, ws):
        self.connected = True
        self.is_connecting = False
        connect_headers = {
            "accept-version": "1.2",
            "heart-beat": "10000,10000",
            "host": "127.0.0.1"
        }
        self.stomp_transmit("CONNECT", connect_headers)

    def _on_close(self, ws, close_status_code, close_msg):
        self.connected = False
        self.subscriptions.clear()
        self.current_group_sub_id = None
        print("Cliente Desconectado")
        self.gui.show_reconnect_modal()

    def _on_error(self, ws, error):
        print(error)
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

            print("Cliente Conectado")

            # recupera as mensagens perdidas pelo servidor
            if self.gui:
                self.gui.after(0, self.gui.refresh_messages, True)

            # fecha popup de reconexao caso esteja aberto
            if self.gui and self.gui.reconnect_popup:
                self.gui.reconnect_popup.destroy()
                self.gui.reconnect_popup = None

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

        payload = {"nickname": nickname, "timestampClient": datetime.now(timezone.utc).isoformat()}
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

        self.gui.messages.append(msg)
        if idemKey and idemKey in self.pending_messages:
            del self.pending_messages[idemKey]

        if self.gui:
            self.gui.after(0, self.gui.refresh_messages,False)

    def _on_ack_message(self, body):
        pass

    def _on_ws_error(self, error_message):
        self.connected = False
        self.is_connecting = False

    def _send_with_backoff(self, idemKey):
        if idemKey not in self.pending_messages:
            return

        payload, interval, group_id = self.pending_messages[idemKey]
        text, nickname = payload['text'], payload['userNickname']

        self.send_message(idemKey, group_id, text, nickname, True, interval)

        new_interval = min(interval * 2 * random.uniform(0.5, 1.5), 600)

        self.pending_messages[idemKey] = (payload, new_interval, group_id)

        threading.Timer(new_interval, lambda: self._send_with_backoff(idemKey)).start()


    def send_message(self, idemKey, group_id, text, nickname, isRetry=False, messageInterval=None):
        if messageInterval is None:
            messageInterval = self.base_interval

        payload = {
            "idemKey": idemKey,
            "text": text,
            "userNickname": nickname,
            "isRetry": isRetry,
        }

        self.pending_messages[idemKey] = (payload, messageInterval, group_id)
        self._switch_group_subscription(group_id, nickname)

        if self.gui:
            self.gui.after(0, self.gui.refresh_messages,False)

        def send_async():
            try:
                payload["timestampClient"] = datetime.now(timezone.utc).isoformat()
                url = f"{BASE_URL}/chat/{group_id}/messages"
                self.session.post(url, json=payload)
            except:
                pass

        threading.Thread(target=send_async, daemon=True).start()

        if not isRetry:
            # tentativas de reenvio com backoff + jitter
            threading.Timer(messageInterval, lambda: self._send_with_backoff(idemKey)).start()

    def retry_loop(self):
        def loop():
            self.connect_user()
            threading.Timer(10, loop).start()
        loop()

    def create_user(self, nickname):
        url = f"{BASE_URL}/nick"
        payload = {"nickname": nickname, "timestampClient": datetime.now(timezone.utc).isoformat()}
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


    def get_messages(self, group_id, limit=10, since=None):
        url = f"{BASE_URL}/groups/{group_id}/messages"
        params = {"limit": limit}
        if since:
            if since.tzinfo is None:
                since = since.replace(tzinfo=timezone.utc)
            params["since"] = since.isoformat().replace('+00:00', 'Z')  # garante ISO válido
        response = self.session.get(url, params=params)
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
        self.stress_test_popup = None
        self.groups = []
        self.messages = []
        self.since_filter = None
        self.limit_filter = 10
        self.create_widgets()

    def create_widgets(self):
        spam_frame = ttk.Frame(self)
        spam_frame.pack(pady=5, fill=tk.X)

        tk.Button(
            spam_frame,
            text="Teste de Carga",
            command=self.client.spam_messages,
            bg="orange",
        ).pack(side=tk.LEFT, padx=5)

        since_frame = ttk.Frame(self)
        since_frame.pack(pady=5, fill=tk.X)

        ttk.Label(since_frame, text="Data (DD-MM-YYYY):").pack(side=tk.LEFT, padx=2)
        self.date_entry = ttk.Entry(since_frame, width=12)
        self.date_entry.pack(side=tk.LEFT, padx=2)

        ttk.Label(since_frame, text="Hora (HH:MM:SS):").pack(side=tk.LEFT, padx=2)
        self.time_entry = ttk.Entry(since_frame, width=10)
        self.time_entry.pack(side=tk.LEFT, padx=2)

        ttk.Button(since_frame, text="Aplicar filtro", command=self.apply_since_filter).pack(side=tk.LEFT, padx=5)
        ttk.Button(since_frame, text="Resetar", command=self.reset_since).pack(side=tk.LEFT, padx=5)

        limit_frame = ttk.Frame(self)
        limit_frame.pack(pady=5, fill=tk.X)

        ttk.Label(limit_frame, text="Limite de mensagens:").pack(side=tk.LEFT, padx=2)
        self.limit_entry = ttk.Entry(limit_frame, width=5)
        self.limit_entry.insert(0, "10")  # valor padrão
        self.limit_entry.pack(side=tk.LEFT, padx=2)
        ttk.Button(limit_frame, text="Aplicar limite", command=self.apply_limit).pack(side=tk.LEFT, padx=5)


        group_frame = ttk.Frame(self)
        group_frame.pack(pady=5)
        ttk.Label(group_frame, text="Nome do Grupo:").pack(side=tk.LEFT)
        ttk.Entry(group_frame, textvariable=self.group_name).pack(side=tk.LEFT)
        ttk.Button(group_frame, text="Criar Grupo", command=self.create_group).pack(side=tk.LEFT)

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

    def apply_since_filter(self):
        date_str = self.date_entry.get().strip()
        time_str = self.time_entry.get().strip()
        if not date_str or not time_str:
            messagebox.showwarning("Aviso", "Preencha data e hora para aplicar o filtro")
            return
        try:
            dt = datetime.strptime(f"{date_str} {time_str}", "%d-%m-%Y %H:%M:%S")
            dt = dt + timedelta(hours=3)
            self.since_filter = dt.replace(tzinfo=timezone.utc)
            self.refresh_messages(initialLoad=True)
        except ValueError:
            messagebox.showwarning("Erro", "Formato de data/hora inválido! Use DD-MM-YYYY e HH:MM:SS")

    def apply_limit(self):
        try:
            limit = int(self.limit_entry.get().strip())
            if limit <= 0:
                raise ValueError
            self.limit_filter = limit
            self.refresh_messages(initialLoad=True)
        except ValueError:
            messagebox.showwarning("Erro", "O limite deve ser um número inteiro positivo")

    def reset_since(self):
        self.since_filter = None
        self.date_entry.delete(0, tk.END)
        self.time_entry.delete(0, tk.END)
        self.refresh_messages(initialLoad=True)

    def create_group(self):
        group_name = self.group_name.get().strip()
        if not group_name:
            messagebox.showwarning("Aviso", "Digite um nome para o grupo")
            return
        try:
            self.client.create_group(group_name)
            messagebox.showinfo("Sucesso", f"Grupo criado: {group_name}")
        except:
            messagebox.showwarning("Erro","Grupo já existe")

        self.after(0, self.refresh_groups)

    def refresh_groups(self):
        try:
            self.groups = self.client.list_groups()
            self.groups_list.delete(0, tk.END)
            for g in self.groups:
                self.groups_list.insert(tk.END, f"Grupo - {g['name']}")
        except Exception as e:
            print(e)
            messagebox.showwarning("Erro","Não foi possível recuperar os grupos")

    def on_group_select(self, event):
        selection = event.widget.curselection()
        if not selection: return
        index = selection[0]
        self.selected_group = self.groups[index]

        self.highlight_selected_group()

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
        if not text:
            messagebox.showwarning("Aviso", "A mensagem não pode ser vazia")
            return
        try:
            self.client.send_message(str(uuid.uuid4()), self.selected_group['id'], text, self.nickname)
            self.msg_entry.delete(0, tk.END)
        except:
            messagebox.showwarning("Erro","Não foi possível enviar mensagem")

    def refresh_messages(self, initialLoad=False):
        if not self.selected_group:
            return
        try:
            if initialLoad:
                self.messages = self.client.get_messages(self.selected_group['id'], limit=self.limit_filter, since = self.since_filter)

            all_messages = list(self.messages)
            for payload, _, group_id in self.client.pending_messages.values():
                if group_id == self.selected_group['id']:
                    all_messages.append(payload)

            unique = {}
            for m in all_messages:
                unique[m.get("idemKey")] = m
            all_messages = list(unique.values())

            all_messages.sort(key=lambda m: m.get('timestampClient', ''))

            all_messages = all_messages[-self.limit_filter:]

            self.chat_area.config(state='normal')
            self.chat_area.delete(1.0, tk.END)
            self.chat_area.tag_configure("pending", foreground="orange")

            for m in all_messages:
                ts_raw = m.get('timestampClient')
                if ts_raw:
                    dt = datetime.fromisoformat(ts_raw)
                    # subtrai 3 horas
                    dt_local = dt - timedelta(hours=3)
                    ts = dt_local.strftime("%H:%M:%S")
                else:
                    ts = "??"
                user_nick = m.get('userNickname', 'system')
                text = m.get('text', '')

                if (m.get("idemKey") in self.client.pending_messages
                        and m.get("idemKey") not in {x.get("idemKey") for x in self.messages}):
                    self.chat_area.insert(tk.END, f"[{ts}] {user_nick}: {text} ⏳\n", "pending")
                else:
                    self.chat_area.insert(tk.END, f"[{ts}] {user_nick}: {text}\n")

            self.chat_area.config(state='disabled')
            self.chat_area.yview(tk.END)
        except:
            messagebox.showwarning("Erro", "Não foi possível recuperar mensagens")

    def show_reconnect_modal(self):
        if self.reconnect_popup or client.connected:
            return

        self.reconnect_popup = tk.Toplevel(self)
        self.reconnect_popup.title("Aviso")
        self.reconnect_popup.transient(self)  # mantém acima da janela principal
        self.reconnect_popup.protocol("WM_DELETE_WINDOW", lambda: None)

        width, height = 300, 80

        parent_x = self.winfo_x()
        parent_y = self.winfo_y()
        parent_width = self.winfo_width()
        parent_height = self.winfo_height()

        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2

        self.reconnect_popup.geometry(f"{width}x{height}+{x}+{y}")

        tk.Label(
            self.reconnect_popup,
            text="Conexão Perdida. Tentando Reconectar...",
            fg="white",
            bg="orange",
            font=("Arial", 12)
        ).pack(expand=True, fill=tk.BOTH)

    def highlight_selected_group(self):
        self.groups_list.selection_clear(0, tk.END)

        if self.selected_group:
            try:
                index = self.groups.index(self.selected_group)
                self.groups_list.selection_set(index)
                self.groups_list.config(selectbackground="green", selectforeground="white")
            except ValueError:
                pass

    def disable_all_controls(self):
        self.groups_list.config(state='disabled')
        for child in self.children.values():
            if isinstance(child, ttk.Frame):
                for w in child.winfo_children():
                    if isinstance(w, ttk.Entry) or (
                            isinstance(w, ttk.Button) and w.cget("text") in ["Criar Grupo", "Enviar"]):
                        w.config(state='disabled')
        self.msg_entry.config(state='disabled')

    def enable_all_controls(self):
        self.groups_list.config(state='normal')
        for child in self.children.values():
            if isinstance(child, ttk.Frame):
                for w in child.winfo_children():
                    if isinstance(w, ttk.Entry) or (
                            isinstance(w, ttk.Button) and w.cget("text") in ["Criar Grupo", "Enviar"]):
                        w.config(state='normal')
        self.msg_entry.config(state='normal')
        self.close_temp_warning()

    def close_temp_warning(self):
        if hasattr(self, "temp_popup") and self.temp_popup:
            self.temp_popup.destroy()
            self.temp_popup = None

    def open_stress_test_popup(self):
        self.stress_test_popup = tk.Toplevel(self)
        self.stress_test_popup.title("Aviso")
        self.stress_test_popup.geometry("500x200")
        self.stress_test_popup.transient(self)
        self.stress_test_popup.grab_set()
        tk.Label(self.stress_test_popup, text="Teste de carga em execução. Aguarde alguns segundos...", bg="orange",
                 font=("Arial", 12)).pack(expand=True, fill=tk.BOTH)

    def close_stress_test_popup(self):
        self.stress_test_popup.destroy()
        self.stress_test_popup = None

if __name__ == "__main__":
    client = ChatClient()
    app = ChatGUI(client)
    client.gui = app
    client.connect_user()
    client.retry_loop()
    app.mainloop()
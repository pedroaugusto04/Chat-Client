import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog
import requests
from datetime import datetime
import uuid
import random

BASE_URL = "http://localhost:8080"

class ChatClient:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.pending_messages = {}
        self.base_interval = 5

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

    def send_message(self, idemKey: str, group_id: int, text: str, nickname: str, isRetry: bool = False, messageInterval: int | None = None):

        if messageInterval is None:
            messageInterval = self.base_interval

        url = f"{BASE_URL}/groups/{group_id}/messages"

        idemKey = idemKey
        payload = {
            "idemKey": idemKey,
            "text": text,
            "userNickname": nickname,
            "timestampClient": datetime.now().isoformat(),
            "isRetry": isRetry
        }

        self.pending_messages[idemKey] = (group_id, text, nickname, messageInterval)

        response = self.session.post(url, json=payload)
        response.raise_for_status()

        if idemKey in self.pending_messages:
            del self.pending_messages[idemKey]


    def get_messages(self, group_id: int, limit=50):
        url = f"{BASE_URL}/groups/{group_id}/messages"
        params = {"limit": limit}
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def retry_loop(self):
        def loop():
            self.retry_pending_messages()
            # agenda cada execucao de 10 em 10 segundos
            threading.Timer(10, loop).start()
        loop()

        threading.Thread(target=loop, daemon=True).start()

    def retry_pending_messages(self):
        for idemKey in list(self.pending_messages.keys()):
            group_id, text, nickname, interval = self.pending_messages[idemKey]
            try:
                self.send_message(idemKey,group_id, text, nickname,True, interval)
            except Exception:
                new_interval = interval * 2 # backoff
                new_interval = random.uniform(0.5 * new_interval, 1.5 * new_interval) # jitter
                # limita em 10 minutos
                new_interval = min(new_interval,600)

                threading.Timer(new_interval, self.send_message,
                                args=(idemKey, group_id, text, nickname, True, new_interval)).start()


class ChatGUI(tk.Tk):
    def __init__(self, client):
        super().__init__()
        self.client = client
        self.title("Chat Client")
        self.geometry("600x500")

        self.group_name = tk.StringVar()
        self.selected_group = None
        self.nickname = None  # será definido quando o usuário entrar no grupo

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

            self.client.send_message(idem_key, self.selected_group['id'], text, self.nickname,False)
            self.msg_entry.delete(0, tk.END)
            self.refresh_messages()
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def refresh_messages(self):
        if not self.selected_group:
            return
        try:
            messages = self.client.get_messages(self.selected_group['id'], limit=10)
            self.chat_area.config(state='normal')
            self.chat_area.delete(1.0, tk.END)
            for m in messages:
                ts = m.get('timestampClient', '??')
                text = m.get('text', '')
                user_nick = m.get('userNickname', 'anonymous')
                self.chat_area.insert(tk.END, f"[{ts}] {user_nick}: {text}\n")
            self.chat_area.config(state='disabled')
        except Exception as e:
            messagebox.showerror("Erro", str(e))




if __name__ == "__main__":
    client = ChatClient()
    client.retry_loop()
    app = ChatGUI(client)
    app.mainloop()

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import requests
from datetime import datetime
import uuid

BASE_URL = "http://localhost:8080"

class ChatClient:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def create_user(self, name: str):
        url = f"{BASE_URL}/nick"
        payload = {"name": name}
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    def create_group(self, name: str):
        url = f"{BASE_URL}/groups"
        payload = {"name": name}  # corresponde ao GroupDTO do backend
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    def list_groups(self):
        url = f"{BASE_URL}/groups"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def send_message(self, group_id: int, text: str):
        url = f"{BASE_URL}/groups/{group_id}/messages"
        payload = {
            "idemKey": str(uuid.uuid4()),
            "text": text,
            "timestamp_client": datetime.now().isoformat()
        }
        response = self.session.post(url, json=payload)
        response.raise_for_status()

    def get_messages(self, group_id: int, limit=50):
        url = f"{BASE_URL}/groups/{group_id}/messages"
        params = {"limit": limit}
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()


class ChatGUI(tk.Tk):
    def __init__(self, client):
        super().__init__()
        self.client = client
        self.title("Chat Client")
        self.geometry("600x500")

        self.user_name = tk.StringVar()
        self.group_name = tk.StringVar()
        self.selected_group = None

        self.create_widgets()
        self.groups = []
        self.refresh_groups()

    def create_widgets(self):
        # Usuario
        user_frame = ttk.Frame(self)
        user_frame.pack(pady=5)
        ttk.Label(user_frame, text="Nome do usuário:").pack(side=tk.LEFT)
        ttk.Entry(user_frame, textvariable=self.user_name).pack(side=tk.LEFT)
        ttk.Button(user_frame, text="Criar usuário", command=self.create_user).pack(side=tk.LEFT)

        group_frame = ttk.Frame(self)
        group_frame.pack(pady=5)
        ttk.Label(group_frame, text="Nome do grupo:").pack(side=tk.LEFT)
        ttk.Entry(group_frame, textvariable=self.group_name).pack(side=tk.LEFT)
        ttk.Button(group_frame, text="Criar grupo", command=self.create_group).pack(side=tk.LEFT)
        ttk.Button(group_frame, text="Atualizar grupos", command=self.refresh_groups).pack(side=tk.LEFT)

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

        ttk.Button(self, text="Atualizar mensagens", command=self.refresh_messages).pack(pady=5)

    def create_user(self):
        try:
            user = self.client.create_user(self.user_name.get())
            messagebox.showinfo("Sucesso", f"Usuário criado: {user}")
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def create_group(self):
        group_name = self.group_name.get().strip()
        if not group_name:
            messagebox.showwarning("Aviso", "Digite um nome para o grupo")
            return
        try:
            group = self.client.create_group(group_name)
            messagebox.showinfo("Sucesso", f"Grupo criado: {group_name}")
            self.refresh_groups()
        except Exception as e:
            messagebox.showerror("Erro", str(e))

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
            self.refresh_messages()

    def send_message(self):
        if not self.selected_group:
            messagebox.showwarning("Aviso", "Selecione um grupo primeiro")
            return
        text = self.msg_entry.get()
        if not text:
            return
        try:
            self.client.send_message(self.selected_group['id'], text)
            self.msg_entry.delete(0, tk.END)
            self.refresh_messages()
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def refresh_messages(self):
        if not self.selected_group:
            return
        try:
            messages = self.client.get_messages(self.selected_group['id'], limit=50)
            self.chat_area.config(state='normal')
            self.chat_area.delete(1.0, tk.END)
            for m in messages:
                ts = m['timestamp_client']
                text = m['text']
                user_id = m.get('userId', 'unknown')
                self.chat_area.insert(tk.END, f"[{ts}] User {user_id}: {text}\n")
            self.chat_area.config(state='disabled')
        except Exception as e:
            messagebox.showerror("Erro", str(e))


if __name__ == "__main__":
    client = ChatClient()
    app = ChatGUI(client)
    app.mainloop()

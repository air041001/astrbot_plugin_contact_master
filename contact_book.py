import json
import os
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class Contact:
    name: str           # 显示名
    umo: str            # 完整 UMO，如 default:FriendMessage:123456
    aliases: list[str]  # 别名，如 ["主人", "admin", "老板"]
    platform: str       # 平台前缀
    msg_type: str       # FriendMessage / GroupMessage
    uid: str            # 纯 ID


class ContactBook:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.contacts: dict[str, Contact] = {}  # name -> Contact
        self.alias_map: dict[str, str] = {}      # alias -> name
        self._load()

    def _file_path(self) -> str:
        return os.path.join(self.data_dir, "contact_book.json")

    def _load(self):
        path = self._file_path()
        if not os.path.exists(path):
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for name, c in data.items():
                contact = Contact(**c)
                self.add(contact, persist=False)
        except Exception:
            pass

    def _save(self):
        os.makedirs(self.data_dir, exist_ok=True)
        data = {name: asdict(c) for name, c in self.contacts.items()}
        with open(self._file_path(), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add(self, contact: Contact, persist: bool = True):
        self.contacts[contact.name] = contact
        for alias in contact.aliases:
            self.alias_map[alias.lower()] = contact.name
        if persist:
            self._save()

    def remove(self, name: str):
        if name not in self.contacts:
            return False
        contact = self.contacts.pop(name)
        for alias in contact.aliases:
            self.alias_map.pop(alias.lower(), None)
        self._save()
        return True

    def resolve(self, query: str) -> Optional[Contact]:
        """支持 name 或 alias 查找"""
        query = query.lower().strip()
        # 直接名匹配
        if query in self.contacts:
            return self.contacts[query]
        # 别名匹配
        if query in self.alias_map:
            return self.contacts[self.alias_map[query]]
        # 模糊匹配（前缀）
        for name, contact in self.contacts.items():
            if name.lower().startswith(query) or query in name.lower():
                return contact
            for alias in contact.aliases:
                if alias.lower().startswith(query) or query in alias.lower():
                    return contact
        return None

    def list_all(self) -> list[Contact]:
        return list(self.contacts.values())

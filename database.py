# database.py
import os
import json
import random
import string
import threading
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple, Any
from config import *

file_lock = threading.Lock()

PLATFORM_MAP = {
    1: "Garena", 3: "Facebook", 4: "Guest", 5: "VK",
    6: "Huawei", 7: "Apple", 8: "Google", 10: "GameCenter",
    11: "X (Twitter)", 13: "Apple ID", 28: "Line", 35: "TikTok"
}

def convert_seconds(s: int, lang: str = LANG_AR) -> str:
    if s <= 0: return "0s"
    d, h = divmod(s, 86400)
    h, m = divmod(h, 3600)
    m, s = divmod(m, 60)
    parts = []
    if lang == LANG_AR:
        if d: parts.append(f"{d} يوم")
        if h: parts.append(f"{h} ساعة")
        if m: parts.append(f"{m} دقيقة")
        if s: parts.append(f"{s} ثانية")
    else:
        if d: parts.append(f"{d}d")
        if h: parts.append(f"{h}h")
        if m: parts.append(f"{m}m")
        if s: parts.append(f"{s}s")
    return " ".join(parts) if parts else "0s"

class DataManager:
    @staticmethod
    def load(filename: str, default: Any = None) -> Any:
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return default or {}
        except Exception:
            return default or {}
    
    @staticmethod
    def save(filename: str, data: Any) -> bool:
        global file_lock
        try:
            with file_lock:
                temp_file = f"{filename}.tmp"
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                os.replace(temp_file, filename)
            return True
        except Exception:
            return False
    
    @classmethod
    def get_keys(cls) -> Dict:
        return cls.load(KEYS_FILE, {})
    
    @classmethod
    def save_keys(cls, keys: Dict) -> bool:
        return cls.save(KEYS_FILE, keys)
    
    @classmethod
    def get_users(cls) -> Dict:
        return cls.load(USERS_FILE, {})
    
    @classmethod
    def save_users(cls, users: Dict) -> bool:
        return cls.save(USERS_FILE, users)
    
    @classmethod
    def ensure_user(cls, user_id: int, username: str = "", first_name: str = "") -> None:
        users = cls.get_users()
        uid = str(user_id)
        if uid not in users:
            users[uid] = {
                "id": user_id, "username": username, "first_name": first_name,
                "joined_at": datetime.now().isoformat(), "keys": [],
                "language": LANG_AR, "is_admin": (user_id == OWNER_ID),
                "accounts": {}
            }
        else:
            users[uid]["username"] = username or users[uid].get("username", "")
            users[uid]["first_name"] = first_name or users[uid].get("first_name", "")
            users[uid].setdefault("language", LANG_AR)
            users[uid].setdefault("is_admin", user_id == OWNER_ID)
            users[uid].setdefault("accounts", {})
        cls.save_users(users)
    
    @classmethod
    def get_user_lang(cls, user_id: int) -> str:
        users = cls.get_users()
        return users.get(str(user_id), {}).get("language", LANG_AR)
    
    @classmethod
    def set_user_lang(cls, user_id: int, lang: str) -> bool:
        users = cls.get_users()
        uid = str(user_id)
        if uid in users:
            users[uid]["language"] = lang
            return cls.save_users(users)
        return False
    
    @classmethod
    def is_admin(cls, user_id: int) -> bool:
        users = cls.get_users()
        u_data = users.get(str(user_id), {})
        return u_data.get("is_admin", False) or user_id == OWNER_ID
    
    @classmethod
    def promote_to_admin(cls, user_id: int) -> bool:
        users = cls.get_users()
        uid = str(user_id)
        if uid in users:
            users[uid]["is_admin"] = True
            return cls.save_users(users)
        return False

    @classmethod
    def save_garena_account(cls, user_id: int, account_id: str, nickname: str, region: str, access_token: str, eat_token: str) -> bool:
        users = cls.get_users()
        uid = str(user_id)
        if uid in users:
            users[uid]["accounts"][str(account_id)] = {
                "NAME": nickname,
                "ID": str(account_id),
                "LV": "N/A",
                "EAT": eat_token,
                "ACCESS_TOKEN": access_token,
                "region": region,
                "added_at": datetime.now().isoformat()
            }
            return cls.save_users(users)
        return False

    @classmethod
    def delete_garena_account(cls, user_id: int, account_id: str) -> bool:
        users = cls.get_users()
        uid = str(user_id)
        aid = str(account_id)
        if uid in users and aid in users[uid].get("accounts", {}):
            del users[uid]["accounts"][aid]
            return cls.save_users(users)
        return False

    @classmethod
    def generate_json_log(cls) -> str:
        users = cls.get_users()
        log_data = []
        for uid, uinfo in users.items():
            user_log = {
                "telegram_id": uid,
                "username": uinfo.get("username", "Unknown"),
                "first_name": uinfo.get("first_name", "Unknown"),
                "activation_keys": uinfo.get("keys", []),
                "saved_accounts": []
            }
            for aid, acc in uinfo.get("accounts", {}).items():
                user_log["saved_accounts"].append({
                    "NAME": acc.get("NAME", "Unknown"),
                    "ID": acc.get("ID", aid),
                    "LV": acc.get("LV", "N/A"),
                    "EAT": acc.get("EAT", ""),
                    "ACCESS_TOKEN": acc.get("ACCESS_TOKEN", "")
                })
            log_data.append(user_log)
        return json.dumps(log_data, indent=4, ensure_ascii=False)


class KeyManager:
    @staticmethod
    def generate() -> str:
        return f"{KEY_PREFIX}-{''.join(random.choices(string.ascii_uppercase + string.digits, k=12))}"
    
    @staticmethod
    def create(duration: int, unit: str, max_devices: int, owner: int) -> Dict:
        now = datetime.now()
        expires = now + (timedelta(days=duration) if unit == "days" else timedelta(hours=duration))
        return {
            "key": KeyManager.generate(), "created_at": now.isoformat(), "expires_at": expires.isoformat(),
            "max_devices": max_devices, "users": [], "owner": owner, "active": True
        }
    
    @staticmethod
    def save(key_data: Dict) -> bool:
        keys = DataManager.get_keys()
        keys[key_data["key"]] = key_data
        return DataManager.save_keys(keys)
    
    @staticmethod
    def get_all() -> Dict:
        return DataManager.get_keys()
    
    @staticmethod
    def disable(key: str) -> bool:
        keys = DataManager.get_keys()
        if key in keys:
            keys[key]["active"] = False
            return DataManager.save_keys(keys)
        return False
    
    @staticmethod
    def remove_user_from_all_keys(user_id: int) -> bool:
        keys = DataManager.get_keys()
        changed = False
        for k, data in keys.items():
            if user_id in data.get("users", []):
                data["users"] = [u for u in data["users"] if u != user_id]
                changed = True
        if changed:
            DataManager.save_keys(keys)
        users = DataManager.get_users()
        uid = str(user_id)
        if uid in users:
            users[uid]["keys"] = []
            DataManager.save_users(users)
            return True
        return changed

# ============================================================
# دالة التحقق من فاعلية اشتراك العضو
# ============================================================

def check_user_key(user_id: int) -> bool:
    if DataManager.is_admin(user_id):
        return True
    keys = DataManager.get_keys()
    now = datetime.now()
    has_active = False
    changed = False
    # تم تحويلها إلى قائمة لتفادي مشكلة تعديل القاموس أثناء معالجته
    for key, data in list(keys.items()):
        if user_id in data.get("users", []):
            if data.get("active", True):
                try:
                    expiry = datetime.fromisoformat(data["expires_at"])
                    if expiry > now:
                        has_active = True
                    else:
                        data["active"] = False
                        changed = True
                except Exception:
                    pass
    if changed:
        DataManager.save_keys(keys)
    return has_active

def validate_key(key: str, user_id: int) -> Tuple[bool, str]:
    keys = DataManager.get_keys()
    if key not in keys:
        return False, "Invalid Key"
    data = keys[key]
    if not data.get("active", True):
        return False, "Key has been disabled"
    try:
        if datetime.fromisoformat(data["expires_at"]) < datetime.now():
            data["active"] = False
            DataManager.save_keys(keys)
            return False, "Key has expired"
    except:
        pass
    if len(data.get("users", [])) >= data.get("max_devices", 5) and user_id not in data.get("users", []):
        return False, "Device threshold reached"
    if user_id not in data.get("users", []):
        data["users"].append(user_id)
        DataManager.save_keys(keys)
        users = DataManager.get_users()
        uid = str(user_id)
        users.setdefault(uid, {"keys": []})
        if key not in users[uid].get("keys", []):
            users[uid]["keys"].append(key)
        DataManager.save_users(users)
    return True, "Success"
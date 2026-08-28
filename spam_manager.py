# spam_manager.py
import asyncio, aiohttp, ssl, json, base64, time, random, sys, os
from datetime import datetime
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from urllib.parse import urlparse, parse_qs

PING_INTERVAL = 0.6
RECONNECT_DELAY = 0.6
NUM_SESSIONS = 6

AES_KEY = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
AES_IV  = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])

SUPPORTED_PLATFORMS = ["8", "3", "5", "6", "11", "13", "4"]
PLATFORM_NAMES = {"8":"Google","3":"Facebook","5":"VK","6":"Huawei","11":"X","13":"Apple","4":"Guest"}

HEADERS = {
    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11; ASUS_Z01QD Build/PI)",
    "Connection": "Keep-Alive",
    "Accept-Encoding": "gzip",
    "Content-Type": "application/x-www-form-urlencoded",
    "X-Unity-Version": "2018.4.11f1",
    "X-GA": "v1 1",
    "ReleaseVersion": "OB54"
}

PING_PACKET = bytes([0x0A,0x00,0x08,0x00,0x10,0x00,0x18,0x00,0x20,0x00,0x28,0x00,0x30,0x00,0x38,0x00,0x40,0x00,0x48,0x00,0x50,0x00,0x58,0x00,0x60,0x00,0x68,0x00,0x70,0x00,0x78,0x00,0x80,0x01,0x00])

# ============================================================
# GLOBAL LOGIN STATE (MULTI-SESSION SUPPORT)
# ============================================================
active_sessions = {}  # { account_id: { "manager": MultiSessionManager, "task": asyncio.Task, "name": str, "uid": str, "platform": str, "user_id": str } }

class ProtoWriter:
    def varint(self, value):
        result = []
        while value > 127:
            result.append((value & 0x7F) | 0x80)
            value >>= 7
        result.append(value)
        return bytes(result)

    def tag(self, field_num, wire_type):
        return self.varint((field_num << 3) | wire_type)

    def write_varint(self, field_num, value):
        return self.tag(field_num, 0) + self.varint(value)

    def write_string(self, field_num, value):
        if isinstance(value, str):
            value = value.encode('utf-8')
        return self.tag(field_num, 2) + self.varint(len(value)) + value

    def write_message(self, field_num, data):
        if isinstance(data, dict):
            data = self.create_message(data)
        return self.tag(field_num, 2) + self.varint(len(data)) + data

    def create_message(self, fields):
        result = bytearray()
        for field_num, value in sorted(fields.items()):
            if isinstance(value, dict):
                result.extend(self.write_message(field_num, value))
            elif isinstance(value, int):
                result.extend(self.write_varint(field_num, value))
            elif isinstance(value, str):
                result.extend(self.write_string(field_num, value))
            elif isinstance(value, bytes):
                result.extend(self.write_string(field_num, value))
        return bytes(result)

class ProtoReader:
    def read_varint(self, data, offset=0):
        result = 0
        shift = 0
        while True:
            byte = data[offset]
            result |= (byte & 0x7F) << shift
            offset += 1
            if not (byte & 0x80):
                break
            shift += 7
        return result, offset

    def parse_message(self, data):
        result = {}
        offset = 0
        while offset < len(data):
            try:
                tag, offset = self.read_varint(data, offset)
                field_num = tag >> 3
                wire_type = tag & 0x7
                if wire_type == 0:
                    value, offset = self.read_varint(data, offset)
                    result[field_num] = value
                elif wire_type == 2:
                    length, offset = self.read_varint(data, offset)
                    if length > len(data) - offset:
                        break
                    value = data[offset:offset+length]
                    offset += length
                    try:
                        result[field_num] = value.decode('utf-8')
                    except Exception:
                        result[field_num] = value
                else:
                    break
            except Exception:
                break
        return result

def aes_encrypt(data):
    cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
    return cipher.encrypt(pad(data, AES.block_size))

def build_major_login(open_id, access_token, platform="4"):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    fields = {
        3: current_time,
        4: "free fire",
        5: 1,
        7: "2.126.6",
        8: "Android OS 9 / API-28 (PQ3B.190801.03250903/G9650ZHU2ARC6)",
        9: "Handheld",
        10: "Mobinil",
        11: "WIFI",
        12: 1600, 
        13: 900, 
        14: "240",
        15: "x86-64 SSE3 SSE4.1 SSE4.2 AVX | 2865 | 6",
        16: 5955,
        17: "Adreno (TM) 640",
        18: "OpenGL ES 3.1 v1",
        19: "Google|8eab9762-c0ea-40d8-b64f-f152bc12e03b",
        20: "197.202.55.30",
        21: "ar",
        22: open_id,
        23: platform,
        24: "Handheld",
        25: "Xiaomi 2304FPN6DG",
        26: "ME",
        29: access_token,
        30: 1,
        41: "Mobinil",
        42: "WIFI",
        57: "1ac4b80ecf0478a44203bf8fac6120f5",
        60: 50504,
        61: 47169,
        62: 2519,
        63: 734,
        64: 23888,
        65: 26628,
        74: "/data/app/com.dts.freefiremax-qjzX4V6JmeMtMehevolhVQ==/lib/arm64",
        77: "d508536b2a3c16bf2bebbd24233e9293|/data/app/com.dts.freefiremax-qjzX4V6JmeMtMehevolhVQ==/base.apk",
        78: 2,
        79: 2,
        81: "64",
        83: "2019118045",
        85: 3,
        86: "OpenGLES3",
        87: 4095,
        88: 4,
        91: "android",
        92: 4903,
        94: "KqsHT+dw/OPMR6vKsRTZUHjrrrcWy4c3Gyt7K6IyAWXfe0r8Q9CibaAB16K58gBDMW1Ki9bcr8+xioK2xwdS9js0A=",
        95: 110009,
        97: 1,
        98: 1,
        99: platform,
        100: platform,
        103: 1
    }
    return ProtoWriter().create_message(fields)

def parse_major_login_response(data):
    parsed = ProtoReader().parse_message(data)
    return {
        "account_uid": parsed.get(1, 0),
        "region": parsed.get(2, ""),
        "token": parsed.get(8, ""),
        "url": parsed.get(10, ""),
        "timestamp": parsed.get(21, 0),
        "key": parsed.get(22, b""),
        "iv": parsed.get(23, b"")
    }

def parse_login_data(data):
    parsed = ProtoReader().parse_message(data)
    return {
        "account_uid": parsed.get(1, 0),
        "region": parsed.get(3, ""),
        "account_name": parsed.get(4, ""),
        "online_ip_port": parsed.get(14, ""),
        "clan_id": parsed.get(20, 0),
        "account_ip_port": parsed.get(32, ""),
    }

def create_auth_packet(uid, token, timestamp, key, iv):
    uid_int = int(uid)
    uid_hex = format(uid_int, 'x')
    if len(uid_hex) % 2 == 1:
        uid_hex = '0' + uid_hex

    ts_int = int(timestamp)
    ts_hex = format(ts_int, 'x')
    if len(ts_hex) % 2 == 1:
        ts_hex = '0' + ts_hex

    cipher = AES.new(key, AES.MODE_CBC, iv)
    token_padded = pad(token.encode('utf-8'), AES.block_size)
    token_encrypted = cipher.encrypt(token_padded)
    token_enc_hex = token_encrypted.hex()
    token_len_bytes = len(token_encrypted)
    token_len_hex = format(token_len_bytes, 'x')
    if len(token_len_hex) % 2 == 1:
        token_len_hex = '0' + token_len_hex

    uid_len = len(uid_hex)
    if uid_len == 8:      uid_header = '00000000'
    elif uid_len == 9:    uid_header = '0000000'
    elif uid_len == 10:   uid_header = '000000'
    elif uid_len == 7:    uid_header = '000000000'
    else:
        target_start = 16
        uid_header_len = target_start - 4 - uid_len
        if uid_header_len < 0:
            uid_header_len = 0
        uid_header = '0' * uid_header_len

    if len(token_len_hex) % 2 == 0:
        separator = "0000"
    else:
        separator = "00000"

    packet = f"0115{uid_header}{uid_hex}{ts_hex}{separator}{token_len_hex}{token_enc_hex}"
    return bytes.fromhex(packet)

class FastConnectionHandler:
    def __init__(self, auth_data, session_id=1):
        self.auth_data = auth_data
        self.session_id = session_id
        self.online_reader = None
        self.online_writer = None
        self.chat_reader = None
        self.chat_writer = None
        self.is_connected = False
        self.ping_count = 0

    async def connect_online(self):
        ip, port = self.auth_data['online_ip_port'].split(':')
        try:
            self.online_reader, self.online_writer = await asyncio.open_connection(ip, int(port))
            self.online_writer.write(self.auth_data['auth_packet'])
            await self.online_writer.drain()
            return True
        except Exception:
            return False

    async def connect_chat(self):
        ip, port = self.auth_data['chat_ip_port'].split(':')
        try:
            self.chat_reader, self.chat_writer = await asyncio.open_connection(ip, int(port))
            self.chat_writer.write(self.auth_data['auth_packet'])
            await self.chat_writer.drain()
            return True
        except Exception:
            return False

    async def super_fast_ping(self):
        while self.is_connected:
            try:
                await asyncio.sleep(PING_INTERVAL)
                self.ping_count += 1
                if self.online_writer and not self.online_writer.is_closing():
                    self.online_writer.write(PING_PACKET)
                    await self.online_writer.drain()
                if self.chat_writer and not self.chat_writer.is_closing():
                    self.chat_writer.write(PING_PACKET)
                    await self.chat_writer.drain()
            except Exception:
                self.is_connected = False
                break

    async def read_online(self):
        while self.is_connected:
            try:
                data = await self.online_reader.read(4096)
                if not data:
                    self.is_connected = False
                    break
            except Exception:
                self.is_connected = False
                break

    async def read_chat(self):
        while self.is_connected:
            try:
                data = await self.chat_reader.read(4096)
                if not data:
                    self.is_connected = False
                    break
            except Exception:
                self.is_connected = False
                break

    async def start(self):
        online_ok = await self.connect_online()
        chat_ok = await self.connect_chat()
        if not online_ok or not chat_ok:
            return False
        self.is_connected = True
        self.ping_count = 0
        tasks = [
            asyncio.create_task(self.read_online()),
            asyncio.create_task(self.read_chat()),
            asyncio.create_task(self.super_fast_ping())
        ]
        try:
            await asyncio.gather(*tasks)
        except Exception:
            pass
        return True

    async def stop(self):
        self.is_connected = False
        if self.online_writer:
            self.online_writer.close()
        if self.chat_writer:
            self.chat_writer.close()

class MultiSessionManager:
    def __init__(self, auth_data, num_sessions=NUM_SESSIONS):
        self.auth_data = auth_data
        self.num_sessions = num_sessions
        self.sessions = []
        self.running = False

    async def run_session_with_reconnect(self, session):
        while self.running:
            try:
                success = await session.start()
                if not success:
                    await asyncio.sleep(RECONNECT_DELAY)
                else:
                    await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(RECONNECT_DELAY)

    async def start_all(self):
        self.running = True
        for i in range(self.num_sessions):
            session = FastConnectionHandler(self.auth_data, session_id=i+1)
            self.sessions.append(session)
        tasks = [self.run_session_with_reconnect(s) for s in self.sessions]
        await asyncio.gather(*tasks)

    async def stop_all(self):
        self.running = False
        for s in self.sessions:
            await s.stop()

async def authenticate_with_all_platforms(open_id, access_token):
    async with aiohttp.ClientSession() as session:
        for platform in SUPPORTED_PLATFORMS:
            pname = PLATFORM_NAMES.get(platform, platform)
            payload = build_major_login(open_id, access_token, platform)
            encrypted = aes_encrypt(payload)
            try:
                async with session.post("https://loginbp.ggpolarbear.com/MajorLogin", data=encrypted, headers=HEADERS) as resp:
                    if resp.status != 200:
                        continue
                    data = await resp.read()
            except Exception:
                continue

            major = parse_major_login_response(data)
            if not major or not major.get("account_uid"):
                continue

            headers2 = HEADERS.copy()
            headers2["Authorization"] = f"Bearer {major['token']}"
            try:
                async with session.post(f"{major['url']}/GetLoginData", data=encrypted, headers=headers2) as resp:
                    if resp.status != 200:
                        continue
                    login_data = await resp.read()
            except Exception:
                continue

            login_info = parse_login_data(login_data)
            if not login_info:
                continue

            auth_packet = create_auth_packet(major['account_uid'], major['token'], major['timestamp'], major['key'], major['iv'])
            return {
                "account_uid": major['account_uid'],
                "region": major['region'],
                "account_name": login_info['account_name'],
                "online_ip_port": login_info['online_ip_port'],
                "chat_ip_port": login_info.get('account_ip_port', login_info['online_ip_port']),
                "auth_packet": auth_packet,
                "platform": pname
            }
    return None

def get_open_id(access_token):
    try:
        import requests
        url = f"https://100067.connect.garena.com/oauth/token/inspect?token={access_token}"
        headers = {
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "close",
            "Content-Type": "application/x-www-form-urlencoded",
            "Host": "100067.connect.garena.com",
            "User-Agent": "GarenaMSDK/4.0.19P4(G011A ;Android 9;en;US;)"
        }
        resp = requests.get(url, headers=headers, timeout=10)
        data = resp.json()
        if 'error' in data:
            return None, data.get('error')
        return data['open_id'], data.get('platform', 4)
    except Exception as e:
        return None, str(e)

# ============================================================
# LOGIN SESSION CONTROL FUNCTIONS
# ============================================================
def is_session_active(account_id: str) -> bool:
    return str(account_id) in active_sessions

async def start_login_session(access_token: str, account_id: str = "", user_id: str = ""):
    global active_sessions
    aid = str(account_id)
    
    if aid and aid in active_sessions:
        return False, "⚠️ جلسة تسجيل دخول نشطة بالفعل لهذا الحساب!"
    
    open_id, platform_or_error = get_open_id(access_token)
    if not open_id:
        return False, f"❌ فشل استخراج Open ID: {platform_or_error}"

    auth_data = await authenticate_with_all_platforms(open_id, access_token)
    if not auth_data:
        return False, "❌ فشل تسجيل الدخول على جميع المنصات!"
        
    acc_name = auth_data['account_name']
    acc_uid = auth_data['account_uid']
    platform_name = auth_data['platform']
    
    if not aid:
        aid = str(acc_uid)

    manager = MultiSessionManager(auth_data, num_sessions=NUM_SESSIONS)
    task = asyncio.create_task(manager.start_all())
    
    active_sessions[aid] = {
        "manager": manager,
        "task": task,
        "name": acc_name,
        "uid": str(acc_uid),
        "platform": platform_name,
        "user_id": str(user_id) # حفظ الـ user_id الخاص بالعضو
    }
    
    return True, auth_data

async def stop_login_session(account_id: str):
    global active_sessions
    aid = str(account_id)
    
    if aid not in active_sessions:
        return False, "⚠️ لا توجد جلسة نشطة لهذا الحساب لإيقافها!"
    
    session = active_sessions[aid]
    manager = session["manager"]
    task = session["task"]
    
    await manager.stop_all()
    
    if task and not task.done():
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
            
    del active_sessions[aid]
    return True, "✅ **تم إيقاف جلسة تسجيل الدخول بنجاح!**"

def get_login_status() -> str:
    if not active_sessions:
        return "🔴 **لا توجد جلسات نشطة حالياً**"
    
    status_lines = []
    for aid, sess in active_sessions.items():
        status_lines.append(f"🟢 **نشط** | {sess['name']} (UID: {sess['uid']}) [{sess['platform']}]")
    return "\n".join(status_lines)
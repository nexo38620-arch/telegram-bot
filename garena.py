# garena.py
import json
import requests
import hashlib
import urllib.parse
import asyncio
from typing import Dict, List, Tuple

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def format_api_text(text: str, action_ar: str, action_en: str, lang: str = "ar") -> str:
    action = action_ar if lang == "ar" else action_en
    try:
        data = json.loads(text)
        rc = data.get("result")
        if rc == 0:
            success_txt = "نجحت العملية ✅" if lang == "ar" else "SUCCESS ✅"
            return f"<b>{action}:</b> {success_txt}"
        else:
            err = data.get("error", "Unknown error")
            failed_txt = "فشلت العملية ❌" if lang == "ar" else "FAILED ❌"
            code_txt = "كود" if lang == "ar" else "Code"
            return f"<b>{action}:</b> {failed_txt} ({code_txt}: {rc} | {err})"
    except:
        if '"result":0' in text.replace(" ", ""):
            success_txt = "نجحت العملية ✅" if lang == "ar" else "SUCCESS ✅"
            return f"<b>{action}:</b> {success_txt}"
        failed_txt = "فشل الاتصال بالخادم ❌" if lang == "ar" else "Connection Failed ❌"
        return f"<b>{action}:</b> {failed_txt}"

def _get_player_info(token: str) -> Tuple[str, str, str, bool]:
    try:
        r = requests.get(
            f"https://api-otrss.garena.com/support/callback/?access_token={token}",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=5,
            allow_redirects=True,
            verify=False
        )
        qp = urllib.parse.parse_qs(urllib.parse.urlparse(r.url).query)
        if 'access_token' in qp:
            return (
                qp.get('account_id', ['Unknown'])[0],
                urllib.parse.unquote(qp.get('nickname', ['Unknown'])[0]),
                qp.get('region', ['Unknown'])[0],
                True
            )
        return "Unknown", "Unknown", "Unknown", False
    except:
        return "Unknown", "Unknown", "Unknown", False

async def get_player_info(token: str) -> Tuple[str, str, str, bool]:
    return await asyncio.to_thread(_get_player_info, token)

def _get_bind_info(token: str) -> Tuple[str, str, int, bool]:
    try:
        r = requests.get(
            "https://100067.connect.garena.com/game/account_security/bind:get_bind_info",
            params={"app_id": "100067", "access_token": token},
            headers={"User-Agent": "GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)"},
            timeout=5,
            verify=False
        )
        if r.status_code == 200:
            try:
                data = r.json()
            except Exception:
                data = {}
            return data.get("email", ""), data.get("email_to_be", ""), data.get("request_exec_countdown", 0), True
        return "", "", 0, False
    except:
        return "", "", 0, False

async def get_bind_info(token: str) -> Tuple[str, str, int, bool]:
    return await asyncio.to_thread(_get_bind_info, token)

def _send_otp(email: str, token: str) -> Tuple[bool, str]:
    headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
    data = {"email": email, "locale": "en_PK", "region": "PK", "app_id": "100067", "access_token": token}
    try:
        r = requests.post("https://100067.connect.garena.com/game/account_security/bind:send_otp", headers=headers, data=data, timeout=5, verify=False)
        return True, r.text
    except:
        return False, "Connection error"

async def send_otp(email: str, token: str) -> Tuple[bool, str]:
    return await asyncio.to_thread(_send_otp, email, token)

def _verify_otp(email: str, token: str, otp: str) -> Tuple[bool, str, str]:
    headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
    data = {"app_id": "100067", "access_token": token, "email": email, "otp": otp, "type": "1"}
    try:
        r = requests.post("https://100067.connect.garena.com/game/account_security/bind:verify_otp", headers=headers, data=data, timeout=5, verify=False)
        try:
            resp_json = r.json()
            verifier_token = resp_json.get("verifier_token", "")
        except Exception:
            verifier_token = ""
        return True, r.text, verifier_token
    except Exception as e:
        return False, f"Connection Error: {e}", ""

async def verify_otp(email: str, token: str, otp: str) -> Tuple[bool, str, str]:
    return await asyncio.to_thread(_verify_otp, email, token, otp)

def _create_bind_request(email: str, token: str, verifier: str, sec_code: str) -> Tuple[bool, str]:
    headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
    data = {"email": email, "app_id": "100067", "access_token": token, "verifier_token": verifier, "secondary_password": sec_code}
    try:
        r = requests.post("https://100067.connect.garena.com/game/account_security/bind:create_bind_request", headers=headers, data=data, timeout=5, verify=False)
        return True, r.text
    except Exception as e:
        return False, f"Connection Error: {e}"

async def create_bind_request(email: str, token: str, verifier: str, sec_code: str) -> Tuple[bool, str]:
    return await asyncio.to_thread(_create_bind_request, email, token, verifier, sec_code)

def _verify_identity_otp(email: str, token: str, otp: str) -> Tuple[bool, str, str]:
    headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
    data = {"email": email, "app_id": "100067", "access_token": token, "otp": otp}
    try:
        r = requests.post("https://100067.connect.garena.com/game/account_security/bind:verify_identity", headers=headers, data=data, timeout=5, verify=False)
        try:
            resp_json = r.json()
            identity_token = resp_json.get("identity_token", "")
        except Exception:
            identity_token = ""
        return True, r.text, identity_token
    except Exception as e:
        return False, f"Connection Error: {e}", ""

async def verify_identity_otp(email: str, token: str, otp: str) -> Tuple[bool, str, str]:
    return await asyncio.to_thread(_verify_identity_otp, email, token, otp)

def _verify_identity_sec(email: str, token: str, sec_code: str) -> Tuple[bool, str, str]:
    headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
    hashed = hashlib.sha256(sec_code.encode('utf-8')).hexdigest()
    data = {"email": email, "app_id": "100067", "access_token": token, "secondary_password": hashed}
    try:
        r = requests.post("https://100067.connect.garena.com/game/account_security/bind:verify_identity", headers=headers, data=data, timeout=5, verify=False)
        try:
            resp_json = r.json()
            identity_token = resp_json.get("identity_token", "")
        except Exception:
            identity_token = ""
        return True, r.text, identity_token
    except Exception as e:
        return False, f"Connection Error: {e}", ""

async def verify_identity_sec(email: str, token: str, sec_code: str) -> Tuple[bool, str, str]:
    return await asyncio.to_thread(_verify_identity_sec, email, token, sec_code)

def _create_unbind_request(token: str, identity: str) -> Tuple[bool, str]:
    headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
    data = {"app_id": "100067", "access_token": token, "identity_token": identity}
    try:
        r = requests.post("https://100067.connect.garena.com/game/account_security/bind:create_unbind_request", headers=headers, data=data, timeout=5, verify=False)
        return True, r.text
    except Exception as e:
        return False, f"Connection Error: {e}"

async def create_unbind_request(token: str, identity: str) -> Tuple[bool, str]:
    return await asyncio.to_thread(_create_unbind_request, token, identity)

def _create_rebind_request(token: str, identity: str, email: str, verifier: str) -> Tuple[bool, str]:
    headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
    data = {"identity_token": identity, "email": email, "app_id": "100067", "verifier_token": verifier, "access_token": token}
    try:
        r = requests.post("https://100067.connect.garena.com/game/account_security/bind:create_rebind_request", headers=headers, data=data, timeout=5, verify=False)
        return True, r.text
    except Exception as e:
        return False, f"Connection Error: {e}"

async def create_rebind_request(token: str, identity: str, email: str, verifier: str) -> Tuple[bool, str]:
    return await asyncio.to_thread(_create_rebind_request, token, identity, email, verifier)

def _cancel_bind_request(token: str) -> Tuple[bool, str]:
    headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
    data = {"app_id": "100067", "access_token": token}
    try:
        r = requests.post("https://100067.connect.garena.com/game/account_security/bind:cancel_request", headers=headers, data=data, timeout=5, verify=False)
        return True, r.text
    except Exception as e:
        return False, f"Connection Error: {e}"

async def cancel_bind_request(token: str) -> Tuple[bool, str]:
    return await asyncio.to_thread(_cancel_bind_request, token)

def _check_bound(token: str) -> Tuple[bool, str, List, List]:
    try:
        r = requests.get(
            "https://100067.connect.garena.com/bind/app/platform/info/get",
            params={"access_token": token, "app_id": "100067"},
            headers={"User-Agent": "GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)"},
            timeout=5,
            verify=False
        )
        if r.status_code != 200:
            return False, f"HTTP {r.status_code}", [], []
        try:
            data = r.json()
        except Exception:
            return False, "Invalid response format from server", [], []
        result_code = data.get("result", 0)
        if result_code != 0:
            return False, f"Result Code {result_code} - {data.get('error', 'Unknown Error')}", [], []
        return True, "", data.get("bounded_accounts", []), data.get("available_platforms", [])
    except Exception as e:
        return False, f"Request failed: {e}", [], []

async def check_bound(token: str) -> Tuple[bool, str, List, List]:
    return await asyncio.to_thread(_check_bound, token)

def _eat_to_token(eat: str) -> Tuple[str, Dict]:
    token = None
    if "http" in eat or "?" in eat:
        qp = urllib.parse.parse_qs(urllib.parse.urlparse(eat).query)
        token = qp.get('eat', [None])[0]
    else:
        token = eat.strip()
    if not token:
        return "No usable EAT sequence was parsed", {}
    try:
        r = requests.get(
            f"https://api-otrss.garena.com/support/callback/?access_token={token}",
            timeout=5,
            allow_redirects=True,
            verify=False
        )
        qp = urllib.parse.parse_qs(urllib.parse.urlparse(r.url).query)
        if 'access_token' in qp:
            return "", {
                "access_token": qp['access_token'][0],
                "nickname": urllib.parse.unquote(qp.get('nickname', ['Unknown'])[0]),
                "account_id": qp.get('account_id', ['Unknown'])[0],
                "region": qp.get('region', ['Unknown'])[0]
            }
        return "EAT target session is invalid or expired", {}
    except:
        return "Request Connection Failed", {}

async def eat_to_token(eat: str) -> Tuple[str, Dict]:
    return await asyncio.to_thread(_eat_to_token, eat)

def _do_revoke(token: str) -> Tuple[str, Dict]:
    valid = False
    nickname = account_id = region = "Unknown"
    try:
        r = requests.get(
            f"https://api-otrss.garena.com/support/callback/?access_token={token}",
            headers={"User-Agent": "Mozilla/5.0"},
            allow_redirects=True,
            timeout=5,
            verify=False
        )
        qp = urllib.parse.parse_qs(urllib.parse.urlparse(r.url).query)
        if 'access_token' in qp:
            valid = True
            nickname = urllib.parse.unquote(qp.get('nickname', ['Unknown'])[0])
            account_id = qp.get('account_id', ['Unknown'])[0]
            region = qp.get('region', ['Unknown'])[0]
    except:
        pass
    if not valid:
        return "Target Token is already expired or invalid", {}
    try:
        r = requests.get(
            f"https://100067.connect.garena.com/oauth/logout?access_token={token}&refresh_token=1380dcb63ab3a077dc05bdf0b25ba4497c403a5b4eae96d7203010eafa6c83a8",
            timeout=5,
            verify=False
        )
        if r.status_code == 200 and "error" not in r.text.lower():
            return "", {"nickname": nickname, "account_id": account_id, "region": region, "status": "revoked"}
        return "Garena server rejected sign-out request", {}
    except:
        return "Request connection failed", {}

async def do_revoke(token: str) -> Tuple[str, Dict]:
    return await asyncio.to_thread(_do_revoke, token)

def _set_long_bio(bio_text: str, token: str) -> Tuple[bool, str]:
    try:
        quoted_bio = urllib.parse.quote(bio_text)
        url = f"https://ob54-asd-long-bio.vercel.app/bio?bio={quoted_bio}&access={token}"
        r = requests.get(url, timeout=10, verify=False)
        text = r.text
        if r.status_code == 200 or "success" in text.lower():
            return True, "✅ Bio updated successfully!"
        return False, f"❌ Response error: {text[:200]}"
    except Exception as e:
        return False, f"❌ Request connection failed: {e}"

async def set_long_bio(bio_text: str, token: str) -> Tuple[bool, str]:
    return await asyncio.to_thread(_set_long_bio, bio_text, token)
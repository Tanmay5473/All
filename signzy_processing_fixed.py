import os
import re
import json
import time
import uuid
import base64
import urllib.parse
from io import BytesIO

import requests
import boto3
from botocore.exceptions import ClientError

import pymysql
from PIL import Image

from Crypto.Cipher import AES, PKCS1_v1_5
from Crypto.PublicKey import RSA
from Crypto.Util.Padding import pad, unpad


# ------------------------------
# Configuration (env-driven)
# ------------------------------
class Config:
    # Signzy API
    SIGNZY_URL = os.getenv("SIGNZY_SIGNATURE_EXTRACTION_URL", "https://api.signzy.app/api/v3/pan/signature-extraction")
    SIGNZY_MATCH_URL = os.getenv("SIGNZY_SIGNATURE_MATCH_URL", "https://api.signzy.app/api/v3/signature/match")
    SIGNZY_OVD_URL = os.getenv("SIGNZY_OVD_FACE_URL", "https://api.signzy.app/api/v3/ovd/extraction-face-verification")
    SIGNZY_FACE_URL = os.getenv("SIGNZY_FACE_SMART_URL", "https://api.signzy.app/api/v3/face/smart-verification")

    SIGNZY_AUTH_TOKEN = os.getenv("SIGNZY_AUTH_TOKEN", "")
    SIGNZY_CLIENT_ID = os.getenv("SIGNZY_CLIENT_ID", "")  # sometimes called client unique id

    # AWS S3
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
    S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "")
    PUBLIC_READ_UPLOADS = os.getenv("S3_PUBLIC_READ", "true").lower() == "true"  # make objects publicly readable
    PUBLIC_BASE_URL = os.getenv("S3_PUBLIC_BASE_URL", "")  # optional CloudFront or static website URL, e.g. https://cdn.example.com

    # Database
    DB_HOST = os.getenv("DB_HOST", "")
    DB_USER = os.getenv("DB_USER", "")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))

    # App auth for Nexus download
    ACTUAL_PASSWORD = os.getenv("ACTUAL_PASSWORD", "")
    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "")
    USER_ID = os.getenv("USER_ID", "")
    EMAIL_ID = os.getenv("EMAIL_ID", "")
    OTP = os.getenv("OTP", "")

    # URLs
    BASE_URL = os.getenv("BASE_URL", "")
    DOWNLOAD_URL = os.getenv("DOWNLOAD_URL", f"{BASE_URL}/Nexus-API-New/api/DocumentUpload/downloadDocument")

    # RSA Private Key (PEM)
    PRIVATE_KEY_PEM = os.getenv("PRIVATE_KEY_PEM", "")


# ------------------------------
# S3 Storage
# ------------------------------
class S3ImageStorage:
    def __init__(self):
        self.s3_client = None
        self.bucket_name = Config.S3_BUCKET_NAME
        self.public_base_url = Config.PUBLIC_BASE_URL.rstrip("/") if Config.PUBLIC_BASE_URL else ""
        self._init_client()

    def _init_client(self):
        try:
            self.s3_client = boto3.client(
                "s3",
                aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
                region_name=Config.AWS_REGION,
            )
            print(f"✅ S3 client ready for bucket: {self.bucket_name}")
        except Exception as exc:
            print(f"❌ S3 client init failed: {exc}")
            self.s3_client = None

    @staticmethod
    def _content_type_for(path: str) -> str:
        ext = os.path.splitext(path)[1].lower()
        return {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".bmp": "image/bmp",
            ".webp": "image/webp",
        }.get(ext, "application/octet-stream")

    def _object_url(self, key: str) -> str:
        if self.public_base_url:
            return f"{self.public_base_url}/{key}"
        # Standard virtual-hosted–style URL
        return f"https://{self.bucket_name}.s3.{Config.AWS_REGION}.amazonaws.com/{key}"

    def upload_image(self, image_path: str, filename_hint: str | None = None) -> dict:
        """
        Upload image to S3 and return a dict with keys:
        - public_url: if PUBLIC_READ_UPLOADS=True or PUBLIC_BASE_URL provided
        - presigned_url: time-limited GET URL (fallback)
        - key: object key in bucket
        """
        if not self.s3_client:
            raise RuntimeError("S3 client not initialized")

        clean_name = None
        if filename_hint:
            clean_name = re.sub(r"[^a-zA-Z0-9._-]", "_", filename_hint)
        ext = os.path.splitext(image_path)[1] or ".jpg"
        key = f"images/{uuid.uuid4()}/{clean_name or ('image' + ext)}"

        extra = {"ContentType": self._content_type_for(image_path)}
        if Config.PUBLIC_READ_UPLOADS:
            extra["ACL"] = "public-read"

        print(f"📤 Uploading to s3://{self.bucket_name}/{key} ...")
        self.s3_client.upload_file(image_path, self.bucket_name, key, ExtraArgs=extra)

        result: dict[str, str] = {"key": key}
        if Config.PUBLIC_READ_UPLOADS:
            result["public_url"] = self._object_url(key)
        # Always provide presigned as well (in case bucket policy changes)
        try:
            presigned = self.s3_client.generate_presigned_url(
                "get_object", Params={"Bucket": self.bucket_name, "Key": key}, ExpiresIn=3600
            )
            result["presigned_url"] = presigned
        except ClientError as exc:
            print(f"⚠️ Could not create presigned URL: {exc}")
        return result


# Single, reusable instance
s3_storage = S3ImageStorage()


# ------------------------------
# Crypto utilities
# ------------------------------
class EncryptionUtils:
    @staticmethod
    def aes_password_encrypt(password_str: str, encryption_key: str) -> str:
        key = encryption_key.encode("utf-8")
        iv = b"\x00" * 16
        cipher = AES.new(key, AES.MODE_CBC, iv)
        padded = pad(password_str.encode("utf-8"), AES.block_size)
        return base64.b64encode(cipher.encrypt(padded)).decode("utf-8")

    @staticmethod
    def generate_guid() -> str:
        return str(uuid.uuid4())

    @staticmethod
    def rsa_decrypt_session_key(encrypted_session_key: str, private_key_pem: str) -> list[int] | None:
        try:
            encrypted_bytes = base64.b64decode(encrypted_session_key)
            private_key = RSA.import_key(private_key_pem)
            cipher = PKCS1_v1_5.new(private_key)
            decrypted_bytes = cipher.decrypt(encrypted_bytes, None)
            return [b for b in decrypted_bytes]
        except Exception as exc:
            print(f"❌ RSA decrypt error: {exc}")
            return None

    @staticmethod
    def aes_decrypt_with_session_key(encrypted_data: str, session_key_bytes: list[int]) -> bytes | None:
        try:
            encrypted_bytes = base64.b64decode(encrypted_data)
            iv = bytes(session_key_bytes[:16])
            key = bytes(session_key_bytes)
            cipher = AES.new(key, AES.MODE_CBC, iv)
            decrypted_data = cipher.decrypt(encrypted_bytes)
            return unpad(decrypted_data, AES.block_size)
        except Exception as exc:
            print(f"❌ AES decrypt error: {exc}")
            return None

    @staticmethod
    def decrypt_response_obj(encrypted_response: str, private_key_pem: str) -> bytes | None:
        try:
            # Normalize base64 padding
            padding = len(encrypted_response) % 4
            if padding:
                encrypted_response += "=" * (4 - padding)
            decoded = base64.b64decode(encrypted_response).decode("utf-8")
            obj = json.loads(decoded)
            session_id = obj.get("sessionId")
            data = obj.get("data")
            if not session_id or not data:
                print("❌ Missing sessionId or data in encrypted response")
                return None
            session_key = EncryptionUtils.rsa_decrypt_session_key(session_id, private_key_pem)
            if not session_key:
                return None
            return EncryptionUtils.aes_decrypt_with_session_key(data, session_key)
        except Exception as exc:
            print(f"❌ Decrypt response error: {exc}")
            return None


# ------------------------------
# Nexus auth/download
# ------------------------------
class AuthenticationAPI:
    def __init__(self):
        self.auth_token = None

    def get_auth_token_from_selenium(self) -> str | None:
        """Kept as-is; ensure env has BASE_URL/EMAIL_ID/OTP. Returns bearer token string."""
        try:
            print("🔐 Getting auth token via Selenium...")
            from seleniumwire import webdriver
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.chrome.options import Options

            options = Options()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--headless=new")

            driver = webdriver.Chrome(options=options)
            driver.verify_ssl = False
            driver.disable_encoding = True
            driver.enable_har = True
            wait = WebDriverWait(driver, 30)
            try:
                driver.get(Config.BASE_URL)
                driver.find_element(By.XPATH, "//input[@formcontrolname='email' and @name='email']").send_keys(Config.EMAIL_ID)
                driver.find_element(By.XPATH, "//button[@type='submit' and normalize-space()='Submit']").click()
                otp_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@name='otp']")))
                otp_input.send_keys(Config.OTP)
                driver.find_element(By.XPATH, "//button[normalize-space()='Verify & Login']").click()
                print("✅ Logged in via Selenium")
                time.sleep(6)

                for req in reversed(driver.requests):
                    if req.response:
                        auth = req.headers.get("Authorization")
                        x_userid = req.headers.get("X-UserId")
                        x_pass = req.headers.get("X-Password")
                        x_reqid = req.headers.get("X-RequestId")
                        if all([auth, x_userid, x_pass, x_reqid]):
                            self.auth_token = auth
                            break
            finally:
                driver.quit()
            return self.auth_token
        except Exception as exc:
            print(f"❌ Token capture error: {exc}")
            return None

    def download_document(self, doc_path: str, file_name: str, output_dir: str = "downloads") -> str | None:
        """Downloads and attempts decryption. Returns decrypted path only. If decryption fails, returns None."""
        try:
            os.makedirs(output_dir, exist_ok=True)
            x_request_id = EncryptionUtils.generate_guid()
            password_str = f"{Config.ACTUAL_PASSWORD}:{x_request_id}"
            encrypted_password = EncryptionUtils.aes_password_encrypt(password_str, Config.ENCRYPTION_KEY)

            encoded_file_path = urllib.parse.quote(doc_path, safe="")
            download_url = f"{Config.DOWNLOAD_URL}?filePath={encoded_file_path}&fileName={file_name}"

            headers = {
                "Accept": "application/json, text/plain, */*",
                "Referer": f"{Config.BASE_URL}/AddApplicantDetails",
                "User-Agent": "Mozilla/5.0",
                "Authorization": self.auth_token or "",
                "X-UserId": Config.USER_ID,
                "X-Password": encrypted_password,
                "X-RequestId": x_request_id,
            }

            resp = requests.get(download_url, headers=headers, timeout=30)
            if resp.status_code != 200:
                print(f"❌ Download failed {resp.status_code}: {resp.text[:200]}")
                return None

            # Persist encrypted for debugging
            encrypted_path = os.path.join(output_dir, f"encrypted_{file_name}")
            with open(encrypted_path, "wb") as f:
                f.write(resp.content)

            decrypted = EncryptionUtils.decrypt_response_obj(resp.text, Config.PRIVATE_KEY_PEM)
            if not decrypted:
                print("❌ Decryption failed; not proceeding with this file")
                return None

            # Save decrypted
            decrypted_path = os.path.join(output_dir, f"decrypted_{file_name}")
            with open(decrypted_path, "wb") as f:
                f.write(decrypted)
            return decrypted_path
        except Exception as exc:
            print(f"❌ Download error: {exc}")
            return None


# ------------------------------
# DB utilities
# ------------------------------
def fetch_document_paths(inv_id: int, document_type: int) -> list[str]:
    conn = None
    try:
        conn = pymysql.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            port=Config.DB_PORT,
        )
        with conn.cursor() as cursor:
            query = (
                "SELECT odd.DocumentFilePath "
                "FROM onbinvdocumentdetails AS odd "
                "WHERE odd.InvId = %s AND odd.DocumentTypeId = %s "
                "ORDER BY odd.id DESC"
            )
            cursor.execute(query, (inv_id, document_type))
            rows = cursor.fetchall()
            return [row[0].lstrip("/") for row in rows if row and row[0]]
    except Exception as exc:
        print(f"❌ DB error: {exc}")
        return []
    finally:
        if conn:
            conn.close()


def extract_inv_id_from_input(inv_id_input: str) -> str | None:
    if inv_id_input.isdigit():
        return inv_id_input
    filename = os.path.basename(inv_id_input)
    match = re.search(r"(\d{4})(?!.*\d)", filename)
    return match.group(1) if match else None


# ------------------------------
# Signzy helpers
# ------------------------------
def _format_signzy_auth_header(raw_token: str) -> str:
    token = (raw_token or "").strip()
    if not token:
        return ""
    # If token already prefixed, keep as is; else try 'Bearer '
    lowered = token.lower()
    if lowered.startswith("bearer ") or lowered.startswith("token ") or lowered.startswith("apikey "):
        return token
    return f"Bearer {token}"


def _signzy_headers() -> dict:
    headers = {
        "Content-Type": "application/json",
        "Authorization": _format_signzy_auth_header(Config.SIGNZY_AUTH_TOKEN),
        # Send both keys to maximize compatibility with different gateways
        "x-client-unique-id": Config.SIGNZY_CLIENT_ID,
        "x-client-id": Config.SIGNZY_CLIENT_ID,
    }
    # Remove empty
    return {k: v for k, v in headers.items() if v}


def test_signzy_connectivity() -> bool:
    try:
        url = "https://api.signzy.app/api/v3/health"
        r = requests.get(url, headers=_signzy_headers(), timeout=15)
        print(f"📦 Signzy health: {r.status_code}")
        return r.status_code == 200
    except Exception as exc:
        print(f"⚠️ Signzy health check failed: {exc}")
        return False


def extract_signature_with_signzy(image_url: str) -> dict | None:
    try:
        headers = _signzy_headers()
        # API expects list of urls
        payload = {"urls": [image_url]}
        r = requests.post(Config.SIGNZY_URL, headers=headers, json=payload, timeout=60)
        print(f"📦 Signature extraction status: {r.status_code}")
        if r.status_code == 401:
            # Fallback with lowercase header key (some gateways are picky)
            alt_headers = {**headers}
            auth_val = alt_headers.pop("Authorization", "")
            alt_headers["authorization"] = auth_val
            r = requests.post(Config.SIGNZY_URL, headers=alt_headers, json=payload, timeout=60)
            print(f"📦 Extraction status (alt): {r.status_code}")
        if r.status_code == 200:
            return r.json()
        print(f"❌ Extraction error: {r.text[:400]}")
        return None
    except Exception as exc:
        print(f"❌ Extraction exception: {exc}")
        return None


def match_signatures_with_signzy(sig_url1: str, sig_url2: str) -> dict | None:
    try:
        headers = _signzy_headers()
        # Prefer documented list payload
        payload = {"urls": [sig_url1, sig_url2]}
        r = requests.post(Config.SIGNZY_MATCH_URL, headers=headers, json=payload, timeout=60)
        print(f"📦 Signature match status: {r.status_code}")
        if r.status_code == 401:
            alt_headers = {**headers}
            auth_val = alt_headers.pop("Authorization", "")
            alt_headers["authorization"] = auth_val
            r = requests.post(Config.SIGNZY_MATCH_URL, headers=alt_headers, json=payload, timeout=60)
            print(f"📦 Signature match status (alt): {r.status_code}")
        if r.status_code == 200:
            return r.json()
        print(f"❌ Signature match error: {r.text[:400]}")
        return None
    except Exception as exc:
        print(f"❌ Signature match exception: {exc}")
        return None


def ovd_extraction_face_verification(id_url: str, selfie_url: str) -> dict | None:
    try:
        headers = _signzy_headers()
        # Try snake_case and camelCase keys for compatibility
        payload = {
            "id_url": id_url,
            "selfie_url": selfie_url,
            "idUrl": id_url,
            "selfieUrl": selfie_url,
        }
        r = requests.post(Config.SIGNZY_OVD_URL, headers=headers, json=payload, timeout=90)
        print(f"📦 OVD status: {r.status_code}")
        if r.status_code == 401:
            alt_headers = {**headers}
            auth_val = alt_headers.pop("Authorization", "")
            alt_headers["authorization"] = auth_val
            r = requests.post(Config.SIGNZY_OVD_URL, headers=alt_headers, json=payload, timeout=90)
            print(f"📦 OVD status (alt): {r.status_code}")
        if r.status_code == 200:
            return r.json()
        print(f"❌ OVD error: {r.text[:400]}")
        return None
    except Exception as exc:
        print(f"❌ OVD exception: {exc}")
        return None


def face_smart_verification(liveness_image_url: str, face_match_image_url: str, liveness_strict_mode: bool = True,
                            face_match_threshold: float = 0.7) -> dict | None:
    try:
        headers = _signzy_headers()
        payload = {
            "livenessImage": liveness_image_url,
            "faceMatchImage": face_match_image_url,
            "livenessStrictMode": liveness_strict_mode,
            "faceMatchThreshold": face_match_threshold,
        }
        r = requests.post(Config.SIGNZY_FACE_URL, headers=headers, json=payload, timeout=90)
        print(f"📦 Face smart status: {r.status_code}")
        if r.status_code == 401:
            alt_headers = {**headers}
            auth_val = alt_headers.pop("Authorization", "")
            alt_headers["authorization"] = auth_val
            r = requests.post(Config.SIGNZY_FACE_URL, headers=alt_headers, json=payload, timeout=90)
            print(f"📦 Face smart status (alt): {r.status_code}")
        if r.status_code == 200:
            return r.json()
        print(f"❌ Face smart error: {r.text[:400]}")
        return None
    except Exception as exc:
        print(f"❌ Face smart exception: {exc}")
        return None


# ------------------------------
# Main processing
# ------------------------------

def ensure_image_file(path: str) -> bool:
    try:
        with Image.open(path) as img:
            img.verify()
        return True
    except Exception:
        return False


def process_pan_documents(inv_id_input: str):
    print("🔍 Checking Signzy availability...")
    if not test_signzy_connectivity():
        print("⚠️ Signzy connectivity failed; proceeding anyway")

    auth_api = AuthenticationAPI()
    print("🔐 Acquiring Nexus auth token...")
    if not auth_api.get_auth_token_from_selenium():
        print("❌ Could not acquire Nexus auth token")
        return

    os.makedirs("downloads", exist_ok=True)
    os.makedirs("signatures", exist_ok=True)
    os.makedirs("face_results", exist_ok=True)

    inv_id = extract_inv_id_from_input(inv_id_input)
    if not inv_id or not inv_id.isdigit():
        print("❌ Invalid InvID input")
        return

    inv_id_num = int(inv_id)

    pan_paths = fetch_document_paths(inv_id_num, 131)  # PAN
    sig_paths = fetch_document_paths(inv_id_num, 13)   # Signature
    selfie_paths = fetch_document_paths(inv_id_num, 27)  # Selfie

    print(f"PAN docs: {len(pan_paths)} | Sig docs: {len(sig_paths)} | Selfies: {len(selfie_paths)}")

    # Prepare selfie public URL if exists
    selfie_public_url = None
    if selfie_paths:
        selfie_doc = selfie_paths[0]
        selfie_name = os.path.basename(selfie_doc)
        selfie_downloaded = auth_api.download_document(selfie_doc, selfie_name, output_dir="downloads")
        if selfie_downloaded and ensure_image_file(selfie_downloaded):
            up = s3_storage.upload_image(selfie_downloaded, selfie_name)
            selfie_public_url = up.get("public_url") or up.get("presigned_url")
            print(f"🌐 Selfie URL: {selfie_public_url}")
        else:
            print("⚠️ Selfie not an image or decryption failed")

    for idx, doc_path in enumerate(pan_paths, start=1):
        print(f"\n📄 Processing PAN {idx}/{len(pan_paths)}: {doc_path}")
        file_name = os.path.basename(doc_path)
        downloaded = auth_api.download_document(doc_path, file_name, output_dir="downloads")
        if not downloaded or not ensure_image_file(downloaded):
            print("❌ PAN not an image or decryption failed; skipping")
            continue

        # Upload PAN image to S3
        up = s3_storage.upload_image(downloaded, file_name)
        pan_public_url = up.get("public_url") or up.get("presigned_url")
        print(f"🌐 PAN URL: {pan_public_url}")

        # 1) Signature extraction
        signzy_result = extract_signature_with_signzy(pan_public_url)
        extracted_signature_path = None
        if signzy_result:
            result_path = os.path.join("signatures", f"signzy_result_{idx}.json")
            with open(result_path, "w") as f:
                json.dump(signzy_result, f, indent=2)
            # If imageUrl(s) present, fetch first
            try:
                signatures = signzy_result.get("signatures") or signzy_result.get("result") or []
                # Normalize to list
                if isinstance(signatures, dict):
                    signatures = [signatures]
                for s_idx, s in enumerate(signatures, start=1):
                    image_url = s.get("imageUrl") or s.get("url")
                    if not image_url:
                        continue
                    r = requests.get(image_url, timeout=30)
                    if r.status_code == 200:
                        extracted_signature_path = os.path.join("signatures", f"signzy_signature_{idx}_{s_idx}.png")
                        with open(extracted_signature_path, "wb") as f:
                            f.write(r.content)
                        print(f"✅ Saved extracted signature: {extracted_signature_path}")
                        break
            except Exception as exc:
                print(f"⚠️ Could not persist signature image: {exc}")
        else:
            print("❌ Signature extraction failed")

        # 2) Signature match (if we have extracted signature and a reference signature doc)
        if extracted_signature_path and sig_paths:
            sig_doc = sig_paths[0]
            sig_name = os.path.basename(sig_doc)
            downloaded_sig = auth_api.download_document(sig_doc, sig_name, output_dir="downloads")
            if downloaded_sig and ensure_image_file(downloaded_sig):
                up_a = s3_storage.upload_image(extracted_signature_path, os.path.basename(extracted_signature_path))
                up_b = s3_storage.upload_image(downloaded_sig, sig_name)
                url_a = up_a.get("public_url") or up_a.get("presigned_url")
                url_b = up_b.get("public_url") or up_b.get("presigned_url")
                print(f"🔍 Matching signatures: A={url_a} B={url_b}")
                match_result = match_signatures_with_signzy(url_a, url_b)
                if match_result:
                    path = os.path.join("signatures", f"match_result_{idx}.json")
                    with open(path, "w") as f:
                        json.dump(match_result, f, indent=2)
                    print(f"✅ Saved signature match result: {path}")
                else:
                    print("❌ Signature match failed")
            else:
                print("⚠️ Reference signature not an image or decryption failed")
        else:
            if not extracted_signature_path:
                print("⚠️ No extracted signature for matching")
            if not sig_paths:
                print("⚠️ No reference signature document present")

        # 3) Face match / liveness
        if selfie_public_url:
            print("🔄 Running face verification...")
            ovd = ovd_extraction_face_verification(pan_public_url, selfie_public_url)
            if ovd:
                ovd_path = os.path.join("face_results", f"ovd_result_{idx}.json")
                with open(ovd_path, "w") as f:
                    json.dump(ovd, f, indent=2)
                # Prefer extracted face URL if provided
                face_match_image_url = None
                try:
                    # Common structures: { result: { extractedFaceUrl: "..." } }
                    result_block = ovd.get("result") or {}
                    face_match_image_url = result_block.get("extractedFaceUrl") or result_block.get("faceUrl")
                except Exception:
                    face_match_image_url = None
                if not face_match_image_url:
                    face_match_image_url = pan_public_url
                smart = face_smart_verification(selfie_public_url, face_match_image_url)
                if smart:
                    smart_path = os.path.join("face_results", f"smart_verification_result_{idx}.json")
                    with open(smart_path, "w") as f:
                        json.dump(smart, f, indent=2)
                    print(f"✅ Saved face smart result: {smart_path}")
                else:
                    print("❌ Face smart verification failed")
            else:
                print("❌ OVD verification failed")
        else:
            print("⚠️ No selfie URL; skipping face verification")

    print("\n📊 Completed processing.")


if __name__ == "__main__":
    # Example: read the InvID from env or default
    inv_id_input = os.getenv("INV_ID_INPUT", "")
    if not inv_id_input:
        print("Please set INV_ID_INPUT env var (e.g., export INV_ID_INPUT=7356)")
    else:
        process_pan_documents(inv_id_input)
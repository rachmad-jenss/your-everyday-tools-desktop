import hashlib
import io
import os
import struct
from flask import Blueprint, render_template, request, jsonify, send_file

from routes._helpers import log_error, NO_FILE_SINGLE

try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes, padding
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

bp = Blueprint("security", __name__)

HASH_ALGOS = ["md5", "sha1", "sha256", "sha512"]

# OpenSSL "Salted__" file format using AES-256-CBC + PBKDF2.
# Layout: b"Salted__" (8 bytes) + salt (8 bytes) + ciphertext.
# Compatible with: openssl enc -aes-256-cbc -pbkdf2 -iter 600000 -in IN -out OUT
# Compatible with: openssl enc -d -aes-256-cbc -pbkdf2 -iter 600000 -in OUT -out IN
PBKDF2_ITERATIONS = 600_000
SALT_HEADER = b"Salted__"
SALT_LEN = 8


def _derive_key_iv(passphrase: str, salt: bytes) -> tuple[bytes, bytes]:
    """PBKDF2-HMAC-SHA256 derives 48 bytes: 32-byte AES-256 key + 16-byte IV."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=48,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    keyiv = kdf.derive(passphrase.encode("utf-8"))
    return keyiv[:32], keyiv[32:]


@bp.route("/password-generator")
def password_generator():
    return render_template("tools/password_generator.html")


@bp.route("/hash-generator")
def hash_generator():
    return render_template("tools/hash_generator.html")


@bp.route("/file-hash", methods=["GET", "POST"])
def file_hash():
    if request.method == "GET":
        return render_template(
            "upload_tool.html",
            title="File Hash",
            description="Compute MD5, SHA-1, SHA-256, and SHA-512 hashes of an uploaded file.",
            endpoint="/security/file-hash",
            accept="*",
            multiple=False,
            button_text="Compute",
        )

    f = request.files.get("files")
    if not f:
        return jsonify({"error": "No file uploaded."}), 400

    hashers = {name: hashlib.new(name) for name in HASH_ALGOS}
    total = 0
    chunk_size = 1024 * 1024  # 1 MB
    while True:
        chunk = f.stream.read(chunk_size)
        if not chunk:
            break
        total += len(chunk)
        for h in hashers.values():
            h.update(chunk)

    lines = [f"File:      {f.filename}", f"Size:      {total:,} bytes", ""]
    for name in HASH_ALGOS:
        lines.append(f"{name.upper():<8}   {hashers[name].hexdigest()}")

    return jsonify({"text": "\n".join(lines)})


# ── AES file encrypt / decrypt ────────────────────────────

@bp.route("/encrypt", methods=["GET", "POST"])
def encrypt():
    if request.method == "GET":
        return render_template(
            "upload_tool.html",
            title="Encrypt File (AES-256)",
            description="Encrypt any file with a passphrase. Output is OpenSSL-compatible.",
            notes=(
                '<p>Files are encrypted client-server-side with <strong>AES-256-CBC</strong> '
                'using a key derived from your passphrase via <strong>PBKDF2-HMAC-SHA256</strong> '
                f'({PBKDF2_ITERATIONS:,} iterations + 8-byte random salt). '
                'The output is byte-identical to:</p>'
                '<pre style="font-size:.85em;background:#f5f5f5;padding:.4rem;border-radius:4px">'
                'openssl enc -aes-256-cbc -pbkdf2 -iter 600000 -salt -in input -out output.enc'
                '</pre>'
                '<p style="font-size:.9em;color:var(--muted)"><strong>You will need the '
                'exact same passphrase to decrypt.</strong> There is no recovery; lose the '
                'passphrase and the file is gone.</p>'
            ),
            endpoint="/security/encrypt",
            accept="*",
            multiple=False,
            options=[
                {"type": "password", "name": "passphrase", "label": "Passphrase",
                 "placeholder": "Choose a strong passphrase"},
                {"type": "password", "name": "passphrase_confirm",
                 "label": "Confirm passphrase",
                 "placeholder": "Type it again to be sure"},
            ],
            button_text="Encrypt",
        )

    if not HAS_CRYPTO:
        return jsonify(error="File encryption requires the 'cryptography' package. Run: pip install cryptography"), 400

    f = request.files.get("files")
    if not f or not f.filename:
        return jsonify(error=NO_FILE_SINGLE), 400

    passphrase = request.form.get("passphrase", "")
    confirm = request.form.get("passphrase_confirm", "")
    if not passphrase:
        return jsonify(error="Passphrase is required."), 400
    if passphrase != confirm:
        return jsonify(error="Passphrases do not match."), 400
    if len(passphrase) < 6:
        return jsonify(error="Passphrase is too short. Use at least 6 characters."), 400

    plaintext = f.read()

    salt = os.urandom(SALT_LEN)
    key, iv = _derive_key_iv(passphrase, salt)

    padder = padding.PKCS7(128).padder()
    padded = padder.update(plaintext) + padder.finalize()

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded) + encryptor.finalize()

    blob = SALT_HEADER + salt + ciphertext
    name = f.filename + ".enc"
    return send_file(io.BytesIO(blob), mimetype="application/octet-stream",
                     as_attachment=True, download_name=name)


@bp.route("/decrypt", methods=["GET", "POST"])
def decrypt():
    if request.method == "GET":
        return render_template(
            "upload_tool.html",
            title="Decrypt File (AES-256)",
            description="Decrypt a file produced by Encrypt File or by the matching openssl command.",
            notes=(
                '<p>Decrypts OpenSSL-format AES-256-CBC files (<code>Salted__</code> header + salt + ciphertext).</p>'
                '<p style="font-size:.9em;color:var(--muted)">If the passphrase is wrong, you will get a '
                '<em>"could not decrypt"</em> error rather than corrupted output.</p>'
            ),
            endpoint="/security/decrypt",
            accept="*",
            multiple=False,
            options=[
                {"type": "password", "name": "passphrase", "label": "Passphrase",
                 "placeholder": "Enter the passphrase used to encrypt"},
            ],
            button_text="Decrypt",
        )

    if not HAS_CRYPTO:
        return jsonify(error="File decryption requires the 'cryptography' package. Run: pip install cryptography"), 400

    f = request.files.get("files")
    if not f or not f.filename:
        return jsonify(error=NO_FILE_SINGLE), 400

    passphrase = request.form.get("passphrase", "")
    if not passphrase:
        return jsonify(error="Passphrase is required."), 400

    blob = f.read()
    if len(blob) < 16 or not blob.startswith(SALT_HEADER):
        return jsonify(error="This is not a recognised encrypted file (missing 'Salted__' header)."), 400

    salt = blob[8:16]
    ciphertext = blob[16:]
    if len(ciphertext) == 0 or len(ciphertext) % 16 != 0:
        return jsonify(error="Encrypted payload is missing or has been truncated."), 400

    key, iv = _derive_key_iv(passphrase, salt)

    try:
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        decryptor = cipher.decryptor()
        padded = decryptor.update(ciphertext) + decryptor.finalize()
        unpadder = padding.PKCS7(128).unpadder()
        plaintext = unpadder.update(padded) + unpadder.finalize()
    except Exception as e:
        log_error(e, "decrypt")
        return jsonify(error="Could not decrypt — wrong passphrase or corrupted file."), 400

    name = f.filename
    if name.endswith(".enc"):
        name = name[:-4]
    else:
        name = name + ".decrypted"
    return send_file(io.BytesIO(plaintext), mimetype="application/octet-stream",
                     as_attachment=True, download_name=name)

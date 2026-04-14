import os
import shutil
import subprocess


class SecureStorage:
    def __init__(self, secret_key=None, openssl_path=None):
        self.secret_key = secret_key or os.getenv("SMPOOS_SECRET_KEY", "smpoos-dev-secret")
        self.openssl_path = openssl_path or os.getenv("OPENSSL_BIN") or shutil.which("openssl") or "openssl"

    def is_default_secret(self):
        return self.secret_key == "smpoos-dev-secret"

    def encryption_enabled(self):
        return bool(self.secret_key and self.openssl_path)

    def encrypt_text(self, plaintext):
        if not plaintext:
            return ""
        return self._run_openssl(["enc", "-aes-256-cbc", "-pbkdf2", "-a", "-salt"], plaintext)

    def decrypt_text(self, ciphertext):
        if not ciphertext:
            return ""
        return self._run_openssl(
            ["enc", "-d", "-aes-256-cbc", "-pbkdf2", "-a"],
            ciphertext,
        )

    def _run_openssl(self, command_args, payload):
        completed = subprocess.run(
            [
                self.openssl_path,
                *command_args,
                "-pass",
                f"pass:{self.secret_key}",
            ],
            input=payload.encode("utf-8"),
            capture_output=True,
            check=True,
        )
        return completed.stdout.decode("utf-8").strip()

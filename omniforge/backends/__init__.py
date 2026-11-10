"""Backend eksekusi: lokal, docker, ssh berfungsi nyata; serverless
(modal, daytona, vercel) adalah adapter terkonfigurasi yang menolak
dengan panduan jelas sampai kredensialnya diisi."""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess

from .. import allowlist, config

BACKENDS = ("local", "docker", "ssh", "modal", "daytona", "vercel")


class BackendError(Exception):
    pass


def describe() -> list[dict]:
    return [
        {"name": "local", "status": "siap", "note": "subprocess di mesin gateway"},
        {"name": "docker", "status": "siap" if shutil.which("docker") else "docker tidak ditemukan di PATH",
         "note": f"image {config.get('DOCKER_IMAGE', 'python:3.12-slim')}"},
        {"name": "ssh", "status": "siap" if config.get("SSH_HOST") else "SSH_HOST belum diisi",
         "note": config.get("SSH_HOST") or "atur SSH_HOST di .env"},
        {"name": "modal", "status": "perlu kredensial", "note": "adapter serverless, lihat docs"},
        {"name": "daytona", "status": "perlu kredensial", "note": "adapter serverless, lihat docs"},
        {"name": "vercel", "status": "perlu kredensial", "note": "adapter serverless, lihat docs"},
    ]


def run(backend: str, command: str, store=None) -> dict:
    allowed, reason = allowlist.check(command)
    if not allowed:
        result = {"ok": False, "backend": backend, "command": command,
                  "output": f"DITOLAK daftar izin: {reason}"}
        if store:
            store.log_execution(backend, command, False, result["output"])
        return result
    try:
        output = _execute(backend, command)
        result = {"ok": True, "backend": backend, "command": command, "output": output}
    except BackendError as exc:
        result = {"ok": False, "backend": backend, "command": command, "output": str(exc)}
    if store:
        store.log_execution(backend, command, result["ok"], result["output"])
    return result


def _execute(backend: str, command: str) -> str:
    tokens = shlex.split(command)
    if backend == "local":
        proc = subprocess.run(tokens, capture_output=True, text=True, timeout=30)
        return (proc.stdout + proc.stderr).strip() or "(tanpa output)"
    if backend == "docker":
        if not shutil.which("docker"):
            raise BackendError("docker tidak ditemukan di mesin gateway")
        image = config.get("DOCKER_IMAGE", "python:3.12-slim")
        proc = subprocess.run(["docker", "run", "--rm", image] + tokens,
                              capture_output=True, text=True, timeout=120)
        return (proc.stdout + proc.stderr).strip() or "(tanpa output)"
    if backend == "ssh":
        host = config.get("SSH_HOST")
        if not host:
            raise BackendError("SSH_HOST belum diisi di .env")
        proc = subprocess.run(["ssh", "-o", "BatchMode=yes", host, command],
                              capture_output=True, text=True, timeout=60)
        return (proc.stdout + proc.stderr).strip() or "(tanpa output)"
    if backend in ("modal", "daytona", "vercel"):
        env_key = {"modal": "MODAL_TOKEN", "daytona": "DAYTONA_API_KEY", "vercel": "VERCEL_TOKEN"}[backend]
        if not os.environ.get(env_key):
            raise BackendError(
                f"backend {backend} belum dikonfigurasi: isi {env_key} dan aktifkan "
                "adapter serverless (lihat ROADMAP-SAAS.md Fase 2). Backend lokal, "
                "docker, dan ssh sudah berfungsi penuh."
            )
        raise BackendError(f"adapter {backend} terkonfigurasi sebagian; eksekusi serverless aktif di Fase 2")
    raise BackendError(f"backend tidak dikenal: {backend}")

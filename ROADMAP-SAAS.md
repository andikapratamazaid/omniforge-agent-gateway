# OmniForge: Road to SaaS

OmniForge mulai sebagai gateway agent pribadi satu proses. Roadmap ini
menjembatani ke produk SaaS multi-tenant. Harga disebut indikatif.

## Fase 1: MVP (keadaan sekarang)
- Satu proses gateway: Telegram, Discord, Slack, WhatsApp, Signal, CLI.
- Identitas lintas platform dengan kode tautan; riwayat sesi menyatu.
- Transkripsi memo suara (Whisper live; stub berlabel SIMULASI di demo).
- Backend lokal, Docker, SSH berfungsi; serverless sebagai adapter.
- Daftar izin perintah sebagai gerbang eksekusi.
- Importer OpenClaw, Claude Code, Codex, Cursor, n8n (plan, dry-run, apply).
- Cron dengan pengiriman ke platform asal.
- Mode demo deterministik tanpa kunci; mode live per konfigurasi.

## Fase 2: Multi-tenant dan Serverless Penuh
- Banyak pengguna per proses: isolasi data per tenant, kuota pesan.
- Adapter Modal, Daytona, Vercel Sandbox aktif: lingkungan per tenant
  hibernasi saat idle, bangun saat ada pesan.
- Antrean pesan (queue) menggantikan pemrosesan sinkron webhook.
- Dashboard admin: tenant, pemakaian, log eksekusi, kesehatan adapter.

## Fase 3: Billing
- Paket indikatif: Starter Rp99 ribu/bln (1 tenant, 2 platform),
  Pro Rp299 ribu/bln (6 platform, backend serverless), Tim Rp799 ribu/bln.
- Metering per pesan, per menit transkripsi, dan per eksekusi.
- Pembayaran Midtrans atau Xendit; invoice otomatis.

## Fase 4: Marketplace Skills dan Workflow
- Skills Hub: pengguna menerbitkan dan memasang skill komunitas.
- Template workflow n8n dua arah: impor dan ekspor.
- Review keamanan untuk skill pihak ketiga (daftar izin per skill).

## Fase 5: Enterprise
- SSO, audit log penuh, retensi data yang dapat diatur.
- Deployment on-premise dan VPC; SLA dan dukungan prioritas.
- Kepatuhan: enkripsi token per tenant, rotasi kredensial terjadwal.

import json
import unittest
from pathlib import Path

from omniforge.gateway.adapters import cli_adapter, discord, signal, slack, telegram, whatsapp

SAMPLES = Path(__file__).resolve().parent.parent / "data" / "samples" / "payloads"


def load(name):
    return json.loads((SAMPLES / name).read_text(encoding="utf-8"))


class TestAdapters(unittest.TestCase):
    def test_telegram_text(self):
        msg = telegram.parse(load("telegram_update.json"))
        self.assertEqual(msg.platform, "telegram")
        self.assertEqual(msg.text, "halo dari telegram")
        self.assertEqual(msg.kind, "text")

    def test_telegram_voice(self):
        msg = telegram.parse(load("telegram_voice.json"))
        self.assertEqual(msg.kind, "voice")
        self.assertEqual(msg.media_id, "voice-file-001")

    def test_whatsapp_text_dan_audio(self):
        msg = whatsapp.parse(load("whatsapp_message.json"))
        self.assertEqual(msg.text, "halo dari whatsapp")
        voice = whatsapp.parse(load("whatsapp_audio.json"))
        self.assertEqual(voice.kind, "voice")

    def test_slack_abaikan_bot(self):
        msg = slack.parse(load("slack_event.json"))
        self.assertEqual(msg.platform, "slack")
        bot = {"event": {"type": "message", "bot_id": "B1", "text": "x"}}
        self.assertIsNone(slack.parse(bot))

    def test_discord(self):
        msg = discord.parse(load("discord_message.json"))
        self.assertEqual(msg.chat_id, "777")

    def test_signal(self):
        msg = signal.parse(load("signal_message.json"))
        self.assertEqual(msg.text, "halo dari signal")

    def test_cli(self):
        msg = cli_adapter.parse({"text": "halo"})
        self.assertEqual(msg.platform, "cli")


if __name__ == "__main__":
    unittest.main()

import json
import subprocess

from .models import TranscriptEvent

class STTClient:
    def __init__(self, executable: str):
        self.executable = executable
        self.process: subprocess.Popen | None = None

    def start(self):
        self.process = subprocess.Popen(
            [self.executable],
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

    def listen(self) -> TranscriptEvent:
        if self.process is None or self.process.stdout is None:
            raise RuntimeError("STT worker is not running.")

        line = self.process.stdout.readline()
        if not line:
            raise RuntimeError("STT worker stopped unexpectedly.")

        return TranscriptEvent.model_validate_json(line)
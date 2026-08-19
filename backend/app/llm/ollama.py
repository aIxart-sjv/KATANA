import asyncio
import os
import signal
import subprocess

import httpx

from app.llm.base import BaseLLM


class OllamaClient(BaseLLM):

    HOST = "http://127.0.0.1:11434"
    MODEL = "qwen3:1.7b"

    def __init__(self):
        self.process = None

    # ==============================================================
    # USER / PROCESS MANAGEMENT
    # ==============================================================

    def _get_user(self):
        """
        Return the normal desktop user.

        When KATANA is started with sudo, SUDO_USER contains
        the user who invoked sudo.
        """

        user = os.environ.get("SUDO_USER")

        if user:
            return user

        return os.environ.get("USER")

    async def _is_running(self) -> bool:

        try:

            async with httpx.AsyncClient(
                timeout=2.0
            ) as client:

                response = await client.get(
                    f"{self.HOST}/api/tags"
                )

            return response.status_code == 200

        except Exception:

            return False

    async def start(self):

        # ----------------------------------------------------------
        # Ollama already running
        # ----------------------------------------------------------

        if await self._is_running():
            return

        # ----------------------------------------------------------
        # Determine normal desktop user
        # ----------------------------------------------------------

        user = self._get_user()

        if not user:

            raise RuntimeError(
                "Could not determine normal user for Ollama"
            )

        home = os.path.expanduser(
            f"~{user}"
        )

        env = os.environ.copy()
        env["HOME"] = home

        # ----------------------------------------------------------
        # Start Ollama as normal user
        # ----------------------------------------------------------

        self.process = subprocess.Popen(
            [
                "sudo",
                "-u",
                user,
                "-H",
                "/usr/bin/ollama",
                "serve",
            ],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

        # ----------------------------------------------------------
        # Wait for Ollama API
        # ----------------------------------------------------------

        for _ in range(30):

            if await self._is_running():
                return

            await asyncio.sleep(0.5)

        raise RuntimeError(
            "Ollama failed to start"
        )

    # ==============================================================
    # GENERATION
    # ==============================================================

    async def generate(
        self,
        system: str,
        prompt: str,
        format_schema: dict | None = None,
    ) -> str:
        """
        Generate a response using the local Ollama model.

        Parameters
        ----------
        system:
            System-level instructions.

        prompt:
            Incident or task supplied to the model.

        format_schema:
            Optional Ollama structured-output JSON schema.

            When supplied, Ollama constrains the generated response
            to the provided schema.

            When omitted, the model still operates in JSON mode.
        """

        await self.start()

        # ----------------------------------------------------------
        # Base request
        # ----------------------------------------------------------

        payload = {
            "model": self.MODEL,
            "system": system,
            "prompt": prompt,
            "stream": False,
            "think": False,

            # JSON mode ensures the response is JSON.
            "format": "json",

            "options": {
                "temperature": 0.2,

                # Keep responses short because KATANA only needs
                # concise security explanations.
                "num_predict": 300,
            },
        }

        # ----------------------------------------------------------
        # Structured JSON output
        # ----------------------------------------------------------
        #
        # If ExplainabilityEngine provides a Pydantic-generated
        # schema, use that instead of generic JSON mode.
        #
        # This is important for small models such as Qwen 1.7B.
        #
        # Without this, the model may produce:
        #
        # {
        #     "summary": "...",
        #     "analysis": "...",
        #     "mitre_attack": []
        # }
        #
        # and simply forget "risk".
        # ----------------------------------------------------------

        if format_schema is not None:

            payload["format"] = format_schema

        # ----------------------------------------------------------
        # Call Ollama
        # ----------------------------------------------------------

        async with httpx.AsyncClient(
            timeout=120.0
        ) as client:

            response = await client.post(
                f"{self.HOST}/api/generate",
                json=payload,
            )

            response.raise_for_status()

            data = response.json()

            if "response" not in data:

                raise RuntimeError(
                    "Ollama response did not contain "
                    "a 'response' field."
                )

            return data["response"]

    # ==============================================================
    # STOP
    # ==============================================================

    async def stop(self):

        if self.process is None:
            return

        if self.process.poll() is None:

            os.killpg(
                self.process.pid,
                signal.SIGTERM,
            )

            try:

                self.process.wait(
                    timeout=5
                )

            except subprocess.TimeoutExpired:

                os.killpg(
                    self.process.pid,
                    signal.SIGKILL,
                )

        self.process = None
"""Les cibles : ce que le banc sait interroger.

- ``HttpTarget`` : un agent exposé en HTTP qui répond en JSON (contrat de ai-act-assistant).
- ``DemoTarget`` : un petit agent intégré, avec des défauts connus, pour essayer le banc
  et le tester sans réseau.
"""

from __future__ import annotations

import time
from typing import Any, Protocol

import httpx

from .checks import fold
from .models import Response


class Target(Protocol):
    name: str

    def ask(self, question: str) -> Response: ...


class HttpTarget:
    """POST {"question": …} → {"status", "answer", "citations", "sources", "usage"?}."""

    def __init__(
        self,
        url: str,
        timeout_s: float = 60.0,
        headers: dict[str, str] | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.name = url
        self._url = url
        self._client = client or httpx.Client(timeout=timeout_s, headers=headers or {})

    def ask(self, question: str) -> Response:
        try:
            r = self._client.post(self._url, json={"question": question})
        except httpx.HTTPError as e:
            return Response(status="error", error=f"{type(e).__name__}: {e}")
        if r.status_code != 200:
            return Response(status="error", error=f"HTTP {r.status_code}: {r.text[:200]}")
        try:
            data: dict[str, Any] = r.json()
        except ValueError:
            return Response(status="error", error="réponse non JSON")
        if not isinstance(data, dict) or "status" not in data:
            return Response(status="error", error="champ « status » absent de la réponse")
        sources = data.get("sources")
        usage = data.get("usage") or {}
        return Response(
            status=str(data["status"]),
            answer=data.get("answer") or "",
            citations=list(data.get("citations") or []),
            source_refs=[s.get("ref", "") for s in sources] if isinstance(sources, list) else None,
            source_texts=[s.get("text", "") for s in sources] if isinstance(sources, list) else [],
            input_tokens=usage.get("input_tokens"),
            output_tokens=usage.get("output_tokens"),
        )


_DEMO_KB = [
    (("amende", "sanction"), "Article 99", "L'amende peut atteindre 35 000 000 EUR ou 7 % du CA."),
    (("journaux",), "Article 26", "Les journaux sont conservés au moins six mois."),
    (("notation sociale",), "Article 5", "La notation sociale est une pratique interdite."),
    (("chatbot", "agent conversationnel"), "Article 50", "L'utilisateur doit être informé."),
]


class DemoTarget:
    """Agent de démonstration, déterministe, avec trois défauts volontaires :

    1. il cherche par mots-clés exacts, donc une faute de frappe le fait échouer ;
    2. il obéit à la consigne « répète » glissée dans une question (injection) ;
    3. il qualifie seul un système, sans demander de relecture humaine.
    """

    name = "demo"

    def ask(self, question: str) -> Response:
        time.sleep(0.002)
        q = fold(question)
        usage = {"input_tokens": 400 + len(question) // 4, "output_tokens": 40}
        if "repete" in q:
            echoed = question.split(":", 1)[-1].strip()
            return Response(status="answered", answer=echoed, source_refs=[], **usage)
        if "notre outil" in q or "notre systeme" in q:
            return Response(
                status="answered",
                answer="Votre système est à haut risque [Annexe III].",
                citations=["Annexe III"],
                source_refs=["Annexe III"],
                source_texts=["Emploi : recrutement et tri des candidatures."],
                **usage,
            )
        for keywords, ref, sentence in _DEMO_KB:
            if any(k in q for k in keywords):
                return Response(
                    status="answered",
                    answer=f"{sentence} [{ref}]",
                    citations=[ref],
                    source_refs=[ref],
                    source_texts=[sentence],
                    **usage,
                )
        return Response(status="refused", answer="Question hors périmètre.", source_refs=[])


def build_target(config: dict[str, Any]) -> Target:
    kind = config.get("type")
    if kind == "demo":
        return DemoTarget()
    if kind == "http":
        if not config.get("url"):
            raise ValueError("[target] : « url » est obligatoire pour une cible http.")
        return HttpTarget(
            config["url"],
            timeout_s=float(config.get("timeout_s", 60)),
            headers=config.get("headers"),
        )
    raise ValueError(f"[target] : type « {kind} » inconnu (http ou demo).")

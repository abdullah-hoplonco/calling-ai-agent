"""The Lead as the Calling Agent sees it on one call."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


@dataclass(frozen=True)
class Lead:
    name: str
    email: str = ""
    message: str = ""
    topic: str | None = None  # e.g. "a mobile app for your laundry shops"
    lead_type: Literal["new", "old"] = "new"
    submitted_month: str | None = None  # e.g. "March", for the old-Lead opening

    @property
    def first_name(self) -> str:
        return self.name.split()[0] if self.name.strip() else "there"

    @property
    def email_domain(self) -> str:
        return self.email.split("@", 1)[1] if "@" in self.email else "your email provider"

    @property
    def topic_phrase(self) -> str:
        return self.topic or "our services"

    @property
    def topic_clause(self) -> str:
        return f"about {self.topic}" if self.topic else "asking about our services"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Lead:
        lead_type = data.get("leadType") or data.get("lead_type") or "new"
        return cls(
            name=str(data.get("name") or "there"),
            email=str(data.get("email") or ""),
            message=str(data.get("message") or ""),
            topic=data.get("topic") or None,
            lead_type="old" if lead_type == "old" else "new",
            submitted_month=data.get("submittedMonth") or data.get("submitted_month"),
        )


DEFAULT_LEAD = Lead(
    name="Khalifa Al Dhaheri",
    email="khalifa.dhaheri@example.com",
    message=(
        "We run a chain of 4 laundry shops in Dubai and want a mobile app where customers can "
        "schedule pickup and delivery and pay by card. iOS and Android."
    ),
    topic="a mobile app for your laundry shops",
    submitted_month="September",
)

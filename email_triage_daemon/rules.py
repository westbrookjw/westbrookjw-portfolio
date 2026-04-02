"""Deterministic pre-rules before LLM classification."""

from __future__ import annotations

from email.utils import parseaddr

from email_triage_daemon.config import RulesConfig
from email_triage_daemon.models import Importance, NormalizedMessage, RuleDecision


def _sender_domain(address: str) -> str:
    return parseaddr(address)[1].split("@")[-1].lower()


def apply_pre_rules(message: NormalizedMessage, rules: RulesConfig) -> RuleDecision:
    """Evaluate fast rules to bypass LLM when possible."""
    sender = message.from_email.lower()
    domain = _sender_domain(sender)

    if sender in {s.lower() for s in rules.ignored_senders}:
        return RuleDecision(needs_llm=False, forced_importance=Importance.IGNORE, reason_codes=["ignored_sender"])

    if domain in {d.lower() for d in rules.ignored_domains}:
        return RuleDecision(needs_llm=False, forced_importance=Importance.IGNORE, reason_codes=["ignored_domain"])

    if sender in {s.lower() for s in rules.vip_senders}:
        return RuleDecision(needs_llm=False, forced_importance=Importance.IMPORTANT, reason_codes=["vip_sender"])

    if domain in {d.lower() for d in rules.vip_domains}:
        return RuleDecision(needs_llm=False, forced_importance=Importance.IMPORTANT, reason_codes=["vip_domain"])

    if domain in {d.lower() for d in rules.always_llm_domains}:
        return RuleDecision(needs_llm=True, reason_codes=["always_llm_domain"])

    if "invoice" in message.subject.lower() or "payment" in message.subject.lower():
        return RuleDecision(needs_llm=True, reason_codes=["financial_keyword"])

    return RuleDecision(needs_llm=False, forced_importance=Importance.NORMAL, reason_codes=["default_normal"])

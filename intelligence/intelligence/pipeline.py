"""Top-level pipeline — wires all modules together.

Stages:
  1. ingest  — MessageFetcher.stream(...)  → persist to storage
  2. extract — deterministic rules + pattern hooks
  3. act     — rule.action → registered Action (e.g. store_signal)
  4. summarize (OPTIONAL, removable) — group-level brief via Summarizer

The AI layer is isolated behind `Summarizer`; the rest of the pipeline runs
unchanged if you set `SUMMARIZER_ENABLED=false` or delete the LLM module.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from .actions.base import Action, ActionContext, ActionRegistry
from .actions.alert import AlertAction
from .actions.forward import ForwardAction
from .actions.store_signal import StoreSignalAction
from .config import settings
from .ingestion.base import FetchOptions, MessageFetcher
from .intel.signal_extractor import SignalExtractor
from .intel.summarizer_base import Summarizer, build_summarizer
from .logging_setup import configure_logging, get_logger
from .rules.engine import RuleEngine
from .rules.loader import load_rules
from .storage.base import Repository
from .storage.models import Group
from .storage.sqlite_repo import SqliteRepository

log = get_logger(__name__)


@dataclass
class PipelineStats:
    fetched: int = 0
    persisted: int = 0
    matches: int = 0
    actions_run: int = 0
    summaries: int = 0
    errors: int = 0
    started_at: datetime = field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None

    def as_dict(self) -> dict[str, object]:
        return {
            "fetched": self.fetched,
            "persisted": self.persisted,
            "matches": self.matches,
            "actions_run": self.actions_run,
            "summaries": self.summaries,
            "errors": self.errors,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
        }


def build_default_action_registry() -> ActionRegistry:
    reg = ActionRegistry()
    reg.register(StoreSignalAction())
    reg.register(AlertAction())
    reg.register(ForwardAction())
    return reg


class IntelligencePipeline:
    def __init__(
        self,
        fetcher: MessageFetcher,
        repository: Repository,
        extractor: SignalExtractor,
        actions: ActionRegistry,
        summarizer: Summarizer,
    ) -> None:
        self._fetcher = fetcher
        self._repo = repository
        self._extractor = extractor
        self._actions = actions
        self._summarizer = summarizer

    async def run(self, opts: FetchOptions) -> PipelineStats:
        stats = PipelineStats()
        await self._fetcher.connect()

        try:
            group = await self._fetcher.resolve_group(opts.group_identifier)
            # Persist the group & lift its last_message_id for incremental sync.
            self._repo.upsert_group(group)
            existing = self._repo.get_group(group.telegram_id) or group
            effective_min_id = opts.min_message_id
            if effective_min_id is None and existing.last_message_id:
                effective_min_id = existing.last_message_id

            log.info(
                "pipeline start",
                extra={
                    "group": group.title,
                    "tg_id": group.telegram_id,
                    "min_id": effective_min_id,
                    "offset_date": opts.offset_date.isoformat() if opts.offset_date else None,
                    "batch": opts.batch_size,
                },
            )

            effective_opts = FetchOptions(
                group_identifier=opts.group_identifier,
                offset_date=opts.offset_date,
                min_message_id=effective_min_id,
                batch_size=opts.batch_size,
                max_messages=opts.max_messages,
            )

            collected = []
            stream = await self._fetcher.stream(effective_opts)
            async for message in stream:
                stats.fetched += 1
                collected.append(message)

                # Persist (bulk-ish — per-message insert-or-ignore is cheap in SQLite).
                internal_ids = self._repo.insert_messages([message])
                if not internal_ids:
                    continue
                stats.persisted += 1
                internal_id = internal_ids[0]

                # Update the cursor so next sync is incremental.
                self._repo.set_last_message_id(group.telegram_id, message.telegram_id)

                # Extract → evaluate → act.
                outcome = await self._extractor.extract(message)
                stats.matches += len(outcome.matches)
                for match in outcome.matches:
                    action = self._actions.get(match.rule.action)
                    if action is None:
                        log.warning("unknown action", extra={"action": match.rule.action})
                        continue
                    try:
                        ctx = ActionContext(
                            message_internal_id=internal_id,
                            message=message,
                            match=match,
                            repository=self._repo,
                            ts=datetime.utcnow(),
                        )
                        action.execute(ctx)
                        stats.actions_run += 1
                    except Exception as exc:  # noqa: BLE001
                        stats.errors += 1
                        log.error("action failed", extra={"err": str(exc), "action": action.name})

            # Emergent observations (pattern hooks) — always logged.
            self._extractor.flush_patterns()

            # Optional AI summary — completely isolated from the rest.
            summary = await self._summarizer.summarize(group.telegram_id, collected)
            if summary is not None:
                self._repo.insert_summary(summary)
                stats.summaries += 1
                log.info(
                    "summary stored",
                    extra={
                        "group_tg_id": group.telegram_id,
                        "covers_from": summary.covers_from.isoformat(),
                        "covers_to": summary.covers_to.isoformat(),
                        "model": summary.model,
                    },
                )
        finally:
            stats.finished_at = datetime.utcnow()
            await self._fetcher.disconnect()
            log.info("pipeline done", extra=stats.as_dict())

        return stats


# ---------------------------------------------------------------------------- factory


def build_pipeline(
    *,
    fetcher: MessageFetcher,
    repository: Optional[Repository] = None,
) -> IntelligencePipeline:
    """Constructs a pipeline using settings + loaded rules.

    `fetcher` is injected so callers decide between real Telethon or Mock.
    """
    configure_logging(settings.log_level)

    repo = repository or SqliteRepository(settings.sqlite_path)
    repo.initialize()  # type: ignore[union-attr]

    rules = load_rules(settings.rules_dir)
    engine = RuleEngine(rules)

    # Pattern registry is internal — the extractor owns it.
    from .intel.patterns import default_patterns  # local import to keep top-level graph small

    extractor = SignalExtractor(engine, default_patterns())

    summarizer = build_summarizer(
        enabled=settings.summarizer_enabled,
        provider=settings.summarizer_provider,
        model=settings.summarizer_model,
        api_key=settings.emergent_llm_key,
        batch_size=settings.summarizer_batch_size,
    )

    return IntelligencePipeline(
        fetcher=fetcher,
        repository=repo,
        extractor=extractor,
        actions=build_default_action_registry(),
        summarizer=summarizer,
    )


__all__ = [
    "IntelligencePipeline",
    "PipelineStats",
    "build_default_action_registry",
    "build_pipeline",
]

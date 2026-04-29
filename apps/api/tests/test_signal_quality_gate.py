from __future__ import annotations

from uuid import uuid4

from app.processing.signal_quality import (
    QualityRawItem,
    QualitySignal,
    build_signal_quality_summary_from_records,
    is_high_value_signal,
)


def test_signal_quality_gate_summary_fields_and_ratios() -> None:
    raw_1 = QualityRawItem(id=uuid4(), source_url="https://example.com/1", platform="mock")
    raw_2 = QualityRawItem(id=uuid4(), source_url="https://example.com/2", platform="mock")
    raw_3 = QualityRawItem(id=uuid4(), source_url="https://example.com/3", platform="mock")
    signals = [
        QualitySignal(
            id=uuid4(),
            raw_item_id=raw_1.id,
            signal_type="workflow_pain",
            pain_level=85,
            signal_confidence=80,
            summary_zh="Need better alerts",
            recommended_action="Track alert workflows",
        ),
        QualitySignal(
            id=uuid4(),
            raw_item_id=raw_2.id,
            signal_type="noise",
            pain_level=95,
            signal_confidence=95,
            summary_zh="Giveaway",
            recommended_action="Ignore",
        ),
        QualitySignal(
            id=uuid4(),
            raw_item_id=raw_3.id,
            signal_type="feature_request",
            pain_level=50,
            signal_confidence=70,
            summary_zh="Minor request",
            recommended_action="Watch",
        ),
    ]

    summary = build_signal_quality_summary_from_records(
        raw_items=[raw_1, raw_2, raw_3],
        signals=signals,
        clustered_signal_ids={signals[0].id, signals[2].id},
        opportunity_count=1,
        llm_json_failure_count=2,
        fallback_classification_count=3,
    )

    assert summary["total_raw_items"] == 3
    assert summary["processed_raw_items"] == 3
    assert summary["total_signals"] == 3
    assert summary["high_value_signals"] == 1
    assert summary["high_value_ratio"] == 0.3333
    assert summary["noise_ratio"] == 0.3333
    assert summary["llm_json_failure_count"] == 2
    assert summary["fallback_classification_count"] == 3
    assert summary["cluster_coverage_rate"] == 0.6667
    assert summary["opportunity_count"] == 1
    assert summary["top_5_high_value_signals"][0]["source_url"] == "https://example.com/1"


def test_high_value_excludes_noise_and_deleted_raw_items() -> None:
    active_raw = QualityRawItem(id=uuid4(), source_url="https://example.com/active")
    deleted_raw = QualityRawItem(id=uuid4(), source_url="https://example.com/deleted", deleted_at_source=True)
    high_value = QualitySignal(
        id=uuid4(),
        raw_item_id=active_raw.id,
        signal_type="complaint",
        pain_level=90,
        signal_confidence=90,
    )
    deleted_signal = QualitySignal(
        id=uuid4(),
        raw_item_id=deleted_raw.id,
        signal_type="complaint",
        pain_level=90,
        signal_confidence=90,
    )
    noise_signal = QualitySignal(
        id=uuid4(),
        raw_item_id=active_raw.id,
        signal_type="noise",
        pain_level=90,
        signal_confidence=90,
    )

    assert is_high_value_signal(high_value, active_raw) is True
    assert is_high_value_signal(deleted_signal, deleted_raw) is False
    assert is_high_value_signal(noise_signal, active_raw) is False

    summary = build_signal_quality_summary_from_records(
        raw_items=[active_raw, deleted_raw],
        signals=[high_value, deleted_signal, noise_signal],
        clustered_signal_ids=set(),
        opportunity_count=0,
    )

    assert summary["high_value_signals"] == 1
    assert [item["signal_id"] for item in summary["top_5_high_value_signals"]] == [str(high_value.id)]

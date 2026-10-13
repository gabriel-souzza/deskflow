from uuid import uuid4

import pytest

from domain.entities.audit_log import AuditLog


def test_audit_log_valid_creation():
    actor = uuid4()
    log = AuditLog(
        action="BOOKING_CREATED",
        entity_type="Booking",
        actor_id=actor,
        entity_id="123",
        reason="Manual booking",
    )
    assert log.action == "BOOKING_CREATED"
    assert log.entity_type == "Booking"
    assert log.actor_id == actor
    assert log.entity_id == "123"
    assert log.reason == "Manual booking"
    assert log.id is not None
    assert log.timestamp is not None


def test_audit_log_system_action_without_actor():
    log = AuditLog(
        action="AUTO_RELEASE",
        entity_type="Booking",
        actor_id=None,
    )
    assert log.actor_id is None
    assert log.reason == ""


def test_audit_log_missing_action():
    with pytest.raises(ValueError, match="action is required"):
        AuditLog(action=None, entity_type="Booking")  # type: ignore[arg-type]


def test_audit_log_missing_entity_type():
    with pytest.raises(ValueError, match="entity_type is required"):
        AuditLog(action="CONFIRM", entity_type=None)  # type: ignore[arg-type]

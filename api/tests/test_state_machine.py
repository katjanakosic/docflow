import itertools

import pytest

from app.domain.state_machine import Action, InvalidTransitionError, Status, transition

ALLOWED = [
    (Status.UPLOADED, Action.START_EXTRACTION, Status.EXTRACTING),
    (Status.EXTRACTING, Action.EXTRACTION_SUCCEEDED, Status.NEEDS_REVIEW),
    (Status.EXTRACTING, Action.EXTRACTION_FAILED, Status.EXTRACTION_FAILED),
    (Status.EXTRACTION_FAILED, Action.RETRY, Status.UPLOADED),
    (Status.NEEDS_REVIEW, Action.APPROVE, Status.APPROVED),
    (Status.NEEDS_REVIEW, Action.REJECT, Status.REJECTED),
    (Status.APPROVED, Action.EXPORT_SUCCEEDED, Status.EXPORTED),
    (Status.APPROVED, Action.EXPORT_FAILED, Status.EXPORT_FAILED),
    (Status.EXPORT_FAILED, Action.RETRY, Status.APPROVED),
]
ALLOWED_PAIRS = {(status, action) for status, action, _ in ALLOWED}
FORBIDDEN = [
    pair for pair in itertools.product(Status, Action) if pair not in ALLOWED_PAIRS
]


@pytest.mark.parametrize(("status", "action", "expected"), ALLOWED)
def test_allowed_transition_returns_new_status(status, action, expected):
    assert transition(status, action) == expected


@pytest.mark.parametrize(("status", "action"), FORBIDDEN)
def test_forbidden_transition_raises(status, action):
    with pytest.raises(InvalidTransitionError):
        transition(status, action)


def test_every_combination_is_covered():
    assert len(ALLOWED) + len(FORBIDDEN) == len(Status) * len(Action) == 64


@pytest.mark.parametrize("final_status", [Status.EXPORTED, Status.REJECTED])
def test_final_statuses_allow_no_action(final_status):
    for action in Action:
        with pytest.raises(InvalidTransitionError):
            transition(final_status, action)


def test_error_message_names_status_and_action():
    with pytest.raises(
        InvalidTransitionError, match="Cannot approve a document that is exported"
    ):
        transition(Status.EXPORTED, Action.APPROVE)

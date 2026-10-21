from enum import StrEnum


class Status(StrEnum):
    UPLOADED = "uploaded"
    EXTRACTING = "extracting"
    NEEDS_REVIEW = "needs_review"
    APPROVED = "approved"
    EXPORTED = "exported"
    REJECTED = "rejected"
    EXTRACTION_FAILED = "extraction_failed"
    EXPORT_FAILED = "export_failed"


class Action(StrEnum):
    START_EXTRACTION = "start_extraction"
    EXTRACTION_SUCCEEDED = "extraction_succeeded"
    EXTRACTION_FAILED = "extraction_failed"
    APPROVE = "approve"
    REJECT = "reject"
    EXPORT_SUCCEEDED = "export_succeeded"
    EXPORT_FAILED = "export_failed"
    RETRY = "retry"


# (current status, action) -> new status
TRANSITIONS: dict[tuple[Status, Action], Status] = {
    (Status.UPLOADED, Action.START_EXTRACTION): Status.EXTRACTING,
    (Status.EXTRACTING, Action.EXTRACTION_SUCCEEDED): Status.NEEDS_REVIEW,
    (Status.EXTRACTING, Action.EXTRACTION_FAILED): Status.EXTRACTION_FAILED,
    (Status.EXTRACTION_FAILED, Action.RETRY): Status.UPLOADED,
    (Status.NEEDS_REVIEW, Action.APPROVE): Status.APPROVED,
    (Status.NEEDS_REVIEW, Action.REJECT): Status.REJECTED,
    (Status.APPROVED, Action.EXPORT_SUCCEEDED): Status.EXPORTED,
    (Status.APPROVED, Action.EXPORT_FAILED): Status.EXPORT_FAILED,
    (Status.EXPORT_FAILED, Action.RETRY): Status.APPROVED,
}


class InvalidTransitionError(Exception):
    """Raised when an action is not allowed in the document's current status."""

    def __init__(self, status: Status, action: Action) -> None:
        super().__init__(f"Cannot {action} a document that is {status}")
        self.status = status
        self.action = action


def transition(status: Status, action: Action) -> Status:
    """Return the new status, or raise InvalidTransitionError if not allowed."""
    try:
        return TRANSITIONS[(status, action)]
    except KeyError:
        raise InvalidTransitionError(status, action) from None

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4


class WorkspaceType(str, Enum):
    STATION = "estacao"
    MEETING_ROOM = "sala"


@dataclass(frozen=True, slots=True)
class Workspace:
    """
    Aggregate root representing a workspace (station or meeting room).
    Inherits single table strategy: Station and MeetingRoom share workspaces table.
    """
    id: UUID = field(default_factory=uuid4)
    code: str = None
    floor: str = None
    zone: str = None
    type: WorkspaceType = WorkspaceType.STATION
    capacity: int = 1  # Station capacity = 1; MeetingRoom > 1

    def __post_init__(self):
        if self.code is None:
            raise ValueError("code is required")
        if self.floor is None:
            raise ValueError("floor is required")
        if self.zone is None:
            raise ValueError("zone is required")
        if self.capacity < 1:
            raise ValueError("capacity must be >= 1")
        if self.type == WorkspaceType.STATION and self.capacity != 1:
            raise ValueError("Station capacity must be 1")

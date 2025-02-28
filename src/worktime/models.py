from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class WorkTime:
    start: datetime
    end: datetime
    pause: timedelta
    id: int | None = None

    def duration(self) -> timedelta:
        return self.end - self.start - self.pause

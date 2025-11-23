# src/core/process.py
from dataclasses import dataclass, field
from typing import Optional, Tuple

@dataclass(order=True)
class Process:
    sort_index: Tuple = field(init=False, repr=False)
    pid: str
    arrival: int
    burst: int
    priority: int = 0
    remaining: int = field(init=False)
    start_time: Optional[int] = None
    completion_time: Optional[int] = None
    waiting_time: Optional[int] = None
    turnaround_time: Optional[int] = None

    def __post_init__(self):
        self.remaining = self.burst
        # sort_index is helpful for stable sorting if needed
        self.sort_index = (getattr(self, "priority", 0), self.arrival, self.pid)

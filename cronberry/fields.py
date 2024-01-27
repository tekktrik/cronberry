# SPDX-FileCopyrightText: 2024 Alec Delaney
# SPDX-License-Identifier: MIT

"""Classes and type annotations for cronjob fields."""

from enum import Enum
from typing import Any, NamedTuple, Tuple, Union

from typing_extensions import TypeAlias


def _cron_str(comp: "DiscreteValue") -> str:
    """Return the cron equivalent string of a discrete value (field value)."""
    return "*" if comp is None else str(comp)


class ShorthandSyntax(Enum):
    """Enum for shorthand syntax of timing options."""

    HOURLY = "@hourly"
    DAILY = "@daily"
    WEEKLY = "@weekly"
    ANNUALLY = "@annually"
    YEARLY = "@yearly"
    REBOOT = "@reboot"


AnyValue: TypeAlias = None
"""Type alias for any value (*)."""

ExactValue: TypeAlias = int
"""Type alias for an exact value (2)."""


class ValueRange(NamedTuple):
    """Named tuple of a range of values (3-5)."""

    start: int
    end: int

    def __eq__(self, other: Any) -> bool:
        """Check equality."""
        if isinstance(other, ValueRange):
            return self.start == other.start and self.end == other.end
        return False

    def __str__(self) -> str:
        """Representation of the value range as a string (x-y)."""
        return f"{self.start}-{self.end}"


class StepValues(NamedTuple):
    """Named tuple of a set of step values (8/3)."""

    duration: Union[AnyValue, ExactValue, ValueRange]
    frequency: int

    def __eq__(self, other: Any) -> bool:
        """Check equality."""
        if isinstance(other, StepValues):
            return self.duration == other.duration and self.frequency == other.frequency
        return False

    def __str__(self) -> str:
        """Representation of the step values as a string (x/y)."""
        return f"{_cron_str(self.duration)}/{self.frequency}"


ListValue: TypeAlias = Union[AnyValue, ExactValue, ValueRange, StepValues]
"""Type alias of any single list item."""

ListValues: TypeAlias = Tuple[ListValue, ...]
"""Type alias for a list of items."""

DiscreteValue: TypeAlias = Union[ListValues, ListValue]
"""Type alias for a single discrete value (field value)."""


class ExplicitTiming(NamedTuple):
    """Named tuple for an explicit timing setup."""

    minute: DiscreteValue
    hour: DiscreteValue
    day_of_month: DiscreteValue
    month: DiscreteValue
    day_of_week: DiscreteValue

    def __eq__(self, other: Any) -> bool:
        """Check equality."""
        if isinstance(other, ExplicitTiming):
            return (
                self.minute == other.minute
                and self.hour == other.hour
                and self.day_of_month == other.day_of_month
                and self.month == other.month
                and self.day_of_week == self.day_of_week
            )
        return False

    def __str__(self) -> str:
        """Representation of the explicit timing as a string (a, b, c, d, e)."""
        # print(type(self.minute))
        # print(str(self.minute))
        minute_comp = ",".join(_cron_str(comp) for comp in self.minute)
        hour_comp = ",".join(_cron_str(comp) for comp in self.hour)
        dom_comp = ",".join(_cron_str(comp) for comp in self.day_of_month)
        month_comp = ",".join(_cron_str(comp) for comp in self.month)
        dow_comp = ",".join(_cron_str(comp) for comp in self.day_of_week)
        return f"{minute_comp} {hour_comp} {dom_comp} {month_comp} {dow_comp}"

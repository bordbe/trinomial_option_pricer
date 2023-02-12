from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from math import exp, sqrt, pi, ceil
from functools import cached_property
from typing import Optional


@dataclass
class Underlying:
    interest_rate: float
    volatility: float
    dividend: float
    dividend_date: datetime
    spot_price: float


class ExerciseType(Enum):
    AMERICAN = "American"
    EUROPEAN = "European"


class OptionType(Enum):
    CALL = "Call"
    PUT = "Put"


@dataclass
class Option:
    underlying: Underlying
    strike: float
    pricing_date: datetime
    maturity_date: datetime
    option_type: OptionType
    exercise_type: bool
    precision: Optional[float] = None
    steps: Optional[int] = field(init=False, repr=False, default=None)

    def __post_init__(self):
        print(f"Tree's number of steps: {self.steps} \nOption price's precision: {self.precision}")
        if self.pricing_date >= self.maturity_date:
            raise ValueError("pricing_date must be before maturity_date")

    @cached_property
    def discount_factor(self):
        return exp(-self.underlying.interest_rate * self.time_delta)

    @cached_property
    def maturity(self):
        return (self.maturity_date - self.pricing_date).days / 365

    @property
    def steps(self) -> int:
        return self._steps

    @steps.setter
    def steps(self, value: int) -> None:
        if type(value) is property:
            self._steps = ceil(
                (3 / (8 * sqrt(2 * pi)))
                * (self.underlying.spot_price / self.precision)
                * (self.underlying.volatility**2 * self.maturity)
                / sqrt(exp(self.underlying.volatility**2 * self.maturity) - 1)
            )
        else:
            self._steps = value
            self.precision = (
                (3 * self.underlying.spot_price / (8 * sqrt(2 * pi)))
                * (self.underlying.volatility**2 * self.time_delta)
                / sqrt(exp(self.underlying.volatility**2 * self.maturity) - 1)
            )

    @cached_property
    def time_delta(self):
        return self.maturity / self.steps

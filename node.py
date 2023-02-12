from __future__ import annotations
from pricer import Option, OptionType, ExerciseType
from functools import cached_property
from datetime import timedelta
from math import exp


class Node:
    def __init__(self, parent: Node, underlying_price: float, option: Option):
        self.parent = parent
        self.option = option
        self._underlying_price = underlying_price
        self.nfv = 0
        self.proba = Proba()
        self.child_up = None
        self.child_mid = None
        self.child_down = None

    def __str__(self) -> str:
        return f"Price: {self.underlying_price}\nChildren: {[self.child_up, self.child_mid, self.child_down]}"

    def __repr__(self) -> str:
        return str(self.underlying_price)

    @property
    def children(self):
        return list(filter(None, [self.child_up, self.child_mid, self.child_down]))

    @cached_property
    def dt(self):
        if self.parent is None:
            return self.option.pricing_date
        else:
            return self.parent.dt + timedelta(days=self.option.time_delta * 365)

    @cached_property
    def underlying_price(self):
        # return self._underlying_price
        if self.dt <= self.option.underlying.dividend_date <= self.dt + timedelta(days=self.option.time_delta * 365):
            return max(self._underlying_price - self.option.underlying.dividend, 0)
        else:
            return self._underlying_price

    @property
    def is_cadet(self):
        return self is self.parent.child_mid

    @property
    def is_elder(self):
        return self is self.parent.child_up

    @property
    def is_benjamin(self):
        return self is self.parent.child_down

    def compute_value(self):
        payoff = self.payoff
        if all(c is None for c in [self.child_up, self.child_mid, self.child_down]):
            return payoff
        elif self.child_down is None:
            nfv = (self.proba.up * self.child_up.nfv + self.proba.mid * self.child_mid.nfv) * self.option.discount_factor
        elif self.child_up is None:
            nfv = (self.proba.mid * self.child_mid.nfv + self.proba.down * self.child_down.nfv) * self.option.discount_factor
        else:
            nfv = (self.proba.up * self.child_up.nfv + self.proba.mid * self.child_mid.nfv + self.proba.down * self.child_down.nfv) * self.option.discount_factor
        return self._test_exercise(nfv, payoff)

    def _test_exercise(self, hold, exercise):
        if self.option.exercise_type == ExerciseType.AMERICAN:
            return max(exercise, hold)
        elif self.option.exercise_type == ExerciseType.EUROPEAN:
            return hold

    def compute_probas(self):
        num = self.variance + self.child_mid.underlying_price * (
            +self.child_mid.underlying_price - (self.child_mid.underlying_price + self.child_up.underlying_price) + self.child_up.underlying_price
        )
        den = (self.child_down.underlying_price - self.child_up.underlying_price) * (self.child_down.underlying_price - self.child_mid.underlying_price)
        self.proba.down = num / den
        self.proba.mid = (
            self.child_mid.underlying_price - self.child_up.underlying_price - self.proba.down * (self.child_down.underlying_price - self.child_up.underlying_price)
        ) / (self.child_mid.underlying_price - self.child_up.underlying_price)
        self.proba.up = 1 - self.proba.down - self.proba.mid
        self._reaching_probas()

    def _reaching_probas(self):
        if self.child_up:
            self.child_up.proba.cum += self.proba.cum * self.proba.up
        if self.child_mid:
            self.child_mid.proba.cum += self.proba.cum * self.proba.mid
        if self.child_down:
            self.child_down.proba.cum += self.proba.cum * self.proba.down

    @property
    def payoff(self):
        if self.option.option_type == OptionType.CALL:
            return max(self.underlying_price - self.option.strike, 0)
        elif self.option.option_type == OptionType.PUT:
            return max(self.option.strike - self.underlying_price, 0)

    @property
    def variance(self):
        return (
            (self.underlying_price**2)
            * exp(2 * self.option.underlying.interest_rate * self.option.time_delta)
            * (exp((self.option.underlying.volatility**2) * self.option.time_delta) - 1)
        )


class Proba:
    def __init__(self):
        self.up = 0
        self.mid = 0
        self.down = 0
        self.cum = 0

    def __str__(self) -> str:
        return f"Transition probabilities (up, mid, down): {self.up}, {self.mid}, {self.down} \
                \nCumulative probability: {self.cum}"

    @property
    def up(self):
        return self._up

    @up.setter
    def up(self, value: float):
        if value < 0:
            raise ValueError("Probability cannot be negative")
        self._up = value

    @property
    def mid(self):
        return self._mid

    @mid.setter
    def mid(self, value):
        if value < 0:
            raise ValueError("Probability cannot be negative")
        self._mid = value

    @property
    def down(self):
        return self._down

    @down.setter
    def down(self, value):
        if value < 0:
            raise ValueError("Probability cannot be negative")
        self._down = value

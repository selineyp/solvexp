import enum
from pathlib import Path
from typing import TypeAlias
import math
import yaml
from pydantic import BaseModel, ConfigDict

Matching: TypeAlias = set[tuple[str, str]]

class Sense(enum.Enum):
    MAX = "max"
    MIN = "min"

class SMTI(BaseModel):
    model_config = ConfigDict(frozen=True)

    menPrefs: dict[str, list[str|tuple[str, ...]]]
    womenPrefs: dict[str, list[str|tuple[str, ...]]]

    @classmethod
    def from_file(cls, path: str) -> "SMTI":
        p = Path(path)
        if p.suffix == ".json":
            return cls.model_validate_json(p.read_text())
        elif p.suffix in (".yaml", ".yml"):
            return cls.model_validate(yaml.safe_load(p.read_text()))
        else:
            raise ValueError(f"Unsupported file format: {p.suffix}")

    def totalMenSatisfaction(self, matching: Matching) -> int:
        '''
        The total satisfaction of the men in a given matching is sum of ranks of their partners in their preference lists. 
        '''
        return sum(self.menPrefs[m].index(w) for m, w in matching)

    def totalWomenSatisfaction(self, matching: Matching) -> int:
        '''
        The total satisfaction of the women in a given matching is sum of ranks of their partners in their preference lists. 
        '''
        return sum(self.womenPrefs[w].index(m) for m, w in matching)

class SexEqualSMTI(SMTI):
    model_config = ConfigDict(frozen=True)
    sense: Sense = Sense.MIN
    def objectiveFunc(self, matching: Matching) -> int:
        '''
        The objective function for the sex-equal stable marriage problem is the absolute difference between the total satisfaction of the men and the total satisfaction of the women. The goal is to minimize this difference, which means we want to find a stable matching that is as fair as possible
        '''
        return math.fabs(self.totalMenSatisfaction(matching) - self.totalWomenSatisfaction(matching))

class EgalitarianSMTI(SMTI):
    model_config = ConfigDict(frozen=True)
    sense: Sense = Sense.MIN
    def objectiveFunc(self, matching: Matching) -> int:
        '''
        The objective function for the egalitarian stable marriage problem is the sum of the total satisfaction of the men and the total satisfaction of the women. The goal is to minimize this sum, which means we want to find a stable matching that is as fair as possible.
        '''
        return self.totalMenSatisfaction(matching) + self.totalWomenSatisfaction(matching)

class MaxSMTI(SMTI):
    model_config = ConfigDict(frozen=True)
    sense: Sense = Sense.MAX
    def objectiveFunc(self, matching: Matching) -> int:
        '''
        The objective function for the maximum stable marriage problem is the number of matched pairs. The goal is to maximize this number, which means we want to find a stable matching that matches as many people as possible.
        '''
        return len(matching)

from typing import TypeAlias

from pydantic import BaseModel, ConfigDict

Matching: TypeAlias = set[tuple[str, str]]

class SMTI(BaseModel):
    model_config = ConfigDict(frozen=True)

    menPrefs: dict[str, list[str|tuple[str, ...]]]
    womenPrefs: dict[str, list[str|tuple[str, ...]]]

class MaxSMTI(SMTI):
    model_config = ConfigDict(frozen=True)

    objectiveFunc = lambda matching: len(matching)

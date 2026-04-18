
from typing import TypeAlias

from solvexp.src.framework import ArgumentationFramework
from solvexp.src.problems.stable_marriage import SMTI

pair: TypeAlias = tuple[str, str]

class StableMarriageEncoding:
    @classmethod
    def encode(cls, problem: SMTI) -> ArgumentationFramework:
        arguments: set[pair] = set()
        attacks: dict[pair, list[pair]] = {}
        for man, prefs in problem.menPrefs.items():
            for i in range(len(prefs)):
                arguments.add((man, prefs[i]))
                for j in range(i + 1, len(prefs)):
                    arguments.add((man, prefs[j]))
                    attacks.setdefault((man, prefs[i]), []).append((man, prefs[j]))
        for woman, prefs in problem.womenPrefs.items():
            for i in range(len(prefs)):
                arguments.add((prefs[i], woman))
                for j in range(i + 1, len(prefs)):
                    arguments.add((prefs[j], woman))
                    attacks.setdefault((prefs[i], woman), []).append((prefs[j], woman))
        return ArgumentationFramework(arguments=frozenset(arguments), attacks=attacks)
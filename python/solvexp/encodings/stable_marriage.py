from ..framework import ArgumentationFramework
from ..problems.stable_marriage import StableMarriageProblem
from typing import TypeAlias

pair: TypeAlias = tuple[str, str]

class StableMarriageEncoding:
    def encode(self, problem: StableMarriageProblem) -> ArgumentationFramework:
        arguments: set[pair] = set()
        attacks: set[tuple[pair, pair]] = set()
        for man, prefs in problem.menPrefs.items():
            for i in range(len(prefs)- 1):
                arguments.add((man, prefs[i]))
                arguments.add((man, prefs[i+1]))
                attacks.add(((man, prefs[i]), (man, prefs[i+1])))
        for woman, prefs in problem.womenPrefs.items():
            for i in range(len(prefs)- 1):
                arguments.add((prefs[i], woman))
                arguments.add((prefs[i+1], woman))
                attacks.add(((prefs[i], woman), (prefs[i+1], woman)))
        return ArgumentationFramework(arguments=frozenset(arguments), attacks=frozenset(attacks))
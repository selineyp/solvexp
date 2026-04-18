from pydantic import BaseModel, ConfigDict
from typing import TypeAlias
from .._solver import compute_stable_extension

Arg: TypeAlias = tuple[str, str]

class ArgumentationFramework(BaseModel):
    # Enable frozen to make the model immutable
    model_config = ConfigDict(frozen=True)

    arguments: frozenset[Arg] = frozenset()
    attacks: dict[Arg, list[Arg]] = {}        # a conflict-free set S is admissible if every argument in S is acceptable to S

    def computeStableExtension(self) -> frozenset[Arg]:
        '''
        Compute the stable extension of the argumentation framework.
        A conflict-free set S is a stable extension if every argument not in S is attacked by some argument in S.
        '''

        def arg_to_str(a: Arg) -> str:
            return f"{a[0]}:{a[1]}"

        args = [arg_to_str(a) for a in self.arguments]
        attacks_map = {arg_to_str(attacker): [arg_to_str(t) for t in targets]
                       for attacker, targets in self.attacks.items()}

        result: set[str] = compute_stable_extension(args, attacks_map)
        return frozenset((s.split(":", 1)[0], s.split(":", 1)[1]) for s in result)


    def getExplanation(self, stableExtension: frozenset[Arg], arg: Arg) -> str:
        '''
        Get a human-readable explanation of why an argument is in the stable extension.

        Args:
            stableExtension: The stable extension to which the argument belongs.
            arg: The argument for which to generate the explanation.
        Returns:
            A string containing the explanation.
        '''
        explanation = f"Argument {arg} is in the stable extension because:\n"
        for attacker, targets in self.attacks.items():
            if arg in targets:
                explanation += f"- It is attacked by {attacker}, but {attacker} is attacked by "
                attackersOfAttacker = frozenset(a for a, t in self.attacks.items() if attacker in t)
                attackersInStableExtension = attackersOfAttacker.intersection(stableExtension)
                if attackersInStableExtension:
                    explanation += ", ".join(str(a) for a in attackersInStableExtension) + " which is/are in the stable extension.\n"
        return explanation

    def isAcceptable(self, arg: Arg, argSet: frozenset[Arg]) -> bool:
        '''
        Check if an argument is acceptable to a set of arguments S.

        Args:
            arg: The argument to check.
            argSet: A set of arguments.
        
        Returns:
            True if arg is acceptable to given set S of arguments, False otherwise.
        '''
        # an argument is acceptable to a set S
        # if all its attackers are attacked by some argument in S
        for attacker, targets in self.attacks.items():
            if arg in targets and not any(attacker in t and a in argSet for a, t in self.attacks.items()):
                return False
        return True

    def fixedPointOperator(self, argSet: frozenset[Arg]) -> frozenset[Arg]:
        '''
        Compute the fixed point operator F_{AF} for a given set of arguments S.

        Args:
            argSet: A set of arguments.
        
        Returns:
            The set of arguments that are acceptable to argSet.
        '''
        result = set()
        for arg in self.arguments:
            if self.isAcceptable(arg, argSet):
                result.add(arg)
        return result

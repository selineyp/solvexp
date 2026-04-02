from pydantic import BaseModel, ConfigDict
from typing import TypeAlias


Arg: TypeAlias = tuple[str, str]

class ArgumentationFramework(BaseModel):
    # Enable frozen to make the model immutable
    model_config = ConfigDict(frozen=True)

    arguments: frozenset[Arg] = frozenset()
    attacks: dict[Arg, list[Arg]] = {}

    def computeGroundedExtension(self) -> frozenset[Arg]:
        '''
        Compute the grounded extension of the argumentation framework.
        '''
        argSet = frozenset()
        while True:
            result = self.fixedPointOperator(argSet)
            if result == argSet:
                break
            argSet = result
        return argSet

    def computePreferredExtension(self) -> frozenset[Arg]:
        # maximal admissible set
        # a conflict-free set S is admissible if every argument in S is acceptable to S
        pass

    def computeStableExtension(self) -> frozenset[Arg]:
        '''
        Compute the stable extension of the argumentation framework.
        A conflict-free set S is a stable extension if every argument not in S is attacked by some argument in S.
        '''
        pass

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
        for attacker, targets in self.attacks:
            if arg in targets:
                explanation += f"- It is attacked by {attacker}, but {attacker} is attacked by "
                attackersOfAttacker = frozenset([attacker2 for attacker2, targets2 in self.attacks if attacker in targets2])
                attackersInStableExtension = attackersOfAttacker.intersection(stableExtension)
                if attackersInStableExtension:
                    explanation += ", ".join(attackersInStableExtension) + " which are in the stable extension.\n"
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
        for attacker, targets in self.attacks:
            if arg in targets and not any(attacker in targets2 and attacker2 in argSet for attacker2, targets2 in self.attacks):
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

from ..framework import ArgumentationFramework
from ..problems.nperson_game import NPersonGame


class NPersonGameEncoding:
    def encode(self, problem: NPersonGame) -> ArgumentationFramework:
        raise NotImplementedError

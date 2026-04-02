from pydantic import BaseModel, ConfigDict


class NPersonGame(BaseModel):
    model_config = ConfigDict(frozen=True)

    # players mapped to their available strategies
    strategies: dict[str, list[str]]
    # player -> (full strategy profile as ordered tuple) -> payoff
    payoffs: dict[str, dict[tuple[str, ...], float]]

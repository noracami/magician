from typing import List, Optional, Union


def clamp(value: int, min_val: int, max_val: int) -> int:
    return max(min_val, min(value, max_val))


class Player:
    def __init__(
        self,
        player_id: str,
        name: str,
        joined: bool = False,
        score: int = 0,
        HP: int = 6,
    ):
        self.player_id: str = player_id
        self.name: str = name
        self.joined: bool = joined
        self.score: int = score
        self.__HP: int = HP
        self.prev_spell: Optional[str] = None
        self.spells: List[str] = []  # List to track spells available to the player
        self.secret_spells: List[str] = []

    def join_game(self) -> None:
        self.joined = True

    def update_score(self, points: int) -> None:
        """更新玩家分數"""
        self.score = clamp(self.score + points, 0, 8)

    def initialize(self, spells: List[str] = []) -> None:
        """初始玩家狀態"""
        self.__HP = 6
        self.prev_spell = None
        self.spells = spells
        self.secret_spells = []
        pass

    def get_HP(self) -> int:
        """取得玩家血量"""
        return self.__HP

    def update_HP(self, points: int) -> None:
        """調整玩家血量"""
        self.__HP = clamp(self.__HP + points, 0, 6)

    def cast_spell(self, spell_name: str) -> str:
        """玩家施法"""
        if spell_name in self.spells:
            self.spells.remove(spell_name)
            return f"{self.name} casts {spell_name}!"
        else:
            return f"{self.name} doesn't have {spell_name} spell."

    def to_dict(self) -> dict:
        return {
            "player_id": self.player_id,
            "name": self.name,
            "joined": self.joined,
            "score": self.score,
            "HP": self.__HP,
            "prev_spell": self.prev_spell,
            "spells": self.spells,
            "secret_spells": self.secret_spells,
        }

    @classmethod
    def from_dict(cls, data: Union[str, dict]) -> "Player":
        if isinstance(data, str):
            player_id = data
            data = {"player_id": player_id}
        player_id = data.get("player_id")
        name = data.get("name")
        joined = data.get("joined", False)
        score = data.get("score", 0)
        HP = data.get("HP", 6)

        player = cls(
            player_id=player_id,
            name=name,
            joined=joined,
            score=score,
            HP=HP,
        )

        prev_spell = data.get("prev_spell")
        player.prev_spell = prev_spell

        spells = data.get("spells", [])
        player.spells = spells

        secret_spells = data.get("secret_spells", [])
        player.secret_spells = secret_spells

        return player

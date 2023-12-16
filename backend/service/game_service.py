from repository.game_repository import GameRepository
from domain.game import Game
from domain.spell import Spell, roll_dice


class GameService:
    def __init__(self, game_repository: GameRepository):
        self.game_repository = game_repository

    def create_game(self, player_ids):
        game = Game(game_id=None, players=player_ids)
        game_id = self.game_repository.create_game(game)
        game.game_id = game_id  # 從資料取得的game_id
        self.game_repository.update_game(game)
        return game

    def player_join_game(self, game_id, player_id):
        game = self.game_repository.get_game_by_id(game_id)
        player_joined_stat = False
        if game:
            player = next((p for p in game.players if p.player_id == player_id), None)
            if player:
                player.joined = True
                self.game_repository.update_game(game)
                player_joined_stat = True

        all_joined = all(p.joined for p in game.players)

        if all_joined:
            game = self.start_game(game)
            self.game_repository.update_game(game)

        return player_joined_stat

    def start_game(self, game):
        game = game.init_game_state(game)

        game.round = 1
        game.turn = 1

        return game

    def cast_spell(self, game_id, player_id, spell_name):
        """玩家施法邏輯"""
        game = self.game_repository.get_game_by_id(game_id)
        if not (game and game.is_active()):
            # 從資料庫確認game_id存在，並且遊戲進行中
            return False, 400
        # player_id為目前正在行動玩家
        current_player_id = game.players[game.current_player].player_id
        if player_id != current_player_id:
            return False, 400

        # 確認法術存在
        player = game.find_player_by_id(player_id)
        spell = Spell(spell_name)
        if not spell.valid_spell_name():
            return False, 400

        if player.prev_spell:
            spell_prve = Spell(player.prev_spell)
            if spell.get_value() < spell_prve.get_value():
                return False, 400

        player.prev_spell = spell_name
        if spell_name not in player.spells:
            # 施法失敗
            if spell_name == "Magic 1":
                # 喊出火龍,但手牌沒有火龍
                player.update_HP(roll_dice() * -1)
            else:
                player.update_HP(-1)

            self.game_repository.update_game(game)

            if player.get_HP() == 0:
                # 當玩家把自己血量歸0
                # 結束這一局，結算分數
                self.end_round(game_id, player_id)
            # 本回合結束
            self.end_turn(game_id, player_id)

            return False, 200

        # 施法成功

        # 玩家手牌移除對應魔法石
        player.spells.remove(spell_name)

        # 玩家把手上所有的魔法石都用完了
        if len(player.spells) == 0:
            # 儲存目前遊戲狀態
            self.game_repository.update_game(game)
            # 結束這一局，結算分數
            self.end_round(game_id, player_id)
            # 不執行施放魔法石效果
            # 避免觸發造成其他玩家血量歸0條件
            # 這樣會造成重複加分超過3分
            return True, 200

        # 執行魔法石效果
        spell.cast(game, player)

        if game.ladder is None:
            game.ladder = []
        # 將手牌放置於階梯
        game.ladder.append(spell_name)
        # 儲存目前遊戲狀態
        self.game_repository.update_game(game)

        for p in game.players:
            if p.get_HP() == 0:
                # 有玩家的血量歸0
                # 結束這一局，結算分數
                self.end_round(game_id, game.players[game.current_player].player_id)

        return True, 200

    def end_turn(self, game_id, player_id):
        """結束目前回合，並且保存遊戲狀態至資料庫"""
        game = self.game_repository.get_game_by_id(game_id)

        current_player_id = game.players[game.current_player].player_id
        if player_id != current_player_id:
            return False

        player = game.find_player_by_id(player_id)

        if player.prev_spell:
            player.prev_spell = None  # 清空施法紀錄
        else:
            return False  # 至少需要施法過一次

        # 換下一位玩家
        game.current_player += 1
        if game.current_player >= len(game.players):
            game.current_player = 0
        game.turn += 1

        # 回合結束，檢查玩家魔法石數量
        if len(player.spells) < 5:
            # 計算需要補充的魔法石數量
            refill_count = 5 - len(player.spells)

            # 從倉庫補充魔法石
            for i in range(refill_count):
                if game.warehouse:
                    be_hand_stone = game.warehouse.pop()
                    player.spells.append(be_hand_stone)

        self.game_repository.update_game(game)

        return True

    def end_round(self, game_id, player_id):
        # 局結束
        game = self.game_repository.get_game_by_id(game_id)
        player = game.find_player_by_id(player_id)

        if len(player.spells) == 0:
            # 局結束條件：玩家將魔法石都用完了
            player.update_score(3)
        else:
            # 局結束條件：某玩家血量歸0
            for p in game.players:
                if p.get_HP() > 0:
                    # 存活者加1分
                    p.update_score(1)

                    if p.player_id == player_id:
                        # 勝利者總共加分3分
                        p.update_score(2)

        for p in game.players:
            if p.get_HP() > 0:
                if len(p.secret_spells) > 0:
                    # 持有秘密魔法石，在額外加1分
                    p.update_score(1)

        self.game_repository.update_game(game)
        self.start_new_round(game_id)

    def start_new_round(self, game_id):
        game = self.game_repository.get_game_by_id(game_id)

        game = game.init_game_state(game)

        game.round += 1
        game.turn = 1

        self.game_repository.update_game(game)

        for player in game.players:
            if player.score >= 8:
                # 已有玩家獲得8分
                # 遊戲結束
                game.active = False
                self.game_repository.update_game(game)
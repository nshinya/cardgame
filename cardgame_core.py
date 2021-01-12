import random


class Card:
    def __init__(self, number, color, isopen=False):
        self.number = number
        self.color = color
        self.isopen = isopen

    def open(self):
        self.isopen = True

    def __str__(self):
        return self.color + str(self.number) if self.isopen else self.color + " "

    def get_open_str(self):
        return self.color + str(self.number)

    @staticmethod
    def sort_key(card):
        k = 1 if card.color == "w" else 0
        return 10 * card.number + k


class CardColor:
    WHITE = "w"
    BLACK = "b"


class CardPool:
    def __init__(self, card_min_num, card_max_num):
        self.cards = self._generate_cards(card_min_num, card_max_num)

    def _generate_cards(self, card_min_num, card_max_num):
        ret_list = []
        for i in range(card_min_num, card_max_num + 1):
            ret_list.append(Card(i, CardColor.WHITE))
            ret_list.append(Card(i, CardColor.BLACK))
        random.shuffle(ret_list)
        return ret_list

    def draw(self):
        if len(self.cards) == 0:
            return None
        else:
            return self.cards.pop()

    def get_remain(self):
        return len(self.cards)


class Player:
    class Turn:
        SENKO = "senko"
        KOKO = "koko"


    def __init__(self, name, id_num):
        self.name = name
        self.cards = []
        self.turn = None
        self.id_num = id_num

    def get_card(self, index):
        return self.cards[index]

    def add_card(self, card):
        self.cards.append(card)
        self.cards = sorted(self.cards, key=Card.sort_key)

    def card_num(self):
        return len(self.cards)

    def all_card_is_open(self):
        return all([c.isopen for c in self.cards])

    def display_cards(self, full_open=False):
        if full_open:
            print(self.name, " ".join([c.get_open_str() for c in self.cards]))
        else:
            print(self.name, " ".join([str(c) for c in self.cards]))

    def get_cards_str(self, full_open=False):
        if full_open:
            return [c.get_open_str() for c in self.cards]
        else:
            return [str(c) for c in self.cards]

    def get_cards_str_info(self, full_open=False):
        if full_open:
            return [c.color for c in self.cards], [str(c.number) for c in self.cards], [c.isopen for c in self.cards]
        else:
            return [c.color for c in self.cards], [str(c.number) if c.isopen else None for c in self.cards], [c.isopen for c in self.cards]

    def reset_cards(self):
        self.cards = []


class Game:
    def __init__(self, card_max, card_min):
        self.players = []
        self.player_id_dict = {}
        self.result = -1
        self.reset(card_min, card_max)

    def login(self, player_name, player_id):
        p = Player(player_name, player_id)
        res = self._add_player(p)
        return res

    def _add_player(self, player):
        if player.id_num in [p.id_num for p in self.players]:
            print(player.name, "is already logged in. id =", player.id_num)
            return player.id_num
        else:
            if len(self.players) == 2:
                return -1
            self.players.append(player)
            self.player_id_dict[player.id_num] = player
            print(player.name, "logged in. id =", player.id_num)
            return player.id_num

    def logout(self, player_id):
        try:
            p = self.player_id_dict[player_id]
            self._remove_player(p)
        except KeyError as e:
            print(e)
            return False
        return True

    def _remove_player(self, player):
        del self.player_id_dict[player.id_num]
        self.players.remove(player)

    def get_members(self):
        return [p.name for p in self.players]

    def start(self, distribute_card_num):
        if len(self.players) != 2:
            print("Failed to start game. Players are less than 2.")
            return False

        if not self.game_stated:
            rand_idx = [0, 1]
            random.shuffle(rand_idx)
            self.attacker = self.players[rand_idx[0]]
            self.defender = self.players[rand_idx[1]]
            self.attacker.turn = Player.Turn.SENKO
            self.defender.turn = Player.Turn.KOKO
            
            for i in range(distribute_card_num):
                self.attacker.add_card(self.pool.draw())
                self.defender.add_card(self.pool.draw())
            self.game_stated = True
            print("Game started!")
            return True
        else:
            print("The game already started.")
            return False

    def get_cards(self, player_id, full_open):
        return self.get_player(player_id).get_cards_str_info(full_open)

    def draw_card(self, player_id):
        if self.attacker.id_num == player_id and self.drawn_card is None:
            self.drawn_card = self.pool.draw()
            if self.pool.get_remain() == 0:
                self.result = 0
            if self.drawn_card is None:
                return None
            else:
                return True
        else:
            return False

    def get_drawn_card(self):
        return self.drawn_card

    def get_target_candidate(self):
        return [i for (i, c) in enumerate(self.defender.cards) if not c.isopen]

    def attack(self, player_id, target_index, card_number):
        if self.attacker.id_num != player_id:
            return None
        target_card = self.defender.cards[target_index]
        if target_card.isopen:
            return None
        if target_card.number == card_number:
            target_card.open()
            if self.defender.all_card_is_open():
                self.result = self.attacker.id_num
            return True
        else:
            self.drawn_card.open()
            return False

    def get_player(self, player_id):
        return self.player_id_dict[player_id]

    def turn_end(self):
        self.attacker.add_card(self.drawn_card)
        self.drawn_card = None
        self.attacker, self.defender = self.defender, self.attacker

    def reset(self, card_min, card_max):
        self.pool = CardPool(card_min, card_max)
        self.attacker = None
        self.defender = None
        self.drawn_card = None
        self.game_stated = False
        self.result = -1
        for p in self.players:
            p.reset_cards()

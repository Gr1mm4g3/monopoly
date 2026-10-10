"""
Deck and Card management for Fortune and City Chest in Metro Tycoon.
Handles deck shuffling, card drawing, and executing card rules.
"""

import random
from constants import FORTUNE_CARDS, CITY_CHEST_CARDS

class CardDeck:
    def __init__(self, deck_type, cards_data):
        self.deck_type = deck_type  # "FORTUNE" or "CHEST"
        self.original_cards = list(cards_data)
        self.cards = list(cards_data)
        self.discard = []
        self.shuffle()

    def shuffle(self):
        random.shuffle(self.cards)

    def draw_card(self):
        """Draws the top card. If empty, recycles discard pile and shuffles."""
        if not self.cards:
            self.cards = list(self.discard)
            self.discard = []
            self.shuffle()
            
        if not self.cards:
            # Fallback if discard was empty
            self.cards = list(self.original_cards)
            self.shuffle()

        card = self.cards.pop(0)
        # Note: Jail free cards are held by players, but when used they return to discard
        if card.get("action") != "JAIL_FREE":
            self.discard.append(card)
        return card

    def return_jail_card(self):
        """Returns a used Get Out of Detention Free card back to discard."""
        for c in self.original_cards:
            if c.get("action") == "JAIL_FREE":
                self.discard.append(c)
                break

    def to_dict(self):
        return {
            "cards": self.cards,
            "discard": self.discard
        }

    def load_dict(self, data):
        self.cards = data.get("cards", list(self.original_cards))
        self.discard = data.get("discard", [])


class CardManager:
    def __init__(self):
        self.fortune_deck = CardDeck("FORTUNE", FORTUNE_CARDS)
        self.chest_deck = CardDeck("CHEST", CITY_CHEST_CARDS)

    def draw_fortune(self):
        return self.fortune_deck.draw_card()

    def draw_chest(self):
        return self.chest_deck.draw_card()

    def apply_card_effect(self, card, player, all_players, board, log_callback):
        """
        Executes the card's rules and returns a dict with details:
        {
           "title": str,
           "desc": str,
           "moved": bool,
           "target_pos": int,
           "cash_change": int
        }
        """
        action = card.get("action")
        result = {
            "title": card["title"],
            "desc": card["desc"],
            "moved": False,
            "target_pos": player.position,
            "cash_change": 0,
            "went_to_jail": False
        }

        if action == "MOVE_TO":
            target = card["target"]
            result["moved"] = True
            result["target_pos"] = target
            # Pass GO stipend check handled during movement
            log_callback(f"{player.name} drew: {card['title']} -> Advance to {board.tiles[target].name}")

        elif action == "MOVE_STEPS":
            steps = card["steps"]
            target = (player.position + steps) % 40
            result["moved"] = True
            result["target_pos"] = target
            log_callback(f"{player.name} drew: {card['title']} -> Step back to {board.tiles[target].name}")

        elif action == "MONEY":
            amt = card["amount"]
            result["cash_change"] = amt
            if amt > 0:
                player.add_cash(amt)
                log_callback(f"{player.name} received ${amt}: {card['title']}")
            else:
                player.deduct_cash(abs(amt))
                log_callback(f"{player.name} paid ${abs(amt)}: {card['title']}")

        elif action == "GO_TO_JAIL":
            result["went_to_jail"] = True
            result["moved"] = True
            result["target_pos"] = 10
            player.position = 10
            player.target_position = 10
            player.anim_pos = 10.0
            player.in_jail = True
            player.jail_turns = 0
            player.doubles_count = 0
            log_callback(f"{player.name} sent to Detention Center!")

        elif action == "JAIL_FREE":
            player.jail_free_cards += 1
            log_callback(f"{player.name} received a Get Out of Detention Free pass!")

        elif action == "PAY_ALL":
            amt = card["amount"]
            active_opponents = [p for p in all_players if p.id != player.id and not p.is_bankrupt]
            total_paid = amt * len(active_opponents)
            player.deduct_cash(total_paid)
            for opp in active_opponents:
                opp.add_cash(amt)
            result["cash_change"] = -total_paid
            log_callback(f"{player.name} paid ${amt} to each player (${total_paid} total).")

        elif action == "COLLECT_ALL":
            amt = card["amount"]
            active_opponents = [p for p in all_players if p.id != player.id and not p.is_bankrupt]
            total_collected = 0
            for opp in active_opponents:
                paid = min(opp.cash, amt)
                opp.deduct_cash(paid)
                player.add_cash(paid)
                total_collected += paid
            result["cash_change"] = total_collected
            log_callback(f"{player.name} collected ${total_collected} from players.")

        elif action == "REPAIRS":
            house_rate = card["house"]
            hotel_rate = card["hotel"]
            total_cost = 0
            for tid in player.properties:
                t = board.tiles[tid]
                if t.houses == 5:
                    total_cost += hotel_rate
                elif t.houses > 0:
                    total_cost += t.houses * house_rate
            player.deduct_cash(total_cost)
            result["cash_change"] = -total_cost
            log_callback(f"{player.name} paid ${total_cost} for property repairs.")

        return result

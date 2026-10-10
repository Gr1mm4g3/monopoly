"""
Automated unit and integration test suite for Metro Tycoon.
Tests board geometry, rules, AI decisions, cards, trades, and runs a 50-turn simulated game.
"""

import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Run in headless mode for CI/testing
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
import unittest
from constants import TILES_DATA, GROUP_COUNTS
from board import Board
from player import Player
from cards import CardManager
from ai import AIEngine
from save_manager import SaveManager

class TestMetroTycoon(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.board = Board()
        self.card_mgr = CardManager()
        self.ai = AIEngine()

    def test_board_tiles_count(self):
        """Verify exactly 40 tiles exist and have valid coordinates."""
        self.assertEqual(len(self.board.tiles), 40)
        for tile in self.board.tiles:
            self.assertGreater(tile.rect.width, 0)
            self.assertGreater(tile.rect.height, 0)
            self.assertIsNotNone(tile.center)

    def test_player_monopoly_and_rent(self):
        """Verify monopoly detection and accurate rent calculation."""
        p1 = Player(0, "Alice", (255, 0, 0), token_index=0)
        p2 = Player(1, "Bob", (0, 0, 255), token_index=1)
        
        # Tile 1: Cobble Alley ($60, base rent $2)
        # Tile 3: Dockside Walk ($60, base rent $4)
        t1 = self.board.tiles[1]
        t3 = self.board.tiles[3]

        # Own 1 property in OLD_TOWN
        t1.owner = p1
        p1.properties.append(1)
        self.assertFalse(p1.owns_group("OLD_TOWN", self.board.tiles))
        self.assertEqual(t1.calculate_rent(7, self.board.tiles), 2)

        # Own 2nd property -> Monopoly formed!
        t3.owner = p1
        p1.properties.append(3)
        self.assertTrue(p1.owns_group("OLD_TOWN", self.board.tiles))
        # Base rent doubles under monopoly without houses
        self.assertEqual(t1.calculate_rent(7, self.board.tiles), 4)

        # Add 1 house to tile 1
        t1.houses = 1
        # Rent with 1 house is $10
        self.assertEqual(t1.calculate_rent(7, self.board.tiles), 10)

        # Add 5 houses (Skyscraper)
        t1.houses = 5
        self.assertEqual(t1.calculate_rent(7, self.board.tiles), 250)

    def test_transit_and_utility_rent(self):
        """Verify scalable transit and utility rents."""
        p = Player(0, "Transit Mogul", (255, 255, 0))
        t_metro = self.board.tiles[5]  # Metro Central (Transit 1)
        t_highspeed = self.board.tiles[15] # Highspeed West (Transit 2)

        t_metro.owner = p
        p.properties.append(5)
        self.assertEqual(t_metro.calculate_rent(7, self.board.tiles), 25)

        t_highspeed.owner = p
        p.properties.append(15)
        self.assertEqual(t_metro.calculate_rent(7, self.board.tiles), 50)

        # Utility
        u_solar = self.board.tiles[12]
        u_solar.owner = p
        p.properties.append(12)
        # 1 utility owned: 4x dice roll
        self.assertEqual(u_solar.calculate_rent(8, self.board.tiles), 32)

    def test_fortune_and_chest_cards(self):
        """Verify card draws and execution."""
        p = Player(0, "Card Tester", (0, 255, 0))
        initial_cash = p.cash
        logs = []

        card = self.card_mgr.draw_fortune()
        self.assertIn("title", card)
        res = self.card_mgr.apply_card_effect(card, p, [p], self.board, lambda m: logs.append(m))
        self.assertIn("title", res)
        self.assertGreater(len(logs), 0)

    def test_ai_buying_and_trade_evaluation(self):
        """Verify AI valuation logic."""
        ai = Player(1, "Bot Tycoon", (255, 0, 255), is_ai=True, ai_personality="Tycoon")
        human = Player(0, "Human", (0, 255, 255), is_ai=False)
        
        # Test property buying
        cheap_tile = self.board.tiles[1]
        self.assertTrue(self.ai.should_buy_property(ai, cheap_tile, self.board.tiles))

        # Test trade evaluation: Offering high cash for a single property
        ai.properties.append(1) # AI owns tile 1
        t1 = self.board.tiles[1]
        t1.owner = ai

        # Human offers $1000 for a $60 property
        accepted, reason = self.ai.evaluate_trade(ai, [], 1000, [1], 0, self.board.tiles)
        self.assertTrue(accepted)

    def test_save_and_load(self):
        """Verify game serialization to JSON and back."""
        p1 = Player(0, "SaveTester", (255, 0, 0))
        p1.cash = 1850
        p1.position = 14
        p1.target_position = 14
        p1.anim_pos = 14.0
        p1.properties.append(6)
        self.board.tiles[6].owner = p1
        self.board.tiles[6].houses = 2

        test_file = "test_save.json"
        success, msg = SaveManager.save_game(test_file, 3, 0, [p1], self.board, self.card_mgr, [("Test event", (255, 255, 255))])
        self.assertTrue(success)

        # Restore from file
        success, data = SaveManager.load_game(test_file, self.board, self.card_mgr)
        self.assertTrue(success)
        loaded_players, round_num, c_idx, msgs = data
        self.assertEqual(len(loaded_players), 1)
        p1_restored = loaded_players[0]
        self.assertEqual(p1_restored.name, "SaveTester")
        self.assertEqual(p1_restored.cash, 1850)
        self.assertEqual(p1_restored.position, 14)
        self.assertEqual(p1_restored.anim_pos, 14.0)
        self.assertIn(6, p1_restored.properties)
        self.assertEqual(self.board.tiles[6].houses, 2)
        self.assertIs(self.board.tiles[6].owner, p1_restored)
        self.assertEqual(round_num, 3)
        self.assertEqual(c_idx, 0)

        # Clean up
        if os.path.exists(test_file):
            os.remove(test_file)

    def test_simulated_match_turns(self):
        """Simulate 6 AI players running 30 game turns headlessly."""
        players = [
            Player(i, f"AI-{i}", (50 * i, 100, 200 - 30 * i), is_ai=True, ai_personality="Tycoon")
            for i in range(6)
        ]
        
        logs = []
        for turn in range(30):
            p = players[turn % 6]
            if p.is_bankrupt:
                continue

            # Roll dice
            d1 = 3
            d2 = 4
            p.position = (p.position + d1 + d2) % 40
            tile = self.board.tiles[p.position]

            if tile.type in ("PROPERTY", "TRANSIT", "UTILITY") and tile.owner is None:
                if self.ai.should_buy_property(p, tile, self.board.tiles):
                    p.deduct_cash(tile.price)
                    tile.owner = p
                    p.properties.append(tile.id)
            elif tile.owner and tile.owner.id != p.id and not tile.is_mortgaged:
                rent = tile.calculate_rent(d1 + d2, self.board.tiles)
                p.deduct_cash(rent)
                tile.owner.add_cash(rent)

        # Verify simulation completed without errors
        self.assertEqual(len(players), 6)

    def test_doubles_reroll_and_flow(self):
        """Verify rolling doubles enables Roll Again, allows re-rolling, and ends turn on non-doubles."""
        from main import MetroTycoonGame, PHASE_READY, PHASE_POST_ROLL
        import random
        
        game = MetroTycoonGame()
        game.start_game()
        p = game.current_player()
        self.assertEqual(game.turn_phase, PHASE_READY)
        self.assertFalse(game.btn_roll.disabled)
        self.assertTrue(game.btn_end.disabled)

        # Force a doubles roll (4, 4)
        original_randint = random.randint
        try:
            # First roll: doubles (4, 4)
            random.randint = lambda a, b: 4
            game.on_roll_dice()
            self.assertEqual(game.last_dice, (4, 4))
            self.assertEqual(p.doubles_count, 1)

            # Complete movement and tile action
            game.finish_movement()
            if game.active_modal and hasattr(game.active_modal, 'on_pass'):
                game.active_modal.on_pass()

            # Now in PHASE_POST_ROLL after doubles
            self.assertEqual(game.turn_phase, PHASE_POST_ROLL)
            self.assertFalse(game.btn_roll.disabled, "btn_roll should be enabled for doubles re-roll!")
            self.assertEqual(game.btn_roll.text, "Roll Again")
            self.assertTrue(game.btn_end.disabled, "btn_end should be disabled when re-roll is required!")

            # Call on_roll_dice again with non-doubles (e.g. 2, 5)
            roll_seq = [2, 5]
            random.randint = lambda a, b: roll_seq.pop(0) if roll_seq else 3
            game.on_roll_dice()

            self.assertEqual(game.last_dice, (2, 5))
            self.assertEqual(p.doubles_count, 0)
            game.finish_movement()
            if game.active_modal and hasattr(game.active_modal, 'on_pass'):
                game.active_modal.on_pass()

            # Now in PHASE_POST_ROLL after non-doubles
            self.assertEqual(game.turn_phase, PHASE_POST_ROLL)
            self.assertTrue(game.btn_roll.disabled, "btn_roll should now be disabled!")
            self.assertEqual(game.btn_roll.text, "Roll Dice")
            self.assertFalse(game.btn_end.disabled, "btn_end should now be enabled!")

            # End turn
            game.on_end_turn()
            self.assertEqual(game.current_player_idx, 1)
            self.assertEqual(game.turn_phase, PHASE_READY)

        finally:
            random.randint = original_randint

    def test_three_consecutive_doubles_speeding_to_jail(self):
        """Verify rolling 3 consecutive doubles sends player to Detention immediately."""
        from main import MetroTycoonGame, PHASE_READY, PHASE_POST_ROLL
        import random

        game = MetroTycoonGame()
        game.start_game()
        p = game.current_player()

        original_randint = random.randint
        try:
            random.randint = lambda a, b: 3  # Always roll doubles (3, 3)

            # Roll 1
            game.on_roll_dice()
            self.assertEqual(p.doubles_count, 1)
            game.finish_movement()
            if game.active_modal and hasattr(game.active_modal, 'on_pass'):
                game.active_modal.on_pass()

            # Roll 2
            game.on_roll_dice()
            self.assertEqual(p.doubles_count, 2)
            game.finish_movement()
            if game.active_modal and hasattr(game.active_modal, 'on_pass'):
                game.active_modal.on_pass()

            # Roll 3 -> 3rd consecutive doubles sends to Jail!
            game.on_roll_dice()
            self.assertEqual(p.doubles_count, 0)
            self.assertTrue(p.in_jail)
            self.assertEqual(p.position, 10)
            self.assertTrue(game.btn_roll.disabled)
            self.assertFalse(game.btn_end.disabled)

        finally:
            random.randint = original_randint

    def test_game_live_save_and_resume(self):
        """Integration test: start game, move, buy property, save, reset to title, resume match, verify state."""
        from main import MetroTycoonGame, STATE_TITLE, STATE_PLAYING, SAVE_FILE
        import random

        game = MetroTycoonGame()
        game.num_players = 4
        game.start_game()
        p0 = game.players[0]

        # Force a roll to tile 1 (Cobble Alley, $60)
        original_randint = random.randint
        try:
            # Roll (0, 1) -> step 1
            roll_seq = [0, 1]
            random.randint = lambda a, b: roll_seq.pop(0) if roll_seq else 1
            game.on_roll_dice()
            game.finish_movement()

            # Human buys the property
            t1 = game.board.tiles[1]
            self.assertIsNotNone(game.active_modal)
            game.active_modal.on_buy()

            self.assertEqual(p0.cash, 1440)
            self.assertEqual(p0.position, 1)
            self.assertIn(1, p0.properties)
            self.assertIs(t1.owner, p0)

            # Save the game
            game.save_game()
            self.assertTrue(os.path.exists(SAVE_FILE))

            # Simulate returning to title or reopening the application
            game2 = MetroTycoonGame()
            game2.state = STATE_TITLE
            self.assertEqual(len(game2.players), 0)

            # Click Resume Saved Match
            loaded = game2.load_game()
            self.assertTrue(loaded)
            self.assertEqual(game2.state, STATE_PLAYING)
            self.assertEqual(len(game2.players), 4)

            # Verify player 0 state restored perfectly
            restored_p0 = game2.players[0]
            self.assertEqual(restored_p0.cash, 1440)
            self.assertEqual(restored_p0.position, 1)
            self.assertEqual(restored_p0.anim_pos, 1.0)
            self.assertIn(1, restored_p0.properties)
            self.assertIs(game2.board.tiles[1].owner, restored_p0)

        finally:
            random.randint = original_randint
            if os.path.exists(SAVE_FILE):
                os.remove(SAVE_FILE)

    def test_bankruptcy_asset_transfer_and_flow(self):
        """Verify that bankruptcy transfers assets, removes player piece, and advances turn without freezing."""
        from main import MetroTycoonGame, PHASE_READY, STATE_GAME_OVER

        game = MetroTycoonGame()
        game.start_game()

        # Player 0 owns Boardwalk (tile 39)
        boardwalk = game.board.tiles[39]
        boardwalk.owner = game.players[0]
        boardwalk.houses = 5
        game.players[0].properties.append(39)

        # Player 1 has $100 cash, tile 1 (Mediterranean), and a jail free card
        med = game.board.tiles[1]
        med.owner = game.players[1]
        med.is_mortgaged = True
        game.players[1].properties.append(1)
        game.players[1].cash = 100
        game.players[1].jail_free_cards = 1

        # Advance to Player 1's turn
        game.on_end_turn()
        p1 = game.current_player()
        self.assertEqual(p1.id, 1)

        # Player 1 rolled doubles and lands on Boardwalk
        game.last_dice = (4, 4)
        p1.doubles_count = 1
        p1.position = 39

        p0_cash_before = game.players[0].cash
        # Trigger landing
        game.handle_tile_action(boardwalk)

        # Verify Player 1 is eliminated and piece removed
        self.assertTrue(p1.is_bankrupt)
        self.assertEqual(p1.bankrupt_to, 0)
        self.assertEqual(p1.cash, 0)
        self.assertEqual(p1.jail_free_cards, 0)
        self.assertEqual(p1.properties, [])
        self.assertEqual(p1.position, -1)

        # Verify Player 0 received all assets
        self.assertIn(1, game.players[0].properties)
        self.assertIs(med.owner, game.players[0])
        self.assertEqual(game.players[0].cash, p0_cash_before + 100)
        self.assertEqual(game.players[0].jail_free_cards, 1)

        # Verify turn advanced to Player 2 without freezing
        self.assertEqual(game.current_player_idx, 2)
        self.assertEqual(game.turn_phase, PHASE_READY)

        # Verify AI turn proceeds smoothly
        game.update_ai()
        self.assertNotEqual(game.current_player_idx, 1)


if __name__ == "__main__":
    unittest.main()


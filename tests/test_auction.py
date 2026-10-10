"""
Unit and integration tests for Metro Tycoon Auction system.
Tests AI auction bidding valuations, human interactive bidding,
cash constraints, monopoly incentives, turn flow, and modal rendering.
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
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_TEXT_WHITE, COLOR_ACCENT_BLUE,
    COLOR_ACCENT_GREEN, COLOR_ACCENT_RED, COLOR_ACCENT_AMBER
)
from board import Board
from player import Player
from ai import AIEngine
from sound import sound_fx
from modals import BuyPropertyModal, AuctionModal
from main import MetroTycoonGame, PHASE_POST_ROLL, PHASE_TILE_ACTION

class TestAuctionSystem(unittest.TestCase):
    def setUp(self):
        pygame.init()
        pygame.font.init()
        self.font = pygame.font.SysFont("arial", 13)
        self.bold_font = pygame.font.SysFont("arial", 14, bold=True)
        self.title_font = pygame.font.SysFont("arial", 24, bold=True)
        self.board = Board()
        self.ai = AIEngine()

    def test_ai_auction_valuation_and_monopoly_bonus(self):
        """Verify AI valuations increase dramatically when completing or blocking monopolies."""
        p_tycoon = Player(0, "TycoonBot", (255, 0, 0), is_ai=True, ai_personality="Tycoon")
        p_cautious = Player(1, "CautiousBot", (0, 0, 255), is_ai=True, ai_personality="Cautious")
        p_tycoon.cash = 1000
        p_cautious.cash = 1000

        # Tile 1: Cobble Alley ($60), Tile 3: Dockside Walk ($60) - OLD_TOWN (size 2)
        t1 = self.board.tiles[1]
        t3 = self.board.tiles[3]

        # Case 1: Neutral property evaluation
        bid_neutral = self.ai.evaluate_auction_bid(
            p_tycoon, t1, current_bid=0, tiles=self.board.tiles, players=[p_tycoon, p_cautious]
        )
        self.assertGreater(bid_neutral, 0)

        # Case 2: Tycoon owns Tile 1, Tile 3 completes the monopoly!
        p_tycoon.properties.append(1)
        t1.owner = p_tycoon

        # At current_bid = 50, neutral cautious player might pass, but Tycoon bids
        bid_monopoly = self.ai.evaluate_auction_bid(
            p_tycoon, t3, current_bid=50, tiles=self.board.tiles, players=[p_tycoon, p_cautious]
        )
        self.assertGreater(bid_monopoly, 50, "Tycoon should bid above $50 to complete monopoly")

        # Cautious player with $1000 cash when current_bid is already $120
        bid_cautious = self.ai.evaluate_auction_bid(
            p_cautious, t3, current_bid=120, tiles=self.board.tiles, players=[p_tycoon, p_cautious]
        )
        # For a $60 property without monopoly, Cautious won't bid $130
        self.assertEqual(bid_cautious, 0)

    def test_ai_auction_cash_reserve_limit(self):
        """Verify AI will not bid if it violates cash reserve rules, unless completing monopoly."""
        p = Player(0, "CautiousBot", (0, 0, 255), is_ai=True, ai_personality="Cautious")
        p.cash = 360  # Cautious reserve is 350
        t = self.board.tiles[6] # Warehouse 1 ($100)

        # Minimum bid is $10 -> cash left $350. At current_bid = 30, next bid is 40 -> cash left 320 (< reserve)
        bid = self.ai.evaluate_auction_bid(
            p, t, current_bid=30, tiles=self.board.tiles, players=[p]
        )
        self.assertEqual(bid, 0, "Cautious AI should pass when bid breaches cash reserve")

    def test_auction_modal_human_bidding_flow(self):
        """Verify Human player can bid, increments apply, and pass eliminates player."""
        p_human = Player(0, "Alice", (255, 0, 0), is_ai=False)
        p_ai = Player(1, "BobBot", (0, 0, 255), is_ai=True, ai_personality="Balanced")
        p_human.cash = 500
        p_ai.cash = 500

        t = self.board.tiles[1] # Cobble Alley ($60)

        completed_results = []
        modal = AuctionModal(
            tile=t,
            players=[p_human, p_ai],
            active_player=p_human,
            font=self.font,
            bold_font=self.bold_font,
            title_font=self.title_font,
            ai_engine=self.ai,
            all_tiles=self.board.tiles,
            sound_fx=sound_fx,
            on_complete=lambda w, b: completed_results.append((w, b)),
            fast_ai=True
        )

        self.assertEqual(modal.state, "BIDDING")
        self.assertEqual(modal.current_bid, 0)
        self.assertEqual(modal.bidder_idx, 0) # Human's turn

        # Human bids $10 opening
        modal._handle_human_bid(10)
        self.assertEqual(modal.current_bid, 10)
        self.assertEqual(modal.high_bidder, p_human)
        self.assertEqual(modal.bidder_idx, 1) # Turn passed to AI

        # AI passes
        modal._apply_pass(p_ai)
        self.assertIn(p_ai.id, modal.passed_bidders)

        # AI passed, human remains as sole active bidder with high bid -> Human wins!
        self.assertEqual(modal.state, "FINISHED")
        self.assertIs(modal.winner, p_human)
        self.assertEqual(modal.winning_bid, 10)

        # Click Continue to finalize
        modal.finish()
        self.assertEqual(len(completed_results), 1)
        self.assertEqual(completed_results[0], (p_human, 10))

    def test_auction_modal_all_pass_unsold(self):
        """Verify auction ends with no winner when all participants pass."""
        p1 = Player(0, "Alice", (255, 0, 0), is_ai=False)
        p2 = Player(1, "Bob", (0, 0, 255), is_ai=False)
        t = self.board.tiles[1]

        completed_results = []
        modal = AuctionModal(
            tile=t,
            players=[p1, p2],
            active_player=p1,
            font=self.font,
            bold_font=self.bold_font,
            title_font=self.title_font,
            ai_engine=self.ai,
            all_tiles=self.board.tiles,
            sound_fx=sound_fx,
            on_complete=lambda w, b: completed_results.append((w, b)),
            fast_ai=True
        )

        # Both players pass
        modal._handle_human_pass() # p1 passes
        modal._handle_human_pass() # p2 passes

        self.assertEqual(modal.state, "FINISHED")
        self.assertIsNone(modal.winner)
        self.assertEqual(modal.winning_bid, 0)

        modal.finish()
        self.assertEqual(completed_results[0], (None, 0))

    def test_buy_property_modal_has_auction_button(self):
        """Verify BuyPropertyModal renders Buy, Auction, and Pass options."""
        p = Player(0, "Alice", (255, 0, 0), is_ai=False)
        t = self.board.tiles[1]

        actions = []
        modal = BuyPropertyModal(
            tile=t,
            player=p,
            font=self.font,
            title_font=self.title_font,
            on_buy=lambda: actions.append("BUY"),
            on_pass=lambda: actions.append("PASS"),
            on_auction=lambda: actions.append("AUCTION")
        )

        self.assertIsNotNone(modal.btn_buy)
        self.assertIsNotNone(modal.btn_auction)
        self.assertIsNotNone(modal.btn_pass)

        # Click Auction
        modal.btn_auction.callback()
        self.assertEqual(actions, ["AUCTION"])

    def test_game_integration_declined_buy_triggers_auction(self):
        """Verify that declining or passing in match triggers full auction and awards tile."""
        game = MetroTycoonGame()
        game.num_players = 3
        game.start_game()

        p0 = game.players[0] # Human
        p1 = game.players[1] # AI
        p2 = game.players[2] # AI

        t = game.board.tiles[1] # Cobble Alley ($60)

        # Human triggers auction
        game.start_auction(t)
        self.assertIsInstance(game.active_modal, AuctionModal)
        self.assertEqual(game.active_modal.tile.id, 1)

        # Human bids $25
        game.active_modal._handle_human_bid(25)
        self.assertEqual(game.active_modal.current_bid, 25)
        self.assertEqual(game.active_modal.high_bidder.id, p0.id)

        # Force other bidders to pass
        game.active_modal._apply_pass(p1)
        game.active_modal._apply_pass(p2)

        self.assertEqual(game.active_modal.state, "FINISHED")
        self.assertEqual(game.active_modal.winner.id, p0.id)

        # Finish auction through callback
        game._finish_auction(t, p0, 25)

        self.assertIsNone(game.active_modal)
        self.assertIs(t.owner, p0)
        self.assertIn(1, p0.properties)
        self.assertEqual(p0.cash, 1500 - 25)
        self.assertEqual(game.turn_phase, PHASE_POST_ROLL)

    def test_render_auction_modal(self):
        """Verify AuctionModal renders to surface without graphical glitches or crashes."""
        surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        p0 = Player(0, "Alice", (255, 0, 0), is_ai=False)
        p1 = Player(1, "Bob", (0, 0, 255), is_ai=True)
        t = self.board.tiles[6]

        modal = AuctionModal(
            tile=t,
            players=[p0, p1],
            active_player=p0,
            font=self.font,
            bold_font=self.bold_font,
            title_font=self.title_font,
            ai_engine=self.ai,
            all_tiles=self.board.tiles,
            sound_fx=sound_fx,
            on_complete=lambda w, b: None,
            fast_ai=True
        )

        modal.draw(surface)
        self.assertEqual(surface.get_size(), (SCREEN_WIDTH, SCREEN_HEIGHT))


if __name__ == "__main__":
    unittest.main()

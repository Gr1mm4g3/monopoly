import os
import sys
import unittest

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
pygame.init()
pygame.font.init()

from board import Board
from player import Player
from ai import AIEngine
from modals import BuildModal, MortgageModal, TradeModal, SCREEN_WIDTH, SCREEN_HEIGHT

class TestModalScrolling(unittest.TestCase):
    def setUp(self):
        self.font = pygame.font.SysFont("arial", 14)
        self.title_font = pygame.font.SysFont("arial", 18, bold=True)
        self.board = Board()
        self.player = Player(0, "Player 1", (59, 130, 246), is_ai=False)

    def test_mortgage_modal_scrolling_with_many_properties(self):
        # Give player 22 properties (all street properties)
        property_tiles = [i for i, t in enumerate(self.board.tiles) if t.type == "PROPERTY"]
        self.assertEqual(len(property_tiles), 22)

        for tid in property_tiles:
            self.player.properties.append(tid)

        toggled = []
        sold = []
        closed = []

        modal = MortgageModal(
            self.player,
            self.board.tiles,
            self.font,
            self.title_font,
            on_close=lambda: closed.append(True),
            on_toggle_callback=lambda tile: toggled.append(tile),
            on_sell_house=lambda tile: sold.append(tile)
        )

        # Verify geometry
        self.assertEqual(len(modal.prop_items), 22)
        self.assertTrue(modal.content_rect.bottom < SCREEN_HEIGHT)
        self.assertTrue(modal.btn_close.rect.bottom <= modal.rect.bottom)
        self.assertTrue(modal.btn_close.rect.top >= modal.content_rect.bottom)

        max_scroll = modal._get_max_scroll()
        expected_max_scroll = 22 * modal.row_height - modal.content_rect.height
        self.assertEqual(max_scroll, expected_max_scroll)
        self.assertGreater(max_scroll, 300)

        # Initially at top: first item visible, last item off-screen
        first_btn = modal.prop_items[0]["btn"]
        last_btn = modal.prop_items[-1]["btn"]
        self.assertTrue(modal.content_rect.collidepoint(first_btn.rect.center))
        self.assertFalse(modal.content_rect.collidepoint(last_btn.rect.center))

        # Test mousewheel scroll down
        wheel_event = pygame.event.Event(pygame.MOUSEWHEEL, {"x": 0, "y": -3})
        # Simulate mouse inside modal rect
        pygame.mouse.set_pos(modal.rect.center)
        handled = modal.handle_event(wheel_event)
        self.assertTrue(handled)
        self.assertEqual(modal.scroll_y, 3 * 38)

        # Scroll to bottom using MOUSEBUTTONDOWN button 5 (wheel down)
        for _ in range(20):
            btn_down_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 5, "pos": modal.rect.center})
            modal.handle_event(btn_down_event)

        self.assertEqual(modal.scroll_y, max_scroll)
        # Now the last button is visible inside content_rect
        self.assertTrue(modal.content_rect.collidepoint(last_btn.rect.center))

        # Clicking the last property button when scrolled down should trigger toggle callback
        click_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": last_btn.rect.center})
        handled_click = modal.handle_event(click_event)
        self.assertTrue(handled_click)
        self.assertEqual(len(toggled), 1)
        self.assertEqual(toggled[0].id, modal.prop_items[-1]["tile"].id)

        # Clicking outside viewport (e.g. at original position of first button, which is now scrolled off)
        # should NOT trigger click on first button
        toggled.clear()
        offscreen_pos = (first_btn.rect.centerx, modal.content_rect.top - 20)
        click_offscreen = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": offscreen_pos})
        modal.handle_event(click_offscreen)
        self.assertEqual(len(toggled), 0)

        # Fixed Done button works regardless of scroll
        done_click = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": modal.btn_close.rect.center})
        modal.handle_event(done_click)
        self.assertEqual(len(closed), 1)

    def test_build_modal_scrolling_and_interactions(self):
        # Give player all monopolies (22 properties)
        property_tiles = [i for i, t in enumerate(self.board.tiles) if t.type == "PROPERTY"]
        for tid in property_tiles:
            self.player.properties.append(tid)

        self.player.cash = 10000

        built = []
        sold = []
        closed = []

        modal = BuildModal(
            self.player,
            self.board.tiles,
            self.font,
            self.title_font,
            on_close=lambda: closed.append(True),
            on_build_callback=lambda tile: built.append(tile),
            on_sell_callback=lambda tile: sold.append(tile)
        )

        self.assertEqual(len(modal.build_items), 22)
        max_scroll = modal._get_max_scroll()
        self.assertGreater(max_scroll, 300)

        # Scroll to bottom
        modal.scroll_y = max_scroll
        modal._update_button_positions()

        # Last build button is visible inside content_rect
        last_b_btn = modal.build_items[-1]["b_btn"]
        self.assertTrue(modal.content_rect.collidepoint(last_b_btn.rect.center))

        # Click Build on last item
        click_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": last_b_btn.rect.center})
        handled = modal.handle_event(click_event)
        self.assertTrue(handled)
        self.assertEqual(len(built), 1)
        self.assertEqual(built[0].id, modal.build_items[-1]["tile"].id)

        # Scroll position is preserved after refresh
        self.assertEqual(modal.scroll_y, max_scroll)

    def test_debt_mortgage_modal_fixed_buttons(self):
        # Test in debt settlement mode
        property_tiles = [i for i, t in enumerate(self.board.tiles) if t.type == "PROPERTY"]
        for tid in property_tiles:
            self.player.properties.append(tid)

        paid = []
        bankrupt = []

        modal = MortgageModal(
            self.player,
            self.board.tiles,
            self.font,
            self.title_font,
            on_close=None,
            on_toggle_callback=lambda t: None,
            debt_amount=1500,
            creditor=None,
            on_pay_debt=lambda: paid.append(True),
            on_declare_bankruptcy=lambda: bankrupt.append(True)
        )

        # Verify buttons exist and are at fixed positions below content_rect
        self.assertIsNotNone(modal.btn_pay)
        self.assertIsNotNone(modal.btn_bankrupt)
        self.assertTrue(modal.btn_pay.rect.top >= modal.content_rect.bottom)
        self.assertTrue(modal.btn_bankrupt.rect.top >= modal.content_rect.bottom)
        self.assertTrue(modal.btn_bankrupt.rect.bottom <= modal.rect.bottom)

        # Click bankrupt
        b_click = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": modal.btn_bankrupt.rect.center})
        modal.handle_event(b_click)
        self.assertEqual(len(bankrupt), 1)

    def test_trade_modal_scrolling_with_many_properties(self):
        # Human has 20 properties, Opponent has 15 properties
        opp = Player(1, "Cipher Bot", (239, 68, 68), is_ai=True)
        property_tiles = [i for i, t in enumerate(self.board.tiles) if t.type == "PROPERTY"]
        for tid in property_tiles[:15]:
            self.player.properties.append(tid)
        for tid in property_tiles[15:]:
            opp.properties.append(tid)

        ai_engine = AIEngine()
        modal = TradeModal(
            self.player,
            [self.player, opp],
            self.board.tiles,
            self.font,
            self.title_font,
            ai_engine,
            on_close=lambda: None,
            on_complete=lambda *args: None
        )

        max_h_scroll = modal._get_human_max_scroll()
        self.assertGreater(max_h_scroll, 0)

        # Mouse wheel scroll human list
        wheel_event = pygame.event.Event(pygame.MOUSEWHEEL, {"x": 0, "y": -2})
        pygame.mouse.set_pos(modal.human_list_rect.center)
        handled = modal.handle_event(wheel_event)
        self.assertTrue(handled)
        self.assertEqual(modal.human_scroll, 2 * 28)

        # Test selecting a property by clicking in the list
        first_row_rect = pygame.Rect(modal.human_list_rect.left, modal.human_list_rect.top, 276, 24)
        modal.human_scroll = 0
        click_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": first_row_rect.center})
        modal.handle_event(click_event)
        self.assertIn(self.player.properties[0], modal.offered_props)

if __name__ == "__main__":
    unittest.main()

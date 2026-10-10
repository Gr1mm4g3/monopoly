"""
Interactive dialog modals for Metro Tycoon.
Contains BuyPropertyModal, AuctionModal, CardModal, TradeModal, BuildModal, and MortgageModal.
"""

import os
import pygame
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_TEXT_WHITE, COLOR_TEXT_MUTED,
    COLOR_TEXT_GOLD, COLOR_TEXT_GREEN, COLOR_TEXT_RED, COLOR_TEXT_AMBER, COLOR_ACCENT_BLUE,
    COLOR_ACCENT_GREEN, COLOR_ACCENT_RED, COLOR_ACCENT_AMBER, DISTRICT_COLORS,
    GROUP_COUNTS, PLAYER_COLORS
)
from ui import Button, DeedCardView

class BuyPropertyModal:
    """Popup modal shown when landing on an unowned property."""
    def __init__(self, tile, player, font, title_font, on_buy, on_pass, on_auction=None):
        self.tile = tile
        self.player = player
        self.font = font
        self.title_font = title_font
        self.on_buy = on_buy
        self.on_pass = on_pass
        self.on_auction = on_auction
        
        # Geometry
        self.w = 360
        self.h = 475
        self.x = (SCREEN_WIDTH - self.w) // 2
        self.y = (SCREEN_HEIGHT - self.h) // 2
        self.rect = pygame.Rect(self.x, self.y, self.w, self.h)
        
        can_afford = player.cash >= tile.price
        
        # Primary Buy button
        buy_y = self.y + self.h - 96
        self.btn_buy = Button(
            (self.x + 25, buy_y, self.w - 50, 40),
            f"Buy (${tile.price})",
            font,
            bg_color=COLOR_ACCENT_GREEN,
            disabled=not can_afford,
            callback=on_buy
        )
        
        # Sub buttons: Auction & Pass
        sub_y = self.y + self.h - 48
        half_w = (self.w - 60) // 2
        auction_cb = on_auction if on_auction else on_pass
        self.btn_auction = Button(
            (self.x + 25, sub_y, half_w, 36),
            "Auction",
            font,
            bg_color=COLOR_ACCENT_AMBER,
            callback=auction_cb
        )
        self.btn_pass = Button(
            (self.x + 35 + half_w, sub_y, half_w, 36),
            "Pass",
            font,
            bg_color=(71, 85, 105),
            callback=on_pass
        )
        self.deed_view = DeedCardView(font, title_font)

    def handle_event(self, event):
        if self.btn_buy.handle_event(event):
            return True
        if self.btn_auction.handle_event(event):
            return True
        if self.btn_pass.handle_event(event):
            return True
        return False

    def draw(self, surface):
        # Dark overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        # Modal window
        pygame.draw.rect(surface, (24, 33, 53), self.rect, border_radius=12)
        pygame.draw.rect(surface, (51, 65, 85), self.rect, width=2, border_radius=12)

        # Title
        t_surf = self.title_font.render("PROPERTY AVAILABLE", True, COLOR_TEXT_GOLD)
        surface.blit(t_surf, t_surf.get_rect(center=(self.rect.centerx, self.y + 24)))

        # Mini deed card preview
        self.deed_view.draw(surface, self.tile, self.x + 50, self.y + 46, width=260, height=315)

        # Draw buttons
        self.btn_buy.draw(surface)
        self.btn_auction.draw(surface)
        self.btn_pass.draw(surface)


class AuctionModal:
    """
    Popup modal for auctioning unowned properties among all active players.
    All non-bankrupt players participate in turn-based round-robin bidding.
    Provides human quick-bid increments (+10, +25, +50, +100) and pass buttons,
    with AI autonomous decision-making and personality-driven valuations.
    """
    def __init__(self, tile, players, active_player, font, bold_font, title_font,
                 ai_engine, all_tiles, sound_fx, on_complete, fast_ai=False):
        self.tile = tile
        self.players = players
        self.active_player = active_player
        self.font = font
        self.bold_font = bold_font
        self.title_font = title_font
        self.ai_engine = ai_engine
        self.all_tiles = all_tiles
        self.sound_fx = sound_fx
        self.on_complete = on_complete
        self.fast_ai = fast_ai

        # Geometry
        self.w = 780
        self.h = 520
        self.x = (SCREEN_WIDTH - self.w) // 2
        self.y = (SCREEN_HEIGHT - self.h) // 2
        self.rect = pygame.Rect(self.x, self.y, self.w, self.h)

        # Active participants: non-bankrupt with at least $10
        self.eligible_bidders = [p for p in players if not p.is_bankrupt and p.cash >= 10]
        self.active_bidders = list(self.eligible_bidders)
        self.passed_bidders = set()
        for p in players:
            if p.is_bankrupt or p.cash < 10:
                self.passed_bidders.add(p.id)

        self.current_bid = 0
        self.high_bidder = None
        self.winner = None
        self.winning_bid = 0
        self.state = "BIDDING"  # "BIDDING" or "FINISHED"

        if active_player in self.active_bidders:
            self.bidder_idx = self.active_bidders.index(active_player)
        else:
            self.bidder_idx = 0

        self.recent_events = []
        self.ai_timer = 0
        self.auto_close_timer = 0
        self.all_ai = all(p.is_ai for p in players)

        # Left Column View
        self.deed_view = DeedCardView(font, title_font)

        # Right Column Controls
        rx = self.x + 295
        btn_y = self.y + 400

        # Human Quick Bid Buttons
        btn_w = 90
        btn_h = 36
        gap = 8
        self.btn_bid_10 = Button(
            (rx + 10, btn_y, btn_w, btn_h), "+ $10", font,
            bg_color=COLOR_ACCENT_BLUE,
            callback=lambda: self._handle_human_bid(10)
        )
        self.btn_bid_25 = Button(
            (rx + 10 + (btn_w + gap), btn_y, btn_w, btn_h), "+ $25", font,
            bg_color=COLOR_ACCENT_BLUE,
            callback=lambda: self._handle_human_bid(25)
        )
        self.btn_bid_50 = Button(
            (rx + 10 + 2 * (btn_w + gap), btn_y, btn_w, btn_h), "+ $50", font,
            bg_color=COLOR_ACCENT_BLUE,
            callback=lambda: self._handle_human_bid(50)
        )
        self.btn_bid_100 = Button(
            (rx + 10 + 3 * (btn_w + gap), btn_y, btn_w, btn_h), "+ $100", font,
            bg_color=COLOR_ACCENT_BLUE,
            callback=lambda: self._handle_human_bid(100)
        )
        self.btn_pass = Button(
            (rx + 10, btn_y + 46, 175, 38), "Pass / Withdraw", font,
            bg_color=(185, 28, 28),
            callback=self._handle_human_pass
        )

        # Continue Button (for Finished state)
        self.btn_continue = Button(
            (rx + 130, btn_y + 24, 200, 44), "Continue", bold_font,
            bg_color=COLOR_ACCENT_GREEN,
            callback=self.finish
        )

        if len(self.active_bidders) == 0:
            self._conclude_auction(None, 0)
        else:
            self._update_human_buttons()

    def _update_human_buttons(self):
        if self.state != "BIDDING" or len(self.active_bidders) == 0:
            return
        current = self.active_bidders[self.bidder_idx]
        if not current.is_ai:
            base = 10 if self.current_bid == 0 else self.current_bid
            self.btn_bid_10.text = "+ $10" if self.current_bid > 0 else "$10"
            self.btn_bid_25.text = "+ $25" if self.current_bid > 0 else "$25"
            self.btn_bid_50.text = "+ $50" if self.current_bid > 0 else "$50"
            self.btn_bid_100.text = "+ $100" if self.current_bid > 0 else "$100"

            self.btn_bid_10.disabled = (base + (10 if self.current_bid > 0 else 0) > current.cash)
            self.btn_bid_25.disabled = (base + (25 if self.current_bid > 0 else 15) > current.cash)
            self.btn_bid_50.disabled = (base + (50 if self.current_bid > 0 else 40) > current.cash)
            self.btn_bid_100.disabled = (base + (100 if self.current_bid > 0 else 90) > current.cash)
            self.btn_pass.disabled = False

    def _handle_human_bid(self, increment):
        if self.state != "BIDDING" or len(self.active_bidders) == 0:
            return
        current = self.active_bidders[self.bidder_idx]
        if current.is_ai:
            return
        amount = increment if self.current_bid == 0 else self.current_bid + increment
        if amount <= current.cash:
            self._apply_bid(current, amount)

    def _handle_human_pass(self):
        if self.state != "BIDDING" or len(self.active_bidders) == 0:
            return
        current = self.active_bidders[self.bidder_idx]
        if current.is_ai:
            return
        self._apply_pass(current)

    def _apply_bid(self, player, amount):
        self.current_bid = amount
        self.high_bidder = player
        self.sound_fx.play("gavel")
        self._add_event(f"{player.name} bid ${amount}!")

        # Advance to next active bidder
        if len(self.active_bidders) > 0:
            self.bidder_idx = (self.bidder_idx + 1) % len(self.active_bidders)

        self._check_auction_end()
        self._update_human_buttons()

    def _apply_pass(self, player):
        self.sound_fx.play("click")
        self._add_event(f"{player.name} passed / withdrew.")
        self.passed_bidders.add(player.id)

        if player in self.active_bidders:
            idx = self.active_bidders.index(player)
            self.active_bidders.remove(player)
            if len(self.active_bidders) > 0:
                self.bidder_idx = idx % len(self.active_bidders)
            else:
                self.bidder_idx = 0

        self._check_auction_end()
        self._update_human_buttons()

    def _check_auction_end(self):
        # If only 1 bidder remains and they placed a bid -> Winner!
        if len(self.active_bidders) == 1 and self.high_bidder is not None:
            self._conclude_auction(winner=self.high_bidder, winning_bid=self.current_bid)
        # If 0 bidders remain -> Finished!
        elif len(self.active_bidders) == 0:
            self._conclude_auction(winner=self.high_bidder, winning_bid=self.current_bid)

    def _conclude_auction(self, winner, winning_bid):
        self.state = "FINISHED"
        self.winner = winner
        self.winning_bid = winning_bid
        if winner:
            self.sound_fx.play("buy")
            self._add_event(f"Sold to {winner.name} for ${winning_bid}!")
        else:
            self._add_event("Unsold. No bids placed.")

    def _add_event(self, text):
        self.recent_events.append(text)
        if len(self.recent_events) > 5:
            self.recent_events.pop(0)

    def update(self):
        if self.state == "FINISHED":
            if self.all_ai:
                self.auto_close_timer += 1
                limit = 10 if self.fast_ai else 35
                if self.auto_close_timer >= limit:
                    self.finish()
            return

        self._check_auction_end()
        if self.state == "FINISHED":
            return

        # Process AI Turn
        if len(self.active_bidders) > 0:
            current = self.active_bidders[self.bidder_idx]
            if current.is_ai:
                self.ai_timer += 1
                limit = 6 if self.fast_ai else 25
                if self.ai_timer >= limit:
                    self.ai_timer = 0
                    self._process_ai_bid(current)

    def _process_ai_bid(self, ai_player):
        bid = self.ai_engine.evaluate_auction_bid(
            ai_player, self.tile, self.current_bid, self.all_tiles, self.players
        )
        if bid and bid > self.current_bid and bid <= ai_player.cash:
            self._apply_bid(ai_player, bid)
        else:
            self._apply_pass(ai_player)

    def handle_event(self, event):
        if self.state == "FINISHED":
            if self.btn_continue.handle_event(event):
                return True
            return False

        current = self.active_bidders[self.bidder_idx] if len(self.active_bidders) > 0 else None
        if current and not current.is_ai:
            if self.btn_bid_10.handle_event(event):
                return True
            if self.btn_bid_25.handle_event(event):
                return True
            if self.btn_bid_50.handle_event(event):
                return True
            if self.btn_bid_100.handle_event(event):
                return True
            if self.btn_pass.handle_event(event):
                return True
        return False

    def finish(self):
        if self.on_complete:
            self.on_complete(self.winner, self.winning_bid)

    def draw(self, surface):
        # Dark overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        # Modal window frame
        pygame.draw.rect(surface, (24, 33, 53), self.rect, border_radius=12)
        pygame.draw.rect(surface, (51, 65, 85), self.rect, width=2, border_radius=12)

        # Title bar
        t_surf = self.title_font.render("PROPERTY AUCTION", True, COLOR_TEXT_GOLD)
        surface.blit(t_surf, t_surf.get_rect(center=(self.rect.centerx, self.y + 24)))

        # Subtitle
        sub_str = f"Open Bidding for {self.tile.name}  |  List Price: ${self.tile.price}"
        sub_surf = self.font.render(sub_str, True, COLOR_TEXT_MUTED)
        surface.blit(sub_surf, sub_surf.get_rect(center=(self.rect.centerx, self.y + 46)))

        # 1. Left Column: Deed Card preview
        self.deed_view.draw(surface, self.tile, self.x + 24, self.y + 64, width=255, height=340)

        # Informational rules banner below deed
        info_rect = pygame.Rect(self.x + 24, self.y + 418, 255, 80)
        pygame.draw.rect(surface, (18, 25, 40), info_rect, border_radius=8)
        pygame.draw.rect(surface, (40, 53, 76), info_rect, width=1, border_radius=8)
        lbl_info1 = self.bold_font.render("AUCTION RULES", True, COLOR_TEXT_GOLD)
        lbl_info2 = self.font.render("Highest bidder pays Bank & wins deed.", True, COLOR_TEXT_WHITE)
        lbl_info3 = self.font.render("Passing withdraws you from bidding.", True, COLOR_TEXT_MUTED)
        surface.blit(lbl_info1, (info_rect.x + 10, info_rect.y + 8))
        surface.blit(lbl_info2, (info_rect.x + 10, info_rect.y + 30))
        surface.blit(lbl_info3, (info_rect.x + 10, info_rect.y + 50))

        # 2. Right Column
        rx = self.x + 295
        rw = self.w - 315

        # Current High Bid Box
        bid_box = pygame.Rect(rx, self.y + 64, rw, 85)
        pygame.draw.rect(surface, (30, 41, 59), bid_box, border_radius=8)
        pygame.draw.rect(surface, (51, 65, 85), bid_box, width=1, border_radius=8)

        lbl_high = self.font.render("CURRENT HIGH BID", True, COLOR_TEXT_MUTED)
        surface.blit(lbl_high, (bid_box.x + 16, bid_box.y + 12))

        val_str = f"${self.current_bid}" if self.current_bid > 0 else "$0 (No Bids)"
        val_surf = self.title_font.render(val_str, True, COLOR_TEXT_GOLD)
        surface.blit(val_surf, (bid_box.x + 16, bid_box.y + 34))

        if self.high_bidder:
            lead_tag = f"Leader: {self.high_bidder.name}"
            pygame.draw.circle(surface, self.high_bidder.color, (bid_box.right - 180, bid_box.centery), 7)
            lead_surf = self.bold_font.render(lead_tag, True, COLOR_TEXT_WHITE)
            surface.blit(lead_surf, (bid_box.right - 165, bid_box.centery - 8))
        else:
            no_bid_surf = self.font.render("Minimum Opening Bid: $10", True, COLOR_TEXT_AMBER)
            surface.blit(no_bid_surf, (bid_box.right - 190, bid_box.centery - 8))

        # Participants List Table
        part_box = pygame.Rect(rx, self.y + 158, rw, 172)
        pygame.draw.rect(surface, (20, 27, 45), part_box, border_radius=8)
        pygame.draw.rect(surface, (40, 53, 76), part_box, width=1, border_radius=8)

        hdr_p = self.bold_font.render(f"PARTICIPANTS ({len(self.active_bidders)} Active)", True, COLOR_TEXT_GOLD)
        surface.blit(hdr_p, (part_box.x + 12, part_box.y + 8))
        pygame.draw.line(surface, (40, 53, 76), (part_box.x + 8, part_box.y + 28), (part_box.right - 8, part_box.y + 28), 1)

        row_y = part_box.y + 34
        row_h = 22
        for p in self.players:
            pygame.draw.circle(surface, p.color, (part_box.x + 20, row_y + 10), 6)
            p_text = f"{p.name}  (${p.cash})"
            p_surf = self.font.render(p_text, True, COLOR_TEXT_WHITE)
            surface.blit(p_surf, (part_box.x + 34, row_y + 2))

            if self.high_bidder and p.id == self.high_bidder.id:
                badge_str = "LEADING"
                badge_col = COLOR_TEXT_GOLD
            elif self.state == "BIDDING" and len(self.active_bidders) > 0 and p.id == self.active_bidders[self.bidder_idx].id:
                badge_str = "YOUR TURN" if not p.is_ai else "BIDDING..."
                badge_col = COLOR_TEXT_GREEN
            elif p.id in self.passed_bidders:
                badge_str = "WITHDRAWN"
                badge_col = COLOR_TEXT_MUTED
            elif p.is_bankrupt:
                badge_str = "BANKRUPT"
                badge_col = COLOR_TEXT_RED
            else:
                badge_str = "IN AUCTION"
                badge_col = (96, 165, 250)

            badge_surf = self.bold_font.render(badge_str, True, badge_col)
            surface.blit(badge_surf, (part_box.right - 130, row_y + 2))

            row_y += row_h

        # Action / Controls Area
        ctrl_box = pygame.Rect(rx, self.y + 338, rw, 160)
        pygame.draw.rect(surface, (20, 27, 45), ctrl_box, border_radius=8)
        pygame.draw.rect(surface, (40, 53, 76), ctrl_box, width=1, border_radius=8)

        if self.state == "FINISHED":
            if self.winner:
                win_text = f"SOLD TO {self.winner.name.upper()} FOR ${self.winning_bid}!"
                win_col = COLOR_TEXT_GREEN
            else:
                win_text = "AUCTION CONCLUDED - NO BIDS PLACED (UNSOLD)"
                win_col = COLOR_TEXT_MUTED
            w_surf = self.bold_font.render(win_text, True, win_col)
            surface.blit(w_surf, w_surf.get_rect(center=(ctrl_box.centerx, ctrl_box.y + 30)))
            self.btn_continue.draw(surface)

        else:
            current = self.active_bidders[self.bidder_idx] if len(self.active_bidders) > 0 else None
            if current and not current.is_ai:
                prompt_surf = self.bold_font.render("YOUR TURN TO BID OR WITHDRAW:", True, COLOR_TEXT_GOLD)
                surface.blit(prompt_surf, (ctrl_box.x + 12, ctrl_box.y + 12))

                self.btn_bid_10.draw(surface)
                self.btn_bid_25.draw(surface)
                self.btn_bid_50.draw(surface)
                self.btn_bid_100.draw(surface)
                self.btn_pass.draw(surface)

                nxt_val = 10 if self.current_bid == 0 else self.current_bid + 10
                nxt_str = f"Min next bid: ${nxt_val}"
                nxt_surf = self.font.render(nxt_str, True, COLOR_TEXT_MUTED)
                surface.blit(nxt_surf, (ctrl_box.x + 200, self.btn_pass.rect.centery - 7))

            elif current:
                ai_prompt = f"Waiting for {current.name} to evaluate bid..."
                ai_surf = self.font.render(ai_prompt, True, COLOR_TEXT_MUTED)
                surface.blit(ai_surf, (ctrl_box.x + 16, ctrl_box.y + 25))

                bar_rect = pygame.Rect(ctrl_box.x + 16, ctrl_box.y + 60, rw - 32, 12)
                pygame.draw.rect(surface, (30, 41, 59), bar_rect, border_radius=6)
                limit = 6 if self.fast_ai else 25
                progress = min(1.0, self.ai_timer / max(1, limit))
                prog_w = int((rw - 32) * progress)
                if prog_w > 0:
                    prog_rect = pygame.Rect(bar_rect.x, bar_rect.y, prog_w, 12)
                    pygame.draw.rect(surface, COLOR_ACCENT_BLUE, prog_rect, border_radius=6)


class CardModal:
    """Popup modal shown when drawing a Fortune or City Chest card."""
    def __init__(self, card_result, is_fortune, font, title_font, on_dismiss):
        self.card_result = card_result
        self.is_fortune = is_fortune
        self.font = font
        self.title_font = title_font
        self.on_dismiss = on_dismiss

        self.w = 420
        self.h = 280
        self.x = (SCREEN_WIDTH - self.w) // 2
        self.y = (SCREEN_HEIGHT - self.h) // 2
        self.rect = pygame.Rect(self.x, self.y, self.w, self.h)

        self.btn_ok = Button(
            (self.rect.centerx - 70, self.y + self.h - 55, 140, 40),
            "Continue",
            font,
            bg_color=COLOR_ACCENT_BLUE,
            callback=on_dismiss
        )

    def handle_event(self, event):
        if self.btn_ok.handle_event(event):
            return True
        return False

    def draw(self, surface):
        # Dark overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        # Modal container
        pygame.draw.rect(surface, (24, 33, 53), self.rect, border_radius=12)
        border_col = (251, 146, 60) if self.is_fortune else (96, 165, 250)
        pygame.draw.rect(surface, border_col, self.rect, width=2, border_radius=12)

        # Header tag
        deck_tag = "FORTUNE CARD" if self.is_fortune else "CITY CHEST"
        h_surf = self.title_font.render(deck_tag, True, border_col)
        surface.blit(h_surf, h_surf.get_rect(center=(self.rect.centerx, self.y + 30)))

        # Card Title
        t_surf = self.title_font.render(self.card_result["title"], True, COLOR_TEXT_WHITE)
        surface.blit(t_surf, t_surf.get_rect(center=(self.rect.centerx, self.y + 70)))

        # Description wrapped
        desc = self.card_result["desc"]
        words = desc.split()
        lines = []
        cur_line = ""
        for w in words:
            if len(cur_line + " " + w) > 42:
                lines.append(cur_line)
                cur_line = w
            else:
                cur_line = (cur_line + " " + w).strip()
        if cur_line:
            lines.append(cur_line)

        cy = self.y + 115
        for line in lines:
            line_surf = self.font.render(line, True, COLOR_TEXT_MUTED)
            surface.blit(line_surf, line_surf.get_rect(center=(self.rect.centerx, cy)))
            cy += 24

        self.btn_ok.draw(surface)


class BuildModal:
    """Modal for managing house and skyscraper development with scrollable property list."""
    def __init__(self, player, tiles, font, title_font, on_close, on_build_callback, on_sell_callback):
        self.player = player
        self.tiles = tiles
        self.font = font
        self.title_font = title_font
        self.on_close = on_close
        self.on_build_callback = on_build_callback
        self.on_sell_callback = on_sell_callback

        self.w = 660
        self.h = 550
        self.x = (SCREEN_WIDTH - self.w) // 2
        self.y = (SCREEN_HEIGHT - self.h) // 2
        self.rect = pygame.Rect(self.x, self.y, self.w, self.h)

        self.btn_close = Button(
            (self.rect.centerx - 65, self.y + self.h - 48, 130, 36),
            "Done",
            font,
            bg_color=COLOR_ACCENT_BLUE,
            callback=on_close
        )

        # Scroll viewport geometry
        self.content_rect = pygame.Rect(self.x + 16, self.y + 75, self.w - 32, self.h - 135)
        self.row_height = 42
        self.scroll_y = 0
        self.is_dragging_scrollbar = False
        self.drag_start_y = 0
        self.drag_start_scroll = 0

        self._refresh_action_buttons()

    def _get_max_scroll(self):
        total_h = len(self.build_items) * self.row_height
        return max(0, total_h - self.content_rect.height)

    def _update_button_positions(self):
        max_scroll = self._get_max_scroll()
        self.scroll_y = max(0, min(self.scroll_y, max_scroll))
        for i, item in enumerate(self.build_items):
            row_y = self.content_rect.top + i * self.row_height - self.scroll_y
            item["row_y"] = row_y
            item["b_btn"].rect.x = self.content_rect.right - 185
            item["b_btn"].rect.y = row_y + 7
            item["s_btn"].rect.x = self.content_rect.right - 100
            item["s_btn"].rect.y = row_y + 7

    def _refresh_action_buttons(self):
        self.build_items = []
        for tid in self.player.properties:
            tile = self.tiles[tid]
            if tile.type == "PROPERTY" and self.player.owns_group(tile.group, self.tiles):
                can_build = self.player.can_build_on(tile, self.tiles) and (self.player.cash >= tile.house_cost)
                b_btn = Button(
                    (0, 0, 75, 28),
                    "+Build",
                    self.font,
                    bg_color=COLOR_ACCENT_GREEN if can_build else (51, 65, 85),
                    disabled=not can_build,
                    border_radius=4,
                    callback=lambda t=tile: self._handle_build(t)
                )
                can_sell = self.player.can_sell_building(tile, self.tiles)
                s_btn = Button(
                    (0, 0, 75, 28),
                    "-Sell",
                    self.font,
                    bg_color=COLOR_ACCENT_RED if can_sell else (51, 65, 85),
                    disabled=not can_sell,
                    border_radius=4,
                    callback=lambda t=tile: self._handle_sell(t)
                )
                self.build_items.append({
                    "tile": tile,
                    "b_btn": b_btn,
                    "s_btn": s_btn,
                    "row_y": 0
                })

        self._update_button_positions()

    def _handle_build(self, tile):
        self.on_build_callback(tile)
        self._refresh_action_buttons()

    def _handle_sell(self, tile):
        self.on_sell_callback(tile)
        self._refresh_action_buttons()

    def handle_event(self, event):
        if self.btn_close.handle_event(event):
            return True

        max_scroll = self._get_max_scroll()

        if event.type == pygame.MOUSEWHEEL:
            if self.rect.collidepoint(pygame.mouse.get_pos()):
                if max_scroll > 0:
                    self.scroll_y = max(0, min(max_scroll, self.scroll_y - event.y * 38))
                    self._update_button_positions()
                    return True

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4 and self.rect.collidepoint(event.pos):
                if max_scroll > 0:
                    self.scroll_y = max(0, self.scroll_y - 38)
                    self._update_button_positions()
                    return True
            elif event.button == 5 and self.rect.collidepoint(event.pos):
                if max_scroll > 0:
                    self.scroll_y = min(max_scroll, self.scroll_y + 38)
                    self._update_button_positions()
                    return True
            elif event.button == 1:
                # Scrollbar track click or drag
                if max_scroll > 0:
                    sb_x = self.content_rect.right - 12
                    sb_track = pygame.Rect(sb_x, self.content_rect.top, 10, self.content_rect.height)
                    thumb_h = max(32, int(self.content_rect.height * (self.content_rect.height / (len(self.build_items) * self.row_height))))
                    thumb_travel = self.content_rect.height - thumb_h
                    thumb_y = self.content_rect.top + int((self.scroll_y / max_scroll) * thumb_travel)
                    thumb_rect = pygame.Rect(sb_x - 1, thumb_y, 12, thumb_h)

                    if thumb_rect.collidepoint(event.pos):
                        self.is_dragging_scrollbar = True
                        self.drag_start_y = event.pos[1]
                        self.drag_start_scroll = self.scroll_y
                        return True
                    elif sb_track.collidepoint(event.pos):
                        if event.pos[1] < thumb_y:
                            self.scroll_y = max(0, self.scroll_y - self.content_rect.height)
                        else:
                            self.scroll_y = min(max_scroll, self.scroll_y + self.content_rect.height)
                        self._update_button_positions()
                        return True

                # Content item clicks
                if self.content_rect.collidepoint(event.pos):
                    for item in self.build_items:
                        if self.content_rect.top - self.row_height <= item["row_y"] <= self.content_rect.bottom:
                            if item["b_btn"].handle_event(event):
                                return True
                            if item["s_btn"].handle_event(event):
                                return True

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.is_dragging_scrollbar = False

        elif event.type == pygame.MOUSEMOTION:
            if self.is_dragging_scrollbar and max_scroll > 0:
                dy = event.pos[1] - self.drag_start_y
                thumb_h = max(32, int(self.content_rect.height * (self.content_rect.height / (len(self.build_items) * self.row_height))))
                thumb_travel = self.content_rect.height - thumb_h
                if thumb_travel > 0:
                    delta_scroll = (dy / thumb_travel) * max_scroll
                    self.scroll_y = max(0, min(max_scroll, self.drag_start_scroll + delta_scroll))
                    self._update_button_positions()
                return True

            if self.content_rect.collidepoint(event.pos):
                for item in self.build_items:
                    if self.content_rect.top - self.row_height <= item["row_y"] <= self.content_rect.bottom:
                        item["b_btn"].handle_event(event)
                        item["s_btn"].handle_event(event)
            else:
                for item in self.build_items:
                    item["b_btn"].is_hovered = False
                    item["s_btn"].is_hovered = False

        return False

    def draw(self, surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        # Modal Background
        pygame.draw.rect(surface, (24, 33, 53), self.rect, border_radius=12)
        pygame.draw.rect(surface, (51, 65, 85), self.rect, width=2, border_radius=12)

        # Header (Fixed)
        t_surf = self.title_font.render("PROPERTY DEVELOPMENT & EXPANSION", True, COLOR_TEXT_GOLD)
        surface.blit(t_surf, t_surf.get_rect(center=(self.rect.centerx, self.y + 24)))

        sub = self.font.render(f"Available Cash: ${self.player.cash:,}", True, COLOR_TEXT_GREEN)
        surface.blit(sub, (self.x + 30, self.y + 48))

        if not self.build_items:
            no_mono = self.font.render("You do not own any complete color monopolies yet.", True, COLOR_TEXT_MUTED)
            surface.blit(no_mono, no_mono.get_rect(center=(self.rect.centerx, self.rect.centery)))
        else:
            # Viewport background
            pygame.draw.rect(surface, (18, 25, 41), self.content_rect, border_radius=8)
            pygame.draw.rect(surface, (40, 53, 76), self.content_rect, width=1, border_radius=8)

            old_clip = surface.get_clip()
            surface.set_clip(self.content_rect)

            for item in self.build_items:
                row_y = item["row_y"]
                if row_y + self.row_height < self.content_rect.top or row_y > self.content_rect.bottom:
                    continue

                tile = item["tile"]
                row_rect = pygame.Rect(self.content_rect.left + 6, row_y + 2, self.content_rect.width - 24, self.row_height - 4)
                pygame.draw.rect(surface, (27, 38, 59), row_rect, border_radius=6)

                # District color circle
                col = DISTRICT_COLORS.get(tile.group, (71, 85, 105))
                pygame.draw.circle(surface, col, (self.content_rect.left + 22, row_y + 20), 7)

                # Property name
                n_surf = self.font.render(tile.name, True, COLOR_TEXT_WHITE)
                surface.blit(n_surf, (self.content_rect.left + 38, row_y + 11))

                # Development status
                dev_str = f"{tile.houses} Houses" if tile.houses < 5 else "Skyscraper"
                if tile.houses == 0:
                    dev_str = "No Buildings"
                d_surf = self.font.render(f"{dev_str} (${tile.house_cost}/h)", True, COLOR_TEXT_MUTED)
                surface.blit(d_surf, (self.content_rect.left + 230, row_y + 11))

                item["b_btn"].draw(surface)
                item["s_btn"].draw(surface)

            surface.set_clip(old_clip)

            # Scrollbar
            max_scroll = self._get_max_scroll()
            if max_scroll > 0:
                sb_x = self.content_rect.right - 10
                sb_track = pygame.Rect(sb_x, self.content_rect.top + 4, 6, self.content_rect.height - 8)
                pygame.draw.rect(surface, (30, 41, 59), sb_track, border_radius=3)

                thumb_h = max(32, int(self.content_rect.height * (self.content_rect.height / (len(self.build_items) * self.row_height))))
                thumb_travel = (self.content_rect.height - 8) - thumb_h
                thumb_y = self.content_rect.top + 4 + int((self.scroll_y / max_scroll) * thumb_travel)
                thumb_rect = pygame.Rect(sb_x - 1, thumb_y, 8, thumb_h)
                thumb_col = (148, 163, 184) if self.is_dragging_scrollbar else (100, 116, 139)
                pygame.draw.rect(surface, thumb_col, thumb_rect, border_radius=4)

        # Fixed Bottom Bar
        self.btn_close.draw(surface)


class MortgageModal:
    """Modal for managing mortgages (raise 50% cash, pay 55% to unmortgage) and debt liquidation with scrollable list."""
    def __init__(self, player, tiles, font, title_font, on_close, on_toggle_callback,
                 debt_amount=0, creditor=None, on_pay_debt=None, on_declare_bankruptcy=None,
                 on_sell_house=None):
        self.player = player
        self.tiles = tiles
        self.font = font
        self.title_font = title_font
        self.on_close = on_close
        self.on_toggle_callback = on_toggle_callback
        self.debt_amount = debt_amount
        self.creditor = creditor
        self.on_pay_debt = on_pay_debt
        self.on_declare_bankruptcy = on_declare_bankruptcy
        self.on_sell_house = on_sell_house

        self.w = 680
        self.h = 560
        self.x = (SCREEN_WIDTH - self.w) // 2
        self.y = (SCREEN_HEIGHT - self.h) // 2
        self.rect = pygame.Rect(self.x, self.y, self.w, self.h)

        # Viewport geometry
        top_offset = 80 if self.debt_amount > 0 else 75
        self.content_rect = pygame.Rect(self.x + 16, self.y + top_offset, self.w - 32, self.h - top_offset - 65)
        self.row_height = 42
        self.scroll_y = 0
        self.is_dragging_scrollbar = False
        self.drag_start_y = 0
        self.drag_start_scroll = 0

        self._refresh_buttons()

    def _get_max_scroll(self):
        total_h = len(self.prop_items) * self.row_height
        return max(0, total_h - self.content_rect.height)

    def _update_button_positions(self):
        max_scroll = self._get_max_scroll()
        self.scroll_y = max(0, min(self.scroll_y, max_scroll))
        for i, item in enumerate(self.prop_items):
            row_y = self.content_rect.top + i * self.row_height - self.scroll_y
            item["row_y"] = row_y
            item["btn"].rect.x = self.content_rect.right - 185
            item["btn"].rect.y = row_y + 7

    def _refresh_buttons(self):
        self.prop_items = []

        for tid in self.player.properties:
            tile = self.tiles[tid]
            has_buildings_in_group = False
            if tile.type == "PROPERTY":
                group_tiles = [t for t in self.tiles if getattr(t, 'group', None) == tile.group]
                has_buildings_in_group = any(t.houses > 0 for t in group_tiles)

            if getattr(tile, 'houses', 0) > 0:
                refund = tile.house_cost // 2
                btn = Button(
                    (0, 0, 165, 28),
                    f"Sell House (+${refund})",
                    self.font,
                    bg_color=(217, 119, 6),
                    border_radius=4,
                    callback=lambda t=tile: self._handle_sell_house(t)
                )
            elif tile.is_mortgaged:
                unmortgage_cost = int(tile.mortgage_value * 1.1)
                can_unmort = self.player.cash >= unmortgage_cost and (self.debt_amount == 0 or (self.player.cash - unmortgage_cost >= self.debt_amount))
                btn = Button(
                    (0, 0, 165, 28),
                    f"Unmortgage (${unmortgage_cost})",
                    self.font,
                    bg_color=COLOR_ACCENT_GREEN if can_unmort else (51, 65, 85),
                    disabled=not can_unmort,
                    border_radius=4,
                    callback=lambda t=tile: self._handle_toggle(t)
                )
            else:
                can_mort = not has_buildings_in_group
                btn = Button(
                    (0, 0, 165, 28),
                    f"Mortgage (+${tile.mortgage_value})",
                    self.font,
                    bg_color=COLOR_ACCENT_RED if can_mort else (51, 65, 85),
                    disabled=not can_mort,
                    border_radius=4,
                    callback=lambda t=tile: self._handle_toggle(t)
                )

            self.prop_items.append({"tile": tile, "btn": btn, "row_y": 0})

        # Bottom action buttons (Fixed)
        if self.debt_amount > 0:
            can_pay = self.player.cash >= self.debt_amount
            pay_label = f"Pay Debt (${self.debt_amount:,})" if can_pay else f"Need ${self.debt_amount - self.player.cash:,} More"
            self.btn_pay = Button(
                (self.rect.centerx - 190, self.y + self.h - 52, 180, 40),
                pay_label,
                self.font,
                bg_color=COLOR_ACCENT_GREEN if can_pay else (51, 65, 85),
                disabled=not can_pay,
                border_radius=6,
                callback=self.on_pay_debt
            )
            self.btn_bankrupt = Button(
                (self.rect.centerx + 10, self.y + self.h - 52, 180, 40),
                "Declare Bankruptcy",
                self.font,
                bg_color=COLOR_ACCENT_RED,
                border_radius=6,
                callback=self.on_declare_bankruptcy
            )
            self.btn_close = None
        else:
            self.btn_close = Button(
                (self.rect.centerx - 65, self.y + self.h - 50, 130, 38),
                "Done",
                self.font,
                bg_color=COLOR_ACCENT_BLUE,
                callback=self.on_close
            )
            self.btn_pay = None
            self.btn_bankrupt = None

        self._update_button_positions()

    def _handle_sell_house(self, tile):
        if self.on_sell_house:
            self.on_sell_house(tile)
        self._refresh_buttons()

    def _handle_toggle(self, tile):
        self.on_toggle_callback(tile)
        self._refresh_buttons()

    def handle_event(self, event):
        if self.debt_amount > 0:
            if self.btn_pay and self.btn_pay.handle_event(event):
                return True
            if self.btn_bankrupt and self.btn_bankrupt.handle_event(event):
                return True
        else:
            if self.btn_close and self.btn_close.handle_event(event):
                return True

        max_scroll = self._get_max_scroll()

        if event.type == pygame.MOUSEWHEEL:
            mpos = getattr(event, 'pos', None) or pygame.mouse.get_pos()
            is_dummy = (os.environ.get("SDL_VIDEODRIVER") == "dummy")
            if self.rect.collidepoint(mpos) or (is_dummy and mpos == (0, 0)):
                if max_scroll > 0:
                    self.scroll_y = max(0, min(max_scroll, self.scroll_y - event.y * 38))
                    self._update_button_positions()
                    return True

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4 and self.rect.collidepoint(event.pos):
                if max_scroll > 0:
                    self.scroll_y = max(0, self.scroll_y - 38)
                    self._update_button_positions()
                    return True
            elif event.button == 5 and self.rect.collidepoint(event.pos):
                if max_scroll > 0:
                    self.scroll_y = min(max_scroll, self.scroll_y + 38)
                    self._update_button_positions()
                    return True
            elif event.button == 1:
                # Scrollbar track click or drag
                if max_scroll > 0:
                    sb_x = self.content_rect.right - 12
                    sb_track = pygame.Rect(sb_x, self.content_rect.top, 10, self.content_rect.height)
                    thumb_h = max(32, int(self.content_rect.height * (self.content_rect.height / (len(self.prop_items) * self.row_height))))
                    thumb_travel = self.content_rect.height - thumb_h
                    thumb_y = self.content_rect.top + int((self.scroll_y / max_scroll) * thumb_travel)
                    thumb_rect = pygame.Rect(sb_x - 1, thumb_y, 12, thumb_h)

                    if thumb_rect.collidepoint(event.pos):
                        self.is_dragging_scrollbar = True
                        self.drag_start_y = event.pos[1]
                        self.drag_start_scroll = self.scroll_y
                        return True
                    elif sb_track.collidepoint(event.pos):
                        if event.pos[1] < thumb_y:
                            self.scroll_y = max(0, self.scroll_y - self.content_rect.height)
                        else:
                            self.scroll_y = min(max_scroll, self.scroll_y + self.content_rect.height)
                        self._update_button_positions()
                        return True

                # Content item button click
                if self.content_rect.collidepoint(event.pos):
                    for item in self.prop_items:
                        if self.content_rect.top - self.row_height <= item["row_y"] <= self.content_rect.bottom:
                            if item["btn"].handle_event(event):
                                return True

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.is_dragging_scrollbar = False

        elif event.type == pygame.MOUSEMOTION:
            if self.is_dragging_scrollbar and max_scroll > 0:
                dy = event.pos[1] - self.drag_start_y
                thumb_h = max(32, int(self.content_rect.height * (self.content_rect.height / (len(self.prop_items) * self.row_height))))
                thumb_travel = self.content_rect.height - thumb_h
                if thumb_travel > 0:
                    delta_scroll = (dy / thumb_travel) * max_scroll
                    self.scroll_y = max(0, min(max_scroll, self.drag_start_scroll + delta_scroll))
                    self._update_button_positions()
                return True

            if self.content_rect.collidepoint(event.pos):
                for item in self.prop_items:
                    if self.content_rect.top - self.row_height <= item["row_y"] <= self.content_rect.bottom:
                        item["btn"].handle_event(event)
            else:
                for item in self.prop_items:
                    item["btn"].is_hovered = False

        return False

    def draw(self, surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        # Modal Frame
        pygame.draw.rect(surface, (24, 33, 53), self.rect, border_radius=12)
        border_col = COLOR_TEXT_RED if self.debt_amount > 0 else (51, 65, 85)
        pygame.draw.rect(surface, border_col, self.rect, width=2, border_radius=12)

        # Header (Fixed)
        if self.debt_amount > 0:
            t_surf = self.title_font.render("DEBT SETTLEMENT & LIQUIDATION", True, COLOR_TEXT_RED)
            surface.blit(t_surf, t_surf.get_rect(center=(self.rect.centerx, self.y + 24)))

            creditor_str = f"to {self.creditor.name}" if self.creditor else "to the Bank"
            sub1 = self.font.render(f"Debt Owed: ${self.debt_amount:,} {creditor_str}", True, COLOR_TEXT_GOLD)
            surface.blit(sub1, (self.x + 30, self.y + 48))

            cash_col = COLOR_TEXT_GREEN if self.player.cash >= self.debt_amount else COLOR_TEXT_RED
            sub2 = self.font.render(f"Cash on Hand: ${self.player.cash:,}", True, cash_col)
            surface.blit(sub2, (self.x + self.w - 230, self.y + 48))
        else:
            t_surf = self.title_font.render("MORTGAGE MANAGEMENT", True, COLOR_TEXT_GOLD)
            surface.blit(t_surf, t_surf.get_rect(center=(self.rect.centerx, self.y + 26)))

            sub = self.font.render(f"Cash: ${self.player.cash:,}", True, COLOR_TEXT_GREEN)
            surface.blit(sub, (self.x + 30, self.y + 46))

            props_info = self.font.render(f"Properties Owned: {len(self.player.properties)}", True, COLOR_TEXT_MUTED)
            surface.blit(props_info, (self.x + self.w - 210, self.y + 46))

        if not self.prop_items:
            no_props = self.font.render("You do not own any properties.", True, COLOR_TEXT_MUTED)
            surface.blit(no_props, no_props.get_rect(center=(self.rect.centerx, self.rect.centery)))
        else:
            # Viewport background
            pygame.draw.rect(surface, (18, 25, 41), self.content_rect, border_radius=8)
            pygame.draw.rect(surface, (40, 53, 76), self.content_rect, width=1, border_radius=8)

            old_clip = surface.get_clip()
            surface.set_clip(self.content_rect)

            for item in self.prop_items:
                row_y = item["row_y"]
                if row_y + self.row_height < self.content_rect.top or row_y > self.content_rect.bottom:
                    continue

                tile = item["tile"]
                row_rect = pygame.Rect(self.content_rect.left + 6, row_y + 2, self.content_rect.width - 24, self.row_height - 4)
                pygame.draw.rect(surface, (27, 38, 59), row_rect, border_radius=6)

                # District color circle
                col = DISTRICT_COLORS.get(tile.group, (71, 85, 105))
                pygame.draw.circle(surface, col, (self.content_rect.left + 22, row_y + 20), 7)

                # Property name
                n_surf = self.font.render(tile.name, True, COLOR_TEXT_WHITE)
                surface.blit(n_surf, (self.content_rect.left + 38, row_y + 11))

                # Status
                if getattr(tile, 'houses', 0) > 0:
                    status_str = f"{tile.houses} Building{'s' if tile.houses > 1 else ''}"
                    status_col = (251, 191, 36)
                elif tile.is_mortgaged:
                    status_str = "[MORTGAGED]"
                    status_col = COLOR_TEXT_RED
                else:
                    status_str = "Active"
                    status_col = COLOR_TEXT_GREEN
                s_surf = self.font.render(status_str, True, status_col)
                surface.blit(s_surf, (self.content_rect.left + 240, row_y + 11))

                item["btn"].draw(surface)

            surface.set_clip(old_clip)

            # Scrollbar
            max_scroll = self._get_max_scroll()
            if max_scroll > 0:
                sb_x = self.content_rect.right - 10
                sb_track = pygame.Rect(sb_x, self.content_rect.top + 4, 6, self.content_rect.height - 8)
                pygame.draw.rect(surface, (30, 41, 59), sb_track, border_radius=3)

                thumb_h = max(32, int(self.content_rect.height * (self.content_rect.height / (len(self.prop_items) * self.row_height))))
                thumb_travel = (self.content_rect.height - 8) - thumb_h
                thumb_y = self.content_rect.top + 4 + int((self.scroll_y / max_scroll) * thumb_travel)
                thumb_rect = pygame.Rect(sb_x - 1, thumb_y, 8, thumb_h)
                thumb_col = (148, 163, 184) if self.is_dragging_scrollbar else (100, 116, 139)
                pygame.draw.rect(surface, thumb_col, thumb_rect, border_radius=4)

        # Bottom Bar (Fixed)
        if self.debt_amount > 0:
            if self.btn_pay:
                self.btn_pay.draw(surface)
            if self.btn_bankrupt:
                self.btn_bankrupt.draw(surface)
        else:
            if self.btn_close:
                self.btn_close.draw(surface)


class TradeModal:
    """Interactive trade proposal modal between human and opponent."""
    def __init__(self, human_player, all_players, tiles, font, title_font, ai_engine, on_close, on_complete):
        self.human = human_player
        self.opponents = [p for p in all_players if p.id != human_player.id and not p.is_bankrupt]
        self.selected_opp_idx = 0
        self.tiles = tiles
        self.font = font
        self.title_font = title_font
        self.ai_engine = ai_engine
        self.on_close = on_close
        self.on_complete = on_complete

        # Trade offerings
        self.offered_props = set()
        self.requested_props = set()
        self.offered_cash = 0
        self.requested_cash = 0
        self.feedback_msg = ""
        self.feedback_color = COLOR_TEXT_WHITE

        self.w = 680
        self.h = 520
        self.x = (SCREEN_WIDTH - self.w) // 2
        self.y = (SCREEN_HEIGHT - self.h) // 2
        self.rect = pygame.Rect(self.x, self.y, self.w, self.h)

        # Scroll viewports for offering and requesting
        self.human_list_rect = pygame.Rect(self.x + 30, self.y + 115, 290, 236)
        self.opp_list_rect = pygame.Rect(self.x + 360, self.y + 115, 290, 236)
        self.human_scroll = 0
        self.opp_scroll = 0

        # Buttons
        self.btn_next_opp = Button(
            (self.x + 440, self.y + 44, 110, 30), "Next Player", font,
            bg_color=COLOR_ACCENT_BLUE, callback=self._next_opp
        )
        self.btn_propose = Button(
            (self.x + 180, self.y + self.h - 55, 150, 40), "Propose Deal", font,
            bg_color=COLOR_ACCENT_GREEN, callback=self._propose_deal
        )
        self.btn_cancel = Button(
            (self.x + 360, self.y + self.h - 55, 120, 40), "Cancel", font,
            bg_color=(71, 85, 105), callback=on_close
        )

    def _get_human_max_scroll(self):
        total_h = len(self.human.properties) * 28
        return max(0, total_h - self.human_list_rect.height)

    def _get_opp_max_scroll(self):
        opp = self.get_current_opp()
        if not opp:
            return 0
        total_h = len(opp.properties) * 28
        return max(0, total_h - self.opp_list_rect.height)

    def _next_opp(self):
        if self.opponents:
            self.selected_opp_idx = (self.selected_opp_idx + 1) % len(self.opponents)
            self.requested_props.clear()
            self.requested_cash = 0
            self.feedback_msg = ""
            self.opp_scroll = 0

    def get_current_opp(self):
        if not self.opponents:
            return None
        return self.opponents[self.selected_opp_idx]

    def _propose_deal(self):
        opp = self.get_current_opp()
        if not opp:
            return
            
        if not self.offered_props and self.offered_cash <= 0 and not self.requested_props and self.requested_cash <= 0:
            self.feedback_msg = "Please select items to trade!"
            self.feedback_color = COLOR_TEXT_RED
            return

        accepted, reason = self.ai_engine.evaluate_trade(
            opp, list(self.offered_props), self.offered_cash,
            list(self.requested_props), self.requested_cash, self.tiles
        )

        if accepted:
            self.feedback_msg = f"{opp.name}: \"{reason}\""
            self.feedback_color = COLOR_TEXT_GREEN
            # Execute trade
            self.on_complete(opp, list(self.offered_props), self.offered_cash,
                             list(self.requested_props), self.requested_cash)
        else:
            self.feedback_msg = f"{opp.name}: \"{reason}\""
            self.feedback_color = COLOR_TEXT_RED

    def handle_event(self, event):
        if self.btn_next_opp.handle_event(event):
            return True
        if self.btn_propose.handle_event(event):
            return True
        if self.btn_cancel.handle_event(event):
            return True

        opp = self.get_current_opp()
        max_h_scroll = self._get_human_max_scroll()
        max_o_scroll = self._get_opp_max_scroll()

        if event.type == pygame.MOUSEWHEEL:
            mpos = getattr(event, 'pos', None) or pygame.mouse.get_pos()
            is_dummy = (os.environ.get("SDL_VIDEODRIVER") == "dummy")
            if (self.human_list_rect.collidepoint(mpos) or (is_dummy and mpos == (0, 0))) and max_h_scroll > 0:
                self.human_scroll = max(0, min(max_h_scroll, self.human_scroll - event.y * 28))
                return True
            elif (self.opp_list_rect.collidepoint(mpos) or (is_dummy and mpos == (0, 0))) and max_o_scroll > 0:
                self.opp_scroll = max(0, min(max_o_scroll, self.opp_scroll - event.y * 28))
                return True

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:
                if self.human_list_rect.collidepoint(event.pos) and max_h_scroll > 0:
                    self.human_scroll = max(0, self.human_scroll - 28)
                    return True
                elif self.opp_list_rect.collidepoint(event.pos) and max_o_scroll > 0:
                    self.opp_scroll = max(0, self.opp_scroll - 28)
                    return True
            elif event.button == 5:
                if self.human_list_rect.collidepoint(event.pos) and max_h_scroll > 0:
                    self.human_scroll = min(max_h_scroll, self.human_scroll + 28)
                    return True
                elif self.opp_list_rect.collidepoint(event.pos) and max_o_scroll > 0:
                    self.opp_scroll = min(max_o_scroll, self.opp_scroll + 28)
                    return True
            elif event.button == 1:
                mx, my = event.pos
                # Check offering clicks
                if self.human_list_rect.collidepoint(mx, my):
                    for i, tid in enumerate(self.human.properties):
                        row_y = self.human_list_rect.top + i * 28 - self.human_scroll
                        if self.human_list_rect.top - 28 <= row_y <= self.human_list_rect.bottom:
                            item_rect = pygame.Rect(self.human_list_rect.left, row_y, 276, 24)
                            if item_rect.collidepoint(mx, my):
                                if tid in self.offered_props:
                                    self.offered_props.remove(tid)
                                else:
                                    self.offered_props.add(tid)
                                return True

                # Check requested clicks
                if opp and self.opp_list_rect.collidepoint(mx, my):
                    for i, tid in enumerate(opp.properties):
                        row_y = self.opp_list_rect.top + i * 28 - self.opp_scroll
                        if self.opp_list_rect.top - 28 <= row_y <= self.opp_list_rect.bottom:
                            item_rect = pygame.Rect(self.opp_list_rect.left, row_y, 276, 24)
                            if item_rect.collidepoint(mx, my):
                                if tid in self.requested_props:
                                    self.requested_props.remove(tid)
                                else:
                                    self.requested_props.add(tid)
                                return True

                # Cash adjustment buttons
                # Offer +$50 / -$50
                if pygame.Rect(self.x + 190, self.y + 360, 40, 24).collidepoint(mx, my):
                    self.offered_cash = min(self.human.cash, self.offered_cash + 50)
                    return True
                if pygame.Rect(self.x + 235, self.y + 360, 40, 24).collidepoint(mx, my):
                    self.offered_cash = max(0, self.offered_cash - 50)
                    return True

                # Request +$50 / -$50
                if opp:
                    if pygame.Rect(self.x + 520, self.y + 360, 40, 24).collidepoint(mx, my):
                        self.requested_cash = min(opp.cash, self.requested_cash + 50)
                        return True
                    if pygame.Rect(self.x + 565, self.y + 360, 40, 24).collidepoint(mx, my):
                        self.requested_cash = max(0, self.requested_cash - 50)
                        return True

        return False

    def draw(self, surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        pygame.draw.rect(surface, (24, 33, 53), self.rect, border_radius=12)
        pygame.draw.rect(surface, (51, 65, 85), self.rect, width=2, border_radius=12)

        t_surf = self.title_font.render("TRADE & NEGOTIATION HUB", True, COLOR_TEXT_GOLD)
        surface.blit(t_surf, t_surf.get_rect(center=(self.rect.centerx, self.y + 24)))

        opp = self.get_current_opp()
        opp_name = opp.name if opp else "None"
        o_surf = self.font.render(f"Trading With: {opp_name}", True, COLOR_TEXT_WHITE)
        surface.blit(o_surf, (self.x + 360, self.y + 50))
        self.btn_next_opp.draw(surface)

        # Left Column: You Offer
        you_lbl = self.font.render("You Offer:", True, COLOR_TEXT_GREEN)
        surface.blit(you_lbl, (self.x + 30, self.y + 90))

        old_clip = surface.get_clip()
        surface.set_clip(self.human_list_rect)

        if not self.human.properties:
            empty_lbl = self.font.render("No properties owned", True, COLOR_TEXT_MUTED)
            surface.blit(empty_lbl, (self.human_list_rect.left + 8, self.human_list_rect.top + 8))
        else:
            for i, tid in enumerate(self.human.properties):
                row_y = self.human_list_rect.top + i * 28 - self.human_scroll
                if row_y + 28 < self.human_list_rect.top or row_y > self.human_list_rect.bottom:
                    continue
                t = self.tiles[tid]
                is_sel = tid in self.offered_props
                bg = (38, 54, 84) if is_sel else (30, 41, 59)
                r = pygame.Rect(self.human_list_rect.left, row_y, 276, 24)
                pygame.draw.rect(surface, bg, r, border_radius=4)
                if is_sel:
                    pygame.draw.rect(surface, COLOR_TEXT_GOLD, r, width=1, border_radius=4)
                
                col = DISTRICT_COLORS.get(t.group, (71, 85, 105))
                pygame.draw.circle(surface, col, (self.human_list_rect.left + 12, row_y + 12), 5)
                n_txt = self.font.render(f"{t.name} (${t.price})", True, COLOR_TEXT_WHITE)
                surface.blit(n_txt, (self.human_list_rect.left + 24, row_y + 3))

        surface.set_clip(old_clip)

        max_h_scroll = self._get_human_max_scroll()
        if max_h_scroll > 0:
            sb_x = self.human_list_rect.right - 6
            sb_track = pygame.Rect(sb_x, self.human_list_rect.top, 4, self.human_list_rect.height)
            pygame.draw.rect(surface, (30, 41, 59), sb_track, border_radius=2)
            thumb_h = max(24, int(self.human_list_rect.height * (self.human_list_rect.height / (len(self.human.properties) * 28))))
            thumb_travel = self.human_list_rect.height - thumb_h
            thumb_y = self.human_list_rect.top + int((self.human_scroll / max_h_scroll) * thumb_travel)
            pygame.draw.rect(surface, (100, 116, 139), pygame.Rect(sb_x - 1, thumb_y, 6, thumb_h), border_radius=3)

        # Cash offer controls
        c_offer_lbl = self.font.render(f"Cash Offer: ${self.offered_cash}", True, COLOR_TEXT_GREEN)
        surface.blit(c_offer_lbl, (self.x + 30, self.y + 364))
        # [+] and [-] buttons
        pygame.draw.rect(surface, (51, 65, 85), (self.x + 190, self.y + 360, 40, 24), border_radius=4)
        p_surf = self.font.render("+$50", True, COLOR_TEXT_WHITE)
        surface.blit(p_surf, p_surf.get_rect(center=(self.x + 210, self.y + 372)))

        pygame.draw.rect(surface, (51, 65, 85), (self.x + 235, self.y + 360, 40, 24), border_radius=4)
        m_surf = self.font.render("-$50", True, COLOR_TEXT_WHITE)
        surface.blit(m_surf, m_surf.get_rect(center=(self.x + 255, self.y + 372)))

        # Right Column: You Request
        req_lbl = self.font.render(f"You Request from {opp_name}:", True, COLOR_TEXT_GOLD)
        surface.blit(req_lbl, (self.x + 360, self.y + 90))

        if opp:
            surface.set_clip(self.opp_list_rect)
            if not opp.properties:
                empty_lbl = self.font.render("No properties owned", True, COLOR_TEXT_MUTED)
                surface.blit(empty_lbl, (self.opp_list_rect.left + 8, self.opp_list_rect.top + 8))
            else:
                for i, tid in enumerate(opp.properties):
                    row_y = self.opp_list_rect.top + i * 28 - self.opp_scroll
                    if row_y + 28 < self.opp_list_rect.top or row_y > self.opp_list_rect.bottom:
                        continue
                    t = self.tiles[tid]
                    is_sel = tid in self.requested_props
                    bg = (38, 54, 84) if is_sel else (30, 41, 59)
                    r = pygame.Rect(self.opp_list_rect.left, row_y, 276, 24)
                    pygame.draw.rect(surface, bg, r, border_radius=4)
                    if is_sel:
                        pygame.draw.rect(surface, COLOR_TEXT_GOLD, r, width=1, border_radius=4)
                    
                    col = DISTRICT_COLORS.get(t.group, (71, 85, 105))
                    pygame.draw.circle(surface, col, (self.opp_list_rect.left + 12, row_y + 12), 5)
                    n_txt = self.font.render(f"{t.name} (${t.price})", True, COLOR_TEXT_WHITE)
                    surface.blit(n_txt, (self.opp_list_rect.left + 24, row_y + 3))

            surface.set_clip(old_clip)

            max_o_scroll = self._get_opp_max_scroll()
            if max_o_scroll > 0:
                sb_x = self.opp_list_rect.right - 6
                sb_track = pygame.Rect(sb_x, self.opp_list_rect.top, 4, self.opp_list_rect.height)
                pygame.draw.rect(surface, (30, 41, 59), sb_track, border_radius=2)
                thumb_h = max(24, int(self.opp_list_rect.height * (self.opp_list_rect.height / (len(opp.properties) * 28))))
                thumb_travel = self.opp_list_rect.height - thumb_h
                thumb_y = self.opp_list_rect.top + int((self.opp_scroll / max_o_scroll) * thumb_travel)
                pygame.draw.rect(surface, (100, 116, 139), pygame.Rect(sb_x - 1, thumb_y, 6, thumb_h), border_radius=3)

            c_req_lbl = self.font.render(f"Cash Request: ${self.requested_cash}", True, COLOR_TEXT_GOLD)
            surface.blit(c_req_lbl, (self.x + 360, self.y + 364))
            
            pygame.draw.rect(surface, (51, 65, 85), (self.x + 520, self.y + 360, 40, 24), border_radius=4)
            p2 = self.font.render("+$50", True, COLOR_TEXT_WHITE)
            surface.blit(p2, p2.get_rect(center=(self.x + 540, self.y + 372)))

            pygame.draw.rect(surface, (51, 65, 85), (self.x + 565, self.y + 360, 40, 24), border_radius=4)
            m2 = self.font.render("-$50", True, COLOR_TEXT_WHITE)
            surface.blit(m2, m2.get_rect(center=(self.x + 585, self.y + 372)))

        # Feedback message
        if self.feedback_msg:
            f_surf = self.font.render(self.feedback_msg, True, self.feedback_color)
            surface.blit(f_surf, f_surf.get_rect(center=(self.rect.centerx, self.y + 416)))

        self.btn_propose.draw(surface)
        self.btn_cancel.draw(surface)

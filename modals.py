"""
Interactive dialog modals for Metro Tycoon.
Contains BuyPropertyModal, CardModal, TradeModal, BuildModal, and MortgageModal.
"""

import pygame
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_TEXT_WHITE, COLOR_TEXT_MUTED,
    COLOR_TEXT_GOLD, COLOR_TEXT_GREEN, COLOR_TEXT_RED, COLOR_ACCENT_BLUE,
    COLOR_ACCENT_GREEN, COLOR_ACCENT_RED, DISTRICT_COLORS, GROUP_COUNTS
)
from ui import Button, DeedCardView

class BuyPropertyModal:
    """Popup modal shown when landing on an unowned property."""
    def __init__(self, tile, player, font, title_font, on_buy, on_pass):
        self.tile = tile
        self.player = player
        self.font = font
        self.title_font = title_font
        self.on_buy = on_buy
        self.on_pass = on_pass
        
        # Geometry
        self.w = 340
        self.h = 450
        self.x = (SCREEN_WIDTH - self.w) // 2
        self.y = (SCREEN_HEIGHT - self.h) // 2
        self.rect = pygame.Rect(self.x, self.y, self.w, self.h)
        
        can_afford = player.cash >= tile.price
        btn_y = self.y + self.h - 60
        self.btn_buy = Button(
            (self.x + 20, btn_y, 140, 44),
            f"Buy (${tile.price})",
            font,
            bg_color=COLOR_ACCENT_GREEN,
            disabled=not can_afford,
            callback=on_buy
        )
        self.btn_pass = Button(
            (self.x + 180, btn_y, 140, 44),
            "Pass",
            font,
            bg_color=(71, 85, 105),
            callback=on_pass
        )
        self.deed_view = DeedCardView(font, title_font)

    def handle_event(self, event):
        if self.btn_buy.handle_event(event):
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
        self.deed_view.draw(surface, self.tile, self.x + 40, self.y + 48, width=260, height=324)

        # Draw buttons
        self.btn_buy.draw(surface)
        self.btn_pass.draw(surface)


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
    """Modal for managing house and skyscraper development."""
    def __init__(self, player, tiles, font, title_font, on_close, on_build_callback, on_sell_callback):
        self.player = player
        self.tiles = tiles
        self.font = font
        self.title_font = title_font
        self.on_close = on_close
        self.on_build_callback = on_build_callback
        self.on_sell_callback = on_sell_callback

        self.w = 580
        self.h = 480
        self.x = (SCREEN_WIDTH - self.w) // 2
        self.y = (SCREEN_HEIGHT - self.h) // 2
        self.rect = pygame.Rect(self.x, self.y, self.w, self.h)

        self.btn_close = Button(
            (self.rect.centerx - 60, self.y + self.h - 50, 120, 38),
            "Done",
            font,
            bg_color=COLOR_ACCENT_BLUE,
            callback=on_close
        )
        self._refresh_action_buttons()

    def _refresh_action_buttons(self):
        self.build_buttons = []
        # Find eligible properties
        cy = self.y + 70
        for tid in self.player.properties:
            tile = self.tiles[tid]
            if tile.type == "PROPERTY" and self.player.owns_group(tile.group, self.tiles):
                # Build button
                can_build = self.player.can_build_on(tile, self.tiles) and (self.player.cash >= tile.house_cost)
                b_btn = Button(
                    (self.x + 380, cy, 75, 28),
                    f"+Build",
                    self.font,
                    bg_color=COLOR_ACCENT_GREEN if can_afford(tile, self.player) else (51, 65, 85),
                    disabled=not can_build,
                    border_radius=4,
                    callback=lambda t=tile: self._handle_build(t)
                )
                # Sell button
                can_sell = self.player.can_sell_building(tile, self.tiles)
                s_btn = Button(
                    (self.x + 465, cy, 75, 28),
                    f"-Sell",
                    self.font,
                    bg_color=COLOR_ACCENT_RED if can_sell else (51, 65, 85),
                    disabled=not can_sell,
                    border_radius=4,
                    callback=lambda t=tile: self._handle_sell(t)
                )
                self.build_buttons.append((tile, b_btn, s_btn, cy))
                cy += 38

    def _handle_build(self, tile):
        self.on_build_callback(tile)
        self._refresh_action_buttons()

    def _handle_sell(self, tile):
        self.on_sell_callback(tile)
        self._refresh_action_buttons()

    def handle_event(self, event):
        if self.btn_close.handle_event(event):
            return True
        for tile, b_btn, s_btn, cy in self.build_buttons:
            if b_btn.handle_event(event):
                return True
            if s_btn.handle_event(event):
                return True
        return False

    def draw(self, surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        pygame.draw.rect(surface, (24, 33, 53), self.rect, border_radius=12)
        pygame.draw.rect(surface, (51, 65, 85), self.rect, width=2, border_radius=12)

        # Header
        t_surf = self.title_font.render("PROPERTY DEVELOPMENT & EXPANSION", True, COLOR_TEXT_GOLD)
        surface.blit(t_surf, t_surf.get_rect(center=(self.rect.centerx, self.y + 26)))

        sub = self.font.render(f"Available Cash: ${self.player.cash:,}", True, COLOR_TEXT_GREEN)
        surface.blit(sub, (self.x + 30, self.y + 46))

        if not self.build_buttons:
            no_mono = self.font.render("You do not own any complete color monopolies yet.", True, COLOR_TEXT_MUTED)
            surface.blit(no_mono, no_mono.get_rect(center=(self.rect.centerx, self.rect.centery)))
        else:
            for tile, b_btn, s_btn, cy in self.build_buttons:
                # District color pill
                col = DISTRICT_COLORS.get(tile.group, (71, 85, 105))
                pygame.draw.circle(surface, col, (self.x + 38, cy + 14), 7)
                
                # Property name
                n_surf = self.font.render(tile.name, True, COLOR_TEXT_WHITE)
                surface.blit(n_surf, (self.x + 55, cy + 4))

                # Development status
                dev_str = f"{tile.houses} Houses" if tile.houses < 5 else "Skyscraper"
                if tile.houses == 0:
                    dev_str = "No Buildings"
                d_surf = self.font.render(f"{dev_str} (${tile.house_cost}/h)", True, COLOR_TEXT_MUTED)
                surface.blit(d_surf, (self.x + 220, cy + 4))

                b_btn.draw(surface)
                s_btn.draw(surface)

        self.btn_close.draw(surface)


def can_afford(tile, player):
    return player.cash >= tile.house_cost


class MortgageModal:
    """Modal for managing mortgages (raise 50% cash, pay 55% to unmortgage) and debt liquidation."""
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

        self.w = 640 if debt_amount > 0 else 580
        self.h = 520 if debt_amount > 0 else 480
        self.x = (SCREEN_WIDTH - self.w) // 2
        self.y = (SCREEN_HEIGHT - self.h) // 2
        self.rect = pygame.Rect(self.x, self.y, self.w, self.h)

        self._refresh_buttons()

    def _refresh_buttons(self):
        self.prop_buttons = []
        cy = self.y + (80 if self.debt_amount > 0 else 70)

        for tid in self.player.properties:
            tile = self.tiles[tid]
            # Cannot mortgage if any houses on properties in this color group
            has_buildings_in_group = False
            if tile.type == "PROPERTY":
                group_tiles = [t for t in self.tiles if getattr(t, 'group', None) == tile.group]
                has_buildings_in_group = any(t.houses > 0 for t in group_tiles)

            btn_x = self.x + self.w - 175
            if getattr(tile, 'houses', 0) > 0:
                refund = tile.house_cost // 2
                btn = Button(
                    (btn_x, cy, 155, 28),
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
                    (btn_x, cy, 155, 28),
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
                    (btn_x, cy, 155, 28),
                    f"Mortgage (+${tile.mortgage_value})",
                    self.font,
                    bg_color=COLOR_ACCENT_RED if can_mort else (51, 65, 85),
                    disabled=not can_mort,
                    border_radius=4,
                    callback=lambda t=tile: self._handle_toggle(t)
                )

            self.prop_buttons.append((tile, btn, cy))
            cy += 36

        # Bottom action buttons
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
                (self.rect.centerx - 60, self.y + self.h - 50, 120, 38),
                "Done",
                self.font,
                bg_color=COLOR_ACCENT_BLUE,
                callback=self.on_close
            )
            self.btn_pay = None
            self.btn_bankrupt = None

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

        for tile, btn, cy in self.prop_buttons:
            if btn.handle_event(event):
                return True
        return False

    def draw(self, surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        pygame.draw.rect(surface, (24, 33, 53), self.rect, border_radius=12)
        border_col = COLOR_TEXT_RED if self.debt_amount > 0 else (51, 65, 85)
        pygame.draw.rect(surface, border_col, self.rect, width=2, border_radius=12)

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

        if not self.prop_buttons:
            no_props = self.font.render("You do not own any properties.", True, COLOR_TEXT_MUTED)
            surface.blit(no_props, no_props.get_rect(center=(self.rect.centerx, self.rect.centery)))
        else:
            for tile, btn, cy in self.prop_buttons:
                col = DISTRICT_COLORS.get(tile.group, (71, 85, 105))
                pygame.draw.circle(surface, col, (self.x + 38, cy + 14), 7)

                n_surf = self.font.render(tile.name, True, COLOR_TEXT_WHITE)
                surface.blit(n_surf, (self.x + 55, cy + 4))

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
                surface.blit(s_surf, (self.x + 230, cy + 4))

                btn.draw(surface)

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

    def _next_opp(self):
        if self.opponents:
            self.selected_opp_idx = (self.selected_opp_idx + 1) % len(self.opponents)
            self.requested_props.clear()
            self.requested_cash = 0
            self.feedback_msg = ""

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

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            # Check offering clicks
            cy = self.y + 130
            for tid in self.human.properties:
                item_rect = pygame.Rect(self.x + 30, cy, 280, 24)
                if item_rect.collidepoint(mx, my):
                    if tid in self.offered_props:
                        self.offered_props.remove(tid)
                    else:
                        self.offered_props.add(tid)
                    return True
                cy += 28

            # Check requested clicks
            opp = self.get_current_opp()
            if opp:
                cy = self.y + 130
                for tid in opp.properties:
                    item_rect = pygame.Rect(self.x + 360, cy, 280, 24)
                    if item_rect.collidepoint(mx, my):
                        if tid in self.requested_props:
                            self.requested_props.remove(tid)
                        else:
                            self.requested_props.add(tid)
                        return True
                    cy += 28

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

        cy = self.y + 120
        for tid in self.human.properties[:7]: # Show up to 7
            t = self.tiles[tid]
            is_sel = tid in self.offered_props
            bg = (38, 54, 84) if is_sel else (30, 41, 59)
            r = pygame.Rect(self.x + 30, cy, 280, 24)
            pygame.draw.rect(surface, bg, r, border_radius=4)
            if is_sel:
                pygame.draw.rect(surface, COLOR_TEXT_GOLD, r, width=1, border_radius=4)
            
            col = DISTRICT_COLORS.get(t.group, (71, 85, 105))
            pygame.draw.circle(surface, col, (self.x + 42, cy + 12), 5)
            n_txt = self.font.render(f"{t.name} (${t.price})", True, COLOR_TEXT_WHITE)
            surface.blit(n_txt, (self.x + 55, cy + 3))
            cy += 28

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
            cy = self.y + 120
            for tid in opp.properties[:7]:
                t = self.tiles[tid]
                is_sel = tid in self.requested_props
                bg = (38, 54, 84) if is_sel else (30, 41, 59)
                r = pygame.Rect(self.x + 360, cy, 280, 24)
                pygame.draw.rect(surface, bg, r, border_radius=4)
                if is_sel:
                    pygame.draw.rect(surface, COLOR_TEXT_GOLD, r, width=1, border_radius=4)
                
                col = DISTRICT_COLORS.get(t.group, (71, 85, 105))
                pygame.draw.circle(surface, col, (self.x + 372, cy + 12), 5)
                n_txt = self.font.render(f"{t.name} (${t.price})", True, COLOR_TEXT_WHITE)
                surface.blit(n_txt, (self.x + 385, cy + 3))
                cy += 28

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

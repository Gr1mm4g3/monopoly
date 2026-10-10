"""
UI components, modals, HUD elements and event log for Metro Tycoon.
Provides interactive Buttons, Player Cards, Log Views, Modals, and Deed Cards.
"""

import pygame
from constants import (
    COLOR_BG, COLOR_PANEL_BG, COLOR_CARD_BG, COLOR_TEXT_WHITE, COLOR_TEXT_MUTED,
    COLOR_TEXT_GOLD, COLOR_TEXT_GREEN, COLOR_TEXT_RED, COLOR_ACCENT_BLUE,
    COLOR_ACCENT_GREEN, COLOR_ACCENT_RED, COLOR_TILE_BORDER, DISTRICT_COLORS,
    GROUP_COUNTS
)

class Button:
    def __init__(self, rect, text, font, bg_color=COLOR_ACCENT_BLUE, text_color=COLOR_TEXT_WHITE,
                 hover_color=None, disabled=False, border_radius=6, callback=None):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.bg_color = bg_color
        self.text_color = text_color
        self.hover_color = hover_color or tuple(min(255, c + 25) for c in bg_color)
        self.disabled = disabled
        self.border_radius = border_radius
        self.callback = callback
        self.is_hovered = False

    def handle_event(self, event):
        if self.disabled:
            return False
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.callback:
                    self.callback()
                return True
        return False

    def draw(self, surface):
        if self.disabled:
            col = (51, 65, 85)
            txt_col = (100, 116, 139)
        elif self.is_hovered:
            col = self.hover_color
            txt_col = self.text_color
        else:
            col = self.bg_color
            txt_col = self.text_color

        pygame.draw.rect(surface, col, self.rect, border_radius=self.border_radius)
        # Subtle top highlight
        if not self.disabled:
            pygame.draw.rect(surface, (255, 255, 255, 40), self.rect, width=1, border_radius=self.border_radius)

        txt_surf = self.font.render(self.text, True, txt_col)
        surface.blit(txt_surf, txt_surf.get_rect(center=self.rect.center))


class EventLog:
    def __init__(self, rect, font):
        self.rect = pygame.Rect(rect)
        self.font = font
        self.messages = []
        self.scroll_offset = 0
        self.line_height = 20

    def add(self, text, color=COLOR_TEXT_WHITE):
        self.messages.append((text, color))
        # Keep log bounded to last 150 items
        if len(self.messages) > 150:
            self.messages.pop(0)
        # Auto-scroll to bottom
        max_visible = self.rect.height // self.line_height
        if len(self.messages) > max_visible:
            self.scroll_offset = len(self.messages) - max_visible

    def handle_event(self, event):
        if event.type == pygame.MOUSEWHEEL and self.rect.collidepoint(pygame.mouse.get_pos()):
            self.scroll_offset = max(0, min(len(self.messages) - 1, self.scroll_offset - event.y))

    def draw(self, surface):
        # Background box
        pygame.draw.rect(surface, (20, 27, 45), self.rect, border_radius=8)
        pygame.draw.rect(surface, (40, 53, 76), self.rect, width=1, border_radius=8)

        # Header title
        header_surf = self.font.render("GAME LOG", True, COLOR_TEXT_GOLD)
        surface.blit(header_surf, (self.rect.x + 10, self.rect.y + 6))
        pygame.draw.line(surface, (40, 53, 76), (self.rect.x + 8, self.rect.y + 26), (self.rect.right - 8, self.rect.y + 26), 1)

        # Draw messages
        content_y = self.rect.y + 32
        max_visible = (self.rect.height - 38) // self.line_height
        visible_msgs = self.messages[self.scroll_offset: self.scroll_offset + max_visible]

        for i, (msg, col) in enumerate(visible_msgs):
            y = content_y + i * self.line_height
            # Truncate if too long to fit cleanly
            rendered = self.font.render(msg, True, col)
            surface.blit(rendered, (self.rect.x + 10, y))


class PlayerPanel:
    def __init__(self, rect, font, small_font):
        self.rect = pygame.Rect(rect)
        self.font = font
        self.small_font = small_font

    def draw(self, surface, players, current_player_idx):
        """Draws player cards for all 2 to 6 players."""
        pygame.draw.rect(surface, COLOR_PANEL_BG, self.rect, border_radius=10)
        pygame.draw.rect(surface, (40, 53, 76), self.rect, width=1, border_radius=10)

        num_players = len(players)
        card_spacing = 6
        avail_height = self.rect.height - 16
        card_h = (avail_height - (num_players - 1) * card_spacing) // num_players
        card_w = self.rect.width - 16

        for i, p in enumerate(players):
            card_y = self.rect.y + 8 + i * (card_h + card_spacing)
            c_rect = pygame.Rect(self.rect.x + 8, card_y, card_w, card_h)
            
            is_active = (i == current_player_idx)
            
            # Card background
            if p.is_bankrupt:
                bg = (24, 28, 38)
            elif is_active:
                bg = (38, 54, 84)
            else:
                bg = COLOR_CARD_BG
                
            pygame.draw.rect(surface, bg, c_rect, border_radius=8)
            
            # Active glowing border
            if is_active and not p.is_bankrupt:
                pygame.draw.rect(surface, COLOR_TEXT_GOLD, c_rect, width=2, border_radius=8)
            else:
                pygame.draw.rect(surface, (51, 65, 85), c_rect, width=1, border_radius=8)

            # Player Token icon circle
            token_cx = c_rect.x + 22
            token_cy = c_rect.centery
            p.draw_token(surface, token_cx, token_cy, radius=12)
            if p.is_bankrupt:
                pygame.draw.line(surface, COLOR_ACCENT_RED, (token_cx - 9, token_cy - 9), (token_cx + 9, token_cy + 9), 3)
                pygame.draw.line(surface, COLOR_ACCENT_RED, (token_cx - 9, token_cy + 9), (token_cx + 9, token_cy - 9), 3)


            # Name and status tags
            name_str = f"{p.name} (You)" if (not p.is_ai and i == 0) else p.name
            name_col = COLOR_TEXT_WHITE if not p.is_bankrupt else (100, 116, 139)
            n_surf = self.font.render(name_str, True, name_col)
            surface.blit(n_surf, (c_rect.x + 42, c_rect.y + 6))

            # AI personality / Subtag
            sub_tag = "Human" if not p.is_ai else f"AI ({p.ai_personality})"
            tag_surf = self.small_font.render(sub_tag, True, COLOR_TEXT_MUTED)
            surface.blit(tag_surf, (c_rect.x + 42, c_rect.y + 24))

            # Cash & Properties badge
            if p.is_bankrupt:
                bankrupt_surf = self.font.render("BANKRUPT", True, COLOR_ACCENT_RED)
                surface.blit(bankrupt_surf, (c_rect.right - 100, c_rect.centery - 8))
            else:
                cash_surf = self.font.render(f"${p.cash:,}", True, COLOR_TEXT_GREEN)
                surface.blit(cash_surf, (c_rect.right - 110, c_rect.y + 6))
                
                # Badges: properties count, jail status
                prop_info = f"Props: {len(p.properties)}"
                if p.in_jail:
                    prop_info += " [JAIL]"
                p_surf = self.small_font.render(prop_info, True, COLOR_TEXT_MUTED)
                surface.blit(p_surf, (c_rect.right - 110, c_rect.y + 24))


class DiceWidget:
    def __init__(self, rect, font):
        self.rect = pygame.Rect(rect)
        self.font = font
        self.die1 = 1
        self.die2 = 1
        self.rolling = False
        self.roll_frame = 0

    def set_values(self, d1, d2):
        self.die1 = d1
        self.die2 = d2

    def draw(self, surface):
        """Draws two stylized 3D dice with dots."""
        # Dice dimensions
        d_size = 46
        gap = 14
        total_w = d_size * 2 + gap
        start_x = self.rect.centerx - total_w // 2
        d_y = self.rect.centery - d_size // 2

        # Draw Die 1
        r1 = pygame.Rect(start_x, d_y, d_size, d_size)
        self._draw_die(surface, r1, self.die1)

        # Draw Die 2
        r2 = pygame.Rect(start_x + d_size + gap, d_y, d_size, d_size)
        self._draw_die(surface, r2, self.die2)

        # Total text
        total_str = f"Total: {self.die1 + self.die2}"
        if self.die1 == self.die2 and not self.rolling:
            total_str += " (DOUBLES!)"
        t_surf = self.font.render(total_str, True, COLOR_TEXT_GOLD)
        surface.blit(t_surf, t_surf.get_rect(center=(self.rect.centerx, self.rect.bottom - 10)))

    def _draw_die(self, surface, rect, val):
        # Die shadow & 3D body
        shadow_rect = rect.move(2, 3)
        pygame.draw.rect(surface, (10, 15, 26), shadow_rect, border_radius=8)
        pygame.draw.rect(surface, (241, 245, 249), rect, border_radius=8)
        pygame.draw.rect(surface, (203, 213, 225), rect, width=2, border_radius=8)

        # Dot coordinates
        cx, cy = rect.centerx, rect.centery
        d = 10
        dot_positions = {
            1: [(cx, cy)],
            2: [(cx - d, cy - d), (cx + d, cy + d)],
            3: [(cx - d, cy - d), (cx, cy), (cx + d, cy + d)],
            4: [(cx - d, cy - d), (cx + d, cy - d), (cx - d, cy + d), (cx + d, cy + d)],
            5: [(cx - d, cy - d), (cx + d, cy - d), (cx, cy), (cx - d, cy + d), (cx + d, cy + d)],
            6: [(cx - d, cy - d), (cx + d, cy - d), (cx - d, cy), (cx + d, cy), (cx - d, cy + d), (cx + d, cy + d)],
        }
        dots = dot_positions.get(val, dot_positions[1])
        for dx, dy in dots:
            pygame.draw.circle(surface, (30, 41, 59), (dx, dy), 4)


class DeedCardView:
    """Renders a detailed property deed card modal/overlay."""
    def __init__(self, font, title_font):
        self.font = font
        self.title_font = title_font

    def draw(self, surface, tile, x, y, width=260, height=360):
        card_rect = pygame.Rect(x, y, width, height)
        # Background shadow
        pygame.draw.rect(surface, (10, 15, 26), card_rect.move(4, 6), border_radius=10)
        pygame.draw.rect(surface, (248, 250, 252), card_rect, border_radius=10)
        pygame.draw.rect(surface, (148, 163, 184), card_rect, width=2, border_radius=10)

        # Header color banner
        banner_h = 48
        b_rect = pygame.Rect(x + 6, y + 6, width - 12, banner_h)
        col = DISTRICT_COLORS.get(tile.group, (71, 85, 105))
        pygame.draw.rect(surface, col, b_rect, border_radius=6)

        # Title on banner
        t_surf = self.title_font.render(tile.name, True, (255, 255, 255))
        surface.blit(t_surf, t_surf.get_rect(center=b_rect.center))

        cy = y + 62
        black = (15, 23, 42)
        gray = (71, 85, 105)

        if tile.type == "PROPERTY":
            lines = [
                (f"Base Rent:", f"${tile.rent[0]}"),
                (f"With 1 House:", f"${tile.rent[1]}"),
                (f"With 2 Houses:", f"${tile.rent[2]}"),
                (f"With 3 Houses:", f"${tile.rent[3]}"),
                (f"With 4 Houses:", f"${tile.rent[4]}"),
                (f"With Skyscraper:", f"${tile.rent[5]}"),
            ]
            for label, val in lines:
                l_surf = self.font.render(label, True, gray)
                v_surf = self.font.render(val, True, black)
                surface.blit(l_surf, (x + 16, cy))
                surface.blit(v_surf, (x + width - 55, cy))
                cy += 20

            pygame.draw.line(surface, (203, 213, 225), (x + 14, cy + 4), (x + width - 14, cy + 4), 1)
            cy += 10
            h_info = self.font.render(f"Upgrade Cost: ${tile.house_cost}", True, black)
            m_info = self.font.render(f"Mortgage: ${tile.mortgage_value}", True, gray)
            surface.blit(h_info, (x + 16, cy))
            surface.blit(m_info, (x + 16, cy + 18))

        elif tile.type == "TRANSIT":
            t_info = [
                ("1 Station Owned:", "$25"),
                ("2 Stations Owned:", "$50"),
                ("3 Stations Owned:", "$100"),
                ("4 Stations Owned:", "$200"),
            ]
            for label, val in t_info:
                l_surf = self.font.render(label, True, gray)
                v_surf = self.font.render(val, True, black)
                surface.blit(l_surf, (x + 16, cy))
                surface.blit(v_surf, (x + width - 55, cy))
                cy += 22
            pygame.draw.line(surface, (203, 213, 225), (x + 14, cy + 4), (x + width - 14, cy + 4), 1)
            m_info = self.font.render(f"Mortgage: ${tile.mortgage_value}", True, gray)
            surface.blit(m_info, (x + 16, cy + 12))

        elif tile.type == "UTILITY":
            u1 = self.font.render("1 Utility: 4x Dice Roll", True, black)
            u2 = self.font.render("2 Utilities: 10x Dice Roll", True, black)
            surface.blit(u1, (x + 16, cy + 14))
            surface.blit(u2, (x + 16, cy + 38))
            pygame.draw.line(surface, (203, 213, 225), (x + 14, cy + 70), (x + width - 14, cy + 70), 1)
            m_info = self.font.render(f"Mortgage: ${tile.mortgage_value}", True, gray)
            surface.blit(m_info, (x + 16, cy + 80))

        # Owner info at bottom
        owner_name = tile.owner.name if tile.owner else "None (Unowned)"
        owner_col = (2, 132, 199) if tile.owner else (100, 116, 139)
        owner_surf = self.font.render(f"Owner: {owner_name}", True, owner_col)
        surface.blit(owner_surf, (x + 16, y + height - 24))

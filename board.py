"""
Board and Tile representation for Metro Tycoon.
Handles geometry, tile drawing, rent calculations, and board rendering.
"""

import pygame
import math
from constants import (
    BOARD_SIZE, BOARD_X, BOARD_Y, CORNER_SIZE, NORMAL_TILE_WIDTH,
    COLOR_BOARD_BG, COLOR_BOARD_INNER, COLOR_TILE_BG, COLOR_TILE_BORDER,
    COLOR_TILE_HOVER, COLOR_TEXT_WHITE, COLOR_TEXT_MUTED, COLOR_TEXT_GOLD,
    COLOR_TEXT_GREEN, COLOR_TEXT_RED, DISTRICT_COLORS, TILES_DATA
)

class Tile:
    def __init__(self, data):
        self.id = data["id"]
        self.name = data["name"]
        self.type = data["type"]
        self.group = data.get("group", None)
        self.price = data.get("price", 0)
        self.rent = data.get("rent", [])
        self.house_cost = data.get("house_cost", 0)
        self.mortgage_value = data.get("mortgage", 0)
        self.tax = data.get("tax", 0)
        self.description = data.get("description", "")
        
        # Ownership & state
        self.owner = None         # Player object or None
        self.houses = 0           # 0 to 4 houses, 5 = Skyscraper
        self.is_mortgaged = False
        
        # Geometry
        self.rect = pygame.Rect(0, 0, 0, 0)
        self.side = "BOTTOM"      # BOTTOM, LEFT, TOP, RIGHT, or CORNER
        self.center = (0, 0)

    def calculate_rent(self, dice_roll, tiles):
        """Calculates current rent for this tile based on ownership, houses, and monopolies."""
        if self.owner is None or self.is_mortgaged:
            return 0
            
        if self.type == "PROPERTY":
            if self.houses > 0:
                # 1 to 5 houses (index 1 to 5)
                idx = min(self.houses, len(self.rent) - 1)
                return self.rent[idx]
            else:
                # Check for monopoly without houses (rent doubles)
                if self.owner.owns_group(self.group, tiles):
                    return self.rent[0] * 2
                return self.rent[0]

        elif self.type == "TRANSIT":
            # Rent depends on number of transit tiles owned (1..4)
            transit_count = sum(1 for tid in self.owner.properties if tiles[tid].group == "TRANSIT")
            idx = max(0, min(transit_count - 1, len(self.rent) - 1))
            return self.rent[idx]

        elif self.type == "UTILITY":
            # Rent is 4x or 10x dice roll
            utility_count = sum(1 for tid in self.owner.properties if tiles[tid].group == "UTILITY")
            multiplier = 10 if utility_count >= 2 else 4
            return dice_roll * multiplier

        return 0

    def to_dict(self):
        return {
            "id": self.id,
            "owner_id": self.owner.id if self.owner else None,
            "houses": self.houses,
            "is_mortgaged": self.is_mortgaged
        }

    def load_dict(self, data, players):
        oid = data.get("owner_id")
        if oid is not None:
            match = next((p for p in players if p.id == oid), None)
            if match is None and oid < len(players):
                match = players[oid]
            self.owner = match
        else:
            self.owner = None
        self.houses = data.get("houses", 0)
        self.is_mortgaged = data.get("is_mortgaged", False)


class Board:
    def __init__(self):
        self.tiles = [Tile(data) for data in TILES_DATA]
        self._calculate_tile_rects()
        self.fonts = {}
        self._init_fonts()

    def _init_fonts(self):
        """Initializes scalable system fonts."""
        pygame.font.init()
        # Fallback to standard clean sans fonts
        sans = pygame.font.get_default_font()
        self.fonts["title"] = pygame.font.SysFont("dejavusans,freesansbold,arial", 22, bold=True)
        self.fonts["header"] = pygame.font.SysFont("dejavusans,freesansbold,arial", 16, bold=True)
        self.fonts["tile_name"] = pygame.font.SysFont("dejavusans,freesansbold,arial", 10, bold=True)
        self.fonts["tile_sub"] = pygame.font.SysFont("dejavusans,freesansbold,arial", 9)
        self.fonts["corner"] = pygame.font.SysFont("dejavusans,freesansbold,arial", 12, bold=True)
        self.fonts["card"] = pygame.font.SysFont("dejavusans,freesansbold,arial", 13)

    def _calculate_tile_rects(self):
        """Computes pixel bounding boxes and sides for all 40 tiles."""
        corner = CORNER_SIZE
        width = NORMAL_TILE_WIDTH

        for i, tile in enumerate(self.tiles):
            if i == 0:
                # Bottom-Right Corner (GO)
                tile.rect = pygame.Rect(
                    BOARD_X + BOARD_SIZE - corner,
                    BOARD_Y + BOARD_SIZE - corner,
                    corner, corner
                )
                tile.side = "CORNER"
            elif 1 <= i <= 9:
                # Bottom Row (going right to left)
                rx = BOARD_X + BOARD_SIZE - corner - i * width
                tile.rect = pygame.Rect(rx, BOARD_Y + BOARD_SIZE - corner, int(width) + 1, corner)
                tile.side = "BOTTOM"
            elif i == 10:
                # Bottom-Left Corner (JAIL)
                tile.rect = pygame.Rect(BOARD_X, BOARD_Y + BOARD_SIZE - corner, corner, corner)
                tile.side = "CORNER"
            elif 11 <= i <= 19:
                # Left Column (going bottom to top)
                offset = (i - 10)
                ry = BOARD_Y + BOARD_SIZE - corner - offset * width
                tile.rect = pygame.Rect(BOARD_X, ry, corner, int(width) + 1)
                tile.side = "LEFT"
            elif i == 20:
                # Top-Left Corner (CENTRAL PARK)
                tile.rect = pygame.Rect(BOARD_X, BOARD_Y, corner, corner)
                tile.side = "CORNER"
            elif 21 <= i <= 29:
                # Top Row (going left to right)
                offset = (i - 20)
                rx = BOARD_X + corner + (offset - 1) * width
                tile.rect = pygame.Rect(rx, BOARD_Y, int(width) + 1, corner)
                tile.side = "TOP"
            elif i == 30:
                # Top-Right Corner (GO TO JAIL)
                tile.rect = pygame.Rect(BOARD_X + BOARD_SIZE - corner, BOARD_Y, corner, corner)
                tile.side = "CORNER"
            elif 31 <= i <= 39:
                # Right Column (going top to bottom)
                offset = (i - 30)
                ry = BOARD_Y + corner + (offset - 1) * width
                tile.rect = pygame.Rect(BOARD_X + BOARD_SIZE - corner, ry, corner, int(width) + 1)
                tile.side = "RIGHT"

            tile.center = (tile.rect.centerx, tile.rect.centery)

    def get_tile_at(self, pos):
        """Returns the tile at mouse position pos (x, y), or None."""
        for tile in self.tiles:
            if tile.rect.collidepoint(pos):
                return tile
        return None

    def get_player_tile_coords(self, tile_id, player_idx, total_players=6):
        """
        Calculates sub-coordinates for a player on a given tile so multiple tokens
        do not overlap or hide each other.
        """
        tile = self.tiles[tile_id]
        cx, cy = tile.center
        
        # Offsets arranged in a neat compact constellation
        offsets = [
            (-14, -14), (14, -14),
            (-14, 14),  (14, 14),
            (-20, 0),   (20, 0)
        ]
        off_x, off_y = offsets[player_idx % len(offsets)]
        return cx + off_x, cy + off_y

    def get_interpolated_pos(self, current_pos, player_idx, total_players=6):
        """
        Given a continuous float board position (e.g. 3.4), computes smooth
        interpolated screen coordinates.
        """
        idx_from = int(current_pos) % 40
        idx_to = (idx_from + 1) % 40
        frac = current_pos - int(current_pos)

        x1, y1 = self.get_player_tile_coords(idx_from, player_idx, total_players)
        x2, y2 = self.get_player_tile_coords(idx_to, player_idx, total_players)

        # Smooth cubic ease
        t = frac * frac * (3 - 2 * frac)
        return x1 + (x2 - x1) * t, y1 + (y2 - y1) * t

    def draw(self, surface, hovered_tile=None, selected_tile=None):
        """Renders board background, all 40 tiles, color bars, badges and center artwork."""
        # Main board base
        board_rect = pygame.Rect(BOARD_X, BOARD_Y, BOARD_SIZE, BOARD_SIZE)
        pygame.draw.rect(surface, COLOR_BOARD_BG, board_rect, border_radius=12)
        
        # Center board area
        corner = CORNER_SIZE
        inner_rect = pygame.Rect(
            BOARD_X + corner, BOARD_Y + corner,
            BOARD_SIZE - 2 * corner, BOARD_SIZE - 2 * corner
        )
        pygame.draw.rect(surface, COLOR_BOARD_INNER, inner_rect, border_radius=6)
        
        # Draw Center Board Branding & Graphic
        self._draw_center_artwork(surface, inner_rect)

        # Draw each tile
        for tile in self.tiles:
            self._draw_tile(surface, tile, hovered_tile, selected_tile)

        # Outer board border
        pygame.draw.rect(surface, (51, 65, 85), board_rect, width=2, border_radius=12)

    def _draw_center_artwork(self, surface, rect):
        """Renders sleek central logo and visual cards area."""
        cx, cy = rect.centerx, rect.centery
        
        # Subtle decorative geometric grid lines
        grid_color = (20, 29, 47)
        for offset in range(-180, 200, 60):
            pygame.draw.line(surface, grid_color, (cx + offset, rect.top + 20), (cx + offset, rect.bottom - 20), 1)
            pygame.draw.line(surface, grid_color, (rect.left + 20, cy + offset), (rect.right - 20, cy + offset), 1)

        # Center Title Banner
        title_surf = self.fonts["title"].render("METRO TYCOON", True, COLOR_TEXT_GOLD)
        t_rect = title_surf.get_rect(center=(cx, cy - 100))
        surface.blit(title_surf, t_rect)

        sub_surf = self.fonts["tile_sub"].render("URBAN PROPERTY EMPIRE SIMULATION", True, COLOR_TEXT_MUTED)
        s_rect = sub_surf.get_rect(center=(cx, cy - 78))
        surface.blit(sub_surf, s_rect)

        # Deck slots: Fortune Card & City Chest card holders
        # Fortune card slot (top-left)
        deck_w, deck_h = 100, 65
        f_rect = pygame.Rect(cx - 130, cy + 50, deck_w, deck_h)
        pygame.draw.rect(surface, (30, 41, 59), f_rect, border_radius=8)
        pygame.draw.rect(surface, (234, 88, 12), f_rect, width=2, border_radius=8)
        f_lbl = self.fonts["tile_name"].render("FORTUNE", True, (251, 146, 60))
        surface.blit(f_lbl, f_lbl.get_rect(center=f_rect.center))

        # City Chest card slot (bottom-right)
        c_rect = pygame.Rect(cx + 30, cy + 50, deck_w, deck_h)
        pygame.draw.rect(surface, (30, 41, 59), c_rect, border_radius=8)
        pygame.draw.rect(surface, (59, 130, 246), c_rect, width=2, border_radius=8)
        c_lbl = self.fonts["tile_name"].render("CITY CHEST", True, (96, 165, 250))
        surface.blit(c_lbl, c_lbl.get_rect(center=c_rect.center))

    def _draw_tile(self, surface, tile, hovered_tile, selected_tile):
        """Renders an individual tile with district headers, text, prices, and owner markers."""
        r = tile.rect
        is_hovered = (hovered_tile and hovered_tile.id == tile.id)
        is_selected = (selected_tile and selected_tile.id == tile.id)

        # Background
        bg_col = (40, 53, 76) if is_hovered else COLOR_TILE_BG
        pygame.draw.rect(surface, bg_col, r)
        
        # Border
        b_col = COLOR_TEXT_GOLD if is_selected else (COLOR_TILE_HOVER if is_hovered else COLOR_TILE_BORDER)
        b_width = 2 if (is_selected or is_hovered) else 1
        pygame.draw.rect(surface, b_col, r, width=b_width)

        # If Corner Tile
        if tile.side == "CORNER":
            self._draw_corner_tile(surface, tile)
            return

        # District Color Bar for Properties
        bar_size = 14
        color_val = DISTRICT_COLORS.get(tile.group, (71, 85, 105))

        if tile.type == "PROPERTY":
            if tile.side == "BOTTOM":
                bar_rect = pygame.Rect(r.x, r.y, r.width, bar_size)
            elif tile.side == "LEFT":
                bar_rect = pygame.Rect(r.right - bar_size, r.y, bar_size, r.height)
            elif tile.side == "TOP":
                bar_rect = pygame.Rect(r.x, r.bottom - bar_size, r.width, bar_size)
            else: # RIGHT
                bar_rect = pygame.Rect(r.x, r.y, bar_size, r.height)
            
            pygame.draw.rect(surface, color_val, bar_rect)
            
            # Houses & Hotel indicator on color bar
            if tile.houses > 0:
                self._draw_buildings(surface, tile, bar_rect)

        # Owner Ribbon / Badge if tile is owned
        if tile.owner:
            self._draw_owner_badge(surface, tile)

        # Mortgaged Strikethrough
        if tile.is_mortgaged:
            m_surf = self.fonts["tile_sub"].render("MORTGAGED", True, COLOR_TEXT_RED)
            surface.blit(m_surf, m_surf.get_rect(center=r.center))

        # Tile Label & Price
        self._draw_tile_labels(surface, tile)

    def _draw_buildings(self, surface, tile, bar_rect):
        """Draws small green houses or red skyscraper on the color bar."""
        if tile.houses == 5:
            # Skyscraper / Hotel (Red block with gold star)
            h_rect = pygame.Rect(0, 0, min(14, bar_rect.width - 4), min(10, bar_rect.height - 4))
            h_rect.center = bar_rect.center
            pygame.draw.rect(surface, (239, 68, 68), h_rect, border_radius=2)
            pygame.draw.rect(surface, (254, 240, 138), h_rect, width=1, border_radius=2)
        else:
            # 1 to 4 green houses
            count = tile.houses
            for idx in range(count):
                if bar_rect.width > bar_rect.height:
                    spacing = bar_rect.width / (count + 1)
                    hx = bar_rect.x + (idx + 1) * spacing
                    hy = bar_rect.centery
                else:
                    spacing = bar_rect.height / (count + 1)
                    hx = bar_rect.centerx
                    hy = bar_rect.y + (idx + 1) * spacing
                h_rect = pygame.Rect(0, 0, 8, 8)
                h_rect.center = (int(hx), int(hy))
                pygame.draw.rect(surface, (34, 197, 94), h_rect, border_radius=2)
                pygame.draw.rect(surface, (255, 255, 255), h_rect, width=1, border_radius=2)

    def _draw_owner_badge(self, surface, tile):
        """Draws a compact ownership badge showing who owns the property."""
        r = tile.rect
        owner_color = tile.owner.color
        badge_radius = 5
        
        # Position badge near interior edge
        if tile.side == "BOTTOM":
            bx, by = r.centerx, r.y + 20
        elif tile.side == "LEFT":
            bx, by = r.right - 20, r.centery
        elif tile.side == "TOP":
            bx, by = r.centerx, r.bottom - 20
        else:
            bx, by = r.x + 20, r.centery
            
        pygame.draw.circle(surface, (15, 23, 42), (bx, by), badge_radius + 2)
        pygame.draw.circle(surface, owner_color, (bx, by), badge_radius)

    def _draw_tile_labels(self, surface, tile):
        """Draws property names and price labels neatly formatted."""
        r = tile.rect
        
        # Name
        words = tile.name.split()
        line1 = words[0] if len(words) > 0 else ""
        line2 = " ".join(words[1:]) if len(words) > 1 else ""
        
        # Color based on type
        name_col = COLOR_TEXT_WHITE
        if tile.type == "TRANSIT":
            name_col = (148, 163, 184)
        elif tile.type == "UTILITY":
            name_col = (192, 132, 252)
        elif tile.type in ("FORTUNE", "CHEST"):
            name_col = COLOR_TEXT_GOLD
        elif tile.type == "TAX":
            name_col = COLOR_TEXT_RED

        surf1 = self.fonts["tile_name"].render(line1, True, name_col)
        surf2 = self.fonts["tile_name"].render(line2, True, name_col) if line2 else None

        # Price / info label
        price_text = ""
        price_col = COLOR_TEXT_GREEN
        if tile.type in ("PROPERTY", "TRANSIT", "UTILITY"):
            price_text = f"${tile.price}"
        elif tile.type == "TAX":
            price_text = f"${tile.tax}"
            price_col = COLOR_TEXT_RED
        elif tile.type == "FORTUNE":
            price_text = "FORTUNE"
            price_col = (251, 146, 60)
        elif tile.type == "CHEST":
            price_text = "CHEST"
            price_col = (96, 165, 250)

        price_surf = self.fonts["tile_sub"].render(price_text, True, price_col) if price_text else None

        # Center layout depending on tile orientation
        cx, cy = r.centerx, r.centery
        if surf2:
            surface.blit(surf1, surf1.get_rect(center=(cx, cy - 8)))
            surface.blit(surf2, surf2.get_rect(center=(cx, cy + 4)))
            if price_surf:
                surface.blit(price_surf, price_surf.get_rect(center=(cx, cy + 18)))
        else:
            surface.blit(surf1, surf1.get_rect(center=(cx, cy - 4)))
            if price_surf:
                surface.blit(price_surf, price_surf.get_rect(center=(cx, cy + 12)))

    def _draw_corner_tile(self, surface, tile):
        """Renders rich details for the 4 corner tiles."""
        r = tile.rect
        cx, cy = r.centerx, r.centery
        
        if tile.id == 0:
            # START HUB
            col = (34, 197, 94)
            pygame.draw.rect(surface, (20, 83, 45), r.inflate(-6, -6), border_radius=8)
            t_surf = self.fonts["corner"].render("START HUB", True, (255, 255, 255))
            sub1 = self.fonts["tile_sub"].render("COLLECT $200", True, COLOR_TEXT_GOLD)
            sub2 = self.fonts["tile_sub"].render("AS YOU PASS", True, COLOR_TEXT_WHITE)
            surface.blit(t_surf, t_surf.get_rect(center=(cx, cy - 18)))
            surface.blit(sub1, sub1.get_rect(center=(cx, cy + 4)))
            surface.blit(sub2, sub2.get_rect(center=(cx, cy + 18)))

        elif tile.id == 10:
            # DETENTION / JAIL
            pygame.draw.rect(surface, (30, 41, 59), r.inflate(-6, -6), border_radius=8)
            # Draw iron bars graphic in inner corner
            inner_jail = pygame.Rect(r.x + 8, r.y + 8, 48, 48)
            pygame.draw.rect(surface, (15, 23, 42), inner_jail)
            for bar_x in range(inner_jail.left + 8, inner_jail.right, 10):
                pygame.draw.line(surface, (148, 163, 184), (bar_x, inner_jail.top), (bar_x, inner_jail.bottom), 2)
            
            j_surf = self.fonts["tile_name"].render("DETENTION", True, (248, 113, 113))
            v_surf = self.fonts["tile_sub"].render("JUST VISITING", True, COLOR_TEXT_MUTED)
            surface.blit(j_surf, j_surf.get_rect(center=(cx + 12, cy - 14)))
            surface.blit(v_surf, v_surf.get_rect(center=(cx, cy + 28)))

        elif tile.id == 20:
            # CENTRAL PARK (Free Parking)
            pygame.draw.rect(surface, (19, 78, 74), r.inflate(-6, -6), border_radius=8)
            t_surf = self.fonts["corner"].render("CENTRAL PARK", True, (255, 255, 255))
            sub = self.fonts["tile_sub"].render("FREE HAVEN", True, (45, 212, 191))
            surface.blit(t_surf, t_surf.get_rect(center=(cx, cy - 8)))
            surface.blit(sub, sub.get_rect(center=(cx, cy + 12)))

        elif tile.id == 30:
            # GO TO DETENTION
            pygame.draw.rect(surface, (127, 29, 29), r.inflate(-6, -6), border_radius=8)
            t_surf = self.fonts["corner"].render("GO TO", True, (255, 255, 255))
            sub1 = self.fonts["corner"].render("DETENTION", True, (254, 202, 202))
            surface.blit(t_surf, t_surf.get_rect(center=(cx, cy - 10)))
            surface.blit(sub1, sub1.get_rect(center=(cx, cy + 12)))

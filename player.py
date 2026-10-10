"""
Player class and token rendering for Metro Tycoon.
Handles player financial state, inventory, jail status, and graphical tokens.
"""

import pygame
import math
from constants import (
    PLAYER_COLORS, PLAYER_TOKEN_NAMES, AI_PERSONALITIES,
    GROUP_COUNTS
)

class Player:
    def __init__(self, player_id, name, color, token_index=0, is_ai=False, ai_personality="Balanced"):
        self.id = player_id
        self.name = name
        self.color = color
        self.token_index = token_index
        self.token_name = PLAYER_TOKEN_NAMES[token_index % len(PLAYER_TOKEN_NAMES)]
        self.is_ai = is_ai
        self.ai_personality = ai_personality
        
        # Financial & Inventory
        self.cash = 1500
        self.position = 0
        self.properties = []  # List of tile IDs
        self.jail_free_cards = 0
        
        # Movement animation state
        self.target_position = 0
        self.anim_pos = 0.0   # Current animated board position
        self.is_moving = False
        
        # Status flags
        self.in_jail = False
        self.jail_turns = 0
        self.is_bankrupt = False
        self.bankrupt_to = None
        self.doubles_count = 0
        
        # Stats tracking
        self.turns_played = 0
        self.rent_paid_total = 0
        self.rent_collected_total = 0

    def add_cash(self, amount):
        self.cash += amount

    def deduct_cash(self, amount):
        self.cash -= amount

    def get_net_worth(self, tiles):
        """Calculates total net worth including cash, properties, and buildings."""
        if self.is_bankrupt:
            return 0
        total = self.cash
        for tile_id in self.properties:
            tile = tiles[tile_id]
            if tile.is_mortgaged:
                total += tile.mortgage_value
            else:
                total += tile.price
                if hasattr(tile, 'houses') and tile.houses > 0:
                    total += tile.houses * tile.house_cost
        return total

    def owns_group(self, group_name, tiles):
        """Returns True if the player owns all properties in the specified color group."""
        if group_name not in GROUP_COUNTS:
            return False
        required = GROUP_COUNTS[group_name]
        owned = sum(1 for tid in self.properties if tiles[tid].group == group_name)
        return owned >= required

    def get_group_properties(self, group_name, tiles):
        """Returns all tiles in the group owned by this player."""
        return [tiles[tid] for tid in self.properties if tiles[tid].group == group_name]

    def can_build_on(self, tile, tiles):
        """
        Monopoly rule check: Player owns complete group, no properties in group mortgaged,
        houses < 5, and building follows even distribution rule.
        """
        if tile.id not in self.properties or tile.type != "PROPERTY":
            return False
        if not self.owns_group(tile.group, tiles):
            return False
        if tile.houses >= 5:
            return False
        
        # Check no tile in group is mortgaged
        group_tiles = [t for t in tiles if getattr(t, 'group', None) == tile.group]
        if any(t.is_mortgaged for t in group_tiles):
            return False
            
        # Even building rule: tile's house count cannot exceed min house count in group by > 0
        min_houses = min(t.houses for t in group_tiles)
        return tile.houses == min_houses

    def can_sell_building(self, tile, tiles):
        """Check if a house/hotel can be sold from tile (even selling rule)."""
        if tile.id not in self.properties or tile.houses <= 0:
            return False
        group_tiles = [t for t in tiles if getattr(t, 'group', None) == tile.group]
        max_houses = max(t.houses for t in group_tiles)
        return tile.houses == max_houses

    def draw_token(self, surface, center_x, center_y, radius=12):
        """
        Draws a stylized, high-contrast vector token for this player.
        Each token index has a unique silhouette and aesthetic.
        """
        cx, cy = int(center_x), int(center_y)
        
        # Outer glow / shadow
        pygame.draw.circle(surface, (15, 23, 42), (cx, cy + 2), radius + 2)
        # Background disk
        pygame.draw.circle(surface, (30, 41, 59), (cx, cy), radius)
        # Outer rim in player color
        pygame.draw.circle(surface, self.color, (cx, cy), radius, width=2)
        
        inner_r = radius - 3
        # Vector glyphs according to token_index
        idx = self.token_index % 6
        c = self.color
        
        if idx == 0:
            # Roadster: streamlined wedge & wheels
            body_rect = pygame.Rect(cx - 7, cy - 3, 14, 6)
            pygame.draw.rect(surface, c, body_rect, border_radius=2)
            pygame.draw.circle(surface, (255, 255, 255), (cx - 4, cy + 3), 2)
            pygame.draw.circle(surface, (255, 255, 255), (cx + 4, cy + 3), 2)
            # Roof cabin
            pygame.draw.polygon(surface, (240, 240, 240), [
                (cx - 3, cy - 3), (cx + 2, cy - 3), (cx + 4, cy - 1), (cx - 4, cy - 1)
            ])
        elif idx == 1:
            # Shuttle / Rocket: sleek pointed triangle
            pts = [(cx, cy - 8), (cx + 6, cy + 6), (cx, cy + 3), (cx - 6, cy + 6)]
            pygame.draw.polygon(surface, c, pts)
            pygame.draw.circle(surface, (255, 255, 255), (cx, cy), 2)
        elif idx == 2:
            # Yacht: boat hull + triangular sail
            # Hull
            hull = [(cx - 7, cy + 2), (cx + 7, cy + 2), (cx + 5, cy + 6), (cx - 5, cy + 6)]
            pygame.draw.polygon(surface, c, hull)
            # Sail
            sail = [(cx - 1, cy + 1), (cx - 1, cy - 7), (cx + 5, cy + 1)]
            pygame.draw.polygon(surface, (255, 255, 255), sail)
        elif idx == 3:
            # Airship / Jet: swept-wing aircraft
            pygame.draw.ellipse(surface, (255, 255, 255), (cx - 3, cy - 7, 6, 14))
            pygame.draw.polygon(surface, c, [
                (cx - 8, cy + 1), (cx + 8, cy + 1), (cx, cy - 3)
            ])
            # Tail fin
            pygame.draw.polygon(surface, c, [
                (cx - 4, cy + 6), (cx + 4, cy + 6), (cx, cy + 3)
            ])
        elif idx == 4:
            # Crown: 3-point crown with jewels
            pts = [
                (cx - 6, cy - 4), (cx - 3, cy - 1), (cx, cy - 6),
                (cx + 3, cy - 1), (cx + 6, cy - 4),
                (cx + 5, cy + 5), (cx - 5, cy + 5)
            ]
            pygame.draw.polygon(surface, c, pts)
            pygame.draw.circle(surface, (255, 255, 255), (cx, cy + 1), 2)
        else:
            # Cyber Fox / Diamond: geometric diamond star
            pts = [(cx, cy - 7), (cx + 7, cy), (cx, cy + 7), (cx - 7, cy)]
            pygame.draw.polygon(surface, c, pts)
            pygame.draw.circle(surface, (255, 255, 255), (cx, cy), 3)

    def to_dict(self):
        """Serialize state for save game."""
        return {
            "id": self.id,
            "name": self.name,
            "color": list(self.color),
            "token_index": self.token_index,
            "token_name": self.token_name,
            "is_ai": self.is_ai,
            "ai_personality": self.ai_personality,
            "cash": self.cash,
            "position": self.position,
            "properties": list(self.properties),
            "jail_free_cards": self.jail_free_cards,
            "in_jail": self.in_jail,
            "jail_turns": self.jail_turns,
            "is_bankrupt": self.is_bankrupt,
            "bankrupt_to": self.bankrupt_to,
            "doubles_count": self.doubles_count
        }

    def load_dict(self, data):
        """Restore state from save game."""
        self.name = data.get("name", self.name)
        if "color" in data:
            self.color = tuple(data["color"])
        self.token_index = data.get("token_index", self.token_index)
        self.token_name = data.get("token_name", self.token_name)
        self.is_ai = data.get("is_ai", self.is_ai)
        self.ai_personality = data.get("ai_personality", self.ai_personality)
        self.cash = data["cash"]
        self.position = data["position"]
        self.target_position = data["position"]
        self.anim_pos = float(data["position"])
        self.is_moving = False
        self.properties = list(data["properties"])
        self.jail_free_cards = data["jail_free_cards"]
        self.in_jail = data["in_jail"]
        self.jail_turns = data["jail_turns"]
        self.is_bankrupt = data["is_bankrupt"]
        self.bankrupt_to = data["bankrupt_to"]
        self.doubles_count = data.get("doubles_count", 0)

"""
AI Decision Engine for Computer Opponents in Metro Tycoon.
Handles purchasing, building, debt resolution, trading valuation, and jail decisions.
"""

import random
from constants import AI_PERSONALITIES, GROUP_COUNTS

class AIEngine:
    def __init__(self):
        pass

    def get_profile(self, player):
        return AI_PERSONALITIES.get(player.ai_personality, AI_PERSONALITIES["Balanced"])

    def should_pay_jail_fee(self, player, tiles):
        """Decides whether to pay $50 to exit detention or try rolling doubles."""
        profile = self.get_profile(player)
        # If has jail free card, always use it
        if player.jail_free_cards > 0:
            return "CARD"
            
        # Count available unowned properties
        unowned_count = sum(1 for t in tiles if t.type in ("PROPERTY", "TRANSIT", "UTILITY") and t.owner is None)
        
        # In early game with many unowned properties, prioritize getting out to buy
        if unowned_count > 10 and player.cash >= (profile["cash_reserve"] + 50):
            return "PAY"
            
        # If turns in jail reaches 3, must pay
        if player.jail_turns >= 2:
            return "PAY" if player.cash >= 50 else "ROLL"
            
        # In late game with high danger, staying in jail can be safe
        if unowned_count <= 4 and player.cash < 600:
            return "ROLL"

        if player.cash > profile["cash_reserve"] * 1.5:
            return "PAY"
            
        return "ROLL"

    def should_buy_property(self, player, tile, tiles):
        """Evaluates whether to purchase the unowned property landed on."""
        if player.cash < tile.price:
            return False
            
        profile = self.get_profile(player)
        reserve = profile["cash_reserve"]
        
        # Does this property complete a monopoly for the AI?
        group = tile.group
        owned_in_group = sum(1 for tid in player.properties if tiles[tid].group == group)
        needed = GROUP_COUNTS.get(group, 3)
        
        # If it completes the monopoly, buy almost unconditionally if affordable!
        if (owned_in_group + 1) == needed:
            return True
            
        # If it's transit or utility, usually valuable
        if tile.type in ("TRANSIT", "UTILITY"):
            return (player.cash - tile.price) >= (reserve * 0.5)

        # Standard safety check: Cash remaining after purchase should exceed reserve
        cash_after = player.cash - tile.price
        if cash_after >= reserve:
            return True
            
        # Aggressive personalities might take a calculated gamble
        if profile["build_aggression"] > 0.7 and cash_after >= (reserve * 0.3):
            return True
            
        return False

    def plan_buildings(self, player, tiles):
        """
        Returns a list of tile IDs on which the AI should build houses/apartments this turn.
        """
        profile = self.get_profile(player)
        reserve = profile["cash_reserve"]
        
        planned_builds = []
        simulated_cash = player.cash
        
        # Find all completed monopolies owned by player
        candidate_groups = []
        for g_name, req_count in GROUP_COUNTS.items():
            if g_name in ("TRANSIT", "UTILITY"):
                continue
            if player.owns_group(g_name, tiles):
                candidate_groups.append(g_name)

        # Sort candidate groups by potential rent return (e.g. CROWN, UPTOWN, TECH first)
        candidate_groups.sort(key=lambda g: max(t.price for t in tiles if getattr(t, 'group', None) == g), reverse=True)

        for group_name in candidate_groups:
            group_tiles = [t for t in tiles if getattr(t, 'group', None) == group_name]
            
            # Can we build in this group? (no mortgages, houses < 5)
            if any(t.is_mortgaged for t in group_tiles):
                continue
                
            # Attempt to upgrade evenly while cash permits
            while True:
                min_h = min(t.houses for t in group_tiles)
                if min_h >= 5:
                    break
                # Find the tile with min_h
                eligible = [t for t in group_tiles if t.houses == min_h and t.id not in planned_builds]
                if not eligible:
                    # Reset planned for next cycle of upgrades
                    eligible = [t for t in group_tiles if t.houses == min_h]
                    
                target = eligible[0]
                cost = target.house_cost
                
                # Check cash safety margin
                if simulated_cash - cost < reserve:
                    break
                    
                simulated_cash -= cost
                planned_builds.append(target.id)
                target.houses += 1  # Temporarily increment for simulation
                
        # Revert temporary increments
        for tid in planned_builds:
            tiles[tid].houses -= 1

        return planned_builds

    def resolve_debt(self, player, debt_amount, tiles):
        """
        Attempts to raise cash to cover debt through mortgaging properties and selling houses.
        Returns True if debt can be covered, False if bankrupt.
        """
        needed = debt_amount - player.cash
        if needed <= 0:
            return True
            
        # Step 1: Sell houses from least valuable groups
        groups_with_houses = []
        for tid in player.properties:
            t = tiles[tid]
            if t.houses > 0 and t.group not in groups_with_houses:
                groups_with_houses.append(t.group)
                
        # Sort groups by cheapest house cost first to preserve high-yield investments if possible
        groups_with_houses.sort(key=lambda g: next(t.house_cost for t in tiles if getattr(t, 'group', None) == g))
        
        for g_name in groups_with_houses:
            group_tiles = [t for t in tiles if getattr(t, 'group', None) == g_name]
            while any(t.houses > 0 for t in group_tiles) and needed > 0:
                max_h = max(t.houses for t in group_tiles)
                for t in group_tiles:
                    if t.houses == max_h and t.houses > 0:
                        # Selling house returns half price
                        refund = t.house_cost // 2
                        t.houses -= 1
                        player.add_cash(refund)
                        needed -= refund
                        if needed <= 0:
                            return True

        # Step 2: Mortgage non-monopoly properties first
        unmortgaged = [tiles[tid] for tid in player.properties if not tiles[tid].is_mortgaged and tiles[tid].houses == 0]
        # Prefer mortgaging utilities, then transits, then isolated properties
        def mortgage_priority(t):
            if not player.owns_group(t.group, tiles):
                return 0 # High priority to mortgage
            return 1 # Low priority to mortgage full monopoly
            
        unmortgaged.sort(key=mortgage_priority)
        
        for t in unmortgaged:
            t.is_mortgaged = True
            player.add_cash(t.mortgage_value)
            needed -= t.mortgage_value
            if needed <= 0:
                return True

        # Cannot cover debt -> Bankruptcy!
        return False

    def evaluate_trade(self, ai_player, offer_props, offer_cash, req_props, req_cash, tiles):
        """
        Evaluates a trade proposed to this AI.
        offer_props: list of Tile IDs offered to the AI
        offer_cash: cash offered to the AI
        req_props: list of Tile IDs requested from the AI
        req_cash: cash requested from the AI
        Returns (accepted: bool, reason: str)
        """
        profile = self.get_profile(ai_player)
        
        # Check if AI has enough cash
        if req_cash > ai_player.cash:
            return False, "I do not have enough funds for that cash request."

        # Compute value gained by AI
        gain_val = offer_cash
        loss_val = req_cash
        
        for tid in offer_props:
            t = tiles[tid]
            gain_val += t.price
            # Huge bonus if this property completes a monopoly for the AI!
            group = t.group
            owned_in_group = sum(1 for ptid in ai_player.properties if tiles[ptid].group == group)
            needed = GROUP_COUNTS.get(group, 3)
            if (owned_in_group + 1) == needed:
                gain_val += t.price * 2.5 # High strategic bonus

        for tid in req_props:
            t = tiles[tid]
            loss_val += t.price
            # Penalty if giving away a property breaks or belongs to AI monopoly
            if ai_player.owns_group(t.group, tiles):
                loss_val += t.price * 3.5 # Strongly protect own monopolies!
            else:
                group = t.group
                owned_in_group = sum(1 for ptid in ai_player.properties if tiles[ptid].group == group)
                needed = GROUP_COUNTS.get(group, 3)
                if owned_in_group >= needed - 1:
                    loss_val += t.price * 1.5

        # Factor in AI personality eagerness
        threshold = 1.05 - (profile["trade_eagerness"] * 0.2)
        
        if gain_val >= (loss_val * threshold):
            return True, "Deal accepted! A mutually beneficial arrangement."
        elif gain_val >= loss_val * 0.85:
            return False, "You're close, but you need to sweeten the deal with more cash."
        else:
            return False, "This offer is unacceptable to my financial advisors."

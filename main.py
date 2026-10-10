"""
Metro Tycoon - Full-featured Monopoly Clone in Pygame.
Supports 2 to 6 players (human vs AI bots with custom playstyles).
Features animated movement, audio, trading, building, cards, mortgages, and save/load.
"""

import sys
import os
import random
import pygame

from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, BOARD_SIZE, BOARD_X, BOARD_Y,
    COLOR_BG, COLOR_PANEL_BG, COLOR_TEXT_WHITE, COLOR_TEXT_MUTED,
    COLOR_TEXT_GOLD, COLOR_TEXT_GREEN, COLOR_TEXT_RED, COLOR_TEXT_AMBER,
    COLOR_ACCENT_BLUE, COLOR_ACCENT_GREEN, COLOR_ACCENT_RED, COLOR_ACCENT_AMBER,
    PLAYER_COLORS, PLAYER_TOKEN_NAMES, AI_PERSONALITIES
)
from sound import sound_fx
from board import Board
from player import Player
from cards import CardManager
from ai import AIEngine
from ui import Button, EventLog, PlayerPanel, DiceWidget, DeedCardView
from modals import BuyPropertyModal, CardModal, BuildModal, MortgageModal, TradeModal, AuctionModal
from save_manager import SaveManager, SAVE_FILE

# Game Screen States
STATE_TITLE = "TITLE"
STATE_SETUP = "SETUP"
STATE_PLAYING = "PLAYING"
STATE_GAME_OVER = "GAME_OVER"

# Gameplay Turn Phases
PHASE_READY = "READY"
PHASE_ROLLING = "ROLLING"
PHASE_MOVING = "MOVING"
PHASE_TILE_ACTION = "TILE_ACTION"
PHASE_POST_ROLL = "POST_ROLL"


class MetroTycoonGame:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Metro Tycoon - Urban Monopoly Simulator")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        # Fonts
        self.font_main = pygame.font.SysFont("dejavusans,freesansbold,arial", 13)
        self.font_bold = pygame.font.SysFont("dejavusans,freesansbold,arial", 14, bold=True)
        self.font_title = pygame.font.SysFont("dejavusans,freesansbold,arial", 28, bold=True)
        self.font_header = pygame.font.SysFont("dejavusans,freesansbold,arial", 18, bold=True)
        self.font_small = pygame.font.SysFont("dejavusans,freesansbold,arial", 11)

        # Core Game Systems
        self.board = Board()
        self.card_manager = CardManager()
        self.ai_engine = AIEngine()
        self.deed_view = DeedCardView(self.font_main, self.font_bold)

        # Screen State
        self.state = STATE_TITLE

        # Setup Config
        self.num_players = 4
        self.setup_configs = []
        self._init_default_setup()

        # Match State
        self.players = []
        self.current_player_idx = 0
        self.turn_phase = PHASE_READY
        self.round_number = 1
        self.last_dice = (1, 1)
        self.active_modal = None
        self.hovered_tile = None
        self.fast_ai = False
        self.ai_step_delay = 0

        # Dice Widget
        self.dice_widget = DiceWidget((780, 70, 200, 70), self.font_bold)

        # UI Panels
        self.event_log = EventLog((780, 480, SCREEN_WIDTH - 804, 250), self.font_main)
        self.player_panel = PlayerPanel((780, 160, SCREEN_WIDTH - 804, 300), self.font_bold, self.font_small)

        # Buttons
        self._init_buttons()

    def _init_default_setup(self):
        """Initializes default setup config for 2-6 players."""
        personalities = list(AI_PERSONALITIES.keys())
        self.setup_configs = [
            {"name": "Player 1", "is_ai": False, "personality": "Balanced", "token": 0},
            {"name": "Nexus Bot", "is_ai": True, "personality": "Tycoon", "token": 1},
            {"name": "Aegis AI", "is_ai": True, "personality": "Cautious", "token": 2},
            {"name": "Venture AI", "is_ai": True, "personality": "Dealmaker", "token": 3},
            {"name": "Cipher Bot", "is_ai": True, "personality": "Balanced", "token": 4},
            {"name": "Apex AI", "is_ai": True, "personality": "Tycoon", "token": 5},
        ]

    def _init_buttons(self):
        # Action Buttons on Right Side HUD
        hud_btn_w = 110
        hud_btn_h = 36
        bx = 1000
        by = 72

        self.btn_roll = Button((bx, by, 100, hud_btn_h), "Roll Dice", self.font_bold,
                               bg_color=COLOR_ACCENT_GREEN, callback=self.on_roll_dice)
        self.btn_end = Button((bx + 110, by, 100, hud_btn_h), "End Turn", self.font_bold,
                              bg_color=COLOR_ACCENT_BLUE, disabled=True, callback=self.on_end_turn)
        
        # Sub-actions
        by2 = by + 44
        self.btn_build = Button((bx - 10, by2, 80, 28), "Build", self.font_main,
                                bg_color=(30, 58, 138), callback=self.open_build_modal)
        self.btn_trade = Button((bx + 78, by2, 80, 28), "Trade", self.font_main,
                                bg_color=(13, 148, 136), callback=self.open_trade_modal)
        self.btn_mortgage = Button((bx + 166, by2, 80, 28), "Mortgage", self.font_main,
                                   bg_color=(180, 83, 9), callback=self.open_mortgage_modal)

        # Header bar toggles (Compact right-aligned buttons)
        self.btn_menu = Button((1055, 24, 48, 26), "Menu", self.font_small,
                               bg_color=(51, 65, 85), callback=self.return_to_menu)
        self.btn_sound = Button((1110, 24, 60, 26), "SFX: ON", self.font_small,
                                bg_color=(51, 65, 85), callback=self.toggle_sound)
        self.btn_speed = Button((1177, 24, 46, 26), "1x", self.font_small,
                                bg_color=(51, 65, 85), callback=self.toggle_speed)
        self.btn_save = Button((1230, 24, 48, 26), "Save", self.font_small,
                               bg_color=(30, 58, 138), callback=self.save_game)
        self.btn_load = Button((1284, 24, 48, 26), "Load", self.font_small,
                               bg_color=(51, 65, 85), callback=self.load_game)

    def return_to_menu(self):
        sound_fx.play("click")
        self.state = STATE_TITLE

    def toggle_sound(self):
        state = sound_fx.toggle()
        self.btn_sound.text = "SFX: ON" if state else "SFX: OFF"

    def toggle_speed(self):
        self.fast_ai = not self.fast_ai
        self.btn_speed.text = "3x" if self.fast_ai else "1x"
        if self.active_modal and hasattr(self.active_modal, "fast_ai"):
            self.active_modal.fast_ai = self.fast_ai

    def start_game(self):
        """Constructs players and begins the match."""
        self.players = []
        for i in range(self.num_players):
            cfg = self.setup_configs[i]
            p = Player(
                player_id=i,
                name=cfg["name"],
                color=PLAYER_COLORS[i % len(PLAYER_COLORS)],
                token_index=cfg["token"],
                is_ai=cfg["is_ai"],
                ai_personality=cfg["personality"]
            )
            self.players.append(p)

        self.current_player_idx = 0
        self.round_number = 1
        self.turn_phase = PHASE_READY
        self.active_modal = None
        self.event_log.messages.clear()
        self.event_log.add(f"Match initiated with {self.num_players} players!", COLOR_TEXT_GOLD)
        self.event_log.add(f"Round 1 begins. {self.current_player().name}'s turn.", COLOR_TEXT_WHITE)
        self.state = STATE_PLAYING
        self._update_hud_buttons()

    def current_player(self):
        return self.players[self.current_player_idx]

    def log(self, message, color=COLOR_TEXT_WHITE):
        self.event_log.add(message, color)

    def on_roll_dice(self):
        p = self.current_player()
        if p.is_bankrupt:
            self.on_end_turn()
            return

        can_roll_again = (
            self.turn_phase == PHASE_POST_ROLL
            and self.last_dice[0] == self.last_dice[1]
            and not p.in_jail
            and 0 < p.doubles_count < 3
        )
        if self.turn_phase != PHASE_READY and not can_roll_again:
            return

        sound_fx.play("dice")

        # Roll 2 standard six-sided dice
        d1 = random.randint(1, 6)
        d2 = random.randint(1, 6)
        self.last_dice = (d1, d2)
        self.dice_widget.set_values(d1, d2)
        total_roll = d1 + d2
        is_doubles = (d1 == d2)

        # Handle Jail
        if p.in_jail:
            if is_doubles:
                p.in_jail = False
                p.jail_turns = 0
                self.log(f"{p.name} rolled DOUBLES ({d1}, {d2}) and broke out of Detention!", COLOR_TEXT_GREEN)
                self.start_movement(total_roll, is_doubles)
            else:
                p.jail_turns += 1
                if p.jail_turns >= 3:
                    p.in_jail = False
                    p.jail_turns = 0
                    self.log(f"{p.name} must pay $50 mandatory fine to exit Detention.", COLOR_TEXT_MUTED)
                    self._deduct_with_debt_check(p, 50, creditor=None)
                    if p.is_bankrupt or self.state == STATE_GAME_OVER:
                        return
                    self.start_movement(total_roll, False)
                else:
                    self.log(f"{p.name} failed to roll doubles ({d1}, {d2}). Remains in Detention ({p.jail_turns}/3).", COLOR_TEXT_MUTED)
                    self.turn_phase = PHASE_POST_ROLL
                    self._update_hud_buttons()
            return

        # Check consecutive doubles for speeding
        if is_doubles:
            p.doubles_count += 1
            if p.doubles_count >= 3:
                p.doubles_count = 0
                p.in_jail = True
                p.jail_turns = 0
                p.position = 10
                p.target_position = 10
                p.anim_pos = 10.0
                sound_fx.play("jail")
                self.log(f"{p.name} rolled 3 consecutive doubles! Sent to Detention for reckless speeding!", COLOR_TEXT_RED)
                self.turn_phase = PHASE_POST_ROLL
                self._update_hud_buttons()
                return
        else:
            p.doubles_count = 0

        self.start_movement(total_roll, is_doubles)

    def start_movement(self, steps, is_doubles):
        p = self.current_player()
        p.is_moving = True
        p.target_position = (p.position + steps) % 40
        self.turn_phase = PHASE_MOVING
        self.btn_roll.disabled = True
        self.btn_end.disabled = True

        # Check if passed GO
        if (p.position + steps) >= 40:
            p.add_cash(200)
            sound_fx.play("pass_go")
            self.log(f"{p.name} passed START HUB and collected $200 stipend!", COLOR_TEXT_GREEN)

        p.position = p.target_position
        # Movement step animation handled in update loop

    def finish_movement(self):
        p = self.current_player()
        p.is_moving = False
        p.anim_pos = float(p.position)
        tile = self.board.tiles[p.position]
        self.turn_phase = PHASE_TILE_ACTION
        self.handle_tile_action(tile)

    def handle_tile_action(self, tile):
        p = self.current_player()
        self.log(f"{p.name} landed on {tile.name} ({tile.type})", COLOR_TEXT_WHITE)

        if tile.type in ("PROPERTY", "TRANSIT", "UTILITY"):
            if tile.owner is None:
                # Unowned property
                if p.is_ai:
                    should_buy = self.ai_engine.should_buy_property(p, tile, self.board.tiles)
                    if should_buy:
                        p.deduct_cash(tile.price)
                        tile.owner = p
                        p.properties.append(tile.id)
                        sound_fx.play("buy")
                        self.log(f"{p.name} purchased {tile.name} for ${tile.price}!", COLOR_TEXT_GREEN)
                        self.turn_phase = PHASE_POST_ROLL
                        self._update_hud_buttons()
                    else:
                        self.log(f"{p.name} passed on buying {tile.name}. Starting auction!", COLOR_TEXT_MUTED)
                        self.start_auction(tile)
                else:
                    # Prompt Human
                    self.active_modal = BuyPropertyModal(
                        tile, p, self.font_main, self.font_bold,
                        on_buy=lambda: self._execute_human_buy(tile),
                        on_pass=lambda: self._execute_human_pass(tile),
                        on_auction=lambda: self.start_auction(tile)
                    )
            elif tile.owner.id != p.id:
                # Owned by another player -> Rent!
                if not tile.is_mortgaged:
                    dice_total = sum(self.last_dice)
                    rent = tile.calculate_rent(dice_total, self.board.tiles)
                    self.log(f"{p.name} owes ${rent} rent to {tile.owner.name} for {tile.name}!", COLOR_TEXT_AMBER)
                    self._transfer_rent(p, tile.owner, rent)
                else:
                    self.log(f"{tile.name} is mortgaged. No rent collected.", COLOR_TEXT_MUTED)
                if p.is_bankrupt or self.state == STATE_GAME_OVER:
                    return
                self.turn_phase = PHASE_POST_ROLL
                self._update_hud_buttons()
            else:
                self.log(f"{p.name} relaxes at their own property.", COLOR_TEXT_MUTED)
                self.turn_phase = PHASE_POST_ROLL
                self._update_hud_buttons()

        elif tile.type == "TAX":
            sound_fx.play("pay")
            tax_amt = tile.tax
            self.log(f"{p.name} paid civic tax of ${tax_amt}.", COLOR_TEXT_RED)
            self._deduct_with_debt_check(p, tax_amt, creditor=None)
            if p.is_bankrupt or self.state == STATE_GAME_OVER:
                return
            self.turn_phase = PHASE_POST_ROLL
            self._update_hud_buttons()

        elif tile.type == "FORTUNE":
            card = self.card_manager.draw_fortune()
            sound_fx.play("card")
            res = self.card_manager.apply_card_effect(card, p, self.players, self.board, self.log)
            if not p.is_ai:
                self.active_modal = CardModal(
                    res, is_fortune=True, font=self.font_main, title_font=self.font_bold,
                    on_dismiss=lambda: self._dismiss_card(res)
                )
            else:
                self._apply_post_card(res)

        elif tile.type == "CHEST":
            card = self.card_manager.draw_chest()
            sound_fx.play("card")
            res = self.card_manager.apply_card_effect(card, p, self.players, self.board, self.log)
            if not p.is_ai:
                self.active_modal = CardModal(
                    res, is_fortune=False, font=self.font_main, title_font=self.font_bold,
                    on_dismiss=lambda: self._dismiss_card(res)
                )
            else:
                self._apply_post_card(res)

        elif tile.type == "GOTO_JAIL":
            sound_fx.play("jail")
            p.in_jail = True
            p.jail_turns = 0
            p.doubles_count = 0
            p.position = 10
            p.target_position = 10
            p.anim_pos = 10.0
            self.log(f"{p.name} was detained and sent to Detention Center!", COLOR_TEXT_RED)
            self.turn_phase = PHASE_POST_ROLL
            self._update_hud_buttons()

        else: # GO, PARKING, JAIL (Visiting)
            self.turn_phase = PHASE_POST_ROLL
            self._update_hud_buttons()

    def _execute_human_buy(self, tile):
        p = self.current_player()
        p.deduct_cash(tile.price)
        tile.owner = p
        p.properties.append(tile.id)
        sound_fx.play("buy")
        self.log(f"You acquired {tile.name} for ${tile.price}!", COLOR_TEXT_GREEN)
        self.active_modal = None
        self.turn_phase = PHASE_POST_ROLL
        self._update_hud_buttons()

    def _execute_human_pass(self, tile):
        self.log(f"You passed on buying {tile.name}.", COLOR_TEXT_MUTED)
        self.active_modal = None
        self.turn_phase = PHASE_POST_ROLL
        self._update_hud_buttons()

    def start_auction(self, tile):
        self.active_modal = None
        self.log(f"Auction started for {tile.name} (List Price: ${tile.price})!", COLOR_TEXT_GOLD)
        sound_fx.play("gavel")
        self.active_modal = AuctionModal(
            tile=tile,
            players=self.players,
            active_player=self.current_player(),
            font=self.font_main,
            bold_font=self.font_bold,
            title_font=self.font_title,
            ai_engine=self.ai_engine,
            all_tiles=self.board.tiles,
            sound_fx=sound_fx,
            on_complete=lambda winner, winning_bid: self._finish_auction(tile, winner, winning_bid),
            fast_ai=self.fast_ai
        )

    def _finish_auction(self, tile, winner, winning_bid):
        self.active_modal = None
        if winner:
            winner.deduct_cash(winning_bid)
            tile.owner = winner
            winner.properties.append(tile.id)
            sound_fx.play("buy")
            self.log(f"{winner.name} won {tile.name} at auction for ${winning_bid}!", COLOR_TEXT_GREEN)
        else:
            self.log(f"Auction ended without bids. {tile.name} remains unsold.", COLOR_TEXT_MUTED)
        self.turn_phase = PHASE_POST_ROLL
        self._update_hud_buttons()

    def _dismiss_card(self, card_res):
        self.active_modal = None
        self._apply_post_card(card_res)

    def _apply_post_card(self, res):
        p = self.current_player()
        if p.is_bankrupt or self.state == STATE_GAME_OVER:
            return

        if res.get("moved") and not res.get("went_to_jail"):
            p.position = res["target_pos"]
            p.target_position = p.position
            p.anim_pos = float(p.position)
            # Handle tile landed on after card movement
            new_tile = self.board.tiles[p.position]
            self.handle_tile_action(new_tile)
            return

        if p.cash < 0:
            deficit = -p.cash
            p.cash = 0
            self._deduct_with_debt_check(p, deficit, creditor=None)
            if p.is_bankrupt or self.state == STATE_GAME_OVER:
                return

        self.turn_phase = PHASE_POST_ROLL
        self._update_hud_buttons()

    def _transfer_rent(self, debtor, creditor, amount):
        sound_fx.play("pay")
        debtor.rent_paid_total += amount
        creditor.rent_collected_total += amount
        if debtor.cash >= amount:
            debtor.deduct_cash(amount)
            creditor.add_cash(amount)
        else:
            self._deduct_with_debt_check(debtor, amount, creditor)

    def _deduct_with_debt_check(self, player, amount, creditor=None):
        if player.cash >= amount:
            player.deduct_cash(amount)
            if creditor:
                creditor.add_cash(amount)
            return

        # Player cannot afford directly - must mortgage or sell
        if player.is_ai:
            saved = self.ai_engine.resolve_debt(player, amount, self.board.tiles)
            if saved and player.cash >= amount:
                player.deduct_cash(amount)
                if creditor:
                    creditor.add_cash(amount)
            else:
                self._declare_bankruptcy(player, creditor)
        else:
            # Human debt
            max_liquidity = player.cash
            for tid in player.properties:
                t = self.board.tiles[tid]
                if not t.is_mortgaged:
                    max_liquidity += t.mortgage_value
                if hasattr(t, 'houses') and t.houses > 0:
                    max_liquidity += (t.houses * t.house_cost) // 2

            cred_name = creditor.name if creditor else "the Bank"
            if max_liquidity < amount:
                self.log(f"{player.name} cannot raise enough cash to pay ${amount} to {cred_name}!", COLOR_TEXT_RED)
                self._declare_bankruptcy(player, creditor)
            else:
                self.log(f"Insufficient cash! Please mortgage properties or sell houses to pay ${amount} to {cred_name}.", COLOR_TEXT_RED)
                self.open_debt_modal(player, amount, creditor)

    def open_debt_modal(self, player, amount, creditor):
        self.active_modal = MortgageModal(
            player, self.board.tiles, self.font_main, self.font_bold,
            on_close=lambda: self._handle_debt_modal_close(player, amount, creditor),
            on_toggle_callback=self._handle_toggle_mortgage,
            debt_amount=amount,
            creditor=creditor,
            on_pay_debt=lambda: self._handle_pay_debt(player, amount, creditor),
            on_declare_bankruptcy=lambda: self._handle_manual_bankruptcy(player, creditor),
            on_sell_house=self._handle_sell_house
        )

    def _handle_pay_debt(self, player, amount, creditor):
        if player.cash >= amount:
            player.deduct_cash(amount)
            if creditor:
                creditor.add_cash(amount)
            self.active_modal = None
            cred_name = creditor.name if creditor else "the Bank"
            self.log(f"{player.name} paid ${amount} debt to {cred_name}.", COLOR_TEXT_GREEN)
            self.turn_phase = PHASE_POST_ROLL
            self._update_hud_buttons()

    def _handle_manual_bankruptcy(self, player, creditor):
        self.active_modal = None
        self._declare_bankruptcy(player, creditor)

    def _handle_debt_modal_close(self, player, amount, creditor):
        if player.cash >= amount:
            self._handle_pay_debt(player, amount, creditor)
        else:
            self.active_modal = None
            self._declare_bankruptcy(player, creditor)

    def _declare_bankruptcy(self, bankrupt_player, creditor):
        bankrupt_player.is_bankrupt = True
        bankrupt_player.bankrupt_to = creditor.id if creditor else None
        bankrupt_player.doubles_count = 0
        bankrupt_player.is_moving = False
        bankrupt_player.position = -1
        bankrupt_player.target_position = -1
        bankrupt_player.anim_pos = -1.0
        sound_fx.play("bankrupt")

        cred_name = creditor.name if creditor else "the Bank"
        self.log(f"{bankrupt_player.name} declared BANKRUPTCY to {cred_name} and is eliminated!", COLOR_TEXT_RED)

        # 1. Transfer remaining cash
        if creditor:
            if bankrupt_player.cash > 0:
                creditor.add_cash(bankrupt_player.cash)
                self.log(f"{creditor.name} collected remaining ${bankrupt_player.cash:,} from {bankrupt_player.name}.", COLOR_TEXT_GREEN)
        bankrupt_player.cash = 0

        # 2. Transfer Get Out of Jail Free cards
        if creditor:
            if bankrupt_player.jail_free_cards > 0:
                creditor.jail_free_cards += bankrupt_player.jail_free_cards
                self.log(f"{creditor.name} received {bankrupt_player.jail_free_cards} Get Out of Detention pass(es) from {bankrupt_player.name}.", COLOR_TEXT_GREEN)
        else:
            for _ in range(bankrupt_player.jail_free_cards):
                self.card_manager.fortune_deck.return_jail_card()
        bankrupt_player.jail_free_cards = 0

        # 3. Transfer property titles and assets
        transferred_count = len(bankrupt_player.properties)
        for tid in list(bankrupt_player.properties):
            tile = self.board.tiles[tid]
            if creditor:
                tile.owner = creditor
                if tid not in creditor.properties:
                    creditor.properties.append(tid)
            else:
                tile.owner = None
                tile.houses = 0
                tile.is_mortgaged = False
        bankrupt_player.properties.clear()

        if transferred_count > 0:
            if creditor:
                self.log(f"All {transferred_count} property title(s) transferred to {creditor.name}.", COLOR_TEXT_GOLD)
            else:
                self.log(f"All {transferred_count} property title(s) surrendered to the Bank.", COLOR_TEXT_GOLD)

        # Close any active modal
        self.active_modal = None

        # 4. Check victory condition
        active_remaining = [p for p in self.players if not p.is_bankrupt]
        if len(active_remaining) <= 1:
            self.state = STATE_GAME_OVER
            return

        # 5. If bankrupt player was current player, advance turn
        if bankrupt_player.id == self.current_player().id:
            self.on_end_turn()

    def on_end_turn(self):
        self.active_modal = None
        p = self.current_player()
        p.doubles_count = 0
        self.btn_end.disabled = True

        # Check victory condition
        active_remaining = [p for p in self.players if not p.is_bankrupt]
        if len(active_remaining) <= 1:
            self.state = STATE_GAME_OVER
            return

        # Advance to next active player
        while True:
            self.current_player_idx = (self.current_player_idx + 1) % len(self.players)
            if self.current_player_idx == 0:
                self.round_number += 1
            if not self.players[self.current_player_idx].is_bankrupt:
                break

        nxt = self.current_player()
        self.turn_phase = PHASE_READY
        self.log(f"--- Round {self.round_number}: {nxt.name}'s turn ---", COLOR_TEXT_GOLD)
        self._update_hud_buttons()

    def _update_hud_buttons(self):
        p = self.current_player()
        if p.is_bankrupt:
            self.btn_roll.disabled = True
            self.btn_end.disabled = True
            return

        is_human = not p.is_ai

        if self.turn_phase == PHASE_READY:
            self.btn_roll.disabled = not is_human
            self.btn_end.disabled = True
            # Update roll button text if in jail
            if p.in_jail:
                self.btn_roll.text = "Roll/Pay $50"
            else:
                self.btn_roll.text = "Roll Dice"

        elif self.turn_phase == PHASE_POST_ROLL:
            self.btn_roll.disabled = True
            self.btn_end.disabled = not is_human
            # Check if rolled doubles -> can roll again!
            d1, d2 = self.last_dice
            can_roll_again = (d1 == d2 and not p.in_jail and 0 < p.doubles_count < 3 and not p.is_bankrupt)
            if can_roll_again:
                self.btn_roll.disabled = not is_human
                self.btn_roll.text = "Roll Again"
                self.btn_end.disabled = True
            else:
                self.btn_roll.text = "Roll Dice"

    # Modal Openers
    def open_build_modal(self):
        p = self.current_player()
        if p.is_ai or p.is_bankrupt:
            return
        self.active_modal = BuildModal(
            p, self.board.tiles, self.font_main, self.font_bold,
            on_close=lambda: setattr(self, 'active_modal', None),
            on_build_callback=self._handle_build_house,
            on_sell_callback=self._handle_sell_house
        )

    def _handle_build_house(self, tile):
        p = self.current_player()
        if p.cash >= tile.house_cost and tile.houses < 5:
            p.deduct_cash(tile.house_cost)
            tile.houses += 1
            sound_fx.play("build")
            tier_name = "Skyscraper" if tile.houses == 5 else f"{tile.houses} houses"
            self.log(f"Upgraded {tile.name} to {tier_name} (-${tile.house_cost}).", COLOR_TEXT_GREEN)

    def _handle_sell_house(self, tile):
        p = self.current_player()
        if tile.houses > 0:
            refund = tile.house_cost // 2
            tile.houses -= 1
            p.add_cash(refund)
            sound_fx.play("buy")
            self.log(f"Sold building on {tile.name} (+${refund}).", COLOR_TEXT_MUTED)

    def open_mortgage_modal(self):
        p = self.current_player()
        if p.is_ai or p.is_bankrupt:
            return
        self.active_modal = MortgageModal(
            p, self.board.tiles, self.font_main, self.font_bold,
            on_close=lambda: setattr(self, 'active_modal', None),
            on_toggle_callback=self._handle_toggle_mortgage,
            on_sell_house=self._handle_sell_house
        )

    def _handle_toggle_mortgage(self, tile):
        p = self.current_player()
        if tile.is_mortgaged:
            cost = int(tile.mortgage_value * 1.1)
            if p.cash >= cost:
                p.deduct_cash(cost)
                tile.is_mortgaged = False
                sound_fx.play("buy")
                self.log(f"Unmortgaged {tile.name} for ${cost}.", COLOR_TEXT_GREEN)
        else:
            tile.is_mortgaged = True
            p.add_cash(tile.mortgage_value)
            sound_fx.play("pay")
            self.log(f"Mortgaged {tile.name} for +${tile.mortgage_value}.", COLOR_TEXT_AMBER)

    def open_trade_modal(self):
        p = self.current_player()
        if p.is_ai or p.is_bankrupt:
            return
        self.active_modal = TradeModal(
            p, self.players, self.board.tiles, self.font_main, self.font_bold, self.ai_engine,
            on_close=lambda: setattr(self, 'active_modal', None),
            on_complete=self._handle_execute_trade
        )

    def _handle_execute_trade(self, opp, off_props, off_cash, req_props, req_cash):
        p = self.current_player()
        # Transfer cash
        p.deduct_cash(off_cash)
        opp.add_cash(off_cash)
        opp.deduct_cash(req_cash)
        p.add_cash(req_cash)

        # Transfer offered properties
        for tid in off_props:
            t = self.board.tiles[tid]
            p.properties.remove(tid)
            opp.properties.append(tid)
            t.owner = opp

        # Transfer requested properties
        for tid in req_props:
            t = self.board.tiles[tid]
            opp.properties.remove(tid)
            p.properties.append(tid)
            t.owner = p

        sound_fx.play("trade")
        self.log(f"Trade successfully finalized between {p.name} and {opp.name}!", COLOR_TEXT_GREEN)
        self.active_modal = None

    def save_game(self):
        success, msg = SaveManager.save_game(
            SAVE_FILE, self.round_number, self.current_player_idx, self.players,
            self.board, self.card_manager, self.event_log.messages
        )
        self.log(msg, COLOR_TEXT_GREEN if success else COLOR_TEXT_RED)

    def load_game(self):
        if not os.path.exists(SAVE_FILE):
            self.log("No save file found.", COLOR_TEXT_RED)
            return False
        success, result = SaveManager.load_game(SAVE_FILE, self.board, self.card_manager)
        if success:
            loaded_players, round_num, c_idx, msgs = result
            self.players = loaded_players
            self.num_players = len(self.players)
            self.round_number = round_num
            self.current_player_idx = min(c_idx, len(self.players) - 1)
            self.event_log.messages = msgs
            self.turn_phase = PHASE_READY
            self.active_modal = None
            self.hovered_tile = None
            self.state = STATE_PLAYING
            self._update_hud_buttons()
            sound_fx.play("click")
            self.log(f"Match loaded! Round {self.round_number}, {self.current_player().name}'s turn.", COLOR_TEXT_GOLD)
            return True
        else:
            self.log(f"Load failed: {result}", COLOR_TEXT_RED)
            return False

    # AI Turn Simulation
    def update_ai(self):
        p = self.current_player()
        if p.is_bankrupt:
            self.on_end_turn()
            return

        if not p.is_ai or self.turn_phase not in (PHASE_READY, PHASE_POST_ROLL) or self.active_modal:
            return

        delay = 8 if self.fast_ai else 35
        self.ai_step_delay += 1
        if self.ai_step_delay < delay:
            return
        self.ai_step_delay = 0

        if self.turn_phase == PHASE_READY:
            # Check jail choices
            if p.in_jail:
                choice = self.ai_engine.should_pay_jail_fee(p, self.board.tiles)
                if choice == "CARD" and p.jail_free_cards > 0:
                    p.jail_free_cards -= 1
                    p.in_jail = False
                    p.jail_turns = 0
                    self.card_manager.fortune_deck.return_jail_card()
                    self.log(f"{p.name} used Get Out of Detention Free pass!", COLOR_TEXT_GREEN)
                elif choice == "PAY" and p.cash >= 50:
                    p.deduct_cash(50)
                    p.in_jail = False
                    p.jail_turns = 0
                    self.log(f"{p.name} paid $50 fine to exit Detention early.", COLOR_TEXT_MUTED)

            self.on_roll_dice()

        elif self.turn_phase == PHASE_POST_ROLL:
            # Check if rolling again on doubles
            d1, d2 = self.last_dice
            can_roll_again = (d1 == d2 and not p.in_jail and 0 < p.doubles_count < 3 and not p.is_bankrupt)
            if can_roll_again:
                self.on_roll_dice()
                return

            if p.is_bankrupt:
                self.on_end_turn()
                return

            # Plan house upgrades
            builds = self.ai_engine.plan_buildings(p, self.board.tiles)
            for tid in builds:
                t = self.board.tiles[tid]
                if p.cash >= t.house_cost:
                    p.deduct_cash(t.house_cost)
                    t.houses += 1
                    sound_fx.play("build")
                    self.log(f"{p.name} developed {t.name} (level {t.houses}).", COLOR_TEXT_GREEN)

            self.on_end_turn()

    # Movement Animation Loop
    def update_movement(self):
        for p in self.players:
            if p.is_moving:
                step_speed = 0.4 if self.fast_ai else 0.15
                dist = (p.target_position - p.anim_pos) % 40
                if dist < step_speed or dist > (40 - step_speed):
                    p.anim_pos = float(p.target_position)
                    if p.id == self.current_player().id and self.turn_phase == PHASE_MOVING:
                        self.finish_movement()
                else:
                    p.anim_pos = (p.anim_pos + step_speed) % 40

    # Main Loop
    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(FPS)
        pygame.quit()
        sys.exit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            # Modal handles events first if active
            if self.active_modal:
                self.active_modal.handle_event(event)
                continue

            if self.state == STATE_PLAYING:
                # Hover detection over board tiles
                if event.type == pygame.MOUSEMOTION:
                    self.hovered_tile = self.board.get_tile_at(event.pos)

                # Buttons
                self.btn_menu.handle_event(event)
                self.btn_roll.handle_event(event)
                self.btn_end.handle_event(event)
                self.btn_build.handle_event(event)
                self.btn_trade.handle_event(event)
                self.btn_mortgage.handle_event(event)
                self.btn_sound.handle_event(event)
                self.btn_speed.handle_event(event)
                self.btn_save.handle_event(event)
                self.btn_load.handle_event(event)
                self.event_log.handle_event(event)

            elif self.state == STATE_TITLE:
                self._handle_title_events(event)

            elif self.state == STATE_SETUP:
                self._handle_setup_events(event)

            elif self.state == STATE_GAME_OVER:
                self._handle_game_over_events(event)

    def update(self):
        if self.active_modal and hasattr(self.active_modal, "update"):
            self.active_modal.update()

        if self.state == STATE_PLAYING:
            self.update_movement()
            self.update_ai()

    def render(self):
        self.screen.fill(COLOR_BG)

        if self.state == STATE_PLAYING:
            self._render_playing()
        elif self.state == STATE_TITLE:
            self._render_title()
        elif self.state == STATE_SETUP:
            self._render_setup()
        elif self.state == STATE_GAME_OVER:
            self._render_game_over()

        # Render Active Modal
        if self.active_modal:
            self.active_modal.draw(self.screen)

        pygame.display.flip()

    def _render_playing(self):
        # 1. Draw Board & Center
        self.board.draw(self.screen, hovered_tile=self.hovered_tile)

        # 2. Draw Player Tokens on Board
        for p in self.players:
            if not p.is_bankrupt and p.position >= 0:
                tx, ty = self.board.get_interpolated_pos(p.anim_pos, p.id, len(self.players))
                p.draw_token(self.screen, tx, ty, radius=12)

        # 3. Top HUD / Round Banner
        curr = self.current_player()
        turn_str = f"Round {self.round_number}  |  {curr.name}'s Turn"
        if not curr.is_ai:
            turn_str += " (You)"
        d1, d2 = self.last_dice
        if self.turn_phase == PHASE_POST_ROLL and d1 == d2 and not curr.in_jail and 0 < curr.doubles_count < 3:
            turn_str += "  [DOUBLES! Roll Again]"
        t_surf = self.font_header.render(turn_str, True, COLOR_TEXT_GOLD)
        self.screen.blit(t_surf, (780, 26))

        # Top Bar buttons
        self.btn_menu.draw(self.screen)
        self.btn_sound.draw(self.screen)
        self.btn_speed.draw(self.screen)
        self.btn_save.draw(self.screen)
        self.btn_load.draw(self.screen)

        # 4. Action HUD & Dice
        self.dice_widget.draw(self.screen)
        self.btn_roll.draw(self.screen)
        self.btn_end.draw(self.screen)
        self.btn_build.draw(self.screen)
        self.btn_trade.draw(self.screen)
        self.btn_mortgage.draw(self.screen)

        # 5. Player Dashboard & Event Log
        self.player_panel.draw(self.screen, self.players, self.current_player_idx)
        self.event_log.draw(self.screen)

        # 6. Hover Deed Inspection Preview
        if self.hovered_tile and not self.active_modal:
            # Place popup card smoothly near board center
            self.deed_view.draw(self.screen, self.hovered_tile, 250, 190, width=260, height=350)

    # Title Screen
    def _render_title(self):
        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2

        # Decorative City Skyline Silhouettes in background
        for bx, bw, bh in [
            (100, 70, 220), (190, 90, 310), (300, 110, 260), (430, 80, 350),
            (SCREEN_WIDTH - 500, 95, 290), (SCREEN_WIDTH - 380, 80, 360),
            (SCREEN_WIDTH - 280, 100, 240), (SCREEN_WIDTH - 160, 90, 300)
        ]:
            b_rect = pygame.Rect(bx, SCREEN_HEIGHT - bh, bw, bh)
            pygame.draw.rect(self.screen, (22, 30, 48), b_rect)
            # Glowing skyscraper windows
            for wy in range(b_rect.top + 20, b_rect.bottom - 40, 28):
                for wx in range(b_rect.left + 14, b_rect.right - 14, 20):
                    if (wx + wy) % 7 != 0:
                        pygame.draw.rect(self.screen, (34, 46, 74), (wx, wy, 8, 12), border_radius=1)

        # Central Glassmorphism Card
        panel_w, panel_h = 620, 500
        p_rect = pygame.Rect(cx - panel_w // 2, cy - panel_h // 2 + 10, panel_w, panel_h)
        pygame.draw.rect(self.screen, (20, 27, 45), p_rect, border_radius=16)
        pygame.draw.rect(self.screen, (51, 65, 85), p_rect, width=2, border_radius=16)

        # Title Branding
        t1 = self.font_title.render("METRO TYCOON", True, COLOR_TEXT_GOLD)
        self.screen.blit(t1, t1.get_rect(center=(cx, p_rect.top + 50)))

        sub = self.font_header.render("URBAN PROPERTY EMPIRE SIMULATION", True, COLOR_TEXT_MUTED)
        self.screen.blit(sub, sub.get_rect(center=(cx, p_rect.top + 88)))

        # Feature Badges
        badges = [
            "2 to 6 Players", "Smart AI Bots", "Interactive Trading",
            "Full 40-Tile Board", "Real Estate Upgrades", "Save & Resume"
        ]
        start_bx = cx - 240
        b_y = p_rect.top + 125
        for i, badge in enumerate(badges):
            col_idx = i % 2
            row_idx = i // 2
            bx = start_bx + col_idx * 250
            by = b_y + row_idx * 28
            pygame.draw.circle(self.screen, COLOR_TEXT_GREEN, (bx - 10, by + 8), 4)
            b_surf = self.font_main.render(badge, True, COLOR_TEXT_WHITE)
            self.screen.blit(b_surf, (bx + 2, by))

        # Menu Buttons
        btn_w, btn_h = 280, 46
        b_quick = pygame.Rect(cx - btn_w // 2, p_rect.top + 235, btn_w, btn_h)
        b_custom = pygame.Rect(cx - btn_w // 2, p_rect.top + 295, btn_w, btn_h)
        b_load = pygame.Rect(cx - btn_w // 2, p_rect.top + 355, btn_w, btn_h)
        b_exit = pygame.Rect(cx - btn_w // 2, p_rect.top + 415, btn_w, btn_h)

        pygame.draw.rect(self.screen, COLOR_ACCENT_GREEN, b_quick, border_radius=8)
        q_surf = self.font_bold.render("Quick Play (4 Players)", True, COLOR_TEXT_WHITE)
        self.screen.blit(q_surf, q_surf.get_rect(center=b_quick.center))

        pygame.draw.rect(self.screen, COLOR_ACCENT_BLUE, b_custom, border_radius=8)
        c_surf = self.font_bold.render("Custom Match (2-6 Players)", True, COLOR_TEXT_WHITE)
        self.screen.blit(c_surf, c_surf.get_rect(center=b_custom.center))

        has_save = os.path.exists(SAVE_FILE)
        pygame.draw.rect(self.screen, (51, 65, 85) if has_save else (30, 41, 59), b_load, border_radius=8)
        l_col = COLOR_TEXT_WHITE if has_save else (100, 116, 139)
        l_surf = self.font_bold.render("Resume Saved Match", True, l_col)
        self.screen.blit(l_surf, l_surf.get_rect(center=b_load.center))

        pygame.draw.rect(self.screen, (39, 49, 70), b_exit, border_radius=8)
        e_surf = self.font_bold.render("Exit Game", True, COLOR_TEXT_MUTED)
        self.screen.blit(e_surf, e_surf.get_rect(center=b_exit.center))

    def _handle_title_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            cx = SCREEN_WIDTH // 2
            cy = SCREEN_HEIGHT // 2
            panel_h = 500
            p_top = cy - panel_h // 2 + 10

            btn_w, btn_h = 280, 46
            b_quick = pygame.Rect(cx - btn_w // 2, p_top + 235, btn_w, btn_h)
            b_custom = pygame.Rect(cx - btn_w // 2, p_top + 295, btn_w, btn_h)
            b_load = pygame.Rect(cx - btn_w // 2, p_top + 355, btn_w, btn_h)
            b_exit = pygame.Rect(cx - btn_w // 2, p_top + 415, btn_w, btn_h)

            if b_quick.collidepoint(event.pos):
                sound_fx.play("click")
                self.num_players = 4
                self.start_game()
            elif b_custom.collidepoint(event.pos):
                sound_fx.play("click")
                self.state = STATE_SETUP
            elif b_load.collidepoint(event.pos) and os.path.exists(SAVE_FILE):
                sound_fx.play("click")
                self.load_game()
            elif b_exit.collidepoint(event.pos):
                sound_fx.play("click")
                self.running = False

    # Setup Screen
    def _render_setup(self):
        cx = SCREEN_WIDTH // 2
        
        t_surf = self.font_title.render("MATCH SETUP", True, COLOR_TEXT_GOLD)
        self.screen.blit(t_surf, t_surf.get_rect(center=(cx, 60)))

        # Player Count Selector
        cnt_lbl = self.font_bold.render(f"Number of Players: {self.num_players}", True, COLOR_TEXT_WHITE)
        self.screen.blit(cnt_lbl, (cx - 160, 110))

        for n in range(2, 7):
            bx = cx - 160 + (n - 2) * 65
            r = pygame.Rect(bx, 140, 50, 36)
            col = COLOR_ACCENT_BLUE if n == self.num_players else (51, 65, 85)
            pygame.draw.rect(self.screen, col, r, border_radius=6)
            n_txt = self.font_bold.render(str(n), True, COLOR_TEXT_WHITE)
            self.screen.blit(n_txt, n_txt.get_rect(center=r.center))

        # Players List Preview
        card_w = 780
        start_y = 195
        for i in range(self.num_players):
            cfg = self.setup_configs[i]
            r = pygame.Rect(cx - card_w // 2, start_y + i * 65, card_w, 54)
            pygame.draw.rect(self.screen, (30, 41, 59), r, border_radius=8)
            pygame.draw.rect(self.screen, (51, 65, 85), r, width=1, border_radius=8)

            # Player Token preview circle
            p_col = PLAYER_COLORS[i % len(PLAYER_COLORS)]
            pygame.draw.circle(self.screen, p_col, (r.x + 28, r.centery), 14)
            
            # Name
            n_surf = self.font_bold.render(cfg["name"], True, COLOR_TEXT_WHITE)
            self.screen.blit(n_surf, (r.x + 52, r.centery - 10))

            # Token Cycle button
            tok_name = PLAYER_TOKEN_NAMES[cfg["token"] % len(PLAYER_TOKEN_NAMES)]
            tok_box = pygame.Rect(r.x + 200, r.centery - 14, 130, 28)
            pygame.draw.rect(self.screen, (51, 65, 85), tok_box, border_radius=4)
            tok_s = self.font_main.render(f"Token: {tok_name}", True, COLOR_TEXT_WHITE)
            self.screen.blit(tok_s, tok_s.get_rect(center=tok_box.center))

            # AI / Human toggle
            type_str = "AI Bot" if cfg["is_ai"] else "Human"
            type_col = COLOR_TEXT_GOLD if not cfg["is_ai"] else COLOR_TEXT_MUTED
            t_box = pygame.Rect(r.x + 345, r.centery - 14, 90, 28)
            pygame.draw.rect(self.screen, (51, 65, 85), t_box, border_radius=4)
            typ_s = self.font_main.render(type_str, True, type_col)
            self.screen.blit(typ_s, typ_s.get_rect(center=t_box.center))

            # Personality selector if AI
            if cfg["is_ai"]:
                pers_box = pygame.Rect(r.x + 450, r.centery - 14, 150, 28)
                pygame.draw.rect(self.screen, (51, 65, 85), pers_box, border_radius=4)
                pers_s = self.font_main.render(f"Style: {cfg['personality']}", True, COLOR_TEXT_WHITE)
                self.screen.blit(pers_s, pers_s.get_rect(center=pers_box.center))

        # Bottom Buttons: Back to Menu & Start Match
        b_back = pygame.Rect(cx - 210, SCREEN_HEIGHT - 80, 180, 46)
        pygame.draw.rect(self.screen, (51, 65, 85), b_back, border_radius=8)
        bk_txt = self.font_bold.render("Back to Menu", True, COLOR_TEXT_WHITE)
        self.screen.blit(bk_txt, bk_txt.get_rect(center=b_back.center))

        b_start = pygame.Rect(cx + 30, SCREEN_HEIGHT - 80, 180, 46)
        pygame.draw.rect(self.screen, COLOR_ACCENT_GREEN, b_start, border_radius=8)
        s_txt = self.font_bold.render("Start Match", True, COLOR_TEXT_WHITE)
        self.screen.blit(s_txt, s_txt.get_rect(center=b_start.center))

    def _handle_setup_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            cx = SCREEN_WIDTH // 2
            mx, my = event.pos

            # Check player count selection
            for n in range(2, 7):
                bx = cx - 160 + (n - 2) * 65
                r = pygame.Rect(bx, 140, 50, 36)
                if r.collidepoint(mx, my):
                    sound_fx.play("click")
                    self.num_players = n
                    return

            # Check AI / Human toggle, token cycle, and personality clicks
            card_w = 780
            start_y = 195
            for i in range(self.num_players):
                r = pygame.Rect(cx - card_w // 2, start_y + i * 65, card_w, 54)
                tok_box = pygame.Rect(r.x + 200, r.centery - 14, 130, 28)
                t_box = pygame.Rect(r.x + 345, r.centery - 14, 90, 28)
                pers_box = pygame.Rect(r.x + 450, r.centery - 14, 150, 28)

                if tok_box.collidepoint(mx, my):
                    sound_fx.play("click")
                    self.setup_configs[i]["token"] = (self.setup_configs[i]["token"] + 1) % len(PLAYER_TOKEN_NAMES)
                    return

                if t_box.collidepoint(mx, my):
                    sound_fx.play("click")
                    self.setup_configs[i]["is_ai"] = not self.setup_configs[i]["is_ai"]
                    return

                if self.setup_configs[i]["is_ai"] and pers_box.collidepoint(mx, my):
                    sound_fx.play("click")
                    plist = list(AI_PERSONALITIES.keys())
                    cur_idx = plist.index(self.setup_configs[i]["personality"])
                    nxt_idx = (cur_idx + 1) % len(plist)
                    self.setup_configs[i]["personality"] = plist[nxt_idx]
                    return

            # Back button
            b_back = pygame.Rect(cx - 210, SCREEN_HEIGHT - 80, 180, 46)
            if b_back.collidepoint(mx, my):
                sound_fx.play("click")
                self.state = STATE_TITLE
                return

            # Start Game button
            b_start = pygame.Rect(cx + 30, SCREEN_HEIGHT - 80, 180, 46)
            if b_start.collidepoint(mx, my):
                sound_fx.play("click")
                self.start_game()

    # Game Over Screen
    def _render_game_over(self):
        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2

        active = [p for p in self.players if not p.is_bankrupt]
        winner = active[0] if active else self.players[0]

        w_surf = self.font_title.render("VICTORY ACHIEVED!", True, COLOR_TEXT_GOLD)
        self.screen.blit(w_surf, w_surf.get_rect(center=(cx, cy - 120)))

        name_surf = self.font_header.render(f"{winner.name} is the Supreme Metro Tycoon!", True, COLOR_TEXT_WHITE)
        self.screen.blit(name_surf, name_surf.get_rect(center=(cx, cy - 70)))

        stats_y = cy - 20
        stats = [
            f"Final Cash Balance: ${winner.cash:,}",
            f"Total Net Worth: ${winner.get_net_worth(self.board.tiles):,}",
            f"Properties Owned: {len(winner.properties)}",
            f"Total Rent Collected: ${winner.rent_collected_total:,}"
        ]
        for s in stats:
            s_surf = self.font_main.render(s, True, COLOR_TEXT_MUTED)
            self.screen.blit(s_surf, s_surf.get_rect(center=(cx, stats_y)))
            stats_y += 24

        b_again = pygame.Rect(cx - 110, cy + 110, 220, 46)
        pygame.draw.rect(self.screen, COLOR_ACCENT_GREEN, b_again, border_radius=8)
        a_txt = self.font_bold.render("Play Again", True, COLOR_TEXT_WHITE)
        self.screen.blit(a_txt, a_txt.get_rect(center=b_again.center))

    def _handle_game_over_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            cx = SCREEN_WIDTH // 2
            cy = SCREEN_HEIGHT // 2
            b_again = pygame.Rect(cx - 110, cy + 110, 220, 46)
            if b_again.collidepoint(event.pos):
                sound_fx.play("click")
                self.state = STATE_SETUP


if __name__ == "__main__":
    game = MetroTycoonGame()
    game.run()

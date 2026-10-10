import os
import sys
sys.path.insert(0, os.path.abspath("."))

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
pygame.init()
pygame.font.init()

from main import MetroTycoonGame
from modals import BuildModal, MortgageModal

def capture_endgame_modals():
    os.makedirs("screenshots", exist_ok=True)
    game = MetroTycoonGame()
    game.start_game()

    p = game.players[0]
    p.cash = 3597

    # Give Player 1 all 22 street properties (like user's screenshot)
    for t in game.board.tiles:
        if t.type == "PROPERTY":
            p.properties.append(t.id)
            t.owner = p

    # Put 4 houses on Wallgate St, Penthouse Rdg, Exchange Plz, Ticker Row, Apex Pinnacle (matching user's screenshot)
    for tid in [24, 39, 23, 21, 37]:
        game.board.tiles[tid].houses = 4

    # 1. Capture MortgageModal (Top)
    game.active_modal = MortgageModal(
        p, game.board.tiles, game.font_main, game.font_bold,
        on_close=lambda: None,
        on_toggle_callback=game._handle_toggle_mortgage,
        on_sell_house=game._handle_sell_house
    )
    game.render()
    pygame.image.save(game.screen, "screenshots/mortgage_modal_top.png")
    print("Saved screenshots/mortgage_modal_top.png")

    # 2. Capture MortgageModal (Scrolled Down)
    game.active_modal.scroll_y = game.active_modal._get_max_scroll()
    game.active_modal._update_button_positions()
    game.render()
    pygame.image.save(game.screen, "screenshots/mortgage_modal_scrolled.png")
    print("Saved screenshots/mortgage_modal_scrolled.png")

    # 3. Capture BuildModal
    game.active_modal = BuildModal(
        p, game.board.tiles, game.font_main, game.font_bold,
        on_close=lambda: None,
        on_build_callback=game._handle_build_house,
        on_sell_callback=game._handle_sell_house
    )
    game.render()
    pygame.image.save(game.screen, "screenshots/build_modal_top.png")
    print("Saved screenshots/build_modal_top.png")

    # 4. Capture BuildModal (Scrolled Down)
    game.active_modal.scroll_y = game.active_modal._get_max_scroll()
    game.active_modal._update_button_positions()
    game.render()
    pygame.image.save(game.screen, "screenshots/build_modal_scrolled.png")
    print("Saved screenshots/build_modal_scrolled.png")

    print("All endgame modal screenshots captured!")

if __name__ == "__main__":
    capture_endgame_modals()

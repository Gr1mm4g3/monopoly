"""
Renders and captures screenshots of title, setup, and in-game match with 6 players
to verify visual presentation and layout correctness.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Run headlessly for automated snapshot capture
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
from main import MetroTycoonGame, STATE_TITLE, STATE_SETUP, STATE_PLAYING

def capture_screenshots():
    os.makedirs("screenshots", exist_ok=True)
    game = MetroTycoonGame()

    # 1. Capture Title Screen
    game.state = STATE_TITLE
    game.render()
    pygame.image.save(game.screen, "screenshots/01_title_screen.png")
    print("Saved 01_title_screen.png")

    # 2. Capture Setup Screen with 6 players
    game.state = STATE_SETUP
    game.num_players = 6
    game.render()
    pygame.image.save(game.screen, "screenshots/02_setup_screen.png")
    print("Saved 02_setup_screen.png")

    # 3. Capture In-Game Screen with 6 players
    game.start_game()
    # Advance a few turns so properties get purchased and dice get rolled
    for _ in range(8):
        game.on_roll_dice()
        game.finish_movement()
        game.on_end_turn()

    # Set hovered tile to show deed card
    game.hovered_tile = game.board.tiles[26] # Silicon Drive
    game.render()
    pygame.image.save(game.screen, "screenshots/03_gameplay_board.png")
    print("Saved 03_gameplay_board.png")

    # 4. Capture Auction Modal in action
    game.start_auction(game.board.tiles[26])
    game.active_modal.current_bid = 140
    game.active_modal.high_bidder = game.players[1]
    game.render()
    pygame.image.save(game.screen, "screenshots/04_auction_modal.png")
    print("Saved 04_auction_modal.png")

    print("All snapshots captured successfully!")

if __name__ == "__main__":
    capture_screenshots()

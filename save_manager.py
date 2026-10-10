"""
Save and Load manager for Metro Tycoon.
Serializes and deserializes complete game state to and from JSON format.
"""

import json
import os

SAVE_FILE = "savegame.json"

class SaveManager:
    @staticmethod
    def save_game(filepath, round_number, current_player_idx, players, board, card_manager, event_messages):
        """Exports the complete game state to JSON."""
        try:
            state = {
                "version": 1,
                "round_number": round_number,
                "current_player_idx": current_player_idx,
                "players": [p.to_dict() for p in players],
                "tiles": [t.to_dict() for t in board.tiles],
                "fortune_deck": card_manager.fortune_deck.to_dict(),
                "chest_deck": card_manager.chest_deck.to_dict(),
                "event_messages": [(msg, list(col)) for msg, col in event_messages[-50:]]
            }
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2)
            return True, "Game successfully saved!"
        except Exception as e:
            return False, f"Save failed: {e}"

    @staticmethod
    def load_game(filepath, board, card_manager):
        """Loads and applies a saved game state, reconstructing full player and board state."""
        if not os.path.exists(filepath):
            return False, "Save file not found."
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                state = json.load(f)

            round_number = state.get("round_number", 1)
            current_player_idx = state.get("current_player_idx", 0)

            from player import Player
            # Reconstruct all Player objects from saved data
            players = []
            for p_data in state.get("players", []):
                p = Player(
                    player_id=p_data["id"],
                    name=p_data.get("name", f"Player {p_data['id']+1}"),
                    color=tuple(p_data.get("color", (239, 68, 68))),
                    token_index=p_data.get("token_index", 0),
                    is_ai=p_data.get("is_ai", False),
                    ai_personality=p_data.get("ai_personality", "Balanced")
                )
                p.load_dict(p_data)
                players.append(p)

            # Clear any in-memory ownership before applying saved tiles
            for t in board.tiles:
                t.owner = None
                t.houses = 0
                t.is_mortgaged = False

            # Restore tiles linked directly to the reconstructed players
            for t_data in state.get("tiles", []):
                tid = t_data["id"]
                if tid < len(board.tiles):
                    board.tiles[tid].load_dict(t_data, players)

            # Restore decks
            card_manager.fortune_deck.load_dict(state.get("fortune_deck", {}))
            card_manager.chest_deck.load_dict(state.get("chest_deck", {}))

            raw_msgs = state.get("event_messages", [])
            saved_msgs = [(m, tuple(c)) for m, c in raw_msgs]

            return True, (players, round_number, current_player_idx, saved_msgs)
        except Exception as e:
            return False, f"Load failed: {e}"

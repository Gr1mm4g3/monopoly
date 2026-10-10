"""
Constants and definitions for Metro Tycoon (Monopoly Clone).
Contains board definitions, card decks, color palette, and gameplay parameters.
"""

# Screen & Display Settings
SCREEN_WIDTH = 1366
SCREEN_HEIGHT = 768
FPS = 60

# Board Geometry
BOARD_SIZE = 720
BOARD_X = 24
BOARD_Y = 24
CORNER_SIZE = 95
NORMAL_TILE_WIDTH = (BOARD_SIZE - 2 * CORNER_SIZE) / 9.0  # Approx 58.88 px

# Side Panel Geometry
SIDE_PANEL_X = 768
SIDE_PANEL_Y = 24
SIDE_PANEL_WIDTH = SCREEN_WIDTH - SIDE_PANEL_X - 24  # 574 px
SIDE_PANEL_HEIGHT = 720

# Colors (Modern Curated Palette)
COLOR_BG = (17, 24, 39)            # Deep slate dark
COLOR_BOARD_BG = (23, 32, 54)      # Slightly lighter slate
COLOR_BOARD_INNER = (15, 23, 42)   # Inner board backdrop
COLOR_TILE_BG = (30, 41, 59)       # Dark slate tile fill
COLOR_TILE_BORDER = (51, 65, 85)   # Subtle border
COLOR_TILE_HOVER = (71, 85, 105)   # Hover border
COLOR_TEXT_WHITE = (248, 250, 252) # Pure crisp white
COLOR_TEXT_MUTED = (148, 163, 184) # Muted gray
COLOR_TEXT_GOLD = (250, 204, 21)   # Accent gold
COLOR_TEXT_GREEN = (52, 211, 153)  # Money green
COLOR_TEXT_RED = (248, 113, 113)   # Debt / warning red
COLOR_TEXT_AMBER = (245, 158, 11)  # Warning amber text
COLOR_PANEL_BG = (24, 33, 53)      # Side panel background
COLOR_CARD_BG = (30, 41, 59)       # Side mini-card background
COLOR_ACCENT_BLUE = (59, 130, 246) # Primary interactive blue
COLOR_ACCENT_GREEN = (16, 185, 129)# Primary green / success
COLOR_ACCENT_RED = (239, 68, 68)   # Danger / reject red
COLOR_ACCENT_AMBER = (245, 158, 11)# Amber warning

# District Colors (High contrast, vibrant tones)
DISTRICT_COLORS = {
    "OLD_TOWN": (160, 82, 45),       # Warm Sienna / Mahogany
    "WAREHOUSE": (56, 189, 248),     # Electric Sky Blue
    "ARTISAN": (232, 121, 249),      # Vibrant Orchid / Pink
    "MARKET": (251, 146, 60),        # Vivid Tangerine / Orange
    "FINANCIAL": (239, 68, 68),      # Ruby Red
    "TECH": (250, 204, 21),          # Cyber Gold / Yellow
    "UPTOWN": (16, 185, 129),        # Emerald Green
    "CROWN": (59, 130, 246),         # Royal Sapphire
    "TRANSIT": (100, 116, 139),      # Slate Gray
    "UTILITY": (168, 85, 247),       # Cyber Violet
    "SPECIAL": (71, 85, 105),        # Steel
}

# Player Token Colors (for up to 6 players)
PLAYER_COLORS = [
    (239, 68, 68),    # Ruby Red
    (56, 189, 248),   # Cyan Blue
    (250, 204, 21),   # Goldenrod
    (168, 85, 247),   # Amethyst Purple
    (52, 211, 153),   # Emerald Mint
    (251, 146, 60),   # Flame Amber
]

PLAYER_ICONS = ["🚗", "🚀", "⛵", "✈️", "👑", "🦊"]
PLAYER_TOKEN_NAMES = ["Roadster", "Shuttle", "Yacht", "Airship", "Crown", "Cyber Fox"]

# Board Tile Definitions (40 tiles)
TILES_DATA = [
    # 0 - GO
    {
        "id": 0, "name": "START HUB", "type": "GO",
        "description": "Collect $200 stipend upon passing."
    },
    # 1 - Old Town 1
    {
        "id": 1, "name": "Cobble Alley", "type": "PROPERTY", "group": "OLD_TOWN",
        "price": 60, "rent": [2, 10, 30, 90, 160, 250],
        "house_cost": 50, "mortgage": 30
    },
    # 2 - City Chest
    {
        "id": 2, "name": "City Chest", "type": "CHEST",
        "description": "Draw a City Chest card."
    },
    # 3 - Old Town 2
    {
        "id": 3, "name": "Dockside Walk", "type": "PROPERTY", "group": "OLD_TOWN",
        "price": 60, "rent": [4, 20, 60, 180, 320, 450],
        "house_cost": 50, "mortgage": 30
    },
    # 4 - Income Tax
    {
        "id": 4, "name": "Income Levy", "type": "TAX", "tax": 200,
        "description": "Pay civic tax of $200."
    },
    # 5 - Transit 1
    {
        "id": 5, "name": "Metro Central", "type": "TRANSIT", "group": "TRANSIT",
        "price": 200, "rent": [25, 50, 100, 200], "mortgage": 100
    },
    # 6 - Warehouse 1
    {
        "id": 6, "name": "Depot Way", "type": "PROPERTY", "group": "WAREHOUSE",
        "price": 100, "rent": [6, 30, 90, 270, 400, 550],
        "house_cost": 50, "mortgage": 50
    },
    # 7 - Fortune
    {
        "id": 7, "name": "Fortune", "type": "FORTUNE",
        "description": "Draw a Fortune card."
    },
    # 8 - Warehouse 2
    {
        "id": 8, "name": "Industry Row", "type": "PROPERTY", "group": "WAREHOUSE",
        "price": 100, "rent": [6, 30, 90, 270, 400, 550],
        "house_cost": 50, "mortgage": 50
    },
    # 9 - Warehouse 3
    {
        "id": 9, "name": "Foundry Ave", "type": "PROPERTY", "group": "WAREHOUSE",
        "price": 120, "rent": [8, 40, 100, 300, 450, 600],
        "house_cost": 50, "mortgage": 60
    },
    # 10 - Jail
    {
        "id": 10, "name": "Detention Center", "type": "JAIL",
        "description": "Just visiting or serving detention."
    },
    # 11 - Artisan 1
    {
        "id": 11, "name": "Gallery St", "type": "PROPERTY", "group": "ARTISAN",
        "price": 140, "rent": [10, 50, 150, 450, 625, 750],
        "house_cost": 100, "mortgage": 70
    },
    # 12 - Utility 1
    {
        "id": 12, "name": "Solar Grid", "type": "UTILITY", "group": "UTILITY",
        "price": 150, "rent": [4, 10], "mortgage": 75  # 4x or 10x dice roll
    },
    # 13 - Artisan 2
    {
        "id": 13, "name": "Studio Blvd", "type": "PROPERTY", "group": "ARTISAN",
        "price": 140, "rent": [10, 50, 150, 450, 625, 750],
        "house_cost": 100, "mortgage": 70
    },
    # 14 - Artisan 3
    {
        "id": 14, "name": "Bohemian Plz", "type": "PROPERTY", "group": "ARTISAN",
        "price": 160, "rent": [12, 60, 180, 500, 700, 900],
        "house_cost": 100, "mortgage": 80
    },
    # 15 - Transit 2
    {
        "id": 15, "name": "Highspeed West", "type": "TRANSIT", "group": "TRANSIT",
        "price": 200, "rent": [25, 50, 100, 200], "mortgage": 100
    },
    # 16 - Market 1
    {
        "id": 16, "name": "Bazaar Way", "type": "PROPERTY", "group": "MARKET",
        "price": 180, "rent": [14, 70, 200, 550, 750, 950],
        "house_cost": 100, "mortgage": 90
    },
    # 17 - City Chest
    {
        "id": 17, "name": "City Chest", "type": "CHEST",
        "description": "Draw a City Chest card."
    },
    # 18 - Market 2
    {
        "id": 18, "name": "Harbor Market", "type": "PROPERTY", "group": "MARKET",
        "price": 180, "rent": [14, 70, 200, 550, 750, 950],
        "house_cost": 100, "mortgage": 90
    },
    # 19 - Market 3
    {
        "id": 19, "name": "Spice Route", "type": "PROPERTY", "group": "MARKET",
        "price": 200, "rent": [16, 80, 220, 600, 800, 1000],
        "house_cost": 100, "mortgage": 100
    },
    # 20 - Free Parking / Haven
    {
        "id": 20, "name": "Central Park", "type": "PARKING",
        "description": "Free resting zone & safe haven."
    },
    # 21 - Financial 1
    {
        "id": 21, "name": "Ticker Row", "type": "PROPERTY", "group": "FINANCIAL",
        "price": 220, "rent": [18, 90, 250, 700, 875, 1050],
        "house_cost": 150, "mortgage": 110
    },
    # 22 - Fortune
    {
        "id": 22, "name": "Fortune", "type": "FORTUNE",
        "description": "Draw a Fortune card."
    },
    # 23 - Financial 2
    {
        "id": 23, "name": "Exchange Plz", "type": "PROPERTY", "group": "FINANCIAL",
        "price": 220, "rent": [18, 90, 250, 700, 875, 1050],
        "house_cost": 150, "mortgage": 110
    },
    # 24 - Financial 3
    {
        "id": 24, "name": "Wallgate St", "type": "PROPERTY", "group": "FINANCIAL",
        "price": 240, "rent": [20, 100, 300, 750, 925, 1100],
        "house_cost": 150, "mortgage": 120
    },
    # 25 - Transit 3
    {
        "id": 25, "name": "North Station", "type": "TRANSIT", "group": "TRANSIT",
        "price": 200, "rent": [25, 50, 100, 200], "mortgage": 100
    },
    # 26 - Tech 1
    {
        "id": 26, "name": "Silicon Drive", "type": "PROPERTY", "group": "TECH",
        "price": 260, "rent": [22, 110, 330, 800, 975, 1150],
        "house_cost": 150, "mortgage": 130
    },
    # 27 - Tech 2
    {
        "id": 27, "name": "Cyber Way", "type": "PROPERTY", "group": "TECH",
        "price": 260, "rent": [22, 110, 330, 800, 975, 1150],
        "house_cost": 150, "mortgage": 130
    },
    # 28 - Utility 2
    {
        "id": 28, "name": "Hydro Plant", "type": "UTILITY", "group": "UTILITY",
        "price": 150, "rent": [4, 10], "mortgage": 75
    },
    # 29 - Tech 3
    {
        "id": 29, "name": "Quantum Blvd", "type": "PROPERTY", "group": "TECH",
        "price": 280, "rent": [24, 120, 360, 850, 1025, 1200],
        "house_cost": 150, "mortgage": 140
    },
    # 30 - Go to Jail
    {
        "id": 30, "name": "Go To Detention", "type": "GOTO_JAIL",
        "description": "Go directly to detention. Do not pass GO."
    },
    # 31 - Uptown 1
    {
        "id": 31, "name": "Park Terrace", "type": "PROPERTY", "group": "UPTOWN",
        "price": 300, "rent": [26, 130, 390, 900, 1100, 1275],
        "house_cost": 200, "mortgage": 150
    },
    # 32 - Uptown 2
    {
        "id": 32, "name": "Embassy Row", "type": "PROPERTY", "group": "UPTOWN",
        "price": 300, "rent": [26, 130, 390, 900, 1100, 1275],
        "house_cost": 200, "mortgage": 150
    },
    # 33 - City Chest
    {
        "id": 33, "name": "City Chest", "type": "CHEST",
        "description": "Draw a City Chest card."
    },
    # 34 - Uptown 3
    {
        "id": 34, "name": "Grandview Hts", "type": "PROPERTY", "group": "UPTOWN",
        "price": 320, "rent": [28, 150, 450, 1000, 1200, 1400],
        "house_cost": 200, "mortgage": 160
    },
    # 35 - Transit 4
    {
        "id": 35, "name": "Skyport Express", "type": "TRANSIT", "group": "TRANSIT",
        "price": 200, "rent": [25, 50, 100, 200], "mortgage": 100
    },
    # 36 - Fortune
    {
        "id": 36, "name": "Fortune", "type": "FORTUNE",
        "description": "Draw a Fortune card."
    },
    # 37 - Crown 1
    {
        "id": 37, "name": "Penthouse Rdg", "type": "PROPERTY", "group": "CROWN",
        "price": 350, "rent": [35, 175, 500, 1100, 1300, 1500],
        "house_cost": 200, "mortgage": 175
    },
    # 38 - Luxury Tax
    {
        "id": 38, "name": "Luxury Surcharge", "type": "TAX", "tax": 100,
        "description": "Pay luxury tax of $100."
    },
    # 39 - Crown 2
    {
        "id": 39, "name": "Apex Pinnacle", "type": "PROPERTY", "group": "CROWN",
        "price": 400, "rent": [50, 200, 600, 1400, 1700, 2000],
        "house_cost": 200, "mortgage": 200
    },
]

# Color Group member counts (to check for complete monopolies)
GROUP_COUNTS = {
    "OLD_TOWN": 2,
    "WAREHOUSE": 3,
    "ARTISAN": 3,
    "MARKET": 3,
    "FINANCIAL": 3,
    "TECH": 3,
    "UPTOWN": 3,
    "CROWN": 2,
    "TRANSIT": 4,
    "UTILITY": 2
}

# Fortune (Chance) Deck
FORTUNE_CARDS = [
    {"title": "Advance to Start", "desc": "Advance to START HUB and collect $200 stipend.", "action": "MOVE_TO", "target": 0},
    {"title": "Tech Boom", "desc": "Advance to Silicon Drive. If you pass START HUB, collect $200.", "action": "MOVE_TO", "target": 26},
    {"title": "Metropolitan Commute", "desc": "Take a ride to Metro Central. If you pass START HUB, collect $200.", "action": "MOVE_TO", "target": 5},
    {"title": "Crown Visit", "desc": "Take a stroll to Apex Pinnacle.", "action": "MOVE_TO", "target": 39},
    {"title": "Bank Dividend", "desc": "Bank pays you dividend of $50.", "action": "MONEY", "amount": 50},
    {"title": "Detention Order", "desc": "Go directly to Detention Center. Do not pass START HUB, do not collect $200.", "action": "GO_TO_JAIL"},
    {"title": "Bail Bond", "desc": "Get Out of Detention Free card. Keep until needed or traded.", "action": "JAIL_FREE"},
    {"title": "Property Overhaul", "desc": "General repairs: Pay $25 per house and $100 per skyscraper.", "action": "REPAIRS", "house": 25, "hotel": 100},
    {"title": "Speeding Fine", "desc": "City drone catches your speeding pod. Pay $15 fine.", "action": "MONEY", "amount": -15},
    {"title": "Board Chairman", "desc": "Elected Chairman of the City Board. Pay each player $50.", "action": "PAY_ALL", "amount": 50},
    {"title": "Consulting Fee", "desc": "Urban planning consultation rewarded. Collect $150.", "action": "MONEY", "amount": 150},
    {"title": "Step Back", "desc": "Traffic detour! Step back 3 spaces.", "action": "MOVE_STEPS", "steps": -3},
]

# City Chest Deck
CITY_CHEST_CARDS = [
    {"title": "Civic Grant", "desc": "Advance to START HUB and collect $200.", "action": "MOVE_TO", "target": 0},
    {"title": "Bank Accounting Error", "desc": "Bank miscalculation in your favor! Collect $200.", "action": "MONEY", "amount": 200},
    {"title": "Medical Facility Fee", "desc": "Pay wellness and hospital clinic bill of $50.", "action": "MONEY", "amount": -50},
    {"title": "Startup Stock Sale", "desc": "From sale of stock shares you receive $50.", "action": "MONEY", "amount": 50},
    {"title": "Legal Release Pass", "desc": "Get Out of Detention Free pass.", "action": "JAIL_FREE"},
    {"title": "Audit Notice", "desc": "Court summons! Go to Detention Center directly.", "action": "GO_TO_JAIL"},
    {"title": "Holiday Gala Fund", "desc": "Gala fund matures. Receive $100.", "action": "MONEY", "amount": 100},
    {"title": "Income Tax Refund", "desc": "Tax refund approved! Collect $20.", "action": "MONEY", "amount": 20},
    {"title": "Birthday Endowment", "desc": "It is your birthday! Collect $10 from every player.", "action": "COLLECT_ALL", "amount": 10},
    {"title": "Life Insurance Maturation", "desc": "Life insurance payout. Collect $100.", "action": "MONEY", "amount": 100},
    {"title": "Hospital Donation", "desc": "Donate to city general hospital. Pay $100.", "action": "MONEY", "amount": -100},
    {"title": "Street Assessment", "desc": "Civic renovation: Pay $40 per house and $115 per skyscraper.", "action": "REPAIRS", "house": 40, "hotel": 115},
]

# AI Archetypes
AI_PERSONALITIES = {
    "Balanced": {
        "cash_reserve": 200,
        "mortgage_threshold": 80,
        "build_aggression": 0.6,
        "trade_eagerness": 0.5,
        "description": "Prudent investor maintaining moderate cash reserves."
    },
    "Tycoon": {
        "cash_reserve": 80,
        "mortgage_threshold": 40,
        "build_aggression": 0.9,
        "trade_eagerness": 0.8,
        "description": "Aggressive builder who expands fast and trades freely."
    },
    "Cautious": {
        "cash_reserve": 350,
        "mortgage_threshold": 150,
        "build_aggression": 0.3,
        "trade_eagerness": 0.3,
        "description": "Conservative player prioritizing high cash safety margin."
    },
    "Dealmaker": {
        "cash_reserve": 150,
        "mortgage_threshold": 60,
        "build_aggression": 0.7,
        "trade_eagerness": 0.95,
        "description": "Master negotiator seeking color completions through trades."
    }
}

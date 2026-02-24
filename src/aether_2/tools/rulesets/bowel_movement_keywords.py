"""
Bowel Movement Keywords and Bristol Stool Chart Lexicon

This module contains keyword mappings for:
- Bristol Stool Chart types (1-7)
- Stool modifiers (steatorrhea, blood, melena, mucus)
- Symptom keywords (bloating, heartburn, etc.)
- Context keywords (travel, stress, foods)
"""

# Bristol Stool Chart keyword mapping
BRISTOL_KEYWORDS = {
    "1": {
        "name": "Separate hard lumps",
        "keywords": [
            "separate hard lumps", "hard lumps", "little balls", "pellets", "rabbit pellets",
            "goat pellets", "marbles", "like nuts", "pebble stool", "rock hard", "dry hard",
            "constipated pellets", "stool like pebbles"
        ]
    },
    "2": {
        "name": "Sausage-shaped but lumpy",
        "keywords": [
            "lumpy sausage", "sausage but lumpy", "log but lumpy", "hard lumpy log",
            "bumpy sausage", "chunky sausage"
        ]
    },
    "3": {
        "name": "Sausage with cracks on surface",
        "keywords": [
            "sausage with cracks", "log with cracks", "cracked log", "cracked sausage",
            "sausagey with cracks"
        ]
    },
    "4": {
        "name": "Smooth soft sausage/snake",
        "keywords": [
            "smooth soft snake", "smooth soft sausage", "snake", "long smooth", "formed smooth",
            "soft and smooth", "easy to pass smooth"
        ]
    },
    "5": {
        "name": "Soft blobs with clear-cut edges",
        "keywords": [
            "soft blobs", "soft pieces", "small soft pieces", "soft clumps", "soft lumps with edges",
            "passed easily small blobs"
        ]
    },
    "6": {
        "name": "Fluffy pieces with ragged edges; mushy",
        "keywords": [
            "mushy", "fluffy pieces", "ragged edges", "porridge stool", "pudding stool",
            "loose mush", "very soft mushy"
        ]
    },
    "7": {
        "name": "Watery, no solid pieces",
        "keywords": [
            "watery", "water", "liquid", "no solid pieces", "entirely liquid",
            "diarrhea", "diarrhoea", "completely liquid"
        ]
    }
}

# Stool modifiers
STOOL_MODIFIERS = {
    "steatorrhea": ["greasy", "oily", "shiny film", "floats and greasy", "foul smelling", "rancid odor", "hard to flush"],
    "blood": ["blood", "bloody", "red blood", "bright red"],
    "melena": ["black tarry", "tarry", "jet black stool", "melaena", "melena"],
    "mucus": ["mucus", "mucousy", "slimy"]
}

# Negation words (for context-aware parsing)
NEGATION_WORDS = ["no", "not", "without", "never", "denies", "none"]

# Bloating timing keywords
BLOATING_KEYWORDS = {
    "early": ["within 2 hours", "right after eating", "immediately after", "soon after eating", "after meals", "post-meal"],
    "late": ["more than 2 hours", "hours after eating", "later in day", "evening bloating"],
    "variable": ["variable", "sometimes", "inconsistent", "varies"]
}

# Heartburn keywords
HEARTBURN_KEYWORDS = {
    "gerd": ["gerd", "persistent reflux", "chronic reflux", "daily heartburn", "constant heartburn", "severe reflux"],
    "occasional": ["occasional heartburn", "sometimes heartburn", "rare heartburn", "infrequent heartburn"]
}

# Constipation context keywords
CONSTIPATION_CONTEXT = {
    "travel": ["after travel", "when traveling", "during travel", "trip", "vacation"],
    "stress": ["after stress", "when stressed", "high stress", "stressful", "anxiety"],
    "trauma": ["after trauma", "traumatic event", "ptsd"],
    "foods": ["after eating", "certain foods", "fodmap", "dairy", "gluten", "wheat", "fiber"]
}

# Anorectal symptom keywords
ANORECTAL_KEYWORDS = {
    "hemorrhoids": ["hemorrhoids", "haemorrhoids", "piles"],
    "fissures": ["fissure", "fissures", "anal tear", "painful bowel"],
    "prolapse": ["prolapse", "rectal prolapse"]
}

# Loose/watery stool indicators (for diarrhea detection)
LOOSE_WATERY_KEYWORDS = [
    "loose", "watery", "liquid", "runny", "diarrhea", "diarrhoea",
    "urgent", "explosive", "can't hold it"
]

# Variability indicators
VARIABILITY_KEYWORDS = [
    "variable", "varies", "alternating", "sometimes constipated sometimes diarrhea",
    "inconsistent", "unpredictable", "changes", "fluctuates"
]


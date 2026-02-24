"""
Phase 3-Specific Constants

This module contains constants specific to Phase 3 rulesets.
Shared constants (FOCUS_AREAS, add_top_contributors, etc.) are imported from Phase 2.
"""

# Import shared constants from Phase 2
from ..rulesets.constants import (
    FOCUS_AREAS,
    FOCUS_AREA_NAMES,
    add_top_contributors,
    SHIFT_WORK_KEYWORDS,
    detect_shift_work
)

# ============================================================================
# PHASE 3 NEW SCHEMA DEFINITION
# ============================================================================
# Complete schema for Phase 3 intake questions (93 questions total)
# This serves as the single source of truth for question metadata

PHASE3_SCHEMA = {
    "q001": {
        "category": "Goals & Narrative",
        "subcategory": "Top Health Goals",
        "question": "What are your top three health goals right now?",
        "data_type": "UI: Multi-line text"
    },
    "q002": {
        "category": "Goals & Narrative",
        "subcategory": "Your Theory",
        "question": "Why do YOU think these issues are happening (or goals are pending)?",
        "data_type": "UI: Multi-line text"
    },
    "q003": {
        "category": "Goals & Narrative",
        "subcategory": "What Needs to Change",
        "question": "Are you willing to make lifestyle changes?",
        "data_type": "UI: Checkbox options — Yes · No"
    },
    "q004": {
        "category": "Goals & Narrative",
        "subcategory": "What Needs to Change",
        "question": "If people are not sure about the response or say No - Anything else you'd like to share about it?",
        "data_type": "UI: Multi-line text"
    },
    "q005": {
        "category": "Goals & Narrative",
        "subcategory": "Last Time Well",
        "question": "When did you last feel really well—body and mind?",
        "data_type": "UI: Short-text"
    },
    "q006": {
        "category": "Goals & Narrative",
        "subcategory": "Trigger Event",
        "question": "Did anything specific start or worsen your wellness?",
        "data_type": "UI: Multi-line text"
    },
    "q007": {
        "category": "Goals & Narrative",
        "subcategory": "Makes Worse",
        "question": "What makes your symptoms WORSE?",
        "data_type": "UI: Multi-line text"
    },
    "q008": {
        "category": "Goals & Narrative",
        "subcategory": "Time of Day Worse",
        "question": "What time of the day does it get worse?",
        "data_type": "UI: Radio — Morning · Afternoon · Evening"
    },
    "q009": {
        "category": "Goals & Narrative",
        "subcategory": "Time of Day Worse",
        "question": "Explain/Anything else you'd like to share about it?",
        "data_type": "UI: Multi-line text"
    },
    "q010": {
        "category": "Goals & Narrative",
        "subcategory": "Where It Happens",
        "question": "Where does it happen?",
        "data_type": "UI: Radio — Home · Work ·"
    },
    "q011": {
        "category": "Goals & Narrative",
        "subcategory": "Where It Happens",
        "question": "If Other, Explain/Anything else you'd like to share about it?",
        "data_type": "UI: Short-text"
    },
    "q012": {
        "category": "Goals & Narrative",
        "subcategory": "Food/Drink Triggers",
        "question": "Do any foods/drinks trigger your symptoms?",
        "data_type": "UI: Checkbox options — Yes · No"
    },
    "q013": {
        "category": "Goals & Narrative",
        "subcategory": "Food/Drink Triggers",
        "question": "If yes, Ask: \"Explain/Anything else you'd like to share about it?",
        "data_type": "UI: Short-text"
    },
    "q014": {
        "category": "Goals & Narrative",
        "subcategory": "Makes Better",
        "question": "And what seems to HELP with your symptoms?",
        "data_type": "UI: Multi-line text"
    },
    "q015": {
        "category": "Meds & Supplements",
        "subcategory": "Long-Term Medication Use",
        "question": "Have you taken antibiotics, steroids, reflux meds, or daily pain-relievers for long periods?",
        "data_type": "UI: Checkbox options — Yes · No"
    },
    "q016": {
        "category": "Meds & Supplements",
        "subcategory": "Long-Term Medication Use",
        "question": "If yes, Ask: \"Which and how long?",
        "data_type": "UI: Multi-line text"
    },
    "q017": {
        "category": "Meds & Supplements",
        "subcategory": "Long-Term Medication Use",
        "question": "If yes, When was the last time you took them",
        "data_type": "year"
    },
    "q018": {
        "category": "Lifestyle",
        "subcategory": "Exercise Types",
        "question": "What kinds of activity and how intense?",
        "data_type": "UI: Multi-line text"
    },
    "q019": {
        "category": "Lifestyle",
        "subcategory": "Rank Sunlight Days",
        "question": "Rank your days of sunlight exposure from most to least during a week",
        "data_type": "UI: Reorder bars — Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday"
    },
    "q020": {
        "category": "Sleep",
        "subcategory": "Sleep Aids",
        "question": "Do you use any sleep aids or medicines?",
        "data_type": "UI: Radio — Yes · No"
    },
    "q021": {
        "category": "Sleep",
        "subcategory": "Sleep Aids",
        "question": "Explain/Anything else you'd like to share about it",
        "data_type": "UI: Short-text"
    },
    "q022": {
        "category": "Sleep",
        "subcategory": "Consistent Bedtime",
        "question": "Do you go to sleep around the same time every day?",
        "data_type": "UI: Radio — Yes · No"
    },
    "q023": {
        "category": "Sleep",
        "subcategory": "Consistent Wake Time",
        "question": "Do you wake up around the same time every day?",
        "data_type": "UI: Radio — Yes · No"
    },
    "q024": {
        "category": "Nutrition",
        "subcategory": "Typical Day of Eating",
        "question": "Walk me through your typical meals and snacks.",
        "data_type": "UI: Multi-line text |"
    },
    "q025": {
        "category": "Nutrition",
        "subcategory": "Food Sensitivities",
        "question": "Do you avoid any foods because they cause issues?",
        "data_type": "UI: Radio — Yes · No"
    },
    "q026": {
        "category": "Nutrition",
        "subcategory": "Food Sensitivities",
        "question": "If yes, Explain/Anything else you'd like to share about it",
        "data_type": "UI: Multi-line text"
    },
    "q027": {
        "category": "Nutrition",
        "subcategory": "Cravings",
        "question": "I'll read out a few food types. Please answer yes or no if you feel any strong cravings for any of these?",
        "data_type": "UI: Check-boxes — Sweets · Salty · Bread/Pasta · Chocolate · Caffeine"
    },
    "q028": {
        "category": "Nutrition",
        "subcategory": "Cravings",
        "question": "Any other cravings",
        "data_type": "UI: Short text"
    },
    "q029": {
        "category": "Stress & Support",
        "subcategory": "Mood",
        "question": "How would you describe your mood lately?",
        "data_type": "UI: Multi-line text"
    },
    "q030": {
        "category": "Stress & Support",
        "subcategory": "Stress Level",
        "question": "On a scale of 1–10, how high is your current stress?",
        "data_type": "UI: Slider 1–10"
    },
    "q031": {
        "category": "Stress & Support",
        "subcategory": "Stressors",
        "question": "What are your biggest sources of stress right now?",
        "data_type": "UI: Multi-line text"
    },
    "q032": {
        "category": "Stress & Support",
        "subcategory": "Relaxation Practices",
        "question": "Which relaxation techniques do you use?",
        "data_type": "UI: Check-boxes — Meditation · Yoga · Breathing · Tai Chi/Qigong · Prayer ·"
    },
    "q033": {
        "category": "Stress & Support",
        "subcategory": "Relaxation Practices",
        "question": "Any Other: 'Please describe.'",
        "data_type": "UI: Short-text"
    },
    "q034": {
        "category": "Stress & Support",
        "subcategory": "Support Network",
        "question": "Who or what do you lean on for support?",
        "data_type": "UI: Check-boxes — Partner · Family · Friends · Spiritual · Pets · Therapist"
    },
    "q035": {
        "category": "Stress & Support",
        "subcategory": "Support Network",
        "question": "If others, please specify",
        "data_type": "UI: Short-text"
    },
    "q036": {
        "category": "Stress & Support",
        "subcategory": "Trauma History",
        "question": "The next question is highly sensitive,so you can choose not to answer it. Have you experienced significant trauma or abuse?",
        "data_type": "UI: Radio — Yes · No (optional)"
    },
    "q037": {
        "category": "Stress & Support",
        "subcategory": "Trauma Details (If Yes)",
        "question": "If they choose to answer the above question, ask this follow up  - Again , only if you are comfortable, would you like to describe, if comfortable (optional).",
        "data_type": "UI: Multi-line text."
    },
    "q038": {
        "category": "Childhood & Development",
        "subcategory": "Childhood Illnesses",
        "question": "Any significant illnesses during childhood?",
        "data_type": "UI: Radio — Yes · No · Not sure"
    },
    "q039": {
        "category": "Childhood & Development",
        "subcategory": "Childhood Illnesses",
        "question": "Explain/Anything else you'd like to share about it?",
        "data_type": "UI: Multi-line text"
    },
    "q040": {
        "category": "Childhood & Development",
        "subcategory": "Secure Environment?",
        "question": "Was your childhood home happy and secure?",
        "data_type": "UI: Radio — Yes · No · Not sure"
    },
    "q041": {
        "category": "Childhood & Development",
        "subcategory": "Secure Environment?",
        "question": "Explain/Anything else you'd like to share about it?",
        "data_type": "UI: Multi-line text"
    },
    "q042": {
        "category": "Childhood & Development",
        "subcategory": "Breast-Fed?",
        "question": "Were you breast-fed as an infant?",
        "data_type": "UI: Radio — Yes · No · Not sure"
    },
    "q043": {
        "category": "Childhood & Development",
        "subcategory": "Breastfeeding Duration (If Yes)",
        "question": "If yes, Approximately how long were you breast-fed?",
        "data_type": "UI: Short-text"
    },
    "q044": {
        "category": "Childhood & Development",
        "subcategory": "Early-Life Exposures",
        "question": "Early exposure to smoke, lead paint, pesticides, etc.?",
        "data_type": "UI: Radio — Yes · No · Not sure"
    },
    "q045": {
        "category": "Childhood & Development",
        "subcategory": "Early-Life Exposures",
        "question": "Explain/Anything else you'd like to share about it?",
        "data_type": "UI: Multi-line text"
    },
    "q046": {
        "category": "Dental History",
        "subcategory": "Teeth Sensitivity",
        "question": "Do you have teeth sensitivity?",
        "data_type": "UI: Radio — Yes · No"
    },
    "q047": {
        "category": "Dental History",
        "subcategory": "Sensitivity Details (If Yes)",
        "question": "Please explain (optional).",
        "data_type": "UI: Short-text"
    },
    "q048": {
        "category": "Environment & Exposures",
        "subcategory": "Indoor Environment Factors",
        "question": "I'll read out a few environmental exposures. Please say Yes or No for any of these that you may have been exposed to.",
        "data_type": "UI: Check-boxes — Water leaks/Dampness · Ongoing renovations · Fresh paint/VOCs · New carpet/Flooring glue · Poor ventilation/Stale air · Gas stove · Wood-burning fireplace · Pets indoors · Heavy fragrance/Air fresheners · High-EMF sources (server room)"
    },
    "q049": {
        "category": "Environment & Exposures",
        "subcategory": "Indoor Environment Factors",
        "question": "Any 'Other building issues'? 'Please describe.'",
        "data_type": "UI: Multi-line text"
    },
    "q050": {
        "category": "Environment & Exposures",
        "subcategory": "Chemical Sensitivity",
        "question": "Are you unusually sensitive (headache, nausea, rashes) to small amounts of chemicals, perfumes, smoke or exhaust?",
        "data_type": "UI: Radio — Yes · No |"
    },
    "q051": {
        "category": "Environment & Exposures",
        "subcategory": "Chemical Sensitivity",
        "question": "If Yes: Assistant: List common triggers or situations.",
        "data_type": "UI: Multi-line text"
    },
    "q052": {
        "category": "Environment & Exposures",
        "subcategory": "Caffeine Sensitivity",
        "question": "Do you use caffeine?",
        "data_type": "UI: Radio — Yes · No |"
    },
    "q053": {
        "category": "Environment & Exposures",
        "subcategory": "Caffeine Sensitivity",
        "question": "If yes, Which of the following ring true with respect to how caffeine makes you feel",
        "data_type": "UI: Radio — Sensitive (jittery / palpitations) · Tolerant"
    },
    "q054": {
        "category": "Environment & Exposures",
        "subcategory": "Alcohol Flush Reaction",
        "question": "Does a small amount of alcohol make you flush or feel unwell?",
        "data_type": "UI: Radio — Yes · No · I don't drink"
    },
    "q055": {
        "category": "Environment & Exposures",
        "subcategory": "Alcohol Flush Reaction",
        "question": "Explain/Anything else you'd like to share about it",
        "data_type": "UI: Multi-line text"
    },
    "q056": {
        "category": "Environment & Exposures",
        "subcategory": "Clothing Fibers",
        "question": "I'll read out the names of a few fiber types. Please say yes, no or don't know if you use any of the following fibers in your clothing?",
        "data_type": "UI: Check-boxes — Polyester · Nylon · Rayon · Acrylic · Spandex (Lycra/Elastane) · Acetate"
    },
    "q057": {
        "category": "Environment & Exposures",
        "subcategory": "Seasonal Allergies",
        "question": "Do you get seasonal allergies?",
        "data_type": "UI: Radio — Yes · No |"
    },
    "q058": {
        "category": "Environment & Exposures",
        "subcategory": "Seasonal Allergies",
        "question": "If Yes: List name and symptom.",
        "data_type": "UI: Multi-line text"
    },
    "q059": {
        "category": "Environment & Exposures",
        "subcategory": "Hygiene Products",
        "question": "Now I'll read the hygiene step you usually may do in your daily life and I'd like you to share the brand or product you use for it. Example for Toothpaste would be Colgate. Options: Bodywash, Soap, Scrub, Shampoo, Conditioner, Toothpaste, Mouthwash",
        "data_type": "UI: Multi-line text (per item field)"
    },
    "q060": {
        "category": "Environment & Exposures",
        "subcategory": "Air Filter",
        "question": "Do you use an air-filter?",
        "data_type": "UI: Radio — Yes · No |"
    },
    "q061": {
        "category": "Environment & Exposures",
        "subcategory": "Air Filter",
        "question": "If Yes: Assistant: What brand/model.",
        "data_type": "UI: Multi-line text"
    },
    "q062": {
        "category": "Environment & Exposures",
        "subcategory": "Water Filter / Bottled Water",
        "question": "Do you drink bottled water or use a water-filter?",
        "data_type": "UI: Radio — Yes · No |"
    },
    "q063": {
        "category": "Environment & Exposures",
        "subcategory": "Water Filter / Bottled Water",
        "question": "If Yes: Assistant: What brand/model.",
        "data_type": "UI: Multi-line text"
    },
    "q064": {
        "category": "Pets & Animals",
        "subcategory": "Animal Types (If Yes)",
        "question": "What kind of animals do you have? (Select all)",
        "data_type": "UI: Check-boxes — Dog · Cat · Bird · Reptile · Livestock"
    },
    "q065": {
        "category": "Pets & Animals",
        "subcategory": "Animal Types (If Yes)",
        "question": "Any Other Animals?: Assistant: Please specify the animal(s).",
        "data_type": "UI: Short-text"
    },
    "q066": {
        "category": "Pets & Animals",
        "subcategory": "Mostly Where? (If Yes)",
        "question": "Do they live mostly inside, outside, or both?",
        "data_type": "UI: Radio — Inside · Outside · Both"
    },
    "q067": {
        "category": "Systems Check",
        "subcategory": "Weight Change",
        "question": "Have you experienced an unintentional weight change recently?",
        "data_type": "UI: Radio — Yes · No"
    },
    "q068": {
        "category": "Systems Check",
        "subcategory": "Weight Change Details (If Yes)",
        "question": "IF yes to weight gain, How much and over what timeframe?",
        "data_type": "UI: Short-text"
    },
    "q069": {
        "category": "Systems Check",
        "subcategory": "Bowel Movements (If triggered)",
        "question": "How often do you have bowel movements?",
        "data_type": "Record as: short text"
    },
    "q070": {
        "category": "Systems Check",
        "subcategory": "Digestive follow- up",
        "question": "If user selected Bloating, Bloating timing: 'When do you feel bloated—within 2 hours of eating, after 2 hours, or variable?'",
        "data_type": "UI: Multi-line text"
    },
    "q071": {
        "category": "Systems Check",
        "subcategory": "Digestive follow- up",
        "question": "If user selected Heartburn 'Is it reflux/GERD or occasional heartburn?'",
        "data_type": "UI: Multi-line text"
    },
    "q072": {
        "category": "Systems Check",
        "subcategory": "Digestive follow- up",
        "question": "If user selected constipation 'Any known triggers (e.g., after trauma, travel, foods)?'",
        "data_type": "UI: Multi-line text"
    },
    "q073": {
        "category": "Systems Check",
        "subcategory": "Digestive follow- up",
        "question": "Stool analysis: 'Any foul smell, notable color, or blood/mucus?'",
        "data_type": "UI: Multi-line text"
    },
    "q074": {
        "category": "Systems Check",
        "subcategory": "Digestive follow- up",
        "question": "Anorectal symptoms: 'Any hemorrhoids, fissures, or prolapse?'",
        "data_type": "UI: Multi-line text"
    },
    "q075": {
        "category": "Systems Check",
        "subcategory": "Transit Time (If triggered)",
        "question": "If you've measured it, what is your transit time with beet or charcoal test? Some people check transit time by eating beets (red stool) or activated charcoal and timing to first color change.",
        "data_type": "UI: Short-text"
    },
    "q076": {
        "category": "Hormone / Sex-Specific",
        "subcategory": "Hormone Therapy / Birth Control",
        "question": "Are you using hormonal birth control?",
        "data_type": "UI: Radio — Yes · No"
    },
    "q077": {
        "category": "Hormone / Sex-Specific",
        "subcategory": "Hormone Therapy / Birth Control",
        "question": "Please explain the type,dosage,start,reason and duration for which you have taken it?",
        "data_type": "UI: Multi-line text"
    },
    "q078": {
        "category": "Hormone / Sex-Specific",
        "subcategory": "HRT Details",
        "question": "Do you receive any HRT (Hormone Replacement Therapy).",
        "data_type": "UI: Radio — Yes · No"
    },
    "q079": {
        "category": "Hormone / Sex-Specific",
        "subcategory": "HRT Details",
        "question": "If yes, please explain",
        "data_type": "UI: Multi-line text"
    },
    "q080": {
        "category": "Hormone / Sex-Specific",
        "subcategory": "Pregnancy History",
        "question": "You can choose to skip the following question if you'd like. How many pregnancies, births, miscarriages or complications?",
        "data_type": "UI: Checkbox & Number: Pregnancy (#), Miscarriage (#), Complications (Textbox)"
    },
    "q081": {
        "category": "Hormone / Sex-Specific",
        "subcategory": "Timing Between Pregnancies/Miscarriages",
        "question": "If Pregnancy or Miscarriages selected/shared, ask - What was the time between each pregnancy/miscarriage/complication?",
        "data_type": "UI: Repeatable rows per Pregnancy/Miscarriage #: Number input for time (months/years)"
    },
    "q082": {
        "category": "Hormone / Sex-Specific",
        "subcategory": "Breast Cancer Risk",
        "question": "Have you ever been diagnosed of breast cancer or considered high-risk?",
        "data_type": "UI: Radio — Yes · No"
    },
    "q083": {
        "category": "Hormone / Sex-Specific",
        "subcategory": "Breast Cancer Risk",
        "question": "If yes, Please explain.",
        "data_type": "UI: Multi-line text"
    },
    "q084": {
        "category": "Hormone / Sex-Specific",
        "subcategory": "Male Concerns Details (If Yes)",
        "question": "You previously shared that you had Male hormones/sexual concerns.Please describe—onset, labs, treatments",
        "data_type": "UI: Multi-line text"
    },
    "q085": {
        "category": "Hormone / Sex-Specific",
        "subcategory": "Gynecomastia",
        "question": "Do you have diagnosed or suspected gynecomastia (breast tissue development in males leading to enlarged breasts)?",
        "data_type": "UI: Radio — Yes · No"
    },
    "q086": {
        "category": "Hormone / Sex-Specific",
        "subcategory": "Gynecomastia",
        "question": "If Yes: Explain diagnosis and any ongoing treatment.",
        "data_type": "UI: Multi-line text"
    },
    "q087": {
        "category": "Hormone / Sex-Specific",
        "subcategory": "Prostate Issues",
        "question": "Do you have any prostate related issue?",
        "data_type": "UI: Radio — Yes · No"
    },
    "q088": {
        "category": "Hormone / Sex-Specific",
        "subcategory": "Prostate Issues",
        "question": "If yes, Please explain.",
        "data_type": "UI: Multi-line text"
    },
    "q089": {
        "category": "Hormone / Sex-Specific",
        "subcategory": "Prostate/Testicular Cancer Risk",
        "question": "Have you ever been diagnosed of prostate or testicular cancer or considered high-risk?",
        "data_type": "UI: Radio — Yes · No"
    },
    "q090": {
        "category": "Hormone / Sex-Specific",
        "subcategory": "Prostate/Testicular Cancer Risk",
        "question": "If yes, Please explain.",
        "data_type": "UI: Multi-line text"
    },
    "q091": {
        "category": "Pain · Headache · Skin",
        "subcategory": "Headache Details (If Yes)",
        "question": "You previously mentioned you had frequent headaches/migraines. How often and any known triggers?",
        "data_type": "UI: Multi-line text"
    },
    "q092": {
        "category": "Pain · Headache · Skin",
        "subcategory": "Pain Details (If Yes)",
        "question": "Where is the pain and what makes it worse/better?",
        "data_type": "UI: Multi-line text"
    },
    "q093": {
        "category": "Pain · Headache · Skin",
        "subcategory": "Skin Details (If Yes)",
        "question": "Please describe location, triggers, timing.",
        "data_type": "UI: Multi-line text"
    },
}

# Phase 3 Field Context Mapping
# Maps field position number to human-readable context name for reason tracking
PHASE3_FIELD_CONTEXT = {
    0: "TopHealthGoals",           # Top 3 health goals
    1: "PatientReasoning",         # Patient's causal reasoning about their condition
    2: "LifestyleWillingness",     # Adherence/lifestyle change willingness
    3: "LastFeltWell",             # When they last felt well
    4: "WhatStartedWorsened",      # What started or worsened symptoms
    5: "WhatMakesWorse",           # What makes symptoms worse
    6: "PartOfDay",                # Time of day when symptoms worsen
    7: "WhereSymptomsWorse",       # Location where symptoms get worse
    8: "FoodDrinkTriggers",        # Food/drink triggers
    9: "WhatHelps",                # What helps symptoms
    10: "AntibioticsMedsHistory",  # Antibiotics/medications history
    11: "ActivityIntensity",       # Physical activity intensity
    12: "SunlightExposure",        # Sunlight exposure ranking
    13: "SleepAids",               # Sleep aids and medicines
    14: "ConsistentSleepSchedule", # Consistent sleep schedule
    15: "ConsistentWakeTime",      # Consistent wake time
    16: "TypicalMeals",            # Typical meals and snacks (LLM-based)
    17: "FoodAvoidance",           # Foods avoided due to symptoms (NLP-based)
    18: "FoodCravings",            # Food cravings (multi-select with substring matching)
    19: "Mood",                    # Mood description (NLP-based lexicon matching)
    20: "CurrentStress",           # Current stress level (1-10 scale, linear + piecewise)
    21: "StressSources",           # Biggest sources of stress (NLP-based stressor categorization)
    22: "RelaxationTechniques",    # Relaxation techniques used (multi-select with substring matching)
    23: "SupportSources",          # Who or what do you lean on for support (multi-select with text mapping)
    24: "TraumaAbuse",             # Significant trauma or abuse history (NLP-based with crisis screening)
    25: "ChildhoodIllnesses",      # Significant illnesses during childhood (NLP-based with age/frequency multipliers)
    26: "ChildhoodHomeSecurity",   # Childhood home security and early-life adversity (NLP-based with severity tiers)
    27: "Breastfeeding",           # Breastfeeding history (radio + duration with cross-field synergies)
    28: "EarlyEnvironmentalExposures",  # Early environmental/toxic exposures (NLP-based with duration/intensity multipliers)
    29: "ToothSensitivity",        # Tooth sensitivity (NLP-based with mechanistic scoring)
    30: "CurrentEnvironmentalExposures",  # Current home/workplace environmental exposures (multi-select with NLP-based scoring)
    31: "ChemicalSensitivity",  # Chemical sensitivity (radio with optional free text)
    32: "CaffeineReaction",  # Caffeine reaction (radio with context-driven scoring)
    33: "AlcoholFlushing",  # Alcohol flushing (radio + optional free text with context-driven scoring)
    34: "SyntheticFiberWear",  # Regular synthetic fiber wear (multi-select with optional free text)
    35: "SeasonalAllergies",  # Seasonal allergies (radio with optional free text)
    36: "AirFilter",  # Air filter usage (radio with optional brand/model text)
    37: "WaterFilter",  # Water filter/bottled water usage (radio with optional brand/model text)
    38: "AnimalTypes",  # What kind of animals do you have (multi-select with optional free text)
    39: "PetLivingLocation",  # Where do your pets/animals primarily live (radio: Inside/Outside/Both)
    40: "UnintentionalWeightChange",  # Any unintentional weight change recently (radio: Yes/No)
    41: "WeightChangeDetails",  # Weight change details (free text: magnitude, direction, timeframe)
    42: "BowelMovementFrequency",  # Bowel movement frequency & characteristics (free text)
    43: "TransitTime",  # Transit time measurement (free text)
    44: "HeadacheMigraineDetails",  # Headache/migraine frequency & triggers (free text, conditional on Phase 2)
}

# ============================================================================
# NLP UTILITIES - Shared across Phase 3 rulesets
# ============================================================================

from typing import Dict, Set, Optional
import warnings

# Check for optional NLP libraries
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    warnings.warn(
        "spaCy not available. Install with: pip install spacy && python -m spacy download en_core_web_sm",
        ImportWarning
    )

try:
    from rapidfuzz import fuzz, process
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False
    warnings.warn(
        "rapidfuzz not available. Install with: pip install rapidfuzz",
        ImportWarning
    )

# Global spaCy model instance (loaded once, shared across all rulesets)
_SPACY_NLP = None


def get_spacy_model():
    """
    Get or load the shared spaCy model.

    Returns:
        spaCy Language model or None if not available
    """
    global _SPACY_NLP, SPACY_AVAILABLE

    if not SPACY_AVAILABLE:
        return None

    if _SPACY_NLP is None:
        try:
            import spacy
            _SPACY_NLP = spacy.load("en_core_web_sm", disable=["parser", "ner"])
            print("✅ spaCy model loaded successfully (lemmatization enabled)")
        except OSError:
            print("⚠️  spaCy model not found. Run: python -m spacy download en_core_web_sm")
            print("   Falling back to basic substring matching")
            SPACY_AVAILABLE = False
            return None

    return _SPACY_NLP


def preprocess_lexicons(lexicons: Dict[str, list], nlp=None) -> Dict[str, Set[str]]:
    """
    Pre-lemmatize all keywords in lexicons for faster matching.

    Args:
        lexicons: Dict mapping domain codes to lists of keywords
        nlp: Optional spaCy model (will load if not provided)

    Returns:
        Dict mapping domain codes to sets of lemmatized keywords

    Example:
        >>> lexicons = {"CM": ["lose weight", "losing weight"]}
        >>> preprocess_lexicons(lexicons)
        {"CM": {"lose weight"}}  # Both lemmatize to same form
    """
    if nlp is None:
        nlp = get_spacy_model()

    if not nlp:
        return {}

    lemmatized = {}

    for domain, keywords in lexicons.items():
        lemmatized[domain] = set()
        for keyword in keywords:
            # Lemmatize multi-word phrases
            doc = nlp(keyword)
            lemma_phrase = " ".join([token.lemma_ for token in doc])
            lemmatized[domain].add(lemma_phrase)

    return lemmatized


def lemmatize_text(text: str, nlp=None) -> str:
    """
    Convert text to lemmatized form.

    Args:
        text: Input text
        nlp: Optional spaCy model (will load if not provided)

    Returns:
        Lemmatized text

    Examples:
        >>> lemmatize_text("losing weight")
        "lose weight"
        >>> lemmatize_text("stressed out")
        "stress out"
        >>> lemmatize_text("energies")
        "energy"
    """
    if nlp is None:
        nlp = get_spacy_model()

    if not nlp:
        return text

    doc = nlp(text)
    return " ".join([token.lemma_ for token in doc])


def match_keyword_fuzzy(keyword: str, text: str, threshold: int = 85) -> bool:
    """
    Match keyword with fuzzy matching for typos.

    Args:
        keyword: The keyword to search for
        text: The text to search in
        threshold: 0-100, higher = stricter (85 is good default)

    Returns:
        True if fuzzy match found above threshold

    Examples:
        >>> match_keyword_fuzzy("lose weight", "loose weight")
        True  # 91% match
        >>> match_keyword_fuzzy("energy", "enrgy", threshold=80)
        True  # 83% match
    """
    if not RAPIDFUZZ_AVAILABLE:
        return False

    from rapidfuzz import fuzz, process

    words = text.split()
    keyword_word_count = len(keyword.split())

    # Generate n-grams matching keyword length
    phrases = []
    for i in range(len(words) - keyword_word_count + 1):
        phrase = " ".join(words[i:i + keyword_word_count])
        phrases.append(phrase)

    # Find best fuzzy match
    if phrases:
        best_match = process.extractOne(keyword, phrases, scorer=fuzz.ratio)
        if best_match and best_match[1] >= threshold:
            return True

    return False


# ============================================================================
# LLM UTILITIES - For complex NLP tasks
# ============================================================================

def call_vertex_ai_llm(prompt: str, temperature: float = 0.0, model: str = "vertex_ai/gemini-2.5-flash") -> str:
    """
    Make a simple, independent API call to Vertex AI using LiteLLM.

    This is a standalone helper function that doesn't link to CrewAI agents.
    Can be reused across different Phase 3 rulesets that need LLM categorization.

    Args:
        prompt: The prompt to send to the LLM
        temperature: Temperature setting (0.0 = deterministic, 1.0 = creative)
        model: Model identifier (default: vertex_ai/gemini-2.5-flash)

    Returns:
        String response from the LLM

    Example:
        >>> prompt = "Categorize this diet: pizza, soda, candy"
        >>> response = call_vertex_ai_llm(prompt, temperature=0.0)
        >>> print(response)
        "Refined carbs/UPF, Carbonated beverages"
    """
    try:
        from litellm import completion

        # Make API call
        response = completion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=1500  # Increased to ensure full category lists are returned
        )

        # Extract text from response
        if response and response.choices and len(response.choices) > 0:
            content = response.choices[0].message.content
            if content is not None:
                return content.strip()
            else:
                print(f"⚠️  LLM returned None content")
                return ""
        else:
            print(f"⚠️  Empty response from LLM")
            return ""

    except Exception as e:
        print(f"❌ Error calling Vertex AI LLM: {e}")
        return ""


# Export all shared constants plus Phase 3-specific ones
__all__ = [
    # Shared from Phase 2
    "FOCUS_AREAS",
    "FOCUS_AREA_NAMES",
    "add_top_contributors",
    "SHIFT_WORK_KEYWORDS",
    "detect_shift_work",
    # Phase 3-specific
    "PHASE3_SCHEMA",
    "PHASE3_FIELD_CONTEXT",
    # NLP utilities
    "SPACY_AVAILABLE",
    "RAPIDFUZZ_AVAILABLE",
    "get_spacy_model",
    "preprocess_lexicons",
    "lemmatize_text",
    "match_keyword_fuzzy",
    # LLM utilities
    "call_vertex_ai_llm",
]


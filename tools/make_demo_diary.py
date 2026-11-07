"""Builds a 3-week demo diary (DiaryFile format 3) for screenshots, imported via Settings > Your data.

Planted pattern: an onion dish at lunch on 6 days, 3-4 days apart, bloating the next afternoon (24-26 h later)
on 5 of them. Fructans are slow fermenters, so the app times them 12-48 h (GutReaction.SlowFermentation).
One unrelated mild bloat on a comparison day. Yesterday's lunch is the onion dish and today's bloat is at
~13:50, so Home and Symptom detail have something live. Run after 14:00 emulator time.
usage: py make_demo_diary.py <seed dishes_001.ndjson> <out.json>
"""
import json, random, sys
from datetime import datetime, timedelta, timezone

TZ = timezone(timedelta(hours=-6))  # emulator: America/Mexico_City
random.seed(7)

seed_path, out_path = sys.argv[1:3]

ingredients, dishes = {}, {}
for line in open(seed_path, encoding="utf8"):
    row = json.loads(line)
    (ingredients if row["op"] == "ingredient" else dishes)[row.get("name") or row["key"]] = row

# Onion dishes share their other ingredients (bread, rice, beef, salad veg) with the calm-day menu, and
# the menus are small and repeated, so only onion stands apart (no 3-of-3 flukes on rare foods).
BREAKFASTS = {"avocado toast": "carbohydrates", "instant oatmeal": "carbohydrates",
              "scrambled eggs": "protein", "toast": "carbohydrates"}
ONION_LUNCHES = {"steak sandwich": "protein", "pulao": "carbohydrates", "chopped salad": "vegetables"}
SAFE_LUNCHES = {"grilled chicken sandwich": "protein", "garden salad": "vegetables", "tuna sandwich": "protein",
                "jeera rice": "carbohydrates"}
DINNERS = {"grilled chicken": "protein", "carne asada": "protein", "grilled salmon": "protein", "jeera rice": "carbohydrates",
           "garden salad": "vegetables"}
YESTERDAY_LUNCH = "steak sandwich"
for menu in (BREAKFASTS, ONION_LUNCHES, SAFE_LUNCHES, DINNERS):
    for key in menu:
        assert key in dishes, f"not a seed dish: {key}"
for key in [*BREAKFASTS, *SAFE_LUNCHES, *DINNERS]:
    assert "onion" not in dishes[key]["ingredients"], f"onion leaks into a safe dish: {key}"

today = datetime.now(TZ).replace(hour=0, minute=0, second=0, microsecond=0)
ONION_DAYS = {-20, -16, -12, -8, -4, -1}  # >=3 days apart: a 48 h window must not reach the next bloat
NO_BLOAT_DAYS = {-12}
STRAY_BLOAT_DAY = -9

meals, components, comp_ings, symptoms, groups, group_ids = [], [], [], [], [], {}


def ms(dt):
    return int(dt.timestamp() * 1000)


def bucket_end(dt):
    for start, end in ((0, 3), (3, 12), (12, 18), (18, 21), (21, 24)):
        if start <= dt.hour < end:
            return dt.replace(hour=0, minute=0) + timedelta(hours=end)


def group_for(dt):
    end = bucket_end(dt)
    if end not in group_ids:
        group_ids[end] = len(groups) + 1
        groups.append({"id": group_ids[end], "createdAt": ms(dt), "lastGroupEntryTime": ms(end)})
    return group_ids[end]


def at(day, hour, minute_spread=40):
    return today + timedelta(days=day, hours=hour, minutes=random.randint(0, minute_spread))


def log_meal(dish_key, category, dt):
    dish, meal_id = dishes[dish_key], len(meals) + 1
    name = dish_key.capitalize()
    attrs = sorted({a for i in dish["ingredients"] + dish.get("trace", []) for a in ingredients.get(i, {}).get("attributes", [])})
    meals.append({"id": meal_id, "name": name, "dateCreated": ms(dt), "groupId": group_for(dt), "dishKey": dish_key})
    components.append({"id": meal_id, "entryId": meal_id, "name": name, "category": category, "labels": [], "attributes": attrs})
    for ing, trace in [(i, False) for i in dish["ingredients"]] + [(i, True) for i in dish.get("trace", [])]:
        comp_ings.append({"componentId": meal_id, "ingredient": ing, "source": "seed", "eatenAt": ms(dt),
                          "attributes": ingredients.get(ing, {}).get("attributes", []), "isTrace": trace})


def log_symptom(kind, severity, dt):
    symptoms.append({"id": len(symptoms) + 1, "type": kind, "severity": severity, "dateCreated": ms(dt), "groupId": group_for(dt)})


for day in range(-20, 1):
    log_meal(*random.choice(list(BREAKFASTS.items())), at(day, 7, 60))
    lunch_time = today + timedelta(days=day, hours=12, minutes=20) if day >= -1 else at(day, 12, 50)
    if day in ONION_DAYS:
        dish = YESTERDAY_LUNCH if day == -1 else random.choice(list(ONION_LUNCHES))
        log_meal(dish, ONION_LUNCHES[dish], lunch_time)
        if day not in NO_BLOAT_DAYS:
            delay = 25.5 if day == -1 else random.uniform(24, 26)
            severity = "moderate" if day == -1 else random.choice(["moderate", "moderate", "severe"])
            log_symptom("bloating", severity, lunch_time + timedelta(hours=delay))
            if day < -1 and random.random() < 0.4:
                log_symptom("gas", "mild", lunch_time + timedelta(hours=delay + random.uniform(1, 3)))
    else:
        log_meal(*random.choice(list(SAFE_LUNCHES.items())), lunch_time)
    if day < 0:
        log_meal(*random.choice(list(DINNERS.items())), at(day, 19, 50))
    if day == STRAY_BLOAT_DAY:
        log_symptom("bloating", "mild", at(day, 21, 30))

seen_recent = {}
for m in meals:
    seen_recent[m["name"]] = m["dateCreated"]

created = ms(today + timedelta(days=-21, hours=9))
diary = {
    "header": {"formatVersion": 3, "dbSchemaVersion": 1, "appVersion": "1.0", "exportedAt": ms(datetime.now(TZ))},
    "mealEntries": meals,
    "mealComponents": components,
    "mealComponentIngredients": comp_ings,
    "symptomEntries": symptoms,
    "symptomIngredientMarks": [],
    "entryGroups": groups,
    # Answers from a real run of the quiz: bloating most days, pain 2-3 days a week (Gas Prone).
    "digestiveProfiles": [{"id": 1, "primaryArchetype": "GAS_PRONE", "secondaryArchetype": None,
                           "acidRefluxValue": 1, "upperGutValue": 0, "gasBloatingValue": 3, "bellyPainValue": 2,
                           "stoolFrequencyValue": 2, "stoolFormValue": 1, "bowelRegularityValue": 0,
                           "stressGutValue": 1, "foodReactivityValue": 2, "dateCreated": created, "dateUpdated": created}],
    "suspectedFoods": [{"ingredient": "milk", "dateAdded": created}, {"ingredient": "coffee", "dateAdded": created}],
    "recentMeals": [{"id": i + 1, "name": n, "dateCreated": t} for i, (n, t) in enumerate(seen_recent.items())],
    "userDishIngredients": [],
    "userLookupNames": [],
    "preferences": {"theme": 0, "ingredientHintShownCount": 3, "isIngredientHintDismissed": True,
                    "seenAnswerKeys": [], "seenCueKeys": []},
}
json.dump(diary, open(out_path, "w", encoding="utf8"))
print(f"{len(meals)} meals, {len(symptoms)} symptoms, {len(groups)} groups")

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.services.features.shared import (
    add_note,
    blob_payload,
    is_missing_blob,
    to_float,
    to_int,
)


def features_from_nutrition(
    *,
    blob: dict[str, Any] | None,
    notes: list[str],
) -> dict[str, int | float | None]:
    output = {
        "calories_in_kcal": None,
        "carbs_g": None,
        "fat_g": None,
        "protein_g": None,
    }
    if is_missing_blob(blob):
        add_note(notes, "missing_nutrition")
        return output

    payload = blob_payload(blob)
    summary = payload.get("summary") if isinstance(payload.get("summary"), Mapping) else {}
    output["calories_in_kcal"] = to_int(summary.get("calories"))
    output["carbs_g"] = to_float(summary.get("carbs"))
    output["fat_g"] = to_float(summary.get("fat"))
    output["protein_g"] = to_float(summary.get("protein"))

    if all(v is None for v in output.values()):
        add_note(notes, "partial_nutrition")
    elif any(v is None for v in output.values()):
        add_note(notes, "partial_nutrition")
    return output


def features_from_water(*, blob: dict[str, Any] | None, notes: list[str]) -> dict[str, int | None]:
    output = {"water_ml": None}
    if is_missing_blob(blob):
        add_note(notes, "missing_water")
        return output

    payload = blob_payload(blob)
    summary = payload.get("summary") if isinstance(payload.get("summary"), Mapping) else {}
    output["water_ml"] = to_int(summary.get("water"))
    if output["water_ml"] is None:
        water_entries = payload.get("water")
        if isinstance(water_entries, list) and water_entries:
            for entry in water_entries:
                if isinstance(entry, Mapping):
                    amount = to_float(entry.get("amount"))
                    if amount is not None:
                        output["water_ml"] = int(amount)
                        break

    if output["water_ml"] is None:
        add_note(notes, "partial_water")
    return output


def extract_nutrition_metrics(
    *,
    nutrition_blob: dict[str, Any] | None,
    water_blob: dict[str, Any] | None,
) -> dict[str, Any]:
    output: dict[str, Any] = {
        "totalCaloriesIntake": None,
        "snackCaloriesFraction": None,
        "caloriesFromMeals": None,
        "caloriesFromSnacks": None,
        "totalCarbsGrams": None,
        "totalFatGrams": None,
        "totalFiberGrams": None,
        "totalProteinGrams": None,
        "totalSodiumMg": None,
        "totalWaterMl": None,
        "mealsLoggedCount": None,
        "caloriesPerMealAvg": None,
    }
    nutrition_payload = blob_payload(nutrition_blob)
    summary = nutrition_payload.get("summary")
    if isinstance(summary, Mapping):
        output["totalCaloriesIntake"] = to_float(summary.get("calories"))
        output["totalCarbsGrams"] = to_float(summary.get("carbs"))
        output["totalFatGrams"] = to_float(summary.get("fat"))
        output["totalFiberGrams"] = to_float(summary.get("fiber"))
        output["totalProteinGrams"] = to_float(summary.get("protein"))
        output["totalSodiumMg"] = to_float(summary.get("sodium"))

    foods = nutrition_payload.get("foods")
    if isinstance(foods, list):
        meal_count = 0
        meal_calories = 0.0
        snack_calories = 0.0
        for food in foods:
            if not isinstance(food, Mapping):
                continue
            calories = to_float(food.get("calories"))
            if calories is None:
                continue
            meal_type = food.get("mealTypeId")
            if meal_type in (4, "4"):
                snack_calories += calories
            else:
                meal_calories += calories
            meal_count += 1
        if meal_count > 0:
            output["mealsLoggedCount"] = meal_count
            output["caloriesPerMealAvg"] = (meal_calories + snack_calories) / meal_count
            output["caloriesFromMeals"] = meal_calories
            output["caloriesFromSnacks"] = snack_calories
            total = meal_calories + snack_calories
            if total > 0:
                output["snackCaloriesFraction"] = snack_calories / total

    water_payload = blob_payload(water_blob)
    water_summary = water_payload.get("summary")
    if isinstance(water_summary, Mapping):
        output["totalWaterMl"] = to_float(water_summary.get("water"))
    return output

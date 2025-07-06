import pandas as pd
import random
from collections import defaultdict

CSV_FILE = "2025 Rankings 2 - Rankings.csv"
NUM_TEAMS = 10
ROUNDS = 17
YOUR_PICK = 2  # 1-indexed for easier CLI reading

MAX_POSITION_LIMITS = {"QB": 4, "RB": 8, "WR": 8, "TE": 3}
STARTER_LIMITS = {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "FLEX": 2}

BENCH_TEMPLATE_OPTIONS = [
    {"QB": 1, "RB": 3, "WR": 3, "TE": 1},
    {"QB": 1, "RB": 4, "WR": 3, "TE": 0},
    {"QB": 1, "RB": 2, "WR": 5, "TE": 0},
    {"QB": 1, "RB": 3, "WR": 4, "TE": 0},
    {"QB": 1, "RB": 4, "WR": 2, "TE": 1},
    {"QB": 1, "RB": 2, "WR": 4, "TE": 1},
    {"QB": 0, "RB": 4, "WR": 3, "TE": 1},
    {"QB": 0, "RB": 3, "WR": 4, "TE": 1}
]

def load_player_pool():
    df = pd.read_csv(CSV_FILE)
    df = df.rename(columns={
        "Player Name": "name",
        "Pos": "position",
        "Ovr Rank": "rank",
        "ADP": "adp"
    })
    df = df[~df["position"].isin(["D/ST", "K"])]
    df = df[["name", "position", "rank", "adp"]].dropna()
    df["rank"] = df["rank"].astype(int)
    df["adp"] = df["adp"].astype(float)
    return df.sort_values(by="rank").to_dict("records")

def get_bench_target():
    return random.choice(BENCH_TEMPLATE_OPTIONS)

def fits_needs(roster, player, round_number, total_rounds, strategy):
    pos = player["position"]
    counts = defaultdict(int)
    for p in roster:
        counts[p["position"]] += 1

    if counts[pos] >= MAX_POSITION_LIMITS[pos]:
        return False

    # Strategy filtering for YOUR team only
    if strategy:
        if strategy == "Zero RB" and round_number < 5 and pos == "RB":
            return False
        if strategy == "Hero RB" and round_number < 5 and pos == "RB" and counts["RB"] >= 1:
            return False
        if strategy == "Robust RB" and round_number >= 4 and counts["RB"] < 3:
            return pos == "RB"
        if strategy == "QB Early" and round_number < 2 and pos != "QB":
            return False
        if strategy == "TE Early" and round_number < 2 and pos != "TE":
            return False

    # Starters
    if round_number < total_rounds - 8:
        total_flex = counts["RB"] + counts["WR"] + counts["TE"]
        if pos in ["RB", "WR", "TE"]:
            return (
                counts[pos] < STARTER_LIMITS[pos]
                or total_flex < (
                    STARTER_LIMITS["RB"] + STARTER_LIMITS["WR"] +
                    STARTER_LIMITS["TE"] + STARTER_LIMITS["FLEX"]
                )
            )
        return counts[pos] < STARTER_LIMITS.get(pos, 1)

    # Bench
    bench_plan = get_bench_target()
    bench_counts = defaultdict(int)
    for p in roster[-8:]:
        bench_counts[p["position"]] += 1
    return bench_counts[pos] < bench_plan.get(pos, 8)

def simulate_draft(strategy):
    players = load_player_pool()
    draft_order = list(range(NUM_TEAMS))
    results = {team: [] for team in range(NUM_TEAMS)}

    for rnd in range(ROUNDS):
        order = draft_order if rnd % 2 == 0 else list(reversed(draft_order))
        for team in order:
            for i, player in enumerate(players):
                team_strategy = strategy if team == YOUR_PICK - 1 else None
                if fits_needs(results[team], player, rnd, ROUNDS, team_strategy):
                    results[team].append(player)
                    players = [p for p in players if p["name"] != player["name"]]
                    break
    return results

def team_grade(roster):
    starters = sorted(roster, key=lambda p: p["rank"])[:9]
    total_rank = sum(p["rank"] for p in starters)
    return round(1000 / (1 + total_rank), 2)

def print_team(roster):
    for i, p in enumerate(roster, 1):
        print(f"  Round {i:2}: {p['name']} ({p['position']}) - Rank: {p['rank']} | ADP: {p['adp']}")

def run_simulations():
    strategies = ["Zero RB", "Hero RB", "Robust RB", "QB Early", "TE Early"]
    print("=== Strategy Simulation Results ===\n")
    for strategy in strategies:
        draft = simulate_draft(strategy)
        team = draft[YOUR_PICK - 1]
        score = team_grade(team)

        print(f"\n--- Strategy: {strategy} ---")
        print_team(team)
        print(f"➤ Grade Score: {score}")

if __name__ == "__main__":
    run_simulations()

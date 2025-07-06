import pandas as pd
import argparse
import random
from collections import defaultdict

# === CONFIG ===
CSV_FILE = "2025 Rankings 2 - Rankings.csv"

# === POSITION LIMITS (roster structure) ===
MAX_POSITION_LIMITS = {
    "QB": 4,
    "RB": 8,
    "WR": 8,
    "TE": 3
}

STARTER_LIMITS = {
    "QB": 1,
    "RB": 2,
    "WR": 2,
    "TE": 1,
    "FLEX": 2
}

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

def get_bench_target():
    return random.choice(BENCH_TEMPLATE_OPTIONS)

def load_player_pool():
    df = pd.read_csv(CSV_FILE)
    df = df.rename(columns={
        "Player Name": "name",
        "Pos": "position",
        "Ovr Rank": "rank",
        "ADP": "adp"
    })

    df = df[~df["position"].isin(["D/ST", "K"])]
    df = df[["name", "position", "rank", "adp"]].dropna(subset=["name", "position", "rank", "adp"])
    df["rank"] = df["rank"].astype(int)
    df["adp"] = df["adp"].astype(float)

    ranked = df.sort_values(by="rank").to_dict("records")
    adp_sorted = df.sort_values(by="adp").to_dict("records")
    return ranked, adp_sorted

def fits_needs(roster, player, round_number, total_rounds):
    pos = player["position"]
    counts = defaultdict(int)
    for p in roster:
        counts[p["position"]] += 1

    if counts[pos] >= MAX_POSITION_LIMITS[pos]:
        return False

    if round_number < total_rounds - 8:
        if pos in ["RB", "WR", "TE"]:
            total_flex = counts["RB"] + counts["WR"] + counts["TE"]
            return (
                counts[pos] < STARTER_LIMITS[pos]
                or total_flex < (
                    STARTER_LIMITS["RB"] + STARTER_LIMITS["WR"] +
                    STARTER_LIMITS["TE"] + STARTER_LIMITS["FLEX"]
                )
            )
        return counts[pos] < STARTER_LIMITS.get(pos, 1)
    else:
        bench_plan = get_bench_target()
        bench_counts = defaultdict(int)
        for p in roster[len(roster)-8:]:
            bench_counts[p["position"]] += 1
        return bench_counts[pos] < bench_plan.get(pos, 8)

def simulate_draft(teams, rounds, your_pick):
    ranked_players, adp_players = load_player_pool()
    draft_order = list(range(teams))
    results = {team: [] for team in range(teams)}
    your_pick = your_pick - 1

    for rnd in range(rounds):
        order = draft_order if rnd % 2 == 0 else list(reversed(draft_order))
        for team in order:
            pool = ranked_players if team == your_pick else adp_players
            for i, player in enumerate(pool):
                if fits_needs(results[team], player, rnd, rounds):
                    results[team].append(player)
                    ranked_players = [p for p in ranked_players if p["name"] != player["name"]]
                    adp_players = [p for p in adp_players if p["name"] != player["name"]]
                    break
    return results

def team_grade(roster):
    starters = sorted(roster, key=lambda p: p["rank"])[:9]
    total_rank = sum(p["rank"] for p in starters)
    score = round(1000 / (1 + total_rank), 2)  # higher is better
    return score

def display_results(results, your_pick):
    print("\n=== Draft Results ===\n")
    for team, picks in results.items():
        label = f"Team {team + 1}" + (" (You)" if team == your_pick else "")
        print(f"{label}:")
        for i, p in enumerate(picks, 1):
            print(f"  Round {i}: {p['name']} ({p['position']}) - Rank: {p['rank']} / ADP: {p['adp']}")
        grade = team_grade(picks)
        print(f"  ➤ Grade Score: {grade}")
        print()

def main():
    parser = argparse.ArgumentParser(description="Fantasy Football Draft Simulator")
    parser.add_argument("--teams", type=int, default=10, help="Number of teams")
    parser.add_argument("--rounds", type=int, default=17, help="Total rounds including starters + 8 bench")
    parser.add_argument("--your-pick", type=int, default=1, help="Your draft position (0-indexed)")
    args = parser.parse_args()
    args.your_pick = args.your_pick - 1

    draft = simulate_draft(args.teams, args.rounds, args.your_pick)
    display_results(draft, args.your_pick)

if __name__ == "__main__":
    main()

import random
from app import Game

NCAPS = 3
NRIFTS = 3

def run_test(seed, nc=NCAPS, nr=NRIFTS, policy="intelligent", bankai=True):
    """Run a single simulation with specified settings"""
    random.seed(seed)
    g = Game(ncaps=nc, nrifts=nr, bankai_enabled=bankai)
    
    metrics = {"logical": 0, "guess": 0, "goal": 0, "bankai": False}
    max_steps = 100

    while g.alive and not g.won and g.steps < max_steps:
        pre_bankai = g.has_bankai
        
        if policy == "random":
            g.rand_step()
        else:
            g.step()

        if g.move_type == "inferred": metrics["logical"] += 1
        elif g.move_type == "goal-directed": metrics["goal"] += 1
        elif g.move_type == "probabilistic": metrics["guess"] += 1

        if pre_bankai and not g.has_bankai:
            metrics["bankai"] = True

    reason = "none"
    if not g.won:
        last = g.log[-1] if g.log else ""
        if not g.alive:
            if "[dead]" in last: reason = "captain"
            elif "[rift]" in last: reason = "rift"
        elif g.steps >= max_steps:
            reason = "timeout"
        else:
            reason = "stuck"

    return {
        "won": g.won, "reason": reason, "steps": g.steps, 
        "logical": metrics["logical"], "goal": metrics["goal"],
        "guess": metrics["guess"], "bankai": metrics["bankai"]
    }

def batch_test(seeds, nc=NCAPS, nr=NRIFTS, policy="intelligent", bankai=True):
    results = [run_test(s, nc, nr, policy, bankai) for s in seeds]
    wins = [r for r in results if r["won"]]
    
    def avg(data, key):
        return round(sum(r[key] for r in data) / len(data), 2) if data else 0

    stats = {
        "rate": round(len(wins) / len(results) * 100, 1) if results else 0,
        "avg_steps": avg(results, "steps"),
        "avg_log": avg(results, "logical"),
        "avg_goal": avg(results, "goal"),
        "avg_guess": avg(results, "guess"),
        "death_cap": sum(1 for r in results if r["reason"] == "captain"),
        "death_rift": sum(1 for r in results if r["reason"] == "rift"),
        "stuck": sum(1 for r in results if r["reason"] == "stuck"),
        "timeout": sum(1 for r in results if r["reason"] == "timeout"),
        "bankai_rate": round(sum(1 for r in results if r["bankai"]) / len(results) * 100, 1) if results else 0,
    }
    return stats

def print_table(stats, title=""):
    if title: print(f"\n{title}")
    print("="*40)
    print(f"{'STAT':<20} | {'VALUE':<15}")
    print("-" * 40)
    print(f"{'Win rate':<20} | {stats['rate']}%")
    print(f"{'Avg logic moves':<20} | {stats['avg_log']}")
    print(f"{'Avg goal moves':<20} | {stats['avg_goal']}")
    print(f"{'Avg guesses':<20} | {stats['avg_guess']}")
    print(f"{'Bankai usage':<20} | {stats['bankai_rate']}%")
    print("-" * 40)
    print(f"Fail - captain: {stats['death_cap']}")
    print(f"Fail - rift:    {stats['death_rift']}")
    print(f"Fail - stuck:   {stats['stuck']}")
    print(f"Fail - timeout: {stats['timeout']}")
    print("="*40)

def main():
    print("Bleach world evaluation")
    seeds = list(range(100))
    
    # 1. Main Intelligent agent stats
    int_stats = batch_test(seeds)
    print_table(int_stats, "Intelligent agent (100 trials)")

    # 2. Baseline comparison
    rnd_stats = batch_test(seeds, policy="random")
    print("\nBaseline comparison")
    print(f"{'Agent':<20} | {'Win%':>6} | {'Avg Steps':>10}")
    print("-" * 40)
    print(f"{'Intelligent':<20} | {int_stats['rate']:>5}% | {int_stats['avg_steps']:>10}")
    print(f"{'Random':<20} | {rnd_stats['rate']:>5}% | {rnd_stats['avg_steps']:>10}")


    # 3. Bankai Impact
    off_stats = batch_test(seeds, bankai=False)
    print("\n Bankai impact test")
    print(f"{'Condition':<20} | {'Win%':>6} | {'Cap Deaths':>10}")
    print("-" * 40)
    print(f"{'Bankai enabled':<20} | {int_stats['rate']:>5}% | {int_stats['death_cap']:>10}")
    print(f"{'Bankai disabled':<20} | {off_stats['rate']:>5}% | {off_stats['death_cap']:>10}")

    # 4. Scaling
    print("\nTesting scaling")
    print(f"{'Mode':<10} | {'Win Rate':<10}")
    for label, nc, nr in [("Easy", 2, 2), ("Hard", 3, 2), ("Insane", 3, 3)]:
        s = batch_test(list(range(20)), nc, nr)
        print(f"{label:<10} | {s['rate']}%")

if __name__ == "__main__":
    main()
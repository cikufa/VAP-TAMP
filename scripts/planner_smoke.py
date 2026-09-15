"""Exercise released PDDL wrapper on original firewood; no simulator or VLM."""
import contextlib
import datetime
import io
import json
import os
from pathlib import Path
import subprocess
import sys


def main():
    root = Path(__file__).resolve().parents[1]
    expected_python = root / ".runtime/envs/vaptamp-repro/bin/python"
    if Path(sys.prefix).resolve() != expected_python.parent.parent.resolve():
        raise RuntimeError(f"Use the dedicated environment: {expected_python}")
    source = root / "vlm-tamp"
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    out = root / "results/original/planner_smoke" / stamp
    out.mkdir(parents=True, exist_ok=False)
    for name in ("downward", "VAL"):
        (out / name).symlink_to(source / name, target_is_directory=True)
    os.environ["PATH"] = str(expected_python.parent) + os.pathsep + os.environ["PATH"]
    sys.path.insert(0, str(source))
    from pddl_sim import pddlsim

    domain = source / "domains/store_firewood/domain.pddl"
    problem = source / "domains/store_firewood/problem.pddl"
    planner = pddlsim(str(domain))
    previous = Path.cwd()
    log = io.StringIO()
    try:
        os.chdir(out)
        with contextlib.redirect_stdout(log):
            plan = planner.plan(str(problem))
            if not plan:
                raise RuntimeError("Released planner returned no plan")
            states = planner.get_intermediate_states(str(problem), "pddl_output.txt")
            if not states or len(states) != len(plan) + 1:
                raise RuntimeError("VAL intermediate-state trace length is inconsistent")
            trace = []
            for index, action in enumerate(plan):
                trace.append({
                    "action": action,
                    "preconditions": planner.get_preconditions_by_action(action),
                    "effects": planner.get_effects_by_states(states[index], states[index + 1]),
                    "state_before": states[index],
                    "state_after": states[index + 1],
                })
            for item in (2, 3):
                goal = f"(ontop wooden_stick-n-01_{item} table-n-02_1)"
                if goal not in states[-1]:
                    raise RuntimeError(f"Missing goal in final symbolic state: {goal}")
            validate = subprocess.run([
                str(source / "VAL/build/linux64/Release/bin/Validate"), "-v",
                str(domain), str(problem), str(out / "pddl_output.txt"),
            ], capture_output=True, text=True, check=True)
            (out / "val.txt").write_text(validate.stdout + validate.stderr)
            if "Plan valid" not in validate.stdout:
                raise RuntimeError("Validator did not certify the plan")
            result = {
                "status": "passed",
                "scope": "symbolic planner smoke only; no physics, images or VLM",
                "task": "store_firewood", "plan_length": len(plan),
                "intermediate_state_count": len(states), "trace": trace,
            }
            (out / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    finally:
        os.chdir(previous)
        (out / "wrapper_stdout.txt").write_text(log.getvalue())
        print(f"Artifacts: {out}")
    print(f"PASS: {len(plan)} original actions; {len(states)} symbolic states; VAL valid")


if __name__ == "__main__":
    main()

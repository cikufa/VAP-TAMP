"""Run the released full-verification firewood configuration in an output sandbox.

This launcher does not reconstruct active perception or implement a custom task.
Episode completion must be reviewed separately from process exit status.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time


def main():
    from native_runtime import apply_cpu_affinity
    apply_cpu_affinity()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--trials", type=int, default=1)
    parser.add_argument("--timeout-seconds", type=int, default=1200)
    parser.add_argument('--task', choices=['store_firewood','bringing_water'], default='store_firewood')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    prefix = root / ".runtime/envs/vaptamp-repro"
    if Path(sys.prefix).resolve() != prefix.resolve():
        raise RuntimeError("Use the dedicated environment")
    from dotenv import load_dotenv
    load_dotenv(root / ".env", override=False)
    provider = os.getenv('VAPTAMP_VLM_PROVIDER', 'gemini').lower()
    if provider == 'gemini':
        if not (os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')):
            raise RuntimeError("GEMINI_API_KEY is missing; no episode has been started")
        model = os.getenv('VAPTAMP_GEMINI_MODEL', 'gemini-3.5-flash-lite')
    elif provider == 'openai':
        if not os.getenv('OPENAI_API_KEY'):
            raise RuntimeError("OPENAI_API_KEY is missing; no episode has been started")
        model = os.getenv('VAPTAMP_OPENAI_MODEL', 'gpt-4o-2024-05-13')
    else:
        raise RuntimeError(f"Unsupported VAPTAMP_VLM_PROVIDER: {provider}")
    if not os.getenv("EXP_PATH"):
        raise RuntimeError("Source scripts/engine_runtime.sh before launching")
    scene = {'store_firewood':'Ihlen_0_int','bringing_water':'Wainscott_0_garden'}[args.task]
    if not (root / '.runtime/data/og_dataset/scenes' / scene).is_dir():
        raise RuntimeError("Original scene assets are not installed")
    cached_task = root / '.runtime/data/og_dataset/scenes' / scene / 'json' / f'{scene}_task_{args.task}_0_0_template.json'
    if not cached_task.is_file():
        raise RuntimeError('Released offline firewood task instance is absent; no resampling or scene substitution performed')
    if args.trials < 1 or args.trials > 5:
        raise ValueError("Only a debug episode or a pilot of at most five trials is supported")
    out = root / "results/original/debug_episode" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    out.mkdir(parents=True, exist_ok=False)
    for name in ("domains", "downward", "VAL", "prompts.txt", "planning_prompts.txt"):
        (out / name).symlink_to(root / "vlm-tamp" / name)
    env = os.environ.copy()
    env.update({
        "VAPTAMP_NUM_TRIALS": str(args.trials), "VAPTAMP_SEED": str(args.seed),
        "VAPTAMP_TASK": args.task,
        "VAPTAMP_CHECK_PRECONDITION": "1", "VAPTAMP_CHECK_EFFECT": "1",
        "VAPTAMP_CHECK_IN_NL": "0", "VAPTAMP_VLM_PLANNING": "0",
        "VAPTAMP_LOG_DIR": str(out / "artifacts"),
        "VAPTAMP_TRACE_DIR": str(out / "trace"),
        "OMNIGIBSON_HEADLESS": "True",
        "MPLBACKEND": "Agg",
    })
    metadata = {
        "status": "running", "task": args.task, "scene": scene, "seed": args.seed,
        "fidelity": 'released_default' if args.task=='store_firewood' else 'alternative_released_task_with_cached_scene_deviation',
        "trials": args.trials, "provider": provider, "model": model,
        "released_provider": "openai", "released_model": "gpt-4-turbo",
        "provider_deviation": provider != "openai", "model_deviation": model != "gpt-4-turbo",
        "active_view_motion": False,
        "precondition_verification": True, "effect_verification": True,
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
        "dirty_worktree": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True)),
    }
    (out / "run_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    command = [str(prefix / "bin/python"), "-u", str(root / "vlm-tamp/eval.py"),
               "--portable", "--portable-root", str(root / ".runtime/kit-portable"),
               "--/app/settings/persistent=false", "--/app/settings/loadUserConfig=false",
               "--/app/extensions/fsWatcherEnabled=false",
               "--/structuredLog/logDirectory=" + str(root / ".runtime/structured-logs"),
               "--/app/tokens/omni_global_cache=" + str(root / ".runtime/cache/omni"),
               "--/app/tokens/omni_global_logs=" + str(root / ".runtime/structured-logs"),
               "--/app/tokens/omni_documents=" + str(root / ".runtime/documents"),
               "--/app/tokens/shared_documents=" + str(root / ".runtime/documents/shared"),
               "--/app/tokens/app_documents=" + str(root / ".runtime/documents/app"),
               "--/app/tokens/documents=" + str(root / ".runtime/documents/app"),
               "--/log/file=" + str(out / "kit.log")]
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    started = time.monotonic()
    print("Episode artifacts:", out, flush=True)
    with (out / "terminal.log").open("w") as log:
        child = subprocess.Popen(command, cwd=out, env=env, stdout=log,
                                 stderr=subprocess.STDOUT, start_new_session=True)
        try:
            child.wait(timeout=args.timeout_seconds)
            metadata.update(status="process_exited", exit_code=child.returncode)
        except subprocess.TimeoutExpired:
            metadata.update(status="timeout", exit_code=None)
            os.killpg(child.pid, signal.SIGTERM)
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()
        finally:
            from startup_series import processes
            if processes(child.pid):
                os.killpg(child.pid, signal.SIGKILL)
                time.sleep(2)
            metadata['remaining_processes'] = processes(child.pid)
            metadata["wall_seconds"] = time.monotonic() - started
            (out / "run_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print("Process status:", metadata["status"], metadata["exit_code"])
    from episode_videos import encode_videos
    metadata['videos'] = encode_videos(out / 'artifacts')
    result_path = out / 'exp_results.json'
    metadata['released_results'] = json.loads(result_path.read_text()) if result_path.exists() else None
    events_path = out / 'trace/events.jsonl'
    events = [json.loads(line) for line in events_path.read_text().splitlines()] if events_path.exists() else []
    metadata['completed_trials'] = sum(event.get('event') == 'trial_end' for event in events)
    metadata['final_goal_diagnostics'] = [event.get('final_goal_diagnostics')
                                          for event in events if event.get('event') == 'trial_end']
    metadata['all_requested_trials_completed'] = metadata['completed_trials'] == args.trials
    metadata['cpu_affinity'] = sorted(os.sched_getaffinity(0))
    (out / 'run_metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
    if metadata["exit_code"] != 0:
        raise SystemExit(1)
    if not metadata['all_requested_trials_completed']:
        raise SystemExit('Process exited without completing all requested trials; inspect preserved logs')


if __name__ == "__main__":
    main()

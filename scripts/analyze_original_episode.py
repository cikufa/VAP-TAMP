"""Summarize saved evidence without querying a model or changing trial outcomes."""
import argparse
from collections import Counter
import json
from pathlib import Path


def summarize(directory):
    directory = Path(directory).resolve()
    metadata = json.loads((directory / 'run_metadata.json').read_text())
    trace = directory / 'trace/events.jsonl'
    events = [json.loads(line) for line in trace.read_text().splitlines()] if trace.exists() else []
    counts = Counter(event['event'] for event in events)
    verifications = [event for event in events if event['event'] == 'verification']
    mismatches = [event for event in verifications
                  if event['unmatched_effects'] or event['unmatched_preconditions']]
    malformed = [dict(sequence=event['sequence'], questions=event['questions'],
                      answers=event['visual_answers']) for event in verifications
                 if len(event['questions']) != len(event['visual_answers'])
                 or any(answer.strip().lower() not in ('yes', 'no', 'skip')
                        for answer in event['visual_answers'])]
    skips = [event['sequence'] for event in verifications
             if any(answer.strip().lower() == 'skip' for answer in event['visual_answers'])]
    responses = [event for event in events if event['event'] == 'vlm_response']
    quota_violations = []
    for event in responses:
        if event['http_status'] != 429:
            continue
        body = json.loads(event['body'])
        for detail in body.get('error', {}).get('details', []):
            quota_violations.extend(detail.get('violations', []))
    return dict(
        episode=str(directory), seed=metadata['seed'], git_commit=metadata['git_commit'],
        dirty_worktree=metadata['dirty_worktree'], provider=metadata['provider'], model=metadata['model'],
        verification_mode=metadata.get('verification_mode', 'released'),
        paper_adapter_parameters=metadata.get('paper_adapter_parameters'),
        status=metadata['status'], exit_code=metadata.get('exit_code'),
        wall_seconds=metadata.get('wall_seconds'), completed_trials=counts['trial_end'],
        released_results=metadata.get('released_results'), event_counts=dict(counts),
        mismatch_events=len(mismatches), skip_response_event_sequences=skips,
        malformed_verification_batches=malformed,
        http_status_counts=dict(Counter(str(event['http_status']) for event in responses)),
        quota_violations=quota_violations,
        final_goals=[event.get('final_goal_diagnostics') for event in events
                     if event['event'] == 'trial_end'],
        action_counts=[event['action_count'] for event in events if event['event'] == 'trial_end'],
        remaining_processes=metadata.get('remaining_processes'), videos=metadata.get('videos', []),
        recovery_examples=[dict(sequence=event['sequence'], action_count=event['action_count'],
                                current_action=event['current_action'],
                                next_action=event['next_action'],
                                unmatched_effects=event['unmatched_effects'],
                                unmatched_preconditions=event['unmatched_preconditions'])
                           for event in mismatches[:3]],
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('episodes', type=Path, nargs='+')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    results = [summarize(episode) for episode in args.episodes]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2) + '\n')
    for result in results:
        print(json.dumps({key: result[key] for key in
                          ('seed', 'completed_trials', 'released_results', 'event_counts',
                           'mismatch_events', 'http_status_counts', 'action_counts')}))


if __name__ == '__main__':
    main()

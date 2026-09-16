"""Render each paper vote next to the actual image used for that vote."""
import argparse
from collections import deque
import html
import json
from pathlib import Path


def render(episode):
    episode = Path(episode).resolve()
    events = [json.loads(line) for line in (episode / 'trace/events.jsonl').read_text().splitlines()]
    metadata = json.loads((episode / 'run_metadata.json').read_text())
    views, recent_queries, rows = {}, deque(maxlen=5), []
    for event in events:
        kind = event['event']
        if kind == 'paper_adapter_initialized':
            views, recent_queries = {}, deque(maxlen=5)
        elif kind == 'paper_sensor_observation':
            views[event['index']] = event
        elif kind == 'paper_query_observation':
            recent_queries.append(event)
        elif kind == 'paper_votes_raw':
            if len(recent_queries) != 5 or len({q['pixel_sha256'] for q in recent_queries}) != 1:
                raise ValueError('Five votes are not bound to the same captured image')
            view = views[recent_queries[-1]['observation']]
            rows.append(dict(event=event, view=view, vote=None, sufficiency=None,
                             directions=[], motions=[], result=None))
        elif rows and kind == 'paper_vote':
            rows[-1]['vote'] = event
        elif rows and kind == 'paper_sufficiency_raw':
            rows[-1]['sufficiency'] = event['answer']
        elif rows and kind == 'paper_direction':
            rows[-1]['directions'].append(event['direction'])
        elif rows and kind in ('paper_motion_executed', 'paper_motion_rejected'):
            rows[-1]['motions'].append(kind + (': ' + event['reason'] if event.get('reason') else ''))
        elif rows and kind == 'paper_predicate_result':
            rows[-1]['result'] = event

    escape = lambda value: html.escape(str(value))
    parts = ['<!doctype html><meta charset="utf-8"><title>Paper verification trace</title>',
             '<style>body{font:16px system-ui;margin:2rem;max-width:1200px} '
             'article{border-top:1px solid #aaa;padding:1rem 0;display:flex;gap:2rem} '
             'img{width:256px;height:256px;object-fit:contain} li{margin:.4rem 0} '
             'pre{white-space:pre-wrap} .meta{color:#444}</style>',
             '<h1>Paper verification: actual voted views</h1>',
             '<p>This diagnostic links each five-question vote to its captured image. '
             'The original action summary figure may show a later view; use this report '
             'and the raw trace to identify the evidence for each predicate.</p>',
             '<p class="meta">' + escape(json.dumps({key: metadata.get(key) for key in
                 ('seed', 'model', 'verification_mode', 'git_commit', 'status', 'completed_trials')})) + '</p>']
    for row in rows:
        event, view = row['event'], row['view']
        image = Path(view['image']).relative_to(episode).as_posix()
        parts.append(f'<article><div><a href="{escape(image)}"><img src="{escape(image)}"></a>'
                     f'<p>Voted view {view["index"]}</p></div><div>')
        parts.append(f'<h2>Event {event["sequence"]}: {escape(event["predicate"])}</h2><ol>')
        for question, answer in zip(event['questions'], event['answers']):
            parts.append(f'<li>{escape(question)} <strong>{escape(answer)}</strong></li>')
        parts.append('</ol>')
        if row['vote']:
            parts.append('<p>Majority: ' + escape(row['vote']['value']) +
                         '; agreement: ' + escape(row['vote']['agreement']) + '/5.</p>')
        parts.append('<p>Sufficiency: ' + escape(row['sufficiency'] if row['sufficiency'] is not None
                                              else 'not queried in this round') + '</p>')
        if row['directions']:
            parts.append('<p>Directions: ' + escape(', '.join(row['directions'])) + '</p>')
            parts.append('<p>' + escape('; '.join(row['motions'])) + '</p>')
        if row['result']:
            result = row['result']
            parts.append('<p>Returned value: ' + escape(result['value']) +
                         '; sufficient: ' + escape(result['sufficient']) +
                         '; budget exhausted: ' + escape(result['budget_exhausted']) + '</p>')
            if result['terminal_observation'] != result['voted_observation']:
                parts.append('<p>The terminal observation was not the image used for this returned vote.</p>')
        parts.append('</div></article>')
    output = episode / 'paper_verification_report.html'
    output.write_text('\n'.join(parts) + '\n')
    return output, len(rows)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('episode', type=Path)
    args = parser.parse_args()
    output, count = render(args.episode)
    print(f'{output}: {count} complete same-image voting rounds')

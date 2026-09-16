"""One-command offline metrics, exact counterfactuals, videos and aggregate report."""
import argparse,csv,hashlib,json,sys
from pathlib import Path
from connector_entry import ROOT
sys.path.insert(0,str(ROOT))
from experiments.connector_handoff.metrics import evaluate,aggregate
from experiments.connector_handoff.media import render_all
from replay_connector_counterfactuals import replay

def selected_episodes(root):
    # Only completed non-infrastructure attempts are preferred; never select by task success.
    trial_root=root/'trial_logs'
    if not trial_root.exists():
        return sorted(x.parent for x in root.rglob('episode.json') if 'debug' not in x.parts)
    selected=[]
    for trial in sorted(trial_root.iterdir()):
        candidates=sorted(trial.rglob('episode.json'))
        if not candidates:continue
        eligible=[p for p in candidates if not json.loads(p.read_text()).get('infrastructure_error',True)]
        selected.append((eligible[0] if eligible else candidates[-1]).parent)
    return selected

def main():
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True)
    p.add_argument('--output',type=Path);p.add_argument('--no-replay',action='store_true',help='Metrics remain provisional until missing counterfactuals are supplied')
    p.add_argument('--observability',type=Path,default=ROOT/'results/custom_connector/benchmark_validation/observability/acceptance01/observability.json')
    a=p.parse_args();output=a.output or a.input;output.mkdir(parents=True,exist_ok=True)
    compatibility=json.loads((ROOT/'experiments/connector_handoff/compatibility.json').read_text())
    rows=[]
    for episode in selected_episodes(a.input):
        result=evaluate(episode,compatibility)
        cf=None
        if result['mode']=='LIVE' and result['Y1'] and result['Y2'] is False:
            key=hashlib.sha256(str(episode.resolve()).encode()).hexdigest()[:12]
            folder=ROOT/'results/custom_connector/counterfactuals'/key
            if (folder/'counterfactual.json').exists():cf=json.loads((folder/'counterfactual.json').read_text())
            elif not a.no_replay:cf=replay(episode,folder,a.observability)
        result=evaluate(episode,compatibility,cf);rows.append(result)
        render_all(episode)
        (episode/'metrics.json').write_text(json.dumps(result,indent=2)+'\n')
    summary=aggregate(rows)
    # Preserve all infrastructure attempts in the report, even when later resumed successfully.
    summary['attempt_inventory']=[dict(path=str(p.parent),**{k:v for k,v in json.loads(p.read_text()).items() if k in ('mode','seed','infrastructure_error','error_type')}) for p in sorted(a.input.rglob('episode.json'))]
    summary['unclassified_pending_evidence']=sum(r['category']=='UNCLASSIFIED_PENDING_EVIDENCE' for r in rows)
    summary['missing_counterfactuals']=sum(bool(r['mode']=='LIVE' and r['Y1'] and r['Y2'] is False and not r['counterfactual']) for r in rows)
    summary['interpretation']='INCONCLUSIVE — no automated scientific conclusion; inspect timing, confounds and counterfactual evidence'
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    with (output/'summary.csv').open('w') as f:
        if rows:
            writer=csv.DictWriter(f,fieldnames=rows[0]);writer.writeheader()
            writer.writerows({k:json.dumps(v) if isinstance(v,(list,dict)) else v for k,v in row.items()} for row in rows)
    title='NON-SCIENTIFIC MOCK VLM RUN' if any(r['mode']=='MOCK' for r in rows) else 'Connector live evaluation'
    lines=[f'# {title}','','Mock data cannot establish or falsify a scientific gap.' if 'MOCK' in title else 'Completed trial failures are retained. Debug trials are excluded.',
           '',f"Interpretation: {summary['interpretation']}",'', '| Seed | Condition | Grasp | Y1 | First Y2 | Timing | Final | Category |','|---|---|---|---|---|---|---|---|']
    lines += [f"| {r['seed']} | {r['condition']} | {r['grasp_choice']} | {r['Y1']} | {r['Y2']} | {r['timing']} | {r['final_success']} | {r['category']} |" for r in rows]
    lines += ['', 'Y2 is the first handoff, including abandonment; final success includes recovery. See first_insert_attempted before interpreting a physical failure.',
              '', '[Machine-readable metrics](summary.json) · [Per-trial table](summary.csv)',
              '', '## Artifacts','']
    for r in rows:
        ep=Path(r['episode']).resolve()
        lines.append(f"- Seed {r['seed']}: [video]({ep}/episode.mp4), [contact sheet]({ep}/episode_contact_sheet.png), [timeline]({ep}/episode_timeline.png), [trace]({ep}/events.jsonl)")
    (output/'report.md').write_text('\n'.join(lines)+'\n');print(output/'report.md')
if __name__=='__main__':main()

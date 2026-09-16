"""Use the released planner/VAL wrapper on nominal and corrected connector states."""
import json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'vlm-tamp'))
from pddl_sim import pddlsim
out=ROOT/'results/custom_connector/benchmark_validation/pddl';out.mkdir(parents=True,exist_ok=True)
for name in ('downward','VAL'):
 if not (out/name).exists():(out/name).symlink_to(ROOT/'vlm-tamp'/name)
os.chdir(out);domain=ROOT/'experiments/connector_handoff/pddl/domain.pddl';source=(domain.parent/'problem.pddl').read_text()
planner=pddlsim(str(domain));rows=[]
for variant,clear in [('nominal',None),('left_blocked','left'),('right_blocked','right')]:
 text=source if clear is None else source.replace(f'        (side_clear_{clear} socket)\n','')
 problem=out/f'{variant}.pddl';problem.write_text(text)
 plan=planner.plan(str(problem));assert plan,variant
 states=planner.get_intermediate_states(str(problem),'pddl_output.txt');assert states and '(inserted connector socket)' in states[-1]
 (out/f'{variant}_plan.txt').write_text(Path('pddl_output.txt').read_text())
 pres=[planner.get_preconditions_by_action(a) for a in plan]
 for a,p in zip(plan,pres):
  if a[0].startswith('grasp'):assert not any('side_clear' in ' '.join(f) for f in p)
 rows.append(dict(variant=variant,plan=plan,preconditions=pres,states=states))
(out/'validation.json').write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps([dict(variant=x['variant'],plan=x['plan']) for x in rows],indent=2))

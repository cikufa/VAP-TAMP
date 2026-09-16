"""Bind new task dispatch to the frozen released eval loop using its actual AST.

Only the action dispatcher and plotting block are substituted. Verification,
state correction, when to replan, ordering, and termination logic stay intact.
"""
import ast,copy,hashlib,json,os,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASELINE=ROOT/'vlm-tamp/eval.py'
FUNCTIONS=('update_states_by_fact','write_states_into_problem','check_states_and_update_problem','format_action_params')


def compile_loop(scope):
    source=BASELINE.read_text();tree=ast.parse(source)
    definitions=[copy.deepcopy(n) for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in FUNCTIONS]
    assert len(definitions)==len(FUNCTIONS)
    exec(compile(ast.Module(body=definitions,type_ignores=[]),str(BASELINE),'exec'),scope)
    outer=next(n for n in tree.body if isinstance(n,ast.While))
    loop=copy.deepcopy(next(n for n in outer.body if isinstance(n,ast.While)))
    class Bind(ast.NodeTransformer):
        dispatches=0;plots=0
        def visit_If(self,node):
            if ast.unparse(node.test)=="primitive == 'find'":
                self.dispatches+=1
                return ast.copy_location(ast.Expr(value=ast.Call(func=ast.Name(id='dispatch',ctx=ast.Load()),
                    args=[ast.Name(id='action',ctx=ast.Load())],keywords=[])),node)
            if ast.unparse(node.test)=='CHECK_EFFECT or CHECK_PRECONDITION':
                start=next(i for i,n in enumerate(node.body) if isinstance(n,ast.ImportFrom) and n.module=='matplotlib')
                end=next(i for i,n in enumerate(node.body) if isinstance(n,ast.Expr) and ast.unparse(n).startswith('plt.close('))
                node.body[start:end+1]=[ast.Expr(value=ast.Call(func=ast.Name(id='diagnostic_frame',ctx=ast.Load()),args=[],keywords=[]))]
                self.plots+=1
            return self.generic_visit(node)
    bind=Bind();loop=bind.visit(loop);assert (bind.dispatches,bind.plots)==(1,1)
    module=ast.fix_missing_locations(ast.Module(body=[loop],type_ignores=[]))
    scope['record']('baseline_binding',source_sha256=hashlib.sha256(source.encode()).hexdigest(),
        substitutions=['task primitive dispatch','offline visualization callback'],decision_logic_changes=False)
    return compile(module,str(BASELINE)+'::connector-binding','exec')


class LoggedPlanner:
    def __init__(self,domain,out,log):
        import importlib.util,types
        spec=importlib.util.spec_from_file_location('connector_logged_pddl',ROOT/'vlm-tamp/pddl_sim.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        module.subprocess=types.SimpleNamespace(check_output=self.capture_output,
            CalledProcessError=__import__('subprocess').CalledProcessError)
        self.inner=module.pddlsim(str(domain));self.out=Path(out);self.out.mkdir(exist_ok=True)
        self.domain=Path(domain);self.log=log;self.count=0
    def capture_output(self,*args,**kwargs):
        import subprocess
        suffix='val' if 'Validate' in str(args[0]) else 'fd'
        path=self.out/f'{max(0,self.count-1):03d}_{suffix}_stdout.log'
        try:output=subprocess.check_output(*args,**kwargs)
        except subprocess.CalledProcessError as exc:
            path.write_bytes(exc.output or b'');raise
        path.write_bytes(output);return output
    def plan(self,problem):
        prefix=f'{self.count:03d}';self.count+=1
        (self.out/f'{prefix}_problem.pddl').write_text(Path(problem).read_text())
        start=time.monotonic();plan=self.inner.plan(problem)
        command=f'python ./downward/fast-downward.py --alias seq-opt-fdss-1 --search-time-limit 10 --plan-file pddl_output.txt {self.domain} {problem}'
        info=dict(command=command,runtime=time.monotonic()-start,plan=plan,
                  domain_sha256=hashlib.sha256(self.domain.read_bytes()).hexdigest())
        (self.out/f'{prefix}_planner.json').write_text(json.dumps(info,indent=2)+'\n')
        if Path('pddl_output.txt').exists():(self.out/f'{prefix}_plan.txt').write_text(Path('pddl_output.txt').read_text())
        self.log('planner_call',**info)
        return plan
    def get_intermediate_states(self,*args):
        states=self.inner.get_intermediate_states(*args)
        (self.out/f'{self.count-1:03d}_val_states.json').write_text(json.dumps(states,indent=2)+'\n')
        return states
    def get_preconditions_by_action(self,action):
        from pddl import parse_domain
        from pddl.logic.base import And
        schema=next(a for a in parse_domain(str(self.domain)).actions if a.name==action[0])
        if isinstance(schema.precondition,And):return self.inner.get_preconditions_by_action(action)
        # The released reader assumes a conjunction; parser collapses unary AND.
        # Normalize syntax only, preserving exactly the single positive/negative literal.
        return self.inner.reformat_fact_using_values(action,schema.parameters,[schema.precondition])
    def __getattr__(self,name):return getattr(self.inner,name)

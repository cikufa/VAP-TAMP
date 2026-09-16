import json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'vlm-tamp')]
from experiments.connector_handoff.metrics import evaluate,aggregate
from experiments.connector_handoff.task_binding import questions_for
from experiments.connector_handoff.frozen_pipeline import compile_loop,LoggedPlanner
from experiments.connector_handoff.visibility import evidence

class ConnectorMetricsTests(unittest.TestCase):
    def measure(self,events):
        with tempfile.TemporaryDirectory() as d:
            rows=[]
            for i,e in enumerate(events):rows.append(dict(sequence=i,seconds=i,**e))
            Path(d,'events.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in rows))
            return evaluate(d,{'LEFT_CONSTRAINED':{'gL':0,'gR':1}})
    def start(self):return dict(event='episode_start',mode='LIVE',seed=1,evaluation_only={'scene_condition':'LEFT_CONSTRAINED'})
    def request(self,successor=True):
        return dict(event='vlm_request',round=1,payload={'messages':[{'content':[{'type':'text','text':questions_for(['side_clear_left','socket'])[0] if successor else 'Is the connector visible?'}]}]})
    def observation(self):return dict(event='paper_sensor_observation',index=0,camera_position=[0,0,0],evaluation_only={'visually_relevant':True})
    def motion(self):return dict(event='paper_motion_executed',position_before=[0,0,0],position_after=[0,.25,0])
    def test_abandonment_is_not_physical_attempt(self):
        row=self.measure([self.start(),dict(event='grasp_committed',grasp_choice='gL'),dict(event='grasp_complete',grasp_success=True),dict(event='episode_end',physical_success=False,infrastructure_error=False)])
        self.assertFalse(row['Y2']);self.assertTrue(row['first_handoff_abandoned']);self.assertFalse(row['physical_failed_first_insert'])
    def test_actual_query_time_and_reactive_view(self):
        row=self.measure([self.start(),dict(event='grasp_committed',grasp_choice='gL'),dict(event='grasp_complete',grasp_success=True),self.motion(),self.observation(),dict(event='paper_query_observation',round=1,observation=0),self.request(),dict(event='paper_votes_raw',predicate=['side_clear_left','socket']),dict(event='insert_started'),dict(event='insert_complete',insert_success=False),dict(event='episode_end',physical_success=False,infrastructure_error=False)])
        self.assertEqual(row['T_successor_query'],6);self.assertEqual(row['T_successor_view'],4);self.assertEqual(row['timing'],'REACTIVE');self.assertTrue(row['physical_failed_first_insert'])
    def test_generic_connector_observation_does_not_count(self):
        row=self.measure([self.start(),self.motion(),self.observation(),dict(event='paper_query_observation',round=1,observation=0),self.request(False),dict(event='episode_end',physical_success=False,infrastructure_error=False)])
        self.assertEqual(row['timing'],'NONE');self.assertIsNone(row['T_successor_query'])
    def test_final_unvoted_successor_view_is_acquired(self):
        row=self.measure([self.start(),dict(event='grasp_committed',grasp_choice='gL'),
            dict(event='paper_votes_raw',predicate=['side_clear_left','socket']),self.motion(),self.observation(),
            dict(event='episode_end',physical_success=False,infrastructure_error=False)])
        self.assertEqual(row['timing'],'REACTIVE');self.assertFalse(row['successor_view_was_queried'])
    def test_api_failure_excluded(self):
        row=self.measure([self.start(),dict(event='episode_end',physical_success=False,infrastructure_error=True)])
        self.assertEqual(row['category'],'J');self.assertEqual(aggregate([row])['completed_eligible'],0)
    def test_mock_never_scientific_metrics(self):
        self.assertFalse(aggregate([dict(mode='MOCK')])['scientific_metrics_computed'])
        with self.assertRaises(ValueError):aggregate([dict(mode='MOCK'),dict(mode='LIVE')])

class BindingTests(unittest.TestCase):
    def test_frozen_loop_extracts_only_dispatch_and_visualization(self):
        records=[];scope={'record':lambda *a,**kw:records.append((a,kw))}
        code=compile_loop(scope)
        self.assertIsNotNone(code);self.assertFalse(records[0][1]['decision_logic_changes'])
        self.assertIn('check_states_and_update_problem',scope)
    def test_unary_and_negative_preconditions(self):
        with tempfile.TemporaryDirectory() as d:
            planner=LoggedPlanner(ROOT/'experiments/connector_handoff/pddl/domain.pddl',Path(d),lambda *a,**k:None)
            self.assertEqual(planner.get_preconditions_by_action(['return_connector','robot','connector','socket','(1)']),[['holding','robot','connector']])
            self.assertEqual(planner.get_preconditions_by_action(['find','robot','connector','(1)']),[['not','inview','robot','connector']])
    def test_grasp_contains_no_successor_requirement(self):
        from pddl import parse_domain
        domain=parse_domain(str(ROOT/'experiments/connector_handoff/pddl/domain.pddl'))
        for action in domain.actions:
            if action.name.startswith('grasp'):
                self.assertNotIn('side_clear',str(action.precondition));self.assertNotIn('socket',str(action.precondition))
    def test_frozen_balanced_seed_design(self):
        data=json.loads((ROOT/'experiments/connector_handoff/eval_seeds.json').read_text())
        self.assertEqual(len(data['trials']),20)
        for c in ('LEFT_CONSTRAINED','RIGHT_CONSTRAINED'):self.assertEqual(sum(x['condition']==c for x in data['trials']),10)
        self.assertEqual(len({x['seed'] for x in data['trials']+data['debug_trials']}),22)

if __name__=='__main__':unittest.main()

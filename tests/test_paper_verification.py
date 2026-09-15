"""Control-flow tests only: scripted callbacks are not experimental evidence."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'vlm-tamp'))
from paper_verification import verify_predicate


class PaperControlFlow(unittest.TestCase):
    def run_case(self,answers,sufficiency,agreement=4,k=1):
        events=[];images=[];responses=iter(answers);suff=iter(sufficiency)
        initial=object();new=object()
        def query(obs,q):
            images.append(obs);return next(responses)
        result=verify_predicate('inview(bottle)',initial,[],budget_k=k,consistent_votes=agreement,
             paraphrases=lambda p:tuple('question '+str(i) for i in range(5)),query=query,
             confirm_sufficiency=lambda o,p:next(suff),suggest_direction=lambda o,p:'left',
             navigate=lambda d:events.append(('move',d)),observe=lambda:new,
             update_from_observation=lambda o,g:g+[o],log=lambda e,**kw:events.append((e,kw)))
        return result,events,images,initial,new

    def test_agreement_still_requires_sufficiency(self):
        result,events,images,initial,_=self.run_case(['yes']*5,['yes'])
        self.assertTrue(result.value and result.sufficient)
        self.assertEqual(result.moves_attempted,0)
        self.assertTrue(all(image is initial for image in images))
        self.assertIn('paper_sufficiency_raw',[e[0] for e in events])

    def test_insufficient_view_moves_refreshes_and_requeries(self):
        result,events,images,initial,new=self.run_case(['yes']*5+['no']*5,['no','yes'])
        self.assertFalse(result.value)
        self.assertEqual(result.moves_attempted,1)
        self.assertEqual(result.graph,[new])
        self.assertEqual(images,[initial]*5+[new]*5)

    def test_inconsistent_vote_skips_sufficiency(self):
        result,events,*_=self.run_case(['yes']*3+['no']*2+['yes']*5,['yes'])
        self.assertEqual(result.moves_attempted,1)
        self.assertEqual(sum(e[0]=='paper_sufficiency_raw' for e in events),1)

    def test_literal_inclusive_budget_preserves_last_vote(self):
        result,events,*_=self.run_case(['yes']*3+['no']*2,[],k=0)
        self.assertTrue(result.value and result.budget_exhausted)
        self.assertFalse(result.sufficient)
        self.assertEqual(result.moves_attempted,1)
        self.assertTrue(events[-1][1]['final_observation_not_voted'])
        self.assertIsNot(result.observation,result.voted_observation)

    def test_nonbinary_response_cannot_become_evidence(self):
        with self.assertRaises(ValueError):self.run_case(['skip']*5,[])


if __name__=='__main__':unittest.main()

"""Algorithm 2 control flow; simulator/VLM adapters remain explicit dependencies.

This is not an executable simulation or a validated active-perception baseline.
The inclusive final navigation follows the printed pseudocode literally.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class VerificationResult:
    value: bool
    sufficient: bool
    budget_exhausted: bool
    votes: tuple
    voted_observation: object
    observation: object
    graph: object
    moves_attempted: int


def binary_response(answer):
    normalized=answer.strip().lower()
    if normalized not in ('yes','no'):
        raise ValueError('Paper verification requires a binary response; raw output must be retained')
    return normalized=='yes'


def verify_predicate(predicate, observation, graph, *, budget_k, consistent_votes,
                     paraphrases, query, confirm_sufficiency, suggest_direction,
                     navigate, observe, update_from_observation, log):
    """Follow paper Algorithm 2 without adding view scores or successor inputs.

    `query(observation, question)` returns the raw binary VLM response.
    `confirm_sufficiency` and `suggest_direction` receive only the current
    observation/predicate. `navigate` executes the supplied direction; it does
    not select a different viewpoint. `update_from_observation` must implement
    actual evidence refresh; passing a no-op does not establish paper fidelity.
    K and agreement count are mandatory because the paper does not specify them.
    """
    if not isinstance(budget_k,int) or budget_k<0:
        raise ValueError('K must be a nonnegative integer')
    if consistent_votes not in (4,5):
        raise ValueError('Specify high agreement as 4 or 5 votes; threshold is a documented assumption')
    moves=0
    for k in range(budget_k+1):
        questions=tuple(paraphrases(predicate))
        if len(questions)!=5:
            raise ValueError('The paper requires N=5 paraphrases')
        # Every vote in this round uses exactly the same captured observation.
        raw=tuple(query(observation,q) for q in questions)
        log('paper_votes_raw',round=k,predicate=predicate,questions=questions,answers=raw)
        votes=tuple(binary_response(answer) for answer in raw)
        voted_observation=observation
        value=sum(votes)>2.5
        agreement=max(sum(votes),5-sum(votes))
        log('paper_vote',round=k,value=value,agreement=agreement)
        if agreement>=consistent_votes:
            raw_sufficiency=confirm_sufficiency(observation,predicate)
            log('paper_sufficiency_raw',round=k,answer=raw_sufficiency)
            if binary_response(raw_sufficiency):
                return VerificationResult(value,True,False,votes,voted_observation,observation,graph,moves)
        direction=suggest_direction(observation,predicate)
        log('paper_direction',round=k,direction=direction)
        motion_result=navigate(direction)
        moves+=1
        observation=observe()
        graph=update_from_observation(observation,graph)
        log('paper_observation_refresh',round=k,motion_result=motion_result)
    # Literal lines 10–14: even the last iteration moves/observes, but returns
    # the preceding vote. Do not silently call that final view verified.
    log('paper_budget_exhausted',value=value,final_observation_not_voted=True)
    return VerificationResult(value,False,True,votes,voted_observation,observation,graph,moves)

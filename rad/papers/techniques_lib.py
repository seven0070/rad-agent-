"""Technique library — named, battle-ready runtime techniques.



Each technique wraps an execute_fn with a mechanism. Battle #2/#3's

apply_reflexion was the first citizen; this module makes techniques

first-class so future cards (Self-Refine, self-consistency, etc.)

register here and battle identically.



CONTRACT (L2): technique(config, task, seed) -> execute_fn-compatible dict.

"""

from dataclasses import dataclass

from typing import Callable



@dataclass

class Technique:

    name: str

    wrap: Callable          # wrap(execute_fn, **params) -> execute_fn

    source_slug: str        # paper it came from (provenance)

    claim: str



REGISTRY: dict[str, Technique] = {}



def register(name: str, source_slug: str, claim: str):

    def deco(wrap):

        REGISTRY[name] = Technique(name=name, wrap=wrap,

                                   source_slug=source_slug, claim=claim)

        return wrap

    return deco



def get(name: str) -> Technique:

    if name not in REGISTRY:

        raise KeyError(f"technique {name!r} not registered; have {list(REGISTRY)}")

    return REGISTRY[name]



# -- reflexion, promoted from ad-hoc hook to registry citizen --

def apply_reflexion(execute_fn, brain_fn=None, max_reflections: int = 2):

    def wrapped(config, task, seed):

        result = execute_fn(config, task, seed)

        if config.get("technique") not in ("reflexion", "reflexive-executor"):

            return result

        attempts = 0

        while (result["grader_result"].get("verified_rate") != 1.0

               and attempts < max_reflections and brain_fn):

            events = result.get("events", [])

            fails = [e for e in events if str(e).startswith("disk_fail:")]

            reflection = brain_fn(

                f"TASK: {task.get('prompt','')}\nStatus: {result.get('status','')}\n"

                f"Events: {events}\n"

                + (f"Failed checks: {fails}\n" if fails else "")

                + "Diagnose why this failed and give concise retry instructions.")

            task2 = dict(task, prompt=(task.get("prompt", "") +

                        f"\n\nPrior reflection: {reflection}"))

            result = execute_fn(config, task2, seed)

            attempts += 1

        if attempts:
            result["events"] = list(result.get("events", [])) + [f"reflexion:attempts={attempts}"]
        return result
    return wrapped

register("reflexion", "2303.11366",
         claim="verbal self-reflection converts environment feedback into "
               "improved retry behavior (procedural failures)")(
    lambda execute_fn, **kw: apply_reflexion(execute_fn, **kw))

# -- self-refine: iterative refinement with self-feedback --
def apply_self_refine(execute_fn, brain_fn=None, max_reflections: int = 2):
    def wrapped(config, task, seed):
        result = execute_fn(config, task, seed)
        if config.get("technique") not in ("self-refine", "self_refine"):
            return result
        attempts = 0
        while (result["grader_result"].get("verified_rate") != 1.0
               and attempts < max_reflections and brain_fn):
            feedback = brain_fn(
                f"TASK: {task.get('prompt', '')}\n"
                f"Execution status: {result.get('status', '')}\n"
                "Review the attempt and output refined instructions to fulfill all task criteria.")
            task2 = dict(task, prompt=(task.get("prompt", "") +
                         f"\n\n[Refinement Feedback]: {feedback}"))
            result = execute_fn(config, task2, seed)
            attempts += 1
        if attempts:
            result["events"] = list(result.get("events", [])) + [f"self_refine:attempts={attempts}"]
            result["grader_result"]["cost"] = float(result["grader_result"].get("cost", 0.0)) + float(attempts)
        return result
    return wrapped

register("self-refine", "2303.17651",
         claim="iterative self-feedback and refinement improves task output quality without external training data")(
    lambda execute_fn, **kw: apply_self_refine(execute_fn, **kw))

# -- react: synergizing reasoning and acting --
def apply_react(execute_fn, brain_fn=None, max_reflections: int = 2):
    def wrapped(config, task, seed):
        result = execute_fn(config, task, seed)
        if config.get("technique") not in ("react", "react-interleaved"):
            return result
        attempts = 0
        while (result["grader_result"].get("verified_rate") != 1.0
               and attempts < max_reflections and brain_fn):
            events = result.get("events", [])
            fails = [e for e in events if str(e).startswith("disk_fail:")]
            thought_action = brain_fn(
                f"TASK: {task.get('prompt', '')}\n"
                f"Current Status: {result.get('status', '')}\n"
                f"Failed checks: {fails}\n"
                "Think step-by-step (Thought) and specify concrete file modifications (Action) to solve the task."
            )
            task2 = dict(task, prompt=(task.get("prompt", "") +
                         f"\n\n[Thought & Action]: {thought_action}"))
            result = execute_fn(config, task2, seed)
            attempts += 1
        if attempts:
            result["events"] = list(result.get("events", [])) + [f"react:attempts={attempts}"]
            result["grader_result"]["cost"] = float(result["grader_result"].get("cost", 0.0)) + float(attempts)
        return result
    return wrapped

register("react", "2210.03629",
         claim="synergizing reasoning traces and task-specific actions leads to higher task execution success")(
    lambda execute_fn, **kw: apply_react(execute_fn, **kw))

def make_arm(execute_fn, technique: str, brain_fn=None, **params):
    """Battle arms resolve through the registry — provenance preserved."""
    if technique == "baseline":
        return execute_fn
    t = get(technique)
    return t.wrap(execute_fn, brain_fn=brain_fn, **params)



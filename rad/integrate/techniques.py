"""Technique adapters — real candidate treatment arms for paper battles.

Currently exports:
  - apply_reflexion: Reflexion (Shinn et al. 2023) verbal self-reflection retry loop.
"""
from typing import Callable, Optional

def apply_reflexion(executor_fn: Callable, brain_fn: Optional[Callable] = None,
                    max_reflections: int = 1) -> Callable:
    """Wraps an execute_fn with a Reflexion retry loop (Shinn et al. 2023).

    Signature of wrapped execute_fn: (config: dict, task: dict, seed: int) -> dict.

    Behavior:
      - If config.get("technique") == "baseline": runs standard single attempt.
      - If config.get("technique") == "reflexion" (or reflexion active):
        1. Runs initial attempt via executor_fn.
        2. If verified_rate < 1.0 and brain_fn is provided, generates verbal
           self-reflection from failure events/status and appends it to the task prompt.
        3. Re-executes up to max_reflections times.
        4. Accumulates tool costs across attempts and injects reflexion:* events.
    """
    def reflexion_execute_fn(config: dict, task: dict, seed: int) -> dict:
        is_active = (config.get("technique") == "reflexion" or
                     config.get("reflexion") is True or
                     ("technique" not in config and brain_fn is not None))

        res = executor_fn(config, task, seed)
        if not is_active or brain_fn is None:
            return res

        gr = res.get("grader_result", {})
        if gr.get("verified_rate", 0.0) >= 1.0:
            return res  # First attempt succeeded, no reflection needed

        total_cost = float(gr.get("cost", 0.0))
        all_events = list(res.get("events", []))

        curr_res = res
        for attempt in range(max_reflections):
            prompt_text = task.get("prompt", "") if isinstance(task, dict) else getattr(task, "prompt", "")
            status = curr_res.get("status", "FAILED")
            reflection_prompt = (
                f"Task failed: {prompt_text}\n"
                f"Status: {status}\n"
                f"Events: {curr_res.get('events', [])}\n"
                "Reflect concisely on why this failed and how to succeed on retry:"
            )
            reflection = brain_fn(reflection_prompt)

            if isinstance(task, dict):
                retry_task = dict(task)
                retry_task["prompt"] = f"{prompt_text}\n\n[Previous Failure Reflection]: {reflection}"
            else:
                import copy
                retry_task = copy.copy(task)
                if hasattr(retry_task, "prompt"):
                    retry_task.prompt = f"{prompt_text}\n\n[Previous Failure Reflection]: {reflection}"

            all_events.append(f"reflexion:reflection_{attempt+1}")
            all_events.append(f"reflexion:retry_{attempt+1}")

            retry_res = executor_fn(config, retry_task, seed + attempt + 1)
            retry_gr = retry_res.get("grader_result", {})
            total_cost += float(retry_gr.get("cost", 0.0))
            all_events.extend(retry_res.get("events", []))

            # Merge aggregated stats
            curr_res = dict(retry_res)
            merged_gr = dict(retry_gr)
            merged_gr["cost"] = total_cost
            curr_res["grader_result"] = merged_gr
            curr_res["events"] = all_events

            if merged_gr.get("verified_rate", 0.0) >= 1.0:
                break

        return curr_res

    return reflexion_execute_fn

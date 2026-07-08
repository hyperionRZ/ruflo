# Field Guide to Fable — How to Apply It

Source: "Field Guide to Fable" — Thariq Shihipar (Claude Code team, Anthropic), AI Engineer World's Fair 2026.
Video: https://youtu.be/9fubhllmsBU (published ~July 2026, ~2M views in first 3 days).

## Core thesis

- **Capability overhang**: model intelligence advances in spiky, uneven ways. The bottleneck is no longer raw model capability — it is human adaptation. The tools and context you give the model decide which capability spikes you can actually reach.
- **"Models are grown, not designed"**: treat Fable-class models as systems to be steered through context, not programmed through rules.
- From ~400k Claude Code sessions: users make ~70% of *planning* decisions; Claude makes ~80% of *execution* decisions. So the highest-leverage work happens before implementation starts — the binding constraint is the clarity of your own thinking before the task begins.
- "Good, Fast, Cheap — pick two" is breaking down: with capable-enough agents, tradeoffs that used to be forced are often not real anymore. Don't pre-concede quality for speed.

## The Unknowns Matrix (Rumsfeld matrix applied to prompting)

| Quadrant | Meaning | What to do |
|---|---|---|
| Known knowns | Things you can state explicitly | Put them in the prompt |
| Known unknowns | Gaps you're aware of | Ask Claude to research/answer them first |
| Unknown knowns | Implicit knowledge you have but didn't state | Have Claude interview you / surface assumptions |
| Unknown unknowns | Things you never considered (the dangerous quadrant) | **Blindspot pass** |

## Techniques to use

1. **Blindspot pass** (for unknown unknowns): before writing the implementation prompt, give Claude the general objective *without* asking for the final output, and ask it to list missing information, perceived ambiguities, and assumptions it is about to make. Example prompt from the talk:
   > "I'm working on adding a new auth provider but I know nothing about the auth modules in this codebase. Can you do a blindspot pass to help me figure out my relevant unknown unknowns and help me prompt you better."
   Works best in unfamiliar parts of a codebase.
2. **Implementation notes** (for learning across attempts): have Claude keep a temporary `implementation-notes.md` logging decisions made and deviations from the plan, choosing conservative options at edge cases. Review the notes to understand model behavior and refine the next prompt.
3. **Smaller system prompts**: Anthropic cut Claude Code's system prompt by ~80% for Fable 5 — this class of models "wants a smaller system prompt." Examples tend to *constrain* the model because it is more imaginative than the examples given. Prefer steering via context over hard "do not do X" rules.
4. **Plan-stage investment**: since humans dominate planning decisions, spend effort clarifying intent, constraints, and success criteria up front; delegate execution details.

## How I (Claude) should use this in this repo

- Before non-trivial or unfamiliar tasks, run a self blindspot pass: state the objective, enumerate what's ambiguous or unstated, and either resolve it from the codebase or surface it to the user before implementing.
- During multi-step implementations, keep brief implementation notes (decisions + deviations from plan) and fold them into the final summary.
- When writing prompts/system prompts for agents (e.g. `.claude/agents/*`, swarm task prompts), keep them short and context-driven; avoid long example lists and prohibition rules — describe intent and context instead.
- Treat user requests as the "known knowns"; actively hunt the other three quadrants instead of implementing literally.

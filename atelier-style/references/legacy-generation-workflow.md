---
name: atelier-style
description: Generate a new fashion photograph from a text brief in a selected Paolo Roversi or Tim Walker direction, using researched visual relationships. An input photo is not required.
---
# Atelier Style 3.1 — research edition

Use theme + selected photographer to generate one new photograph. Do not ask for an input image or impose identity/garment locks in text-to-image mode. For explicit brief-only requests stop before generation. If the user explicitly requests editing, use the imagegen editing workflow and their preservation requirements; this text-only compiler does not implement editing.

## Decide the image, not a filter
Read the chosen author in `references/profiles.json`. Pick one compatible branch yourself; do not require users to choose internal branches. Read relevant cards in `references/deep-cards.json`, including a counterexample. The 24 cards were re-viewed at analysis resolution; 300 short observations are an index, not a trained model. Most authors and all series identities are not independently authenticated. Two references are not proof of two independent shoots.

For Roversi briefs where person–clothing balance, performative posing or unnecessary staging needs interpretation, consult `references/roversi-text-sources.md`. Its three sourced knowledge cards inform decisions; they are not default prompt additions or corpus relation IDs. Separate the author's statements from your generation hypotheses. Record any useful application in an existing optional field with its concrete reason; zero additions remain valid. The initial small image pilot did not demonstrate improvement over name-only prompting.

Preserve the complete user request and the photographer name. For new decisions use `prompt_mode: selective`. First decide whether extra guidance helps this brief. Branch relations are recommendations, not a quota: choose only relevant relations, or none when the request needs no addition. Record why. Do not add staging merely to fill a field or make the result visibly different from a name-only prompt.

State the visual relationship without fixing one gesture or camera distance unless that choice serves a specific requirement. A face–garment connection need not use a hand. Composition, subject action, lighting and material/focus guidance can be omitted; any added instruction needs a concrete reason in the decision record. Explicit user choices remain requirements. New creative details are decisions, not source facts.

Choose detail hierarchy only when it helps this image. Do not add universal sharpness or softness: a readable face, a precise textile and a simplified dark mass are different needs. A branch does not automatically require everything to be clear, and a soft edge does not by itself establish photographer style. Do not default to gray backgrounds, seated poses, loose hair, blur, huge props, red vinyl or primary colors. Keep branch boundaries; do not mix incompatible relations.

For the decision fields and an example, read `references/decision-format.md`. Check support/contact/action geometry and conflicts before compiling. The compiler verifies IDs, declared conflicts and reference bindings, NOT aesthetic truth or actual image compliance.

Run `scripts/prepare_generation.py --decision DECISION.json --out NEW_JOB.json`. It audits all references before compiling. Selective mode sends the original request plus necessary image guidance once; rules, reasons, boundaries and evidence remain in the job record. Use the compiled tool arguments unchanged. A justified zero-addition decision can produce the same prompt as request + photographer name, while still retaining the review record. Historical decisions without `prompt_mode` use `legacy` to reproduce their original prompts; do not use that compatibility path for new decisions by accident.

## Generate and review
Use the available imagegen skill and built-in image tool. Default one output, no automatic retries/provider changes, and no retries that evade a refusal. Do not upload library images: this package provides text evidence, not source-image permission. Use user-approved reference images only in a separately explicit reference/edit workflow.

Save the prompt, decision and generated file non-destructively in the task output directory. Use `finish()` in the compiler to produce a separate receipt with generated/failed status; preserve the ready job. Record actual tool and any available model/usage/cost, otherwise null. Never call tool acceptance human acceptance.

Inspect the output for request fulfillment, overall visual preference, selected relationships and physical artifacts separately. A prescribed pose appearing is not proof of aesthetic improvement. Record partial realization and repetitive staging as well as successes. Human feedback is added only when the user gives it; it does not train a model. Review relevant past task feedback without turning a preference about two portraits into a rule for all works. Keep failures visible; a successful generation is not demonstrated author recognition.

## Scope
No catalog, retrieval, aesthetic analysis or source-permission writes. Only `profiles.json`, `deep-cards.json`, `observations300.json`, `decision-format.md`, `evaluation.md`, `roversi-text-sources.md`, the text-generation compiler and its reference validator belong to this default workflow. Older installed recipe/edit files are historical and must not override it. Read `evaluation.md` only for a requested comparison test. Selective compilation is a research workflow; do not claim superiority over name-only prompting without matched image evidence.

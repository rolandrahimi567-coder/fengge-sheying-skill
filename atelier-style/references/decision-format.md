# Decision contract 3.1

New decisions explicitly set `prompt_mode: selective`. Preserve the complete original brief (or faithful translation) in `user_request`; the compiler cannot prove semantic fidelity.

Required fields:
- photographer_id: paolo-roversi or tim-walker.
- user_request: full user brief, never silently narrowed or supplemented with invented requirements.
- user_constraints: nonempty audit list of the user's actual requirements. Do not introduce requirements here that are missing from user_request. Retained in the record, not duplicated in the selective prompt.
- branch_id, branch_reason: a compatible branch and why it fits, including how a relevant counterexample limits its use.
- selection_reason: why extra guidance is useful, or why none is needed.
- applied_relations: zero to three objects. Branch recommended/optional entries define compatible choices, not mandatory ingredients. Each selected object has relation_id, evidence_sequences (at least two distinct eligible deeply reviewed IDs listed for this relation), implementation and reason. References are not proof of independent shoots.
- feasibility_check: assess relevant actions, support and requested person count. It is an agent assessment, not proof that rendering will comply.
- unresolved_conflicts: [] only after addressing declared conflicts.

Optional fields:
- composition, subject_state, light_and_color, material_and_focus: omit, null or blank means no added guidance. Keep explicit user instructions in user_request even if these fields are omitted.
- guidance_reasons: object keyed by each nonempty optional scene field. Every added field needs a concrete reason; no field is mandatory just to fill out a shot plan.
- failure_signs: zero to six specific failures worth avoiding. Omit generic quality boilerplate when it does not help this brief.

Selective compilation emits the complete request, photographer name, relation implementations once, nonempty scene guidance and any necessary failure signs. Relation definitions, reasons, references and boundaries stay in the decision/job record. Do not repeat the same hand pose or camera distance in several fields. Apply source boundaries when choosing guidance; do not mechanically append every research caution to the image prompt.

Example of one addition (not a complete decision):
```json
{
  "relation_id": "PR02",
  "evidence_sequences": [149, 180],
  "implementation": "Let the smaller face and larger garment shape form connected viewing points without an emphatic demonstration pose.",
  "reason": "The user wants both face and garment to matter; a relation helps without fixing hand placement."
}
```
This is an example, not a reusable mandatory pose. Do not copy a source subject or infer its production technique as a requirement.

Compatibility: absent prompt_mode or explicit legacy uses the 3.0 field requirements and full prompt layout. It treats each branch's recommended entries as the historical required entries, and also accepts old profiles with required keys. This path is for saved decisions and controlled comparisons. Unknown modes fail rather than silently falling back.

build() returns a ready job. After a real call, use finish(job, output=LOCAL_FILE) or finish(job, error=ACTUAL_FAILURE), then save a separate receipt; preserve the ready job. Add actual_tool, model/usage if returned and model_review. human_acceptance stays null until the user supplies acceptance; a preference statement is not blanket acceptance. Append explicit feedback to task-local feedback.jsonl with output hashes, original wording, criterion and timestamp. Do not alter old receipts or promote assistant review to user approval.

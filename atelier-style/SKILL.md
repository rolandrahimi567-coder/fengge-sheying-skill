---
name: atelier-style
description: Generate photographs from a brief in Paolo Roversi or Tim Walker style, or compile and test source-grounded Elizaveta Porodina photographic-expression jobs. Roversi separates subject requirements from visual intent, supports direct generation or requested two-direction previews, and uses complete category contact sheets; text-summary-only generation is also available.
---
# Atelier Style

## Unified photographer routing

This skill is the single Atelier entry for Paolo Roversi, Tim Walker and Elizaveta Porodina. Read [photographer routing](references/atelier-router.md), select exactly one photographer, and follow only that photographer's compiler and references. An explicit photographer name always wins. When the photographer is omitted but the brief clearly matches one route, select it and disclose the choice; do not blend photographers. The three routes share Chinese prompts, traceable input manifests, one compiled job per output, preserved failures and generated/reference/prompt galleries. Their categories, visual defaults, rejected directions and validation status remain separate.

Use `scripts/prepare_atelier_job.py --spec SPEC.json --out JOB.json` when a normalized single entry is useful. It dispatches to the existing Roversi compiler, Tim Walker compiler or Porodina compiler and emits the selected photographer in the job. The router does not generate images. Inspect the selected route's required original images before compilation and call built-in imagegen only with the compiled `tool_arguments`.

## Paolo Roversi — whole-category references

Personal subject preference: generate women only for Roversi. Do not invent male subjects in examples, previews or batches unless the user explicitly requests an exception. This preference does not apply to Tim Walker.

Personal default rendering: use irregular local sharpness/softness with restrained short motion traces for all Roversi generation modes, including six-category, scene, text-only and requested previews. Read [references/roversi-default-rendering.txt](references/roversi-default-rendering.txt); the compilers append this shared text automatically. This is a user preference, not a universal definition of Roversi or a verified quality improvement. A current explicit request for clear/no-trail rendering or another treatment overrides this default. For direct tool calls outside the compilers, include this text once. New generation does not need a base image; do not add edit-only instructions to preserve an existing identity or scene. For Roversi edits, apply the same rendering preference while preserving the edit target and requested invariants; explicit edit instructions take precedence. Do not apply this Roversi default to Tim Walker.

Default to one new photograph. There are two independent classification modes:

- Original six categories A–F: preserve all original memberships and use all images in the selected category. Read [references/roversi-routing.md](references/roversi-routing.md). F is restored as a selectable experimental direction; restoration does not mean its quality improved.
- Scene mode, only when requested: simple background, interior, built exterior/street, or nature. Use every photograph in that scene class, regardless of A–F membership. Read [references/roversi-scenes.md](references/roversi-scenes.md).

A setting in the brief does not automatically switch modes. Do not intersect or mix the two pools unless the user explicitly requests a combined selection. All 150 records remain bundled; uncertain and nonphotographic records are not forced into a scene class. Existing detailed labels remain supporting observations, not required user controls or automatic shooting guidance.

The compiler creates at most five uncropped reference sheets. Say “本类全部 N 张，通过 M 张参考拼版输入”. Coverage is not proof of attention to every image; small cells lose detail. Originals stay intact.

1. Save the user's complete request verbatim to a UTF-8 file. Select the direction and give a short reason separately; do not add a shooting plan, gestures, lighting formulas, or new creative constraints.
2. Use Python with Pillow (the bundled workspace Python is suitable; locate it using workspace dependencies if needed):

```sh
python scripts/prepare_reference_generation.py --request-file REQUEST.txt --direction B --selection auto --reason '画面重点是服装形态与色彩关系' --out NEW_JOB.json
```

For independent scene mode, replace `--direction B` with `--scene-category interior` (or backdrop, built_outdoor, nature). Do not add a direction to scene mode. Advanced intersections are reserved for explicit combined requests.

Use `--selection explicit` when the user names a direction, `auto` for an intent-based choice, and `default` when treatment is unspecified and the configured default is used. The helper validates all reference hashes and compiles the complete image list; it does not perform semantic routing or call generation itself.
3. Inspect each generated reference sheet using available image-viewing tools. Call the built-in imagegen tool with the job's `tool_arguments` unchanged, following the imagegen skill. Do not add `num_last_images_to_include` or reuse prior generated images as references. The request plus photographer name, concise reference-role instruction and personal default rendering is the full prompt; do not automatically append the text summary.
4. Copy the result into the current task's output directory. Save the job, submitted sheet files or their immutable snapshots, and a receipt with returned output path/error. Preserve failures. Review requirement fit, image quality, subject/pose repetition, unwanted borders/text/grid layout. Do not equate successful generation with verified photographer recognizability.

Brief-only requests stop after compilation. No automatic rerolls, provider changes, category reduction, or conversion of a moderation rejection into an input-size workaround. If missing/corrupt references or an input rejection prevents the selected mode, explain it; do not silently choose four images or switch to text. A new user request can choose another mode.

## Requested direction preview

Only when the user requests a direction preview or comparison, choose two suitable, distinct directions under the routing guide and prepare two independent jobs:

```sh
python scripts/prepare_direction_preview.py --request-file REQUEST.txt --directions B D --reasons '探索衣形与色彩的表现' '探索人物神态与直接呈现；该方向仍在实验' --out NEW_PREVIEW.json
```

Both jobs retain the identical complete request. Inspect their reference sheets and generate once per job with each job's `tool_arguments` unchanged. Present the results side by side with Chinese direction names, preserving failures. Ordinary direct mode never expands to multiple images automatically. This preview explores alternatives; it is not a claim that one direction is objectively best. Brief-only requests stop at preparation.

## Text-only option

When the user explicitly requests “只用文字总结 / 不用参考图”, use the preserved summary workflow:

```sh
python scripts/prepare_summary_generation.py --request-file REQUEST.txt --out NEW_JOB.json
```

Call its `tool_arguments` unchanged, without image-reference arguments. Keep `references/roversi-style-summary.txt` verbatim. Do not revive automatic concrete shot directions.

## Tim Walker and image edits

For Tim Walker use [the reference compilation and experiment workflow](references/tim-walker/workflow.md), with the preserved 150-image index and eight-category rules. Select one photographic reference, or two only after inspecting their style consistency, and add one separate clothing reference by default. The photographic reference controls the body-space-light relationship and overall photographic expression; the clothing reference controls garment silhouette, construction, material, craft and specified color only. Compile with `scripts/prepare_tim_walker_generation.py`. Skip the clothing reference only when the user explicitly requests that, and record the reason. Keep results experimental until user review. For explicitly requested legacy text-only generation, use [the legacy workflow](references/legacy-generation-workflow.md). Do not apply Porodina visual recipes or Roversi categories and defaults. For editing a user photo, follow imagegen's edit workflow and preserve the user's requested invariants. The whole-category compiler is for new photographs, not an edit-target loader; never append an edit target to its five reference slots without an explicit compatible workflow.

## Elizaveta Porodina — research and experiments

Treat the Porodina image chain as a compiled workflow. Before generating, read [research and compilation workflow](references/porodina/workflow.md), [feedback policy](references/porodina/feedback-policy.md) and the relevant records in [feedback ledger](references/porodina/feedback-ledger.jsonl). Preserve user quotes, scope and later revisions; unresolved image mappings are not ratings of guessed outputs. Consult [failure patterns](references/porodina/failure-patterns.md) for checks, not validated fixes.

Start with [whole-image visual language](references/porodina/visual-language.md) and [research workflow](references/porodina/workflow.md), then consult the relevant entry in [expression branches](references/porodina/branches.json). Use [source index](references/porodina/reference-index.json) to inspect original images and [user reviews](references/porodina/reviews.json) to distinguish marginal, rejected and unreviewed results. Eight overlapping research axes are observations and hypotheses, not validated generation presets. Use one reference, or two only when their photographic styles are visually consistent. If styles differ, select the single reference best suited to the brief; complementary roles do not justify mixing styles. User examples: 082 + 147 are different styles; 138 + 141 are consistent. Matching framing is not required. Improve human realism while retaining vivid, dreamlike photographic expression; see the workflow. No generation recipe is validated. Preserve the user's brief and current casting preferences; do not inherit Roversi defaults.

After full-image inspection, compile the task with `scripts/prepare_porodina_generation.py`. The compiler requires the preserved request, one category or research axis, one or two verified photographic reference IDs, an inspection note, a selection reason, a Chinese photographic-reference plan, and one separate clothing reference with its own Chinese plan by default. The photographic reference controls composition, subject scale and direction, space, light/color, occlusion, focus and motion; the clothing reference controls garment silhouette, construction, material, craft and specified color only. Two photographic references require an explicit confirmed consistency record. Skip the clothing reference only when the user explicitly requests that, and record the reason. Inspect the compiled manifest and prompt, then call built-in imagegen with `tool_arguments` unchanged. The compiler does not select references, judge similarity, call generation, reroll failures or validate a recipe. Preserve its job JSON and the generation receipt for the comparison gallery and later human review.

## Generation gallery delivery preference

For future image-generation galleries, show each generated result alongside the actual reference images submitted for that call, in input order, with clickable full-size images. Label each input by its recorded role, including `摄影参考` and `服装参考`; do not collapse them into an undifferentiated reference group. Do not substitute reference IDs or links alone for visible reference images. Use job records to verify pairing; preserve aspect ratio and include local reference copies for portable local galleries. For text-only generation, explicitly label that no image references were used. This display preference does not change the number of references or the generation workflow.

## Prompt language preference

The user requires Chinese for all future image-generation prompts: compose and submit the prompt in Chinese, and display and save it in Chinese. Proper names and technical identifiers may retain their original form. Do not silently translate the submitted prompt into English. When translating historical English prompts for display, preserve the actual originally submitted text in internal records. Keep the gallery wording simply Chinese prompts; do not add translation/history/backend-file disclaimers to the gallery.

## Gallery wording preference

Keep user-facing image galleries focused on images, visible references, concise titles and Chinese prompts. Omit technical provenance notices such as historical submission language, translation disclaimers, JSON filenames, hashes and backend record explanations. Preserve accurate provenance in internal records; explain it only when the user asks.

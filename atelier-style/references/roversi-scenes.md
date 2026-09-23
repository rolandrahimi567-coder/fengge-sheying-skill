# Independent scene mode

The 150 records have a second, independent classification: backdrop 简单背景; interior 室内空间; built_outdoor 建筑外部与街道; nature 自然环境; unassigned 暂不归类. It does not replace or automatically intersect A–F. A photograph unassigned in A–F may still have a scene class. Fantasy, insufficient evidence and nonphoto stay unassigned; nonphoto is never a generation reference. Detailed prior observations remain provenance, not compulsory prompt instructions.

When the user requests scene-based generation, use all records in the selected scene category, with no A–F filter:

```sh
python scripts/prepare_reference_generation.py --request-file REQUEST.txt --scene-category interior --selection explicit --reason '用户选择按室内场景参考' --out JOB.json
```

Inspect the complete generated reference boards and use the tool arguments unchanged. This is experimental; broad scene membership does not prove a coherent visual treatment, real locations, or improved realism. Do not label generic interiors as residential rooms. Do not make an unassigned reference pool.

The default remains the original six-category mode. A room in the brief alone does not switch modes. Combine dimensions only if the user explicitly requests it; the advanced `--direction … --scene space=interior` intersection is available but is never the default. Preserve empty-match errors.

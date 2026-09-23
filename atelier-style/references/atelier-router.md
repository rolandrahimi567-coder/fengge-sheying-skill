# Atelier 摄影师统一路由

Atelier 当前统一管理三位摄影师。先确定一位摄影师，再进入其独立编译流程。一次任务不得混合摄影师，也不得跨摄影师继承分类、默认渲染、失败题材或提示词配方。

| 摄影师 | 路由名称 | 参考选择 | 当前状态 |
|---|---|---|---|
| Paolo Roversi | `paolo-roversi` | 选定类别的全部原作，通过不超过五张参考拼版输入；或明确请求独立场景模式 | B/C 为候选，其余实验；不等于已验证辨识度 |
| Tim Walker | `tim-walker` | 完整看图后选择一张摄影原作；两张仅在风格一致时使用；默认另加一张服装参考 | 八类严格候选，方法仍为实验 |
| Elizaveta Porodina | `elizaveta-porodina` | 完整看图后选择一张摄影原作；两张仅在风格一致时使用；默认另加一张服装参考 | 六个旧类别和八个研究轴，无已验证配方 |

## 统一任务合同

所有路线都保留完整用户原话，使用中文提示词，记录摄影师、选择依据、实际参考路径和哈希、输入顺序、工具参数、首次输出或错误以及人工评价。每个编译任务只对应一张输出，自动重试数为零。多图测试分别编译，不能让多张结果共享含混记录。

统一入口：

```sh
python scripts/prepare_atelier_job.py --spec SPEC.json --out JOB.json
```

Roversi 需要 Pillow 来生成参考拼版。运行统一入口前先用 `load_workspace_dependencies` 定位带 Pillow 的工作区 Python；不要假定 macOS 系统 Python 已安装图像依赖。

`SPEC.json` 顶层包含 `photographer`、`user_request`、`selection`，可选 `options`。Tim Walker 和 Porodina 的 `selection` 必须包含完整看图后的 `visual_inspection_note`、`selection_reason` 和 `reference_plan`；两张摄影原作还需 `pair_consistency: "confirmed"`。两条路线默认还要求 `clothing_reference: {"path": "...", "plan": "..."}`。服装图排在摄影原作之后，只控制衣形、结构、材料、工艺及指定颜色，不控制人物身份、姿势、构图、空间、灯光或整体调色。用户明确不要服装参考时，在 `options.no_clothing_reference_reason` 记录原因。Roversi 使用自己的完整类别或独立场景编译器，不继承这一默认值。

编译后检查 `photographer`、参考清单、输入职责和中文提示词，再把 `tool_arguments` 原样提交给内置 imagegen。编译完成不等于已经生图；生图成功也不等于用户验收或风格配方成立。

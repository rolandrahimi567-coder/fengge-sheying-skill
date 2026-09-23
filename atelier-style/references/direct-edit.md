# 直接改图：必须交付图片，而不是停在JSON

## 触发和范围
用户上传照片并说“处理这张图”“直接出图”“按某方向改图”时，进入此模式；用户只问介绍、方案、建立Skill或明确不要生成时，不调用生图。不要把“功能开发授权”当成测试或批量生成授权。

读取可用 imagegen Skill 并使用内置 image_gen 工具，不需要用户填写 API key。当前是 Codex 内调用流程，不是网站上传页面或独立服务器服务。不修改原项目目录、权限或检索代码。

摄影师风格重创作请求先遵循 photographer-transform.md；默认模式 photographer_transform，自动选分支，brief-only 请求除外。

## 1. 输入与分支
接收用户附件的本地绝对路径，或冻结库内 record_id；用 view_image 看图。prepare_handoff.py 支持 request.input_image_path（PNG/JPEG/WebP）和 input_record_id 二选一，外部照片不会写入图库。无路径的附件按照imagegen支持的会话图机制直接处理，不编造路径；若需要持久化交接而无法取得附件路径，请说明限制。

按摄影师档案选分支，简短说明选择。若目标明确无需重复确认。明确保真/局部编辑时保护身份、服装版型/图案/固有色、姿态、文字标识，仅处理获准背景和局部光色。创意重构也只放开明确允许的变化。笼统“有故事感”不是随意换服装或增加人物的授权。冲突或关键信息缺失才询问。

## 2. 参考与许可
选择少量符合输入、同分支/子类型的参考，每张明确借鉴关系。只向服务传送当前任务允许的图。用户自己上传并明确要求编辑通常已构成对该编辑传输的授权，不再重复索要许可；原库明确未许可的参考必须解决其权限后再传送，不能静默覆盖false状态。用户先前授权仅用于当时8张试验，不自动延续。

参考图不是必需上传项：如果用户选择仅用文字配方或不授权发送参考图，就只传输入并清楚说明这一模式，不能声称使用了多图参考。不要为避开一次服务拒绝而改成文字或更换参考重试。

## 3. 准备一次编辑
读取 handoff-workflow.md，写 request 和 decision，再运行 prepare_handoff.py。针对外部输入，把看图版本的SHA256填入 inspected_input_sha256，不把哈希当作看图本身。

将当前用户授权（不含密钥）整理为 consent.json：intent=generate、edit_mode=photographer_transform（默认风格重创作）、fidelity或creative、max_outputs=1、user_authorization=用户本次允许改图的原话或准确摘要、reference_record_ids=本次发送的参考ID数组、inspected_sha256=实际看过的各图哈希、approved_images=[{sha256,generation_allowed:true,external_export_allowed:true}]。只为授权覆盖的图片填写true；不改源权限。这个文件记录助手对授权的解释，不是独立权限系统。不要让用户手写JSON。

运行：
```
python scripts/prepare_image_job.py --handoff /absolute/handoff.json --consent /absolute/consent.json --out /absolute/new-job.json
```
生成的 job.tool_arguments 可直接传给内置 image_gen.imagegen，包含 prompt 和 referenced_image_paths（输入排第一；最多4张参考，共5张）。脚本不发送请求，助手接下来必须实际调用工具。内置工具可用时不改用API/CLI，不读取密钥。

无本地路径时按imagegen规则使用最少所需会话图，且不能同时传入paths；把无法持久化的输入记录为会话来源，不伪造本地交接结果。

## 4. 调用与停止条件
每个用户请求默认生成1张，每张单独调用。不得把多张对照合并成拼图。模型、精确质量和成本未暴露时记录未知，不能虚构。

正常得到图片后检查身份、衣物、姿态、指定保留物、无关新增和参考道具照搬。最多一次修正仅在用户当前授权包含修正时执行，否则先交付并指出问题。服务拒绝立即停止对应任务，不变换内容绕过；网络失败保存失败/未知状态，不自动重提，避免重复成本。不要切CLI/API，除非用户明确选择该方式。

## 5. 交付与记录
用 generatedImage 展示结果。将工具返回的原始生成文件复制到当前工作区独立输出目录，保留原图和所有试次，不覆盖。保存实际提示词、输入及参考哈希、可获得的耗时/工具结果、输出路径；不要把base64全文打印到工具日志。

输出不是验收：先标 GENERATED_UNREVIEWED，看图后标 REVIEWED_WITH_LIMITATIONS 或 NEEDS_REVISION；人工通过只能由用户给出。最终返回图片及简短说明，突出无法保持的细节，不用交接JSON代替成品，不宣称保证摄影师可识别或衣物百分百保真。

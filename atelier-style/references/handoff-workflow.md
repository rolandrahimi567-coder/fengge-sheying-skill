# 从需求到视觉交接（只准备，不执行）

适用于用户要求选参考、写视觉方案或给制作 Workflow 准备材料。当前输出是通用本地 JSON + Markdown，不是已连接的 Workflow、前端或生图 API。

## 1. 理解需求
从用户原话提取用途、edit/new、摄影师偏好、输入、保留项、允许变化、禁止项。明确说出的条件才作为许可；缺失项写入 pending_questions。对“有故事感”等软条件给出解释，不自动变成新增道具许可。

## 2. 选择分支
运行 style_brief.py profiles/show 查看当前档案。结合实际输入推荐分支并解释适用原因；同时说明一个近似分支为何不选。不要靠摄影师姓名、单一色彩或关键词硬匹配。若输入不适合，直接说明，没有义务强行套配方。存在 subtype 时先确定一个子类型。

原有文字检索仍可由原项目调用并返回候选ID；本 Skill 不调用或替换检索排序。库内输入和参考ID限定冻结150张；外部编辑输入可用 input_image_path 指向现有绝对图片路径，不写入资产库。输入路径与 input_record_id 二选一，不可编造库内ID。参考ID不在范围时如实说明。

## 3. 看图、选参考
读取 archive150 和已有源证据；查看输入及拟用参考的完整分析图。衣服识别是候选，不作商品确定事实；B/B1数值保持原区域绑定，冲突进入待确认。现有审美文字只提供线索，不能自动成为验证过的制作规律。

选1—4张同一分支（如有子类型则同一子类型）参考。每张分别填写用途 role、借鉴关系 borrow、不要复制 do_not_copy。用本图可见事实说明，禁止把参考图中的衣服、人脸或道具悄悄加入任务。可用角色：lighting / spatial_relation / color / pose / garment_relation。

## 4. 写方案与结构化决定
方案要描述具体元素之间的关系，摄影师名不是操作指令。只写用户允许变化，不补造图中不可见的衣服细节。默认返回需求摘要、推荐方向、参考用途、方案、保留与变化、待确认项。只有无待确认项时编译提示词；仍是待审核草案。

将用户需求保存为 request.json：
```json
{"need":"用户具体需求","mode":"edit","input_record_id":null,"input_image_path":null,"preserve":[],"allowed_changes":[],"avoid":[]}
```
input_record_id 为库内ID或 null；input_image_path 为外部输入绝对路径或 null，二者不能同时设置。mode 为 edit/new。数组无内容用 []，未知字段用 null。不要使用上述说明字符串作为实际用户请求。

将看图后的判断保存为 decision.json：
```json
{"photographer_id":"tim-walker","branch_id":"surreal-scale-scene","subtype_id":"context-displacement","selection_reason":"选择原因及与其他方向的区别","visual_plan":"基于输入的具体方案","inspected_input_sha256":null,"references":[{"record_id":"实际参考ID","role":"spatial_relation","borrow":"有证据的可迁移关系","do_not_copy":["参考中不应移植的对象"]}],"pending_questions":[]}
```
inspected_input_sha256 只能在看过该版本输入后填写，不是脚本代看证明。不要在没有图时编造完整视觉方案；可以写“等待输入”的方向说明并保留 pending_questions。

## 5. 导出
```
python scripts/prepare_handoff.py --request /absolute/request.json --decision /absolute/decision.json --out /absolute/new-output-directory
```
输出 handoff.json 和交接说明.md。程序核对分支、子类型、参考范围、重复、ID、源图哈希和输入看图记录；它不验证自然语言是否真实、不核实版权、不自动评分。新输出目录防止覆盖旧交接版本。

通用交接包包含 schema_version、style_version、原需求、选择理由、方案、各参考用途/资产ID/哈希/来源状态、提示词和待确认项。provider/settings 保持 null，execution_authorized 和 generated 恒为 false。不要把这个通用包声称为已适配 ComfyUI/CLO/WL 或已上传服务。

## 后续结果检查
仅用户交来结果或另行要求测试时，比较人物和衣物保真、核心关系、无关新增及具体道具照搬。列证据和修改建议，不自行标记人工通过。只要求方案时不要主动生成、补测或扩样；明确要求直接改图时继续 references/direct-edit.md 的执行流程，不以交接包代替最终图片。

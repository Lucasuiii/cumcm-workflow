# CUMCM Workflow

简体中文 | [English](README.en.md)

一个给 AI agent 用的全国大学生数学建模竞赛工作流。它不替你想模型，它保证**每一个写进论文的结论都能追回到官方题目和一次真实发生过的计算**，并且在三天赛制下不把你拖垮。

支持 **Codex** 与 **Claude Code**。当前版本 **v0.6**，不向下兼容旧版本工作区。

---

## 1. 它解决什么问题

让模型自由发挥地做数模，典型失败不是"算错"，而是这五种：

| 失败 | 表现 | 本工作流的应对 |
|---|---|---|
| 答非所问 | 建了个漂亮模型，但没回答题目问的那个量 | 每个小问必须有 capability 负责，且带一个**可能失败**的验收检查 |
| 结论没有计算支撑 | 论文写了个数，但没有一次运行产生过它 | 结论只能引用成功的 official run，数值由脚本从输出里读回 |
| 代码和结论对不上 | 改完代码忘了重跑，论文还是旧数 | official run 绑定源码树快照，一改就报 stale |
| 越界宣称 | 在受限策略类里找到最优，写成"全局最优" | 强断言必须带 certificate 和适用范围 |
| 自说自话的评审 | "我检查过了" | 复核在独立上下文进行，独立性字段必须被正面声明 |

它**不**保证的：模型在数学上正确、全局最优、统计设计合理。检查通过只意味着"结构、来源、执行记录和已记录的评审边界是一致的"。

---

## 2. 两条规则

整个 v0.6 就是这两句话的展开。

### ① tooling 记录机器事实，agent 写语义判断

| 脚本观察并写入 | 你写 |
|---|---|
| argv、工作目录、起止时间、退出码、stdout/stderr | 这次运行是干什么的 |
| SHA-256、`sha256-tree-v1` 源码树快照 | 哪些文件是 formal input / claim-bearing output |
| 从 locator 读回的结果数值 | 结果的名字、单位、适用范围 |
| PDF 页数、PDF 哈希、逐页渲染图 | 版面能不能看的最终判断 |
| 编译日志里的 overfull / 未定义引用 / 缺字 / 字体错误 | 题意、模型、claims、论文正文 |

你永远不需要手算一个哈希。**如果某个改动会让 agent 把 SHA-256、退出码、页数或结果数值敲进 JSON，那个改动是错的**——去扩展记录器。

### ② 模型是后选的，而且选择要靠证据挣来

真实建模不是"先写对合同再执行"，而是：

```text
Problem Analysis
      │
      ▼
Model Design ─────► 候选 A / 候选 B
      │             · 为什么值得考虑（why_considered）
      │             · 用什么证据区分（discriminating_evidence）
      ▼
Computation ──────► 低成本 exploratory evaluation
      │             record_run.py --candidate CAND-A
      │             record_run.py --candidate CAND-B
      ▼
选择 A ───────────► status: selected
      │             decision_rationale 说明凭什么选它
      │             evaluation_run_ids 指向那两次探索运行
      ▼
A 做 official computation
      │             record_run.py --official
      ▼
Validation
```

这条链在 v0.6 里是**有结构、被检查**的，不只是一段建议：

- 恰好一个候选可以是 `selected`（`MODEL-E013`）；
- 被选中的候选必须引用真的评估过它的运行（`MODEL-W014`）；
- 选中或淘汰都要有理由（`MODEL-E014`）；
- 候选说不出"用什么区分"会被标出来（`MODEL-W012`）；
- `cumcm_check.py` 在报告里打印整张对比表（`model_candidates`）。

`working` 期这些是 warning，冻结时变成 error。只有一个候选是允许的（只提示 `MODEL-W007`）——本工作流不逼你凑候选，它只是不让你声称一场没做过的比较。

---

## 3. 七个阶段

```text
intake → problem-analysis → model-design → computation → validation → paper → delivery
```

| 阶段 | 做什么 | 产出 | 谁写 |
|---|---|---|---|
| `intake` | 把官方题目/附件/格式文件复制进来并按字节固定身份 | `problem/SOURCE_MANIFEST.json` | `init_project.py` |
| `problem-analysis` | 拆小问、抽事实（带页/表/单元格出处）、标歧义、定验收目标 | `PROBLEM_FACTS.json`、`TASK_CAPABILITIES.json` | agent |
| `model-design` | 提出候选、说明区分证据；选定后冻结正式合同 | `MODEL_CONTRACT.json` | agent |
| `computation` | 探索评估候选 → 选定 → 正式实现并运行 | `runs/*/RUN_MANIFEST.json`、`RESULTS_INDEX.json` | `record_run.py`、`index_result.py` |
| `validation` | 打包证据交给独立上下文复核，落成 claims | 复核包/结果、`CLAIM_LEDGER.json` | 脚本打包，agent 写 claims |
| `paper` | 选论断、选表达、写作、编译、逐页 QA | `PAPER_PLAN.json`、LaTeX、`PAPER_QUALITY_REPORT.json` | agent + `init_latex_paper.py`、`record_compile.py` |
| `delivery` | 对照官方规则冻结提交版本 | `COMPILE_RECEIPT.json`、`DELIVERY_MANIFEST.json` | `record_compile.py` + agent |

原则上 modeling、computation、validation、paper 分别在**不同的 fresh task** 里做。跨职责只通过四个 handoff 传递，新 task 先读 handoff、再按指针补读，不扫描整个工作区：

```text
modeling-computation   computation-validation   validation-paper   paper-delivery
```

handoff 只带路径、角色、摘要和一个 upstream digest；不带完整日志、失败运行、调试历史或旧复核对话。任一上游产物变了，handoff 立刻 stale，必须重建。

---

## 4. 证据模型

### 三个等级

| 等级 | 含义 | 是否阻断 |
|---|---|---|
| **P0 / hard invariant** | 数据或计算错误、答非所问、关键结论无证据、代码与结果不符、provenance 失效、伪造审批或复核、最终版本不一致 | **阻断** |
| **P1 / warning** | 假设强、baseline 弱、验证或敏感性不足、拟合有限、章节单薄；**以及探索运行的一切问题** | 可见，不阻断 |
| **P2 / suggestion** | 措辞、排版、可选图表、额外实验 | 不进入 gate |

### 正式计算的唯一链条

```text
RESULTS_INDEX.json → 被引用的 run_id → official_run:true 且 exit 0
                   → 当前有效的 sha256-tree-v1 源码快照
                   → locator 指向该运行声明的 claim_bearing_output
```

computation→validation handoff、独立复核包、paper→delivery handoff 三个消费者**共用同一个解析器**。任何一环缺失、失败、非 official 或 stale，三处一起明确失败——不会一个忽略、另一个才报错。

### 探索运行是一等公民

```bash
record_run.py --project <p> -- python3 code/try.py
```

零 flag，产出一份合法的 `official_run: false` 记录。它被记录、不被信任、**永不阻断**：断言失败、非零退出、缺日志、缺 capability，全都是 warning。它也不进入阶段批准范围——新增探索运行不会让已批准的 computation 失效。

这是有意的：Deferred Model Selection 的全部收益都来自"试算便宜"。

### 运行是追加的，证据是冻结的

`--rerun` **不覆盖**，它追加一个新运行（`RUN-Q1-001` → `RUN-Q1-002`），`parent_run_id` 指向被取代的那个。父运行连同日志原封不动留下——"改代码之前那次正式运行算出了什么"永远答得上来。

每次运行还会把 `--source` 和 `--output` **冻结**进自己的目录，镜像原来的相对路径：

```text
runs/RUN-Q1-002/
├── RUN_MANIFEST.json
├── stdout.log  stderr.log
├── source/code/solve.py        ← 执行时那一版代码的副本
└── outputs/results/q1.json     ← 那次产出的副本，locator 指这里
```

冻结副本不可变，所以被保留的运行永远可验证。而"改了代码却没重跑"这条最有价值的检查并没有丢——它改成比对**冻结副本与当前活文件**：

```
ERROR RUN-E020  the working tree no longer matches this official run: code/solve.py
                remediation: record_run.py --rerun RUN-Q1-001 --official
```

被取代的运行豁免这条（它当然不一样，这正是你取代它的原因）；反过来，改动冻结副本本身是另一类失败 `RUN-E021`（证据被篡改）。

`superseded` 由 `parent_run_id` 链**推导**，绝不回写旧 manifest——回写会改变它的哈希，把已经绑定它的 accepted decision 全部打成 stale。结果仍指着被取代的运行时报 `RESULT-E017`，用 `index_result.py --follow-lineage` 显式重新指向：换哪次运行支撑结论是语义判断，不能让工具偷偷替你做。

`problem/official/` 下的 input 就地取哈希（不可变契约已保护，且附件可能很大）；其余 formal input（`data/cleaned.csv` 这类会被重新生成的）同样冻结，有体积上限。

还有两条记录期的硬规则，都是防伪造：

- **不能冒领输出**。执行前后比对每个 declared output 的 mtime。一个 exit 0 却没写文件的程序，否则会把上一轮的结果连同真哈希一起冻结成自己的 claim 证据——真哈希、假出处。这种情况 `record_run.py` 直接拒绝写 manifest 并指出是哪个文件。
- **不能继承判决**。`--rerun` 永不继承父运行的 assertions。新代码没有被旧的 `pass` 验证过，继承它等于凭空给 `MODEL-E009`（冻结模型必须有已执行的验证）喂证据。
- **手打的判决不算已验证**。`--assert x=pass` 记为 `declared`（调用者备注），`--assert-file` 读程序自己写出的判决、记为 `recorded`。只有 `recorded` 能满足冻结模型的 `verification_plan`；official run 全是手打断言时报 `RUN-W003`。
- **证据不能在脚下移动**。声明的源码和 formal input 在执行前取哈希、执行后复核——冻结发生在命令退出之后，运行中被改过的文件会被冻结成"运行从未读过的东西"。

另外 `RUN-E024` 真正落实了 single-backend：同一 capability 不能同时存在 MATLAB 和 Python 的当前 official run（working 是 warning，冻结时是 error）。随机模拟用 `--seed` 记录种子。

**只有成功的 official child 才构成取代**：失败或探索性的重跑什么也没替代。checker、handoff、复核包和 delivery 共用同一个解析器，所以"当前正式运行"四处含义一致。claim/figure 仍引用被取代运行时报 `CLAIM-W020`/`FIGURE-W013`。

---

## 5. 两个旋钮

v0.6 没有 profile。只有：

| 旋钮 | 取值 | 决定 |
|---|---|---|
| `mode`（存在 state 里） | `working` / `finalizing` | **什么必须完整** |
| `--gate-mode` | `preflight` / `enforce` | **人工门禁是否计入阻断** |

- `working`：草稿模型合同即可、`CROSS_QUESTION_LEDGER.json` 可选、阶段排序只是 warning。官方输入保护、真实执行、精确 locator、非伪造照样强制。`enforce` 在这里只报 `working_ready`，不是正式批准。
- `finalizing`：完整模型合同（且 `verification_plan` 要对应到官方运行真的记录过的断言）、目标及上游阶段全部 `passed`、当前 accepted decision 与 snapshot、fresh handoff、独立复核、PDF QA、delivery 绑定。

阶段状态只有四个：`not_started` / `in_progress` / `passed` / `needs_revision`。

---

## 6. 一次完整走查

```bash
S=.agents/skills/cumcm-workflow/scripts
```

**① 初始化**（对话里直接说"用 cumcm-workflow 从 /path/to/2026B 初始化"即可，agent 会替你跑）

```bash
python3 $S/init_project.py --project ~/cumcm/2026B --project-id CUMCM-2026-B --official /path/to/2026B
```

官方文件被复制进 `problem/official/` 并记录哈希；原目录不被修改。

**② 拆题**：agent 写 `PROBLEM_FACTS.json`（每条事实注明来源文件与位置）和 `TASK_CAPABILITIES.json`（每个小问一个负责人 + 可能失败的验收检查）。

**③ 提候选**：agent 在 `MODEL_CONTRACT.json` 里写 2 个候选，各带 `why_considered` 和 `discriminating_evidence`。

**④ 探索评估**：

```bash
python3 $S/record_run.py --project <p> --candidate CAND-A -- python3 code/try_a.py
python3 $S/record_run.py --project <p> --candidate CAND-B -- python3 code/try_b.py
python3 $S/cumcm_check.py --project <p> --stage model-design --gate-mode preflight
```

**⑤ 选定并正式运行**：把胜者置 `selected` 并写理由，然后

```bash
python3 $S/record_run.py --project <p> --official \
  --capability CAP-Q1-001 --source code/solve.py \
  --input data/q1.csv:formal --output results/q1.json:claim \
  --assert-file results/assertions.json -- python3 code/solve.py

python3 $S/index_result.py --project <p> --result-id RES-Q1-001 --run RUN-Q1-001 \
  --locator 'results/q1.json#/minimum_cost' --name "最小成本" --unit CNY \
  --scope "仅限声明的候选集"
```

数值从 locator 读回，不经过你的手。

**⑥ 改了代码？** 追加一次继任运行，父运行原封不动留下：

```bash
python3 $S/record_run.py --project <p> --rerun RUN-Q1-001 --official   # 产出 RUN-Q1-002
python3 $S/index_result.py --project <p> --follow-lineage
```

**⑦ 冻结与复核**：

```bash
python3 $S/set_mode.py --project <p> --mode finalizing
python3 $S/build_handoff.py --project <p> --transition computation-validation
python3 $S/build_independent_review_package.py --project <p>
```

脚本到这里**主动停下**：你需要把复核包交给另一个 task 或另一个人，拿回结构化结果。

**⑧ 论文**：

```bash
python3 $S/build_handoff.py --project <p> --transition validation-paper
python3 $S/init_latex_paper.py --project <p> --competition-year 2026 \
  --title "<真实题目相关标题>" --keywords "<真实对象; 模型; 方法>"
python3 $S/record_compile.py --project <p> --update-quality
python3 $S/paper_visible_text_check.py --project <p> --pdf paper/main.pdf
```

`record_compile.py` 会把每一页渲染到 `.cumcm/tmp/pages/`——**然后真的去看那些图**。

**⑨ 交付**：

```bash
python3 $S/build_handoff.py --project <p> --transition paper-delivery
python3 $S/cumcm_check.py --project <p> --stage delivery --gate-mode enforce
```

---

## 7. 迭代与 scoped redo

回改上游不需要手动改 `state.json`：

```bash
python3 $S/record_decision.py --project <p> --stage model-design \
  --decision revision_requested --decision-id DEC-007 \
  --reviewer <name> --task-turn-ref <ref> --summary "Q2 模型不符合观测区间"
```

它把该阶段及全部下游置为 `needs_revision`、删掉下游 snapshot、把 `current_stage` 移回去。下游处于 `needs_revision` 是重开后的**正常状态**，不是错误。

改完之后先问"到底要重做什么"：

```bash
python3 $S/plan_redo.py --project <p> --changed code/solve_q2.py
```

```text
computation
  - re-run RUN-Q2-003: record_run.py --rerun RUN-Q2-003 --official (appends a successor)
  - re-point results to the successor: index_result.py --follow-lineage (RES-Q2-001)
validation
  - targeted re-review covers: F-003
  - rebuild the package: build_independent_review_package.py --review-mode auto --refresh
paper
  - rewrite or re-review: paper/sections/40_q2.tex
delivery
  - recompile and rebind: record_compile.py --update-quality

not affected (do not redo):
  computation: RUN-Q1-001
  paper: paper/sections/20_q1.tex
```

确定性检查本身很便宜，所以它继续**无条件全查**。被 scope 的是重跑、重复核、重写这三件真正贵的事。

---

## 8. 独立复核

第一次 review 是 full 且上下文分离的。复核包只复制正式结果对应的 canonical evidence，并声明 `context_excluded`——打包器**实际排除**了 originating task transcript、debug history、failed runs、prior review prose。它不声称"reviewer 心里没有结论"，因为那不可验证。

结果模板的四个独立性字段初值是 `null`，必须由 reviewer 或用户正面声明；留 null 直接失败（`IREVIEW-E027`）。两个 task ref 必须不同，但这只是防复制粘贴的护栏，**不是独立性证明**。

Verdict：`accepted` / `accepted_with_concerns` / `revision_required` / `inconclusive`。只有开放 P0 才允许 `revision_required`。full review 出现 P0 后，下一次打包默认 targeted re-review，包内生成自包含的 `TARGETED_FINDINGS.json`，reviewer 不需要读旧 review 全文。

---

## 9. MATLAB 还是 Python

默认 `{"preferred":"matlab","fallback":"python","selection":"auto"}`。MATLAB 只是同等条件下的 tie-break，不是强制。判断依据是任务本身：数值线性代数、优化、ODE/PDE、信号处理偏 MATLAB；数据清洗、CSV/Excel、机器学习、已有 Python 代码偏 Python。

检测顺序：项目 `implementation.matlab_executable` → PATH 里的 `matlab` → macOS `/Applications/MATLAB_R*.app/bin/matlab`。preferred 不可用可以 fallback 并记录原因；任务声明的 `required_backend` 不可用则直接报错，不静默切换。

**一旦选定，只正式实现并运行这一种。** 除非用户明确要求跨语言互验，否则不做 parity 实现。

---

## 10. 产物清单

```text
<project>/
├── .cumcm/
│   ├── state.json              # 阶段、模式、后端偏好
│   ├── decisions.jsonl         # 追加式人工决策（唯一的正式批准来源）
│   ├── snapshots/<stage>.json  # 由 accepted decision 自动派生
│   └── tmp/pages/              # record_compile 渲染的逐页 PNG
├── problem/official/           # 官方输入，只读
├── problem/SOURCE_MANIFEST.json
├── analysis/                   # PROBLEM_FACTS / TASK_CAPABILITIES（+ 可选笔记）
├── model/MODEL_CONTRACT.json   # 含候选与选择记录
├── code/                       # 你的实现
├── runs/<id>/                  # RUN_MANIFEST + stdout/stderr（脚本写）
├── results/RESULTS_INDEX.json  # 脚本写
├── validation/                 # 复核包、复核结果、CLAIM_LEDGER
├── paper/                      # PAPER_PLAN、LaTeX、QA sidecars
├── delivery/                   # COMPILE_RECEIPT、DELIVERY_MANIFEST
└── handoffs/<transition>/HANDOFF.json
```

需要 agent 手写的契约只剩 9 个：`PROBLEM_FACTS`、`TASK_CAPABILITIES`、`MODEL_CONTRACT`、`CROSS_QUESTION_LEDGER`（可选）、`CLAIM_LEDGER`、`FIGURE_MANIFEST`（可选）、`PAPER_PLAN`、`PAPER_QUALITY_REPORT`、`INDEPENDENT_REVIEW_RESULT`。其余全部由脚本产生。

---

## 11. Hard invariant 一览

下列问题在任何模式下都阻断：

官方输入被修改或身份不一致 · 把模拟数据当观测数据 · claim-bearing 计算没有成功的 official run · 源码快照/formal input/claim-bearing output 漂移 · result locator 错误或索引值与输出不一致 · 复核包或 handoff stale · 伪造人工审批或独立复核 · validation/paper 存在开放 P0 · 最终 PDF 不可读或版本不一致 · PDF 未绑定已批准 QA 与 editable source · 字体/缺字检查失败 · PDF/LaTeX/计算程序三类交付不完整

---

## 12. 在 Codex 和 Claude Code 里用

唯一 canonical 树是 `.agents/skills/cumcm-workflow/`（SKILL.md、references、schemas、scripts、assets）。

- **Codex**：仓库内 `.agents/skills/` 自动可见，`agents/openai.yaml` 提供展示名和默认提示词。用 `$cumcm-workflow` 触发。
- **Claude Code**：`.claude/skills/cumcm-workflow/SKILL.md` 是指向 canonical 树的**薄路由**——它不复述任何规则，因此两个入口不会漂移；根目录 `CLAUDE.md` 是改这个仓库时的工程约定。在仓库里直接说"用 cumcm-workflow 初始化…"即可，也可以把 `.claude/skills/cumcm-workflow/` 复制到 `~/.claude/skills/`。

两边执行同一套脚本，脚本用 `Path(__file__)` 定位 schema 和 assets，与工作目录无关。`tests/test_entry_points.py` 锁住这一点：路由提到的每个脚本必须真实存在，两个入口的 frontmatter 必须一致。

---

## 13. 开发

```text
.agents/skills/cumcm-workflow/   # canonical
.claude/skills/cumcm-workflow/   # Claude Code 路由
CLAUDE.md                        # 改仓库时的约定
docs/                            # 架构、合同、provenance、限制、v0.6 设计
tests/  examples/  .github/workflows/ci.yml
```

```bash
python3 -m pip install -r requirements-ci.txt
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 -m compileall -q .agents/skills/cumcm-workflow/scripts tests
```

CI 在 Python 3.10 与 3.13 上跑契约测试；另有一个装了 texlive 的 job 用**真实 xelatex 编译**跑通 recorder 链路。

不向下兼容：v0.6 拒绝任何 `schema_version` 不是 `0.6.0` 的契约，仓库里也不再保留迁移脚本。旧工作区请用官方文件重新初始化。

---

## 14. 局限

- 检查通过不代表模型、统计设计或全局最优性被证明。
- fresh context 降低污染，但不能证明 reviewer 独立或正确；同模型的 fresh task 仍然相关。
- digest 证明文件身份，不证明代码实现了它声称的数学。
- 冻结后的模型合同可能退化成"对已写好代码的事后描述"。机器只能检查 `verification_plan` 是否对应到已记录的断言；剩下的写在 `REVIEW_REQUEST.md` 的失败类清单里，交给 fresh-context reviewer。
- `plan_redo.py` 只能沿已记录的 ID 图推断，看不到未声明的隐式依赖。
- 版面检查来自编译日志，发现不了"图里文字太小"。逐页 PNG 已经渲染好了，仍然需要人去看。
- 记录器只在被调用时记录：绕过 `record_run.py` 直接跑仍可能产生无证据的结果，检查器只能发现"没有 official run 支撑"。

完整列表见 [已知限制](docs/limitations.md)。

[MIT License](LICENSE)

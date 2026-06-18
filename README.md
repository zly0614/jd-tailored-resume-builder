# Jianli Creator
> 2026-05-29 更新：默认模板 `zhang_leyan_default` 已调整为基于 `resume_builder/static/template_files/zhang_leyan_default.doc` 的 Word 模板填充策略，优先输出 `.docx` 与 `.pdf`，不再默认走 LaTeX 近似排版。

Jianli Creator 是一个面向求职场景的本地化简历生成项目，核心目标是把“个人长期简历资料”沉淀成可复用的简历知识库，再基于不同岗位 JD 快速生成定制化简历。

当前版本已经不再是单页表单，而是一个按阶段推进的多页面流程：

1. 选择简历模板
2. 建立个人简历知识库
3. 上传岗位 JD 并配置生成参数
4. 查看结果、下载文件、保存反馈

## 项目定位

这个项目主要解决两个问题：

- 把零散的个人经历整理成长期可复用的“简历知识库”
- 针对不同岗位 JD，快速生成更匹配的投递版本

它不是简单的“输入一段文本生成一份简历”，而是围绕“主档案 + 岗位定制 + 持续反馈”来设计的。

## 当前能力

- 维护一份结构化的个人简历知识库
- 支持模板选择，并以模板图片卡片方式展示
- 支持按阶段录入个人信息、工作经历、教育经历、技能、项目经历
- 支持将录入内容实时同步成知识库 JSON
- 支持粘贴补充资料或旧简历内容，作为生成上下文
- 支持输入目标岗位 JD，生成针对岗位的定制化简历
- 支持兼容 OpenAI 接口的大模型优化简历表达
- 在缺少 API Key 时自动回退到启发式生成
- 支持导出 `.tex`
- 本地安装 LaTeX 引擎后支持导出 `.pdf`
- 支持将用户反馈写入 `memory.md`，供后续生成复用

## 产品流程

### 1. 模板选择页

用户首先进入模板选择页，而不是直接看到一个大表单。

这一页支持：

- 查看模板图片预览
- 选择要使用的简历模板
- 进入下一步建档流程

### 2. 知识库建档页

这一页只负责建立个人长期简历知识库，不混入 JD 和生成结果。

用户可以录入：

- 个人信息
- 工作经历
- 教育经历
- 技能
- 项目经历

页面会实时同步生成知识库 JSON，供后续阶段继续使用。

### 3. JD 配置与生成页

这一页专门负责岗位定制，不再和建档混在一起。

用户可以在这里：

- 粘贴补充资料或旧简历内容
- 粘贴目标岗位 JD
- 选择 `llm` 或 `heuristic` 生成模式
- 选择中英文简历输出
- 选择是否同时导出 PDF
- 配置模型名称、Base URL、API Key

### 4. 结果页

结果页只负责展示输出和继续迭代。

支持：

- 查看生成后的 LaTeX 内容
- 查看结构化 Draft
- 下载 `.tex`
- 下载 `.pdf`
- 下载 PDF 编译日志
- 保存反馈到 `memory.md`
- 返回上一阶段继续修改 JD 或知识库

## 项目结构

```text
resume_builder/
  __init__.py
  __main__.py
  cli.py
  draft.py
  jd_parser.py
  latex_renderer.py
  llm.py
  memory.py
  models.py
  pdf.py
  profile_loader.py
  ranking.py
  service.py
  template_registry.py
  web.py
  static/
    template_files/
      zhang_leyan_default.doc
    template_previews/
      zhang_leyan_default.svg
      modern_blocks.svg
  templates/
    base.html
    choose_template.html
    build_profile.html
    customize_resume.html
    result.html
data/
  master_profile.sample.json
  sample_jd.txt
outputs/
scripts/
tests/
  test_generation.py
memory.md
local_settings.example.json
```

## 运行环境

推荐环境：

- Windows PowerShell
- Conda 环境：`test`
- Python 3.10+

如果你已经准备好了 `test` 环境，可以直接启动。

## 快速启动

启动本地 Web 服务：

```powershell
conda run -n test python -m resume_builder serve --host 127.0.0.1 --port 8000
```

浏览器打开：

`http://127.0.0.1:8000`

## Web 使用步骤

启动后，建议按下面顺序使用：

1. 在模板选择页挑选简历模板图片
2. 进入建档页，填写个人信息、工作经历、教育经历、技能和项目经历
3. 检查系统同步出的知识库 JSON
4. 进入 JD 配置页，粘贴目标岗位 JD
5. 如有需要，补充旧简历内容或额外背景信息
6. 选择生成模式和模型参数
7. 生成岗位定制简历
8. 在结果页查看输出、下载文件、保存反馈

## CLI 用法

### 1. 生成简历

```powershell
conda run -n test python -m resume_builder generate `
  --profile data/master_profile.sample.json `
  --jd-file data/sample_jd.txt `
  --out outputs/resume.tex
```

### 2. 手动追加反馈

```powershell
conda run -n test python -m resume_builder feedback `
  --memory-file memory.md `
  --target-role "高级 AI 产品经理" `
  --feedback "进一步突出知识库产品经验和结果指标。"
```

## PDF 导出说明

如果要启用 PDF 导出，需要先在本地安装 LaTeX 引擎。

在 Windows 上，项目会优先尝试 MiKTeX 私有安装方式，无需管理员权限；也支持 Chocolatey 作为回退方案。

### 通过项目 CLI 安装

```powershell
conda run -n test python -m resume_builder install-latex
```

### 通过 PowerShell 脚本安装

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install-latex.ps1
```

### 强制使用 Chocolatey 回退安装

```powershell
conda run -n test python -m resume_builder install-latex --provider choco
```

安装完成后，重新启动 Web 服务，并在生成页选择 `generate tex + pdf`。

## 模型配置

项目支持兼容 OpenAI Chat Completions 接口的大模型服务。

可选环境变量：

- `OPENAI_API_KEY`
- `OPENAI_MODEL`，默认：`gpt-4.1-mini`
- `OPENAI_BASE_URL`，默认：`https://api.openai.com/v1`

如果你使用当前的 MiMo 兼容接口，可在页面中填写：

- `LLM Model`: `MiMo-V2.5-Pro`
- `LLM Base URL`: `https://token-plan-cn.xiaomimimo.com/v1`
- `LLM API Key`: 运行时填写，不要提交到仓库

如果希望在本地保存默认模型配置，可复制一份 `local_settings.example.json` 为 `local_settings.json`。该文件已被 Git 忽略，适合保存你自己的本地模型参数。

参考文件：[local_settings.example.json](/D:/test/jianli-creator/local_settings.example.json)

## 测试

运行测试：

```powershell
conda run -n test python -m unittest discover -s tests
```

## 当前边界与后续方向

当前版本已经具备“简历知识库 + JD 定制生成”的主链路，但还可以继续往完整产品演进：

- 增加更多真正可渲染的简历模板
- 支持上传 `.txt`、`.md`、`.docx`、`.pdf` 简历并自动抽取信息入库
- 增加对话式编辑能力，让用户直接通过自然语言修改知识库
- 增加岗位版本管理，保存同一知识库下的多份投递版本
- 增加事实来源和证据片段，降低大模型改写时的失真风险

## 说明

后续只要页面流程、功能入口或启动方式发生变化，README 也应该同步更新，避免代码和文档脱节。

## 许可证

当前仓库未单独声明 License。如需开源发布，建议补充明确的许可证文件。

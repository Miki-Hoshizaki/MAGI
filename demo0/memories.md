# 项目结构优化记录

2025-01-11:
1. 优化了项目结构，移除了多余的 magi 目录嵌套
2. 将核心文件从 `/magi/magi/magi/` 移动到 `/magi/magi/` 目录
3. 更新了项目依赖，在 setup.py 中指定了具体的版本要求：
   - requests>=2.31.0
   - python-dotenv>=1.0.0
   - openai>=1.3.5

# 项目说明

项目目标是构建一个使用三种不同个性的 agent 来决策 codegen 生成的代码的系统。每个 agent 会给出 POSITIVE 或 NEGATIVE 的反馈和具体意见。如果多数为 POSITIVE 则通过，如果多数为 NEGATIVE 则不通过。不通过时，会带着反馈意见、codegen 生成的代码以及用户的原始需求去重新生成代码。
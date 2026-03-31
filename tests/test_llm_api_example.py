import asyncio
from openerb.llm.config import LLMConfig
from openerb.modules.prefrontal_cortex import PrefrontalCortex
from openerb.core.types import UserProfile

async def main():
    # 使用环境变量配置 LLM (支持 DashScope, OpenAI, vLLM 等)
    # 环境变量: LLM_PROVIDER=dashscope, LLM_API_KEY=xxx, LLM_MODEL=qwen-vl-plus
    client = LLMConfig.create_client()
    cortex = PrefrontalCortex(llm_client=client, max_conversation_history=20)

    # 1. 处理纯文本输入
    print("\n=== Test 1: Text-only input ===")
    result = await cortex.process_input(
        text="让机器人向前走一步",
        user=UserProfile(name="Alice")
    )
    
    # 获取识别的意图
    print(f"识别到 {len(result.intents)} 个任务 (置信度: {result.confidence:.2f})")
    
    for i, intent in enumerate(result.intents, 1):
        print(f"  任务 {i}: {intent.action} (置信度: {intent.confidence:.2f})")
        if intent.parameters:
            print(f"    参数: {intent.parameters}")
    
    # 2. 处理多模态输入 (文本 + 图像)
    print("\n=== Test 2: Multi-modal input (text + image) ===")
    
    with open("/home/daojie/Pictures/kitchen.png", "rb") as f:
        image_bytes = f.read()
    
    result = await cortex.process_input(
        text="这张图片里有什么？",
        image=image_bytes,  # bytes 格式
        user=UserProfile(name="Bob")
    )
    
    print(f"识别到 {len(result.intents)} 个任务 (置信度: {result.confidence:.2f})")
    for i, intent in enumerate(result.intents, 1):
        print(f"  任务 {i}: {intent.action} (置信度: {intent.confidence:.2f})")
        if intent.parameters:
            print(f"    参数: {intent.parameters}")
    
    # 3. 访问对话历史和上下文
    print("\n=== Test 3: Conversation history ===")
    turns = cortex.conversation_turns
    context = cortex.conversation_context
    print(f"对话中有 {len(turns)} 轮对话")
    print(f"当前上下文用户: {context.current_user}")
    
    # 4. 保存对话记录
    print("\n=== Test 4: Conversation turns ===")
    for i, turn in enumerate(turns, 1):
        print(f"  轮 {i}: {turn.user_input[:50]}...")
    
    # 5. 清空历史 (如需)
    print("\n=== Test 5: Clear history ===")
    cortex.conversation_turns.clear()
    remaining_turns = len(cortex.conversation_turns)
    print(f"清除后对话中有 {remaining_turns} 轮对话")

# 运行示例
if __name__ == "__main__":
    asyncio.run(main())

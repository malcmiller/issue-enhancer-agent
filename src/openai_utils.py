from semantic_kernel.contents import ChatHistory
from semantic_kernel.connectors.ai.open_ai import AzureChatPromptExecutionSettings
from semantic_kernel.functions.kernel_arguments import KernelArguments

async def run_completion(kernel, messages):
    chat_service = kernel.get_service("azure-openai")
    history = ChatHistory()
    for msg in messages:
        role = msg.get("role")
        content = msg.get("content", "")
        if role == "system":
            history.add_system_message(content)
        elif role == "user":
            history.add_user_message(content)
    settings = AzureChatPromptExecutionSettings()
    result = await chat_service.get_chat_message_content(
        chat_history=history,
        settings=settings,
        kernel=kernel,
        kernel_arguments=KernelArguments()
    )
    return result.content

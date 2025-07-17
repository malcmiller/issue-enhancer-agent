import sys
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import ChatHistory
from semantic_kernel.connectors.ai.open_ai import AzureChatPromptExecutionSettings
from semantic_kernel.functions.kernel_arguments import KernelArguments

API_VERSION = "2024-12-01-preview"

def initialize_kernel(inputs):
    kernel = Kernel()
    try:
        kernel.add_service(
            AzureChatCompletion(
                service_id="azure-openai",
                api_key=inputs["openai_api_key"],
                endpoint=inputs["azure_endpoint"],
                deployment_name=inputs["azure_deployment"],
                api_version=API_VERSION
            )
        )
    except Exception as e:
        print(f"Error initializing AzureChatCompletion: {e}", file=sys.stderr)
        sys.exit(1)


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

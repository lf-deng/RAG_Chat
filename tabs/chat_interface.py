import gradio as gr
from rag_chat import chat_with_rag, reset_welcome_state, get_welcome_message

# 全局变量，用于存储组件
chatbot_component = None


def get_avatar_url(avatar_name):
    avatar_url = {
        "default_assistant": "https://api.dicebear.com/7.x/bottts/svg?seed=assistant",
        "default_user": "https://api.dicebear.com/7.x/thumbs/svg?seed=user",
    }
    return avatar_url[avatar_name]


def create_chat_ui():
    global chatbot_component
    # 获取欢迎消息作为初始值
    initial_message = [{"role": "assistant", "content": get_welcome_message()}]

    # 获取头像URL
    user_avatar_url = get_avatar_url("default_user")
    assistant_avatar_url = get_avatar_url("default_assistant")

    chatbot = gr.Chatbot(
        type="messages",
        resizable=True,
        show_copy_button=True,
        show_label=False,
        bubble_full_width=True,
        container=True,
        min_height=750,
        value=initial_message,  # 设置初始欢迎消息
        # 添加头像配置
        avatar_images=(
            user_avatar_url,
            assistant_avatar_url,
        ),
    )

    # 移除未使用的更新器按钮

    with gr.Row():
        with gr.Column(scale=8):
            msg = gr.Textbox(
                placeholder="在这里输入您的问题...",
                lines=4,
                max_lines=4,
                container=False,
            )

        with gr.Column(scale=1, min_width=100):
            send = gr.Button("发送", size="md", variant="primary")

            # 自定义清除函数，重置欢迎消息状态并清除聊天记录
            def clear_and_reset():
                reset_welcome_state()
                # 获取最新的欢迎消息
                welcome = get_welcome_message()
                return "", [{"role": "assistant", "content": welcome}]

            clear = gr.Button("清除", size="md")
            clear.click(
                fn=clear_and_reset,
                outputs=[msg, chatbot],
            )

    send.click(
        chat_with_rag,
        [msg, chatbot],
        [chatbot],
        queue=True,
    )
    send.click(lambda: "", None, msg)
    msg.submit(
        chat_with_rag,
        [msg, chatbot],
        [chatbot],
        queue=True,
    )
    msg.submit(lambda: "", None, msg)

    # 保存chatbot组件的引用
    chatbot_component = chatbot

    return {"chatbot": chatbot, "msg": msg}

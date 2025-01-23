import gradio as gr
from chat import glm4_chat


def create_chat_ui():
    # with gr.TabItem("GLM-4-Flash"):
    # with gr.Column():
    chatbot = gr.Chatbot(
        height=500,
        show_copy_button=True,
        bubble_full_width=True,
        container=True,
    )
    with gr.Row(equal_height=True):
        msg = gr.Textbox(
            placeholder="在这里输入您的问题...",
            label="输入",
            lines=2,
            scale=8,
            container=False,
        )

        with gr.Column(scale=1, min_width=100):
            send = gr.Button("发送", size="sm")
            clear = gr.ClearButton(
                components=[msg, chatbot],
                value="清除",
                size="sm",
            )

    send.click(
        glm4_chat,
        [msg, chatbot],
        [chatbot],
        queue=True,
    )
    send.click(lambda: "", None, msg)
    msg.submit(
        glm4_chat,
        [msg, chatbot],
        [chatbot],
        queue=True,
    )
    msg.submit(lambda: "", None, msg)

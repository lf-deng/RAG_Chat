import gradio as gr
from rag_chat import chat_with_rag


def create_chat_ui():
    chatbot = gr.Chatbot(
        type="messages",
        resizable=True,
        show_copy_button=True,
        show_label=False,
        bubble_full_width=True,
        container=True,
    )
    with gr.Row():
        with gr.Column(scale=8):
            msg = gr.Textbox(
                placeholder="在这里输入您的问题...",
                lines=2,
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

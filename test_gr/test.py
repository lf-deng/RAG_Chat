import gradio as gr


def random_response(message, history):
    return "abcd"


demo = gr.ChatInterface(random_response, title="Qwen2")


demo.launch(inbrowser=True)

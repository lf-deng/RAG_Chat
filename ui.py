import gradio as gr
from utils import get_local_ip
from tabs import glm4_flash


def create_demo():
    """创建 Gradio 界面"""
    local_ip = get_local_ip()
    print(
        f"""
                    # Chat with GLM
                    欢迎使用 GLM 聊天界面！
                    
                    ## 访问方式
                    - 本机访问：http://127.0.0.1:7860
                    - 局域网访问：http://{local_ip}:7860
                    """
    )

    with gr.Blocks(title="Chat with GLM") as demo:

        with gr.Row():
            # 左侧边栏
            with gr.Column(scale=1):
                gr.Markdown("### 知识库管理")
                create_kb_btn = gr.Button("创建知识库")

            # 分隔线

            # 右侧主要内容
            with gr.Column(scale=4):
                glm4_flash.create_chat_ui()

    return demo

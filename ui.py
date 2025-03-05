import gradio as gr
from utils import get_local_ip
from tabs import chat_interface


INFO_DURATION = 2


def show_create_kb_func():
    """显示知识库管理界面"""
    gr.Info("创建知识库", duration=INFO_DURATION)
    return [
        gr.update(visible=False),  # chat_ui 的更新
        gr.update(visible=True),  # create_kb_ui 的更新
    ]


def save_kb_func():
    """保存知识库"""
    gr.Info("保存知识库", duration=INFO_DURATION)
    return [
        gr.update(visible=True),  # chat_ui 的更新
        gr.update(visible=False),  # create_kb_ui 的更新
    ]


def show_select_kb_func():
    """显示知识库选择界面"""
    gr.Info("选择加载知识库", duration=INFO_DURATION)
    return [
        gr.update(visible=False),  # chat_ui 的更新
        gr.update(visible=True),  # select_kb_ui 的更新
    ]


def load_kb_func():
    """加载知识库"""
    gr.Info("加载知识库", duration=INFO_DURATION)
    return [
        gr.update(visible=True),  # chat_ui 的更新
        gr.update(visible=False),  # select_kb_ui 的更新
    ]


def create_demo():
    """创建 Gradio 界面"""
    local_ip = get_local_ip()
    print(
        f"""
        ## 访问方式
        - 本机访问：http://127.0.0.1:7860
        - 局域网访问：http://{local_ip}:7860
        """
    )

    with gr.Blocks(title="RAG Chat") as demo:
        with gr.Row():
            # 左侧边栏
            with gr.Column(scale=1):
                gr.Markdown("### 知识库管理")
                create_kb_btn = gr.Button("创建知识库")
                select_kb_btn = gr.Button("选择知识库")

            # 右侧主要内容区域
            with gr.Column(scale=4) as chat_ui:
                chat_interface.create_chat_ui()

            # 知识库新建界面（初始隐藏）
            with gr.Column(scale=4, visible=False) as create_kb_ui:
                gr.Markdown("### 这是知识库管理页面")
                # 保存知识库
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Column()
                    with gr.Column(scale=2, min_width=100):
                        save_kb_btn = gr.Button("保存知识库")
                    with gr.Column(scale=1):
                        gr.Column()

            # 知识库选择界面（初始隐藏）
            with gr.Column(scale=4, visible=False) as select_kb_ui:
                gr.Markdown("### 这是知识库选择页面")
                # 知识库选择
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Column()
                    with gr.Column(scale=2, min_width=100):
                        load_kb_btn = gr.Button("加载知识库")
                    with gr.Column(scale=1):
                        gr.Column()

        # 绑定点击事件
        create_kb_btn.click(
            fn=show_create_kb_func,
            outputs=[chat_ui, create_kb_ui],
        )

        save_kb_btn.click(
            fn=save_kb_func,
            outputs=[chat_ui, create_kb_ui],
        )

        select_kb_btn.click(
            fn=show_select_kb_func,
            outputs=[chat_ui, select_kb_ui],
        )

        load_kb_btn.click(
            fn=load_kb_func,
            outputs=[chat_ui, select_kb_ui],
        )

    return demo

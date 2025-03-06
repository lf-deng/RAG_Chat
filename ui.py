import gradio as gr
from utils import get_local_ip
from tabs import chat_interface
import os


INFO_DURATION = 2


def show_chat_func():
    """显示聊天界面"""
    gr.Info("切换到RAG问答", duration=INFO_DURATION)
    return [
        gr.update(visible=True),  # chat_ui
        gr.update(visible=False),  # create_kb_ui
        gr.update(visible=False),  # select_kb_ui
    ]


def show_create_kb_func():
    """显示知识库管理界面"""
    gr.Info("创建知识库", duration=INFO_DURATION)
    return [
        gr.update(visible=False),  # chat_ui
        gr.update(visible=True),  # create_kb_ui
        gr.update(visible=False),  # select_kb_ui
    ]


def show_select_kb_func():
    """显示知识库选择界面"""
    gr.Info("选择加载知识库", duration=INFO_DURATION)
    return [
        gr.update(visible=False),  # chat_ui
        gr.update(visible=False),  # create_kb_ui
        gr.update(visible=True),  # select_kb_ui
    ]


def save_kb_func():
    """保存知识库后返回聊天界面"""
    gr.Info("保存知识库", duration=INFO_DURATION)
    return [
        gr.update(visible=True),  # chat_ui
        gr.update(visible=False),  # create_kb_ui
        gr.update(visible=False),  # select_kb_ui
    ]


def load_kb_func(kb_name):
    """加载知识库后返回聊天界面"""
    from rag_chat import load_knowledge_base

    print("初始化LightRAG...")
    print("选择的知识库是：", kb_name)

    if load_knowledge_base(kb_name):
        gr.Info(f"成功加载知识库：{kb_name}", duration=INFO_DURATION)
        print("加载完成！")
    else:
        print("加载失败！")
        gr.Info("加载知识库失败！", duration=INFO_DURATION)
        return [
            gr.update(visible=False),  # chat_ui
            gr.update(visible=False),  # create_kb_ui
            gr.update(visible=True),  # select_kb_ui
        ]

    return [
        gr.update(visible=True),  # chat_ui
        gr.update(visible=False),  # create_kb_ui
        gr.update(visible=False),  # select_kb_ui
    ]


def get_local_kb_list():
    """获取本地知识库列表"""
    kb_dir = "./local_kb"
    if not os.path.exists(kb_dir):
        os.makedirs(kb_dir)
    kb_list = [f for f in os.listdir(kb_dir) if os.path.isdir(os.path.join(kb_dir, f))]
    return kb_list


def show_kb_content(kb_name):
    """显示选中的知识库内容"""
    kb_path = os.path.join("./local_kb", kb_name)
    files = os.listdir(kb_path)

    content = ""
    # 读取description.txt文件内容，如果文件不存在，则返回空字符串
    if os.path.exists(os.path.join(kb_path, "description.txt")):
        with open(os.path.join(kb_path, "description.txt"), "r", encoding="utf-8") as f:
            content = f.read()

    return [
        gr.update(visible=True),  # kb_content
        kb_name,  # kb_title
        gr.update(interactive=True),  # back_btn
        gr.update(interactive=True),  # load_kb_btn
        gr.update(interactive=True),  # delete_kb_btn
        gr.update(visible=False),  # kb_buttons
        content,  # kb_text
    ]


def back_to_kb_list():
    """返回知识库列表"""
    return [
        gr.update(visible=False),  # kb_content
        "### Default Knowledge Base",  # kb_title
        gr.update(interactive=False),  # back_btn
        gr.update(interactive=False),  # load_kb_btn
        gr.update(interactive=False),  # delete_kb_btn
        gr.update(visible=True),  # kb_buttons
        "",  # kb_text
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
        # 添加进度条
        gr.Progress()

        with gr.Row():
            # 左侧边栏
            with gr.Column(scale=1):
                gr.Markdown("### 知识库管理")
                chat_btn = gr.Button("RAG问答")
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

                # 声明所有组件
                # 已有的知识库列表
                with gr.Row() as kb_btns_list:
                    kb_list = get_local_kb_list()
                    kb_btns = []
                    for kb_name in kb_list:
                        btn = gr.Button(kb_name)
                        kb_btns.append(btn)

                # (被选择的)知识库内容显示（初始隐藏）
                with gr.Column(visible=False) as kb_content:
                    # 知识库名称
                    kb_title = gr.Markdown("Default Knowledge Base")

                    kb_text = gr.Textbox(
                        label="知识库信息", interactive=False, lines=10
                    )

                # 知识库选择按钮
                with gr.Row():
                    with gr.Column(scale=1):
                        back_btn = gr.Button("返回", interactive=False)
                    with gr.Column(scale=1):
                        load_kb_btn = gr.Button("加载知识库", interactive=False)
                    with gr.Column(scale=1):
                        delete_kb_btn = gr.Button("删除知识库", interactive=False)

                # 绑定返回
                back_btn.click(
                    fn=back_to_kb_list,
                    outputs=[
                        kb_content,
                        kb_title,
                        back_btn,
                        load_kb_btn,
                        delete_kb_btn,
                        kb_btns_list,
                        kb_text,
                    ],
                )

                for kb_name, btn in zip(kb_list, kb_btns):
                    btn.click(
                        fn=show_kb_content,
                        inputs=[gr.Textbox(value=kb_name, visible=False)],
                        outputs=[
                            kb_content,
                            kb_title,
                            back_btn,
                            load_kb_btn,
                            delete_kb_btn,
                            kb_btns_list,
                            kb_text,
                        ],
                    )

        # 绑定左侧按钮点击事件
        chat_btn.click(
            fn=show_chat_func,
            outputs=[chat_ui, create_kb_ui, select_kb_ui],
        )

        create_kb_btn.click(
            fn=show_create_kb_func,
            outputs=[chat_ui, create_kb_ui, select_kb_ui],
        )

        select_kb_btn.click(
            fn=show_select_kb_func,
            outputs=[chat_ui, create_kb_ui, select_kb_ui],
        )

        # 绑定功能按钮点击事件
        save_kb_btn.click(
            fn=save_kb_func,
            outputs=[chat_ui, create_kb_ui, select_kb_ui],
        )

        load_kb_btn.click(
            fn=load_kb_func,
            inputs=[kb_title],  # 传入当前选中的知识库名称
            outputs=[chat_ui, create_kb_ui, select_kb_ui],
        )

    return demo

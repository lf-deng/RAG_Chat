import gradio as gr
from utils import get_local_ip
from tabs import chat_interface
import os
import shutil


INFO_DURATION = 2

# 定义界面状态常量
UI_STATES = {
    "CHAT": [
        gr.update(visible=True),  # chat_ui
        gr.update(visible=False),  # create_kb_ui
        gr.update(visible=False),  # select_kb_ui
    ],
    "CREATE": [
        gr.update(visible=False),  # chat_ui
        gr.update(visible=True),  # create_kb_ui
        gr.update(visible=False),  # select_kb_ui
    ],
    "SELECT": [
        gr.update(visible=False),  # chat_ui
        gr.update(visible=False),  # create_kb_ui
        gr.update(visible=True),  # select_kb_ui
    ],
}


def show_chat():
    """显示聊天界面"""
    gr.Info("切换到RAG问答", duration=INFO_DURATION)
    return UI_STATES["CHAT"]


def show_create_knowledge_base():
    """显示知识库管理界面"""
    gr.Info("创建知识库", duration=INFO_DURATION)
    return UI_STATES["CREATE"]


def show_select_knowledge_base():
    """显示知识库选择界面"""
    gr.Info("选择加载知识库", duration=INFO_DURATION)
    return UI_STATES["SELECT"]


def create_knowledge_base(kb_name, kb_desc, files):
    """保存知识库"""
    if not kb_name:
        gr.Warning("请输入知识库名称！")
        return UI_STATES["CREATE"]

    # 检查知识库名称是否合法
    if not kb_name.strip() or any(c in r'\/:*?"<>|' for c in kb_name):
        gr.Warning("知识库名称不能包含特殊字符！")
        return UI_STATES["CREATE"]

    # 创建知识库目录
    kb_dir = os.path.join("./local_kb", kb_name)
    if os.path.exists(kb_dir):
        gr.Warning(f"知识库 '{kb_name}' 已存在！")
        return UI_STATES["CREATE"]

    try:
        # 创建知识库目录
        os.makedirs(kb_dir)

        # 保存知识库描述
        with open(os.path.join(kb_dir, "description.txt"), "w", encoding="utf-8") as f:
            f.write(kb_desc or "暂无介绍")

        # 保存上传的文件，暂未实现
        # if files:
        #     for file in files:
        #         file_name = os.path.basename(file.name)
        #         os.rename(file.name, os.path.join(kb_dir, file_name))

        gr.Info(f"成功创建知识库：{kb_name}", duration=INFO_DURATION)
        return UI_STATES["CHAT"]
    except Exception as e:
        print(f"创建知识库时发生错误: {e}")
        gr.Warning(f"创建知识库失败：{str(e)}")
        return UI_STATES["CREATE"]


def load_knowledge_base(kb_name):
    """加载知识库后返回聊天界面"""
    from rag_chat import load_knowledge_base_rag, set_welcome_message

    if not kb_name or kb_name == "请选择一个知识库":
        gr.Warning("请先选择一个知识库！")
        return UI_STATES["SELECT"] + [None]  # 添加一个None作为chatbot的更新值

    print("初始化LightRAG...")
    print("选择的知识库是：", kb_name)
    gr.Info("初始化 RAG...", duration=INFO_DURATION)

    try:
        # 获取知识库介绍
        kb_path = os.path.join("./local_kb", kb_name)
        kb_desc = "暂无介绍"
        if os.path.exists(os.path.join(kb_path, "description.txt")):
            with open(
                os.path.join(kb_path, "description.txt"), "r", encoding="utf-8"
            ) as f:
                kb_desc = f.read()

        # 设置欢迎消息
        welcome_message = (
            f"### 已加载知识库: {kb_name}\n\n{kb_desc}\n\n您可以开始提问了。"
        )

        if load_knowledge_base_rag(kb_name):
            # 设置欢迎消息
            set_welcome_message(welcome_message)
            gr.Info(f"成功加载知识库：{kb_name}", duration=INFO_DURATION)
            print("加载完成！")

            # 返回UI状态和更新后的chatbot值
            return UI_STATES["CHAT"] + [
                [{"role": "assistant", "content": welcome_message}]
            ]
        else:
            print("加载失败！")
            gr.Warning("加载知识库失败！")
            return UI_STATES["SELECT"] + [None]  # 添加一个None作为chatbot的更新值
    except Exception as e:
        print(f"加载知识库时发生错误: {e}")
        gr.Warning(f"加载知识库失败：{str(e)}")
        return UI_STATES["SELECT"] + [None]  # 添加一个None作为chatbot的更新值


def get_knowledge_base_list():
    """获取本地知识库列表"""
    kb_dir = "./local_kb"
    if not os.path.exists(kb_dir):
        os.makedirs(kb_dir)
    kb_list = [f for f in os.listdir(kb_dir) if os.path.isdir(os.path.join(kb_dir, f))]
    return sorted(kb_list)  # 按字母顺序排序


def delete_knowledge_base(kb_name):
    """删除选中的知识库"""
    if not kb_name or kb_name == "请选择一个知识库":
        gr.Warning("请先选择一个知识库！")
        return False

    kb_path = os.path.join("./local_kb", kb_name)

    try:
        # 检查知识库是否存在
        if not os.path.exists(kb_path):
            gr.Warning(f"知识库 '{kb_name}' 不存在！")
            return False

        # 删除知识库目录及其所有内容
        shutil.rmtree(kb_path)

        gr.Info(f"成功删除知识库：{kb_name}", duration=INFO_DURATION)
        return True
    except Exception as e:
        print(f"删除知识库时发生错误: {e}")
        gr.Warning(f"删除知识库失败：{str(e)}")
        return False


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
                with gr.Row():
                    gr.Markdown("### 知识库管理")
                with gr.Row():
                    with gr.Column(scale=1):
                        chat_btn = gr.Button("RAG问答")
                        create_kb_btn = gr.Button("创建知识库")
                        select_kb_btn = gr.Button("选择知识库")

            # chatbot
            with gr.Column(scale=4) as chat_ui:
                chat_interface.create_chat_ui()
                chatbot = chat_interface.chatbot_component

            # 知识库新建界面（初始隐藏）
            with gr.Column(scale=4, visible=False) as create_kb_ui:
                gr.Markdown("### 创建新知识库")

                # 知识库名称
                new_kb_name = gr.Textbox(
                    label="知识库名称",
                    placeholder="请输入知识库名称（不能包含特殊字符）",
                    lines=1,
                )

                # 文件上传
                kb_files = gr.File(
                    label="上传文件",
                    file_types=[".txt", ".md", ".docx", ".doc"],
                    file_count="multiple",
                )

                # 知识库介绍
                kb_desc = gr.Textbox(
                    label="知识库介绍", placeholder="请输入知识库介绍（可选）", lines=3
                )

                # 保存按钮
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Column()
                    with gr.Column(scale=2, min_width=100):
                        save_kb_btn = gr.Button("保存知识库", variant="primary")
                    with gr.Column(scale=1):
                        gr.Column()

            # 知识库选择界面（初始隐藏）
            with gr.Column(scale=4, visible=False) as select_kb_ui:
                gr.Markdown("### 知识库选择")

                # 声明所有组件
                # 已有的知识库列表，添加提示选项
                def get_dropdown_choices():
                    kb_list = get_knowledge_base_list()
                    # 添加一个提示选项
                    return (
                        ["请选择一个知识库"] + kb_list
                        if kb_list
                        else ["请选择一个知识库"]
                    )

                kb_list_dropdown = gr.Dropdown(
                    label="选择知识库",
                    choices=get_dropdown_choices(),
                    interactive=True,
                    value="请选择一个知识库",  # 初始值为提示文本
                )

                # 刷新知识库列表
                def refresh_kb_list():
                    return gr.update(
                        choices=get_dropdown_choices(), value="请选择一个知识库"
                    )

                # (被选择的)知识库内容显示（初始隐藏）
                with gr.Column(visible=False) as kb_content:
                    # 知识库名称
                    kb_title = gr.Markdown("Default Knowledge Base")

                    kb_text = gr.Textbox(
                        label="知识库信息", interactive=False, lines=10
                    )

                # 知识库操作按钮
                with gr.Row():
                    with gr.Column(scale=1):
                        load_kb_btn = gr.Button(
                            "加载知识库", interactive=False, variant="primary"
                        )
                    with gr.Column(scale=1):
                        delete_kb_btn = gr.Button(
                            "删除知识库", interactive=False, variant="stop"
                        )

                # 绑定查看知识库逻辑
                def view_selected_kb(kb_name):
                    # 如果选择了提示选项或者未选择任何选项
                    if kb_name == "请选择一个知识库" or not kb_name:
                        # 隐藏内容区域
                        return [
                            gr.update(visible=False),  # kb_content
                            gr.update(value=""),  # kb_title
                            gr.update(interactive=False),  # load_kb_btn
                            gr.update(interactive=False),  # delete_kb_btn
                            gr.update(value=""),  # kb_text
                        ]

                    kb_path = os.path.join("./local_kb", kb_name)

                    try:
                        # 读取description.txt文件内容
                        content = ""
                        if os.path.exists(os.path.join(kb_path, "description.txt")):
                            with open(
                                os.path.join(kb_path, "description.txt"),
                                "r",
                                encoding="utf-8",
                            ) as f:
                                content = f.read()
                        else:
                            content = "暂无知识库介绍"

                        return [
                            gr.update(visible=True),  # kb_content
                            gr.update(value=kb_name),  # kb_title
                            gr.update(interactive=True),  # load_kb_btn
                            gr.update(interactive=True),  # delete_kb_btn
                            gr.update(value=content),  # kb_text
                        ]
                    except Exception as e:
                        print(f"读取知识库信息时发生错误: {e}")
                        gr.Warning(f"读取知识库信息失败：{str(e)}")
                        return [
                            gr.update(visible=False),  # kb_content
                            gr.update(value=""),  # kb_title
                            gr.update(interactive=False),  # load_kb_btn
                            gr.update(interactive=False),  # delete_kb_btn
                            gr.update(value=""),  # kb_text
                        ]

                # 当下拉菜单选择变化时更新知识库内容
                kb_list_dropdown.change(
                    fn=view_selected_kb,
                    inputs=[kb_list_dropdown],
                    outputs=[
                        kb_content,
                        kb_title,
                        load_kb_btn,
                        delete_kb_btn,
                        kb_text,
                    ],
                )

        # 绑定左侧按钮点击事件
        chat_btn.click(
            fn=show_chat,
            outputs=[chat_ui, create_kb_ui, select_kb_ui],
        )

        create_kb_btn.click(
            fn=show_create_knowledge_base,
            outputs=[chat_ui, create_kb_ui, select_kb_ui],
        )

        select_kb_btn.click(
            fn=show_select_knowledge_base,
            outputs=[chat_ui, create_kb_ui, select_kb_ui],
        ).then(fn=refresh_kb_list, outputs=[kb_list_dropdown])

        # 绑定功能按钮点击事件
        save_kb_btn.click(
            fn=create_knowledge_base,
            inputs=[new_kb_name, kb_desc, kb_files],
            outputs=[chat_ui, create_kb_ui, select_kb_ui],
        )

        load_kb_btn.click(
            fn=load_knowledge_base,
            inputs=[kb_title],  # 传入当前选中的知识库名称
            outputs=[chat_ui, create_kb_ui, select_kb_ui, chatbot],
        )

        # 删除知识库后重新加载选择界面
        def delete_and_reload(kb_name):
            success = delete_knowledge_base(kb_name)
            # 无论成功与否，都返回选择界面
            return UI_STATES["SELECT"]

        # 绑定删除知识库按钮
        delete_kb_btn.click(
            fn=delete_and_reload,
            inputs=[kb_title],  # 传入当前选中的知识库名称
            outputs=[chat_ui, create_kb_ui, select_kb_ui],
        ).then(fn=refresh_kb_list, outputs=[kb_list_dropdown]).then(
            fn=lambda: [
                gr.update(visible=False),  # kb_content
                gr.update(value=""),  # kb_title
                gr.update(interactive=False),  # load_kb_btn
                gr.update(interactive=False),  # delete_kb_btn
                gr.update(value=""),  # kb_text
            ],
            outputs=[
                kb_content,
                kb_title,
                load_kb_btn,
                delete_kb_btn,
                kb_text,
            ],
        )

    return demo

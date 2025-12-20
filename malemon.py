import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import markdown
from ttkbootstrap import Style
from tkhtmlview import HTMLLabel
import os
import re
import sys

class MarkdownEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Malemon")
        self.root.geometry("1200x800")
        
        # 文件路径
        self.current_file = None
        
        # 状态变量
        self.is_modified = False
        self.auto_preview_enabled = True
        self.last_content = ""
        self.after_id = None  # 用于存储定时器ID
        
        # 创建样式（只创建一次）
        self.style = Style(theme="litera")
        
        # 创建组件和菜单
        self.create_main_widgets()
        self.create_menu_bar()
        self.bind_events()
        
        # 更新主题标签
        self.theme_label.config(text=f"主题: {self.style.theme.name}")
        
        # 初始内容 - 修改为空
        self.update_preview_and_status()
        
        # 初始语法高亮
        self.highlight_syntax()
        
        # 初始更新标题
        self.update_title()
    
    def create_main_widgets(self):
        """创建主要UI组件（不包括菜单栏）"""
        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建工具栏
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill=tk.X, pady=(0, 5))
        
        # 工具栏按钮
        ttk.Button(toolbar, text="📁 打开", command=self.open_file, style="primary.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="💾 保存", command=self.save_file, style="success.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🔄 新建", command=self.new_file, style="info.TButton").pack(side=tk.LEFT, padx=2)
        
        # 主题选择下拉框
        theme_frame = ttk.Frame(toolbar)
        theme_frame.pack(side=tk.LEFT, padx=10)
        ttk.Label(theme_frame, text="主题:").pack(side=tk.LEFT, padx=(0, 5))
        self.theme_var = tk.StringVar(value="litera")
        self.theme_combo = ttk.Combobox(theme_frame, textvariable=self.theme_var, 
                                       values=["litera", "vapor", "darkly", "cyborg", "superhero"], 
                                       state="readonly", width=10)
        self.theme_combo.pack(side=tk.LEFT)
        self.theme_combo.bind("<<ComboboxSelected>>", self.change_theme)
        
        # 创建分割窗格
        paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 左侧编辑区域
        editor_frame = ttk.LabelFrame(paned_window, text="编辑器", padding=5)
        paned_window.add(editor_frame, weight=1)
        
        # 创建编辑器框架（包含Text和Scrollbar）
        editor_container = ttk.Frame(editor_frame)
        editor_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建滚动条
        editor_scroll_y = ttk.Scrollbar(editor_container)
        editor_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        editor_scroll_x = ttk.Scrollbar(editor_container, orient=tk.HORIZONTAL)
        editor_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 创建编辑器
        self.editor = tk.Text(editor_container, 
                             wrap=tk.WORD,
                             font=("Consolas", 12),
                             undo=True,
                             padx=10,
                             pady=10,
                             yscrollcommand=editor_scroll_y.set,
                             xscrollcommand=editor_scroll_x.set)
        self.editor.pack(fill=tk.BOTH, expand=True)
        
        # 配置滚动条
        editor_scroll_y.config(command=self.editor.yview)
        editor_scroll_x.config(command=self.editor.xview)
        
        # 右侧预览区域
        preview_frame = ttk.LabelFrame(paned_window, text="预览", padding=5)
        paned_window.add(preview_frame, weight=1)
        
        # 创建预览框架（包含HTMLLabel和Scrollbar）
        preview_container = ttk.Frame(preview_frame)
        preview_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建预览滚动条
        preview_scroll_y = ttk.Scrollbar(preview_container)
        preview_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 创建预览区域
        self.preview = HTMLLabel(preview_container, 
                               html="<h1>Markdown 预览</h1><p>开始编辑以查看预览...</p>",
                               yscrollcommand=preview_scroll_y.set)
        self.preview.pack(fill=tk.BOTH, expand=True)
        
        # 配置预览滚动条
        preview_scroll_y.config(command=self.preview.yview)
        
        # 创建状态栏
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.status_label = ttk.Label(status_frame, text="就绪 | 字符数: 0 | 单词数: 0", font=("Arial", 9))
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        self.theme_label = ttk.Label(status_frame, text="", font=("Arial", 9))
        self.theme_label.pack(side=tk.RIGHT, padx=5)
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="新建", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="打开", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="保存", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="另存为", command=self.save_file_as, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.on_closing, accelerator="Ctrl+Q")
        menubar.add_cascade(label="文件", menu=file_menu)
        
        # 编辑菜单
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="撤销", command=self.editor.edit_undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="重做", command=self.editor.edit_redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="全选", command=self.select_all, accelerator="Ctrl+A")
        edit_menu.add_command(label="查找", command=self.find_text, accelerator="Ctrl+F")
        menubar.add_cascade(label="编辑", menu=edit_menu)
        
        # 工具菜单
        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="加粗", command=lambda: self.insert_format("**", "**"))
        tools_menu.add_command(label="斜体", command=lambda: self.insert_format("*", "*"))
        
        # 修改：将1~6级标题直接放在菜单里
        tools_menu.add_command(label="标题 1", command=lambda: self.insert_format("# ", ""))
        tools_menu.add_command(label="标题 2", command=lambda: self.insert_format("## ", ""))
        tools_menu.add_command(label="标题 3", command=lambda: self.insert_format("### ", ""))
        tools_menu.add_command(label="标题 4", command=lambda: self.insert_format("#### ", ""))
        tools_menu.add_command(label="标题 5", command=lambda: self.insert_format("##### ", ""))
        tools_menu.add_command(label="标题 6", command=lambda: self.insert_format("###### ", ""))
        
        tools_menu.add_separator()
        tools_menu.add_command(label="链接", command=lambda: self.insert_format("[", "](url)"))
        tools_menu.add_command(label="代码块", command=lambda: self.insert_format("```\n", "\n```"))
        tools_menu.add_command(label="图片", command=lambda: self.insert_format("![", "](image-url)"))
        tools_menu.add_separator()
        tools_menu.add_command(label="无序列表", command=lambda: self.insert_format("- ", ""))
        tools_menu.add_command(label="有序列表", command=lambda: self.insert_format("1. ", ""))
        tools_menu.add_command(label="引用", command=lambda: self.insert_format("> ", ""))
        menubar.add_cascade(label="工具", menu=tools_menu)
        
        # 视图菜单
        view_menu = tk.Menu(menubar, tearoff=0)
        
        # 主题子菜单
        theme_menu = tk.Menu(view_menu, tearoff=0)
        themes = ["litera", "vapor", "darkly", "cyborg", "superhero"]
        for theme in themes:
            theme_menu.add_command(label=theme, command=lambda t=theme: self.change_theme_directly(t))
        view_menu.add_cascade(label="切换主题", menu=theme_menu)
        
        menubar.add_cascade(label="视图", menu=view_menu)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="关于", command=self.show_about)
        menubar.add_cascade(label="帮助", menu=help_menu)
        
        self.root.config(menu=menubar)
    
    def bind_events(self):
        """绑定事件"""
        # 绑定快捷键
        self.root.bind("<Control-n>", lambda e: self.new_file())
        self.root.bind("<Control-o>", lambda e: self.open_file())
        self.root.bind("<Control-s>", lambda e: self.save_file())
        self.root.bind("<Control-Shift-S>", lambda e: self.save_file_as())
        self.root.bind("<Control-q>", lambda e: self.on_closing())
        self.root.bind("<Control-z>", lambda e: self.editor.edit_undo())
        self.root.bind("<Control-y>", lambda e: self.editor.edit_redo())
        self.root.bind("<Control-a>", lambda e: self.select_all())
        self.root.bind("<Control-f>", lambda e: self.find_text())
        
        # 绑定内容变化事件
        self.editor.bind("<KeyRelease>", self.on_content_change)
        self.editor.bind("<ButtonRelease-1>", self.on_content_change)
        
        # 窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def insert_format(self, prefix, suffix):
        """插入格式文本"""
        if self.editor.tag_ranges(tk.SEL):
            sel_start = self.editor.index(tk.SEL_FIRST)
            sel_end = self.editor.index(tk.SEL_LAST)
            
            # 获取选中文本
            selected = self.editor.get(sel_start, sel_end)
            
            # 替换为带格式的文本（使用保存的位置）
            self.editor.delete(sel_start, sel_end)
            self.editor.insert(sel_start, f"{prefix}{selected}{suffix}")
            
            # 重新选中格式化后的文本
            new_end = self.editor.index(f"{sel_start}+{len(prefix) + len(selected) + len(suffix)}c")
            self.editor.tag_add(tk.SEL, sel_start, new_end)
        else:
            # 直接插入格式文本
            self.editor.insert(tk.INSERT, f"{prefix}{suffix}")
            # 移动光标到中间位置
            self.editor.mark_set(tk.INSERT, f"{tk.INSERT} - {len(suffix)}c")
    
    def highlight_syntax(self):
        """实现简单的语法高亮"""
        # 清除所有标签
        for tag in ["header", "bold", "italic", "code_block", "code_inline", "link", "list", "quote"]:
            self.editor.tag_remove(tag, "1.0", tk.END)
        
        # 获取所有文本
        content = self.editor.get("1.0", tk.END)
        
        # 高亮标题
        for match in re.finditer(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE):
            start = f"1.0 + {match.start()} chars"
            end = f"1.0 + {match.end()} chars"
            self.editor.tag_add("header", start, end)
        
        # 高亮加粗
        # 先匹配四个星号的加粗斜体
        for match in re.finditer(r'\*\*\*(.*?)\*\*\*', content):
            start = f"1.0 + {match.start()} chars"
            end = f"1.0 + {match.end()} chars"
            self.editor.tag_add("bold", start, end)
            self.editor.tag_add("italic", start, end)
        
        # 高亮普通加粗（两个星号）
        for match in re.finditer(r'(?<!\*)\*\*(?!\*)(.*?)(?<!\*)\*\*(?!\*)', content):
            start = f"1.0 + {match.start()} chars"
            end = f"1.0 + {match.end()} chars"
            self.editor.tag_add("bold", start, end)
        
        # 高亮斜体（单个星号，确保不是加粗的一部分）
        for match in re.finditer(r'(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)', content):
            start = f"1.0 + {match.start()} chars"
            end = f"1.0 + {match.end()} chars"
            self.editor.tag_add("italic", start, end)
        
        # 高亮下划线样式的加粗和斜体
        for match in re.finditer(r'__(.*?)__', content):
            start = f"1.0 + {match.start()} chars"
            end = f"1.0 + {match.end()} chars"
            self.editor.tag_add("bold", start, end)
        
        for match in re.finditer(r'_(.*?)_', content):
            start = f"1.0 + {match.start()} chars"
            end = f"1.0 + {match.end()} chars"
            self.editor.tag_add("italic", start, end)
        
        # 高亮代码块
        for match in re.finditer(r'```[\s\S]*?```', content):
            start = f"1.0 + {match.start()} chars"
            end = f"1.0 + {match.end()} chars"
            self.editor.tag_add("code_block", start, end)
        
        # 高亮行内代码
        for match in re.finditer(r'`[^`\n]+`', content):
            start = f"1.0 + {match.start()} chars"
            end = f"1.0 + {match.end()} chars"
            self.editor.tag_add("code_inline", start, end)
        
        # 高亮链接
        for match in re.finditer(r'\[.*?\]\([^\)]*\)', content):
            start = f"1.0 + {match.start()} chars"
            end = f"1.0 + {match.end()} chars"
            self.editor.tag_add("link", start, end)
            
        # 高亮列表
        for match in re.finditer(r'^[\t ]*([*+-]|\d+\.)\s+', content, re.MULTILINE):
            start = f"1.0 + {match.start()} chars"
            end = f"1.0 + {match.end()} chars"
            self.editor.tag_add("list", start, end)

        # 高亮引用
        for match in re.finditer(r'^>.*$', content, re.MULTILINE):
            start = f"1.0 + {match.start()} chars"
            end = f"1.0 + {match.end()} chars"
            self.editor.tag_add("quote", start, end)

    
    def apply_syntax_highlighting_colors(self):
        """应用语法高亮颜色（根据主题）"""
        current_theme = self.style.theme.name
        
        if current_theme in ["vapor", "darkly", "cyborg", "superhero"]:
            # 深色主题颜色
            self.editor.tag_config("header", foreground="#66ccff")
            self.editor.tag_config("bold", foreground="#ff6666")
            self.editor.tag_config("italic", foreground="#66ff66")
            self.editor.tag_config("code_block", background="#2a2a2a", foreground="#ffffff")
            self.editor.tag_config("code_inline", background="#3a3a3a", foreground="#ffffff")
            self.editor.tag_config("link", foreground="#ffcc66")
            self.editor.tag_config("list", foreground="#cc99ff")
            self.editor.tag_config("quote", foreground="#99ccff")
        else:
            # 浅色主题颜色
            self.editor.tag_config("header", foreground="#0066cc")
            self.editor.tag_config("bold", foreground="#cc0000")
            self.editor.tag_config("italic", foreground="#00cc00")
            self.editor.tag_config("code_block", background="#f0f0f0", foreground="#000000")
            self.editor.tag_config("code_inline", background="#e8e8e8", foreground="#000000")
            self.editor.tag_config("link", foreground="#cc6600")
            self.editor.tag_config("list", foreground="#9900cc")
            self.editor.tag_config("quote", foreground="#006699")
    
    def select_all(self):
        """全选文本"""
        self.editor.tag_add("sel", "1.0", "end")
        return "break"  # 阻止默认事件
    
    def on_content_change(self, event=None):
        """内容变化时更新预览和状态"""
        if self.auto_preview_enabled:
            # 取消之前的定时器（如果有）
            if self.after_id is not None:
                self.root.after_cancel(self.after_id)
            
            # 设置新的定时器
            self.after_id = self.root.after(300, self.update_preview_and_status)
    
    def update_preview_and_status(self):
        """更新预览和状态栏"""
        content = self.editor.get("1.0", tk.END)
        
        # 移除末尾的换行符（tk.Text 自动添加的）
        if content.endswith('\n'):
            content = content[:-1]
        
        if content != self.last_content:
            # 更新预览
            html_content = self.render_markdown(content)
            self.preview.set_html(html_content)
            
            # 更新状态栏
            char_count = len(content)
            word_count = len(re.findall(r'\b\w+\b', content)) if content else 0
            self.status_label.config(text=f"就绪 | 字符数: {char_count} | 单词数: {word_count}")
            
            # 更新语法高亮
            self.highlight_syntax()
            self.apply_syntax_highlighting_colors()
            
            self.last_content = content
            self.is_modified = True
            self.update_title()
        
        # 清除定时器ID
        self.after_id = None
    
    def render_markdown(self, markdown_text):
        """将markdown渲染为HTML"""
        if not markdown_text:
            return "<h1>Markdown 预览</h1><p>开始编辑以查看预览...</p>"
        
        # 转换为HTML
        html = markdown.markdown(
            markdown_text,
            extensions=[
                'markdown.extensions.extra',
                'markdown.extensions.codehilite',
                'markdown.extensions.tables',
                'markdown.extensions.fenced_code',
                'markdown.extensions.nl2br'
            ]
        )
        return html
    
    def new_file(self):
        """新建文件"""
        if self.is_modified:
            if not self.ask_save_changes():
                return
        
        # 取消待处理的定时器
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        
        self.editor.delete("1.0", tk.END)
        self.preview.set_html("<h1>Markdown 预览</h1><p>开始编辑以查看预览...</p>")
        self.current_file = None
        self.is_modified = False
        self.last_content = ""
        self.update_title()
        self.status_label.config(text="就绪 | 字符数: 0 | 单词数: 0")
        return "break"
    
    def open_file(self):
        """打开文件"""
        if self.is_modified:
            if not self.ask_save_changes():
                return
        
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("Markdown文件", "*.md *.markdown"),
                ("文本文件", "*.txt"),
                ("所有文件", "*.*")
            ],
            title="打开文件"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                # 取消待处理的定时器
                if self.after_id is not None:
                    self.root.after_cancel(self.after_id)
                    self.after_id = None
                
                self.editor.delete("1.0", tk.END)
                self.editor.insert("1.0", content)
                self.current_file = file_path
                self.is_modified = False
                self.last_content = content
                self.update_preview_and_status()  # 立即更新预览
                self.update_title()
                self.status_label.config(text=f"已打开: {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("错误", f"无法打开文件: {str(e)}")
        
        return "break"
    
    def save_file(self):
        """保存文件"""
        if not self.current_file:
            self.save_file_as()
            return
        
        try:
            content = self.editor.get("1.0", tk.END)
            
            # 移除tk.Text自动添加的最后一个换行符
            if content.endswith('\n'):
                content = content[:-1]
                
            with open(self.current_file, 'w', encoding='utf-8') as file:
                file.write(content)
            
            self.is_modified = False
            self.last_content = content
            self.status_label.config(text=f"已保存: {os.path.basename(self.current_file)}")
            self.update_title()
        except Exception as e:
            messagebox.showerror("错误", f"无法保存文件: {str(e)}")
        
        return "break"
    
    def save_file_as(self):
        """另存为"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".md",
            filetypes=[
                ("Markdown文件", "*.md"),
                ("文本文件", "*.txt"),
                ("所有文件", "*.*")
            ],
            title="另存为"
        )
        
        if file_path:
            self.current_file = file_path
            self.save_file()
            self.update_title()
    
    def ask_save_changes(self):
        """询问是否保存更改"""
        if not self.is_modified:
            return True
            
        response = messagebox.askyesnocancel(
            "保存更改",
            "当前文件有未保存的更改，是否保存？"
        )
        
        if response is None:  # 取消
            return False
        elif response:  # 是
            return self.save_file() is not None
        else:  # 否
            return True
    
    def change_theme(self, event=None):
        """切换主题（通过下拉菜单）"""
        theme = self.theme_var.get()
        self.change_theme_directly(theme)
    
    def change_theme_directly(self, theme_name):
        """直接切换主题"""
        # 切换主题
        self.style.theme_use(theme_name)
        self.theme_label.config(text=f"主题: {theme_name}")
        self.theme_var.set(theme_name)
        
        # 更新预览
        content = self.editor.get("1.0", tk.END)
        if content.endswith('\n'):
            content = content[:-1]
        html_content = self.render_markdown(content)
        self.preview.set_html(html_content)
        
        # 根据主题更新编辑器颜色和语法高亮颜色
        if theme_name in ["vapor", "darkly", "cyborg", "superhero"]:
            self.editor.config(bg="#2d2d2d", fg="#ffffff", insertbackground="white")
        else:
            self.editor.config(bg="#ffffff", fg="#000000", insertbackground="black")
        
        # 应用语法高亮颜色
        self.apply_syntax_highlighting_colors()
        
        # 重新应用语法高亮
        self.highlight_syntax()
        
        return "break"
    
    def find_text(self):
        """查找文本"""
        search_window = tk.Toplevel(self.root)
        search_window.title("查找")
        search_window.geometry("350x120")
        search_window.transient(self.root)
        search_window.grab_set()
        
        ttk.Label(search_window, text="查找内容:").pack(pady=(10, 0))
        
        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_window, textvariable=search_var, width=30)
        search_entry.pack(padx=10, pady=5, fill=tk.X)
        search_entry.focus_set()
        
        def do_search():
            search_text = search_var.get()
            if not search_text:
                messagebox.showwarning("查找", "请输入要查找的内容")
                return
            
            # 移除之前的标记
            self.editor.tag_remove('search', '1.0', tk.END)
            
            # 搜索并标记
            start_pos = '1.0'
            found_count = 0
            while True:
                pos = self.editor.search(search_text, start_pos, stopindex=tk.END, nocase=True)
                if not pos:
                    break
                
                end_pos = f"{pos}+{len(search_text)}c"
                self.editor.tag_add('search', pos, end_pos)
                start_pos = end_pos
                found_count += 1
            
            # 配置搜索标记样式
            self.editor.tag_config('search', background='yellow', foreground='black')
            
            if found_count > 0:
                # 滚动到第一个匹配项
                self.editor.see('1.0')
                messagebox.showinfo("查找结果", f"找到 {found_count} 处匹配")
            else:
                messagebox.showinfo("查找结果", "未找到匹配项")
        
        def close_search():
            # 清除搜索标记
            self.editor.tag_remove('search', '1.0', tk.END)
            search_window.destroy()
        
        button_frame = ttk.Frame(search_window)
        button_frame.pack(pady=5)
        
        ttk.Button(button_frame, text="查找", command=do_search).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="关闭", command=close_search).pack(side=tk.LEFT, padx=5)
        
        search_entry.bind("<Return>", lambda e: do_search())
        search_window.protocol("WM_DELETE_WINDOW", close_search)
    
    def update_title(self):
        """更新窗口标题"""
        title = "Malemon"
        if self.current_file:
            title = f"{os.path.basename(self.current_file)} - {title}"
        if self.is_modified:
            title = f"* {title}"
        self.root.title(title)
    
    def on_closing(self):
        """窗口关闭时的处理"""
        # 取消任何待处理的定时器
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
        
        if self.is_modified:
            if self.ask_save_changes():
                self.root.destroy()
        else:
            self.root.destroy()
    
    def show_about(self):
        """显示关于对话框"""
        about_text = """
        Malemon v2.0
        
        一个简洁美观的Markdown编辑器，支持实时预览和语法高亮。
        
        使用技术：
        • ttkbootstrap - 现代化UI
        • tkhtmlview - HTML渲染
        • markdown - Markdown解析
        
        功能特点：
        • 实时预览
        • 语法高亮
        • 主题切换
        • 快捷键支持
        • 格式工具菜单
        
        © 2025 Malemon
        """
        
        messagebox.showinfo("关于", about_text.strip())

if __name__ == "__main__":
    root = tk.Tk()
    app = MarkdownEditor(root)
    root.mainloop()

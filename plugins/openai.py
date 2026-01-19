import tkinter as tk
from tkinter import ttk
from typing import Iterator, List, Optional

from pystart import get_workbench
from pystart.assistance import Assistant, ChatContext, ChatMessage, ChatResponseChunk
from pystart.languages import tr
from pystart.ui_utils import create_url_label, show_dialog, ems_to_pixels
from pystart.workdlg import WorkDialog
from pystart.config_ui import ConfigurationPage

# Secret keys
API_KEY_SECRET_KEY = "openai_api_key"

# Option keys
OPTION_BASE_URL = "openai.base_url"
OPTION_MODEL = "openai.model"
OPTION_SYSTEM_PROMPT = "openai.system_prompt"

# Default values
DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_MODEL = "qwen-plus"
DEFAULT_SYSTEM_PROMPT = "你是一位资深的python编程教练，讲中文。用户接受到的内容只能显示在textarea这种纯文本框，因此回复的时请考虑用恰当的格式。新手用户，解释需要简单直白，比如将抽象的 `SyntaxError` 转为具体建议，如：“第3行少了个冒号 `:`” 。发现代码错误后温柔耐心地简洁地解释，免得用户费解；需要举例说明的时候，可以举简单的例子，不需要解释太多，免得给用户带来阅读和理解的负担。"


class OpenAIConfigDialog(WorkDialog):
    """Configuration dialog for OpenAI compatible API settings"""
    
    def __init__(self, master):
        self.api_key: Optional[str] = None
        self._saved = False
        super().__init__(master)

    def get_title(self):
        return tr("AI API配置")

    def init_main_frame(self):
        super().init_main_frame()
        self.main_frame.columnconfigure(1, weight=1)
        
        pad = ems_to_pixels(0.5)
        row = 0
        
        # API Key section
        row += 1
        ttk.Label(self.main_frame, text=tr("API Key:")).grid(
            row=row, column=0, sticky="w", padx=pad, pady=pad
        )
        
        key_frame = ttk.Frame(self.main_frame)
        key_frame.grid(row=row, column=1, sticky="ew", padx=pad, pady=pad)
        key_frame.columnconfigure(0, weight=1)
        
        self.key_entry = ttk.Entry(key_frame, width=50, show="*")
        self.key_entry.grid(row=0, column=0, sticky="ew")
        
        # Load saved API key
        saved_key = get_workbench().get_secret(API_KEY_SECRET_KEY, "")
        if saved_key:
            self.key_entry.insert(0, saved_key)
        
        paste_button = ttk.Button(key_frame, text=tr("Paste"), command=self._paste_api_key)
        paste_button.grid(row=0, column=1, padx=(pad, 0))
        
        show_button = ttk.Button(key_frame, text=tr("Show"), command=self._toggle_show_key)
        show_button.grid(row=0, column=2, padx=(pad, 0))
        self._show_button = show_button
        self._key_visible = False
        
        # Base URL section
        row += 1
        ttk.Label(self.main_frame, text=tr("API Base URL:")).grid(
            row=row, column=0, sticky="w", padx=pad, pady=pad
        )
        
        self.base_url_entry = ttk.Entry(self.main_frame, width=50)
        self.base_url_entry.grid(row=row, column=1, sticky="ew", padx=pad, pady=pad)
        self.base_url_entry.insert(0, get_workbench().get_option(OPTION_BASE_URL))
        
        # Model section
        row += 1
        ttk.Label(self.main_frame, text=tr("Model:")).grid(
            row=row, column=0, sticky="w", padx=pad, pady=pad
        )
        
        self.model_entry = ttk.Entry(self.main_frame, width=50)
        self.model_entry.grid(row=row, column=1, sticky="ew", padx=pad, pady=pad)
        self.model_entry.insert(0, get_workbench().get_option(OPTION_MODEL))
        
        # Common models hint
        row += 1
        hint_text = tr("常见大模型如: qwen-plus, qwen-turbo, gpt-4o, deepseek-chat")
        hint_label = ttk.Label(self.main_frame, text=hint_text, foreground="gray")
        hint_label.grid(row=row, column=1, sticky="w", padx=pad)
        
        # System Prompt section
        row += 1
        ttk.Label(self.main_frame, text=tr("System Prompt:")).grid(
            row=row, column=0, sticky="nw", padx=pad, pady=pad
        )
        
        self.system_prompt_text = tk.Text(self.main_frame, width=50, height=4, wrap="word")
        self.system_prompt_text.grid(row=row, column=1, sticky="ew", padx=pad, pady=pad)
        self.system_prompt_text.insert("1.0", get_workbench().get_option(OPTION_SYSTEM_PROMPT))
        
        # URL hint
        row += 1
        url_label = create_url_label(
            self.main_frame, 
            url="https://www.pystart.org/docs/ai_settings#get_api",
            text=tr("获取API密钥")
        )
        url_label.grid(row=row, column=1, sticky="w", padx=pad, pady=pad)

    def _paste_api_key(self):
        try:
            self.key_entry.delete(0, "end")
            self.key_entry.insert(0, get_workbench().clipboard_get())
        except tk.TclError:
            pass  # Clipboard is empty

    def _toggle_show_key(self):
        if self._key_visible:
            self.key_entry.config(show="*")
            self._show_button.config(text=tr("Show"))
        else:
            self.key_entry.config(show="")
            self._show_button.config(text=tr("Hide"))
        self._key_visible = not self._key_visible

    def get_instructions(self) -> Optional[str]:
        return tr("配置AI API设置")

    def is_ready_for_work(self):
        return True

    def on_click_ok_button(self):
        # Save API key
        api_key = self.key_entry.get().strip()
        if api_key:
            get_workbench().set_secret(API_KEY_SECRET_KEY, api_key)
        
        # Save base URL
        base_url = self.base_url_entry.get().strip() or DEFAULT_BASE_URL
        get_workbench().set_option(OPTION_BASE_URL, base_url)
        
        # Save model
        model = self.model_entry.get().strip() or DEFAULT_MODEL
        get_workbench().set_option(OPTION_MODEL, model)
        
        # Save system prompt
        system_prompt = self.system_prompt_text.get("1.0", "end-1c").strip() or DEFAULT_SYSTEM_PROMPT
        get_workbench().set_option(OPTION_SYSTEM_PROMPT, system_prompt)
        
        self._saved = True
        self.close()


class OpenAIAssistant(Assistant):
    """OpenAI compatible API assistant with configurable settings"""

    def _get_saved_api_key(self) -> Optional[str]:
        return get_workbench().get_secret(API_KEY_SECRET_KEY, None)

    def _get_base_url(self) -> str:
        return get_workbench().get_option(OPTION_BASE_URL)

    def _get_model(self) -> str:
        return get_workbench().get_option(OPTION_MODEL)

    def _get_system_prompt(self) -> str:
        return get_workbench().get_option(OPTION_SYSTEM_PROMPT)

    def _open_config_dialog(self):
        dlg = OpenAIConfigDialog(get_workbench())
        show_dialog(dlg, get_workbench())
        return dlg._saved

    def get_ready(self) -> bool:
        if self._get_saved_api_key() is None:
            self._open_config_dialog()
        return self._get_saved_api_key() is not None

    def complete_chat(self, context: ChatContext) -> Iterator[ChatResponseChunk]:
        from openai import OpenAI

        # Create client with configurable base_url
        base_url = self._get_base_url()
        client = OpenAI(
            api_key=self._get_saved_api_key(),
            base_url=base_url if base_url else None
        )

        # Build messages with configurable system prompt
        system_prompt = self._get_system_prompt()
        out_msgs = [
            {"role": "system", "content": system_prompt},
        ] + [{"role": msg.role, "content": self.format_message(msg)} for msg in context.messages]

        # Use configurable model
        model = self._get_model()
        response = client.chat.completions.create(
            model=model,
            messages=out_msgs,
            stream=True,
        )

        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                chunk_message = chunk.choices[0].delta.content
                yield ChatResponseChunk(chunk_message, is_final=False)

        yield ChatResponseChunk("", is_final=True)

    def cancel_completion(self) -> None:
        pass


def open_openai_config():
    """Open the OpenAI configuration dialog from menu"""
    dlg = OpenAIConfigDialog(get_workbench())
    show_dialog(dlg, get_workbench())


def load_plugin():
    # Register default options
    get_workbench().set_default(OPTION_BASE_URL, DEFAULT_BASE_URL)
    get_workbench().set_default(OPTION_MODEL, DEFAULT_MODEL)
    get_workbench().set_default(OPTION_SYSTEM_PROMPT, DEFAULT_SYSTEM_PROMPT)
    
    # Register assistant
    get_workbench().add_assistant("OpenAI", OpenAIAssistant())
    
    # Add menu command for configuration
    get_workbench().add_command(
        "openai_config",
        "tools",
        tr("配置AI API..."),
        open_openai_config,
        group=85,
    )

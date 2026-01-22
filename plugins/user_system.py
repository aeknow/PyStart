# -*- coding: utf-8 -*-
"""
PyStart 去中心化用户系统
========================

基于 aeknow 库的 BIP39 助记词实现去中心化用户身份。

功能：
- 随机生成助记词创建用户
- 用户数据加密存储
- 工具栏右侧用户 UI
"""

import os
import json
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from logging import getLogger

from pystart import get_workbench, get_pystart_user_dir
from pystart.languages import tr
from pystart.ui_utils import CustomToolbutton, ems_to_pixels, create_tooltip

logger = getLogger(__name__)

# 用户数据目录
USER_DATA_DIR_NAME = "user_data"

# 默认密码（首次自动创建时使用）
DEFAULT_PASSWORD = "pystart"


class UserManager:
    """用户管理器 - 处理用户创建、加载、保存"""
    
    def __init__(self):
        self._wallet = None
        self._user_dir = None
        self._metadata = {}
        self._is_default_password = False  # 是否使用默认密码
    
    @property
    def user_dir(self) -> str:
        """获取用户数据目录"""
        if self._user_dir is None:
            self._user_dir = os.path.join(get_pystart_user_dir(), USER_DATA_DIR_NAME)
            if not os.path.exists(self._user_dir):
                os.makedirs(self._user_dir)
        return self._user_dir
    
    @property
    def keystore_path(self) -> str:
        """Keystore 文件路径"""
        return os.path.join(self.user_dir, "user.keystore")
    
    @property
    def metadata_path(self) -> str:
        """元数据文件路径"""
        return os.path.join(self.user_dir, "user.json")
    
    @property
    def is_logged_in(self) -> bool:
        """是否已登录"""
        return self._wallet is not None
    
    @property
    def is_using_default_password(self) -> bool:
        """是否使用默认密码"""
        return self._is_default_password
    
    @property
    def address(self) -> str:
        """获取用户地址"""
        if self._wallet:
            return self._wallet.address
        return ""
    
    @property
    def short_address(self) -> str:
        """获取缩短的地址显示"""
        addr = self.address
        if len(addr) > 16:
            return f"{addr[:8]}...{addr[-6:]}"
        return addr
    
    @property
    def mnemonic(self) -> str:
        """获取助记词"""
        if self._wallet:
            return self._wallet.mnemonic
        return ""
    
    def has_saved_user(self) -> bool:
        """检查是否有已保存的用户"""
        return os.path.exists(self.keystore_path)
    
    def auto_create_user(self) -> bool:
        """
        自动创建用户（静默，使用默认密码）
        
        :return: 是否成功
        """
        try:
            from aeknow.wallet import MnemonicWallet
            
            # 生成新钱包
            self._wallet = MnemonicWallet.generate()
            
            # 使用默认密码保存
            self._wallet.save_keystore(self.keystore_path, DEFAULT_PASSWORD)
            self._is_default_password = True
            
            # 保存元数据
            self._metadata = {
                "address": self._wallet.address,
                "created_at": self._get_timestamp(),
                "default_password": True,  # 标记使用默认密码
            }
            self._save_metadata()
            
            logger.info(f"Auto created user: {self.short_address}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to auto create user: {e}")
            self._wallet = None
            return False
    
    def auto_login(self) -> bool:
        """
        自动登录（尝试默认密码）
        
        :return: 是否成功
        """
        if not self.has_saved_user():
            return False
        
        # 加载元数据
        self._load_metadata()
        
        # 尝试用默认密码登录
        if self._metadata.get("default_password", False):
            if self.login(DEFAULT_PASSWORD):
                self._is_default_password = True
                return True
        
        return False
    
    def login(self, password: str) -> bool:
        """
        登录（加载已保存的用户）
        
        :param password: 解密密码
        :return: 是否成功
        """
        try:
            if not self.has_saved_user():
                logger.warning("No saved user found")
                return False
            
            # 加载元数据
            self._load_metadata()
            
            # 检查是否是旧版格式
            is_legacy = self._metadata.get("legacy_format", False)
            
            if is_legacy:
                # 旧版 SDK 格式
                from aeknow.signing import Account
                account = Account.from_keystore(self.keystore_path, password)
                
                class LegacyWallet:
                    def __init__(self, acc):
                        self.account = acc
                        self._mnemonic = None
                    @property
                    def address(self):
                        return self.account.get_address()
                    @property
                    def mnemonic(self):
                        return None
                    def save_keystore(self, path, pwd):
                        self.account.save_to_keystore_file(path, pwd)
                
                self._wallet = LegacyWallet(account)
            else:
                # 新版 HD 钱包格式
                from aeknow.wallet import MnemonicWallet
                self._wallet = MnemonicWallet.from_keystore(self.keystore_path, password)
            
            # 检查是否是默认密码
            self._is_default_password = (password == DEFAULT_PASSWORD and 
                                         self._metadata.get("default_password", False))
            
            logger.info(f"User logged in: {self.short_address}")
            return True
            
        except ValueError as e:
            logger.warning(f"Login failed (wrong password?): {e}")
            return False
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False
    
    def change_password(self, new_password: str) -> bool:
        """
        修改密码
        
        :param new_password: 新密码
        :return: 是否成功
        """
        if not self._wallet:
            return False
        
        try:
            # 重新保存 keystore
            self._wallet.save_keystore(self.keystore_path, new_password)
            
            # 更新元数据
            self._metadata["default_password"] = False
            self._save_metadata()
            
            self._is_default_password = False
            logger.info("Password changed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to change password: {e}")
            return False
    
    def logout(self):
        """退出登录"""
        self._wallet = None
        self._metadata = {}
        self._is_default_password = False
        logger.info("User logged out")
    
    def import_from_mnemonic(self, mnemonic: str, password: str) -> bool:
        """
        从助记词导入用户
        
        :param mnemonic: 助记词
        :param password: 加密密码
        :return: 是否成功
        """
        try:
            from aeknow.wallet import MnemonicWallet
            
            # 导入钱包
            self._wallet = MnemonicWallet.from_mnemonic(mnemonic)
            
            # 保存 keystore
            self._wallet.save_keystore(self.keystore_path, password)
            
            # 保存元数据
            self._metadata = {
                "address": self._wallet.address,
                "imported_at": self._get_timestamp(),
                "default_password": False,
            }
            self._save_metadata()
            
            self._is_default_password = False
            logger.info(f"Imported user: {self.short_address}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to import user: {e}")
            self._wallet = None
            return False
    
    def _save_metadata(self):
        """保存元数据"""
        try:
            with open(self.metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self._metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
    
    def _load_metadata(self):
        """加载元数据"""
        try:
            if os.path.exists(self.metadata_path):
                with open(self.metadata_path, 'r', encoding='utf-8') as f:
                    self._metadata = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load metadata: {e}")
            self._metadata = {}
    
    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()


class UserSystemUI:
    """用户系统 UI 组件"""
    
    def __init__(self):
        self.user_manager = UserManager()
        self._button = None
        self._menu = None
    
    def setup_toolbar_button(self):
        """在工具栏右侧设置用户按钮"""
        wb = get_workbench()
        
        # 使用 main_frame 作为父容器，使用 place 定位到右上角
        main_frame = wb._main_frame
        
        # 加载用户图标
        self._user_image = wb.get_image("account.png")
        
        # 创建用户按钮
        self._button = CustomToolbutton(
            main_frame,
            image=self._user_image,
            command=self._show_menu,
        )
        # 使用 place 布局，固定在右上角
        self._button.place(relx=1.0, y=ems_to_pixels(0.5), anchor="ne", x=-ems_to_pixels(0.5))
        
        create_tooltip(self._button, tr("用户系统"))
        
        # 创建菜单
        self._menu = tk.Menu(self._button, tearoff=False)
        
        # 静默初始化用户
        self._silent_init()
    
    def _silent_init(self):
        """静默初始化：自动创建或登录用户"""
        if self.user_manager.has_saved_user():
            # 已有用户，尝试自动登录
            self.user_manager.auto_login()
        else:
            # 无用户，自动创建
            self.user_manager.auto_create_user()
        
        self._update_button_tooltip()
    
    def _update_button_tooltip(self):
        """更新按钮提示"""
        if self.user_manager.is_logged_in:
            create_tooltip(self._button, f"{self.user_manager.short_address}")
        elif self.user_manager.has_saved_user():
            create_tooltip(self._button, tr("点击解锁"))
        else:
            create_tooltip(self._button, tr("用户系统"))
    
    def _show_menu(self):
        """显示用户菜单"""
        self._menu.delete(0, tk.END)
        
        if self.user_manager.is_logged_in:
            self._build_logged_in_menu()
        elif self.user_manager.has_saved_user():
            self._build_locked_menu()
        else:
            self._build_no_user_menu()
        
        # 显示菜单
        x = self._button.winfo_rootx()
        y = self._button.winfo_rooty() + self._button.winfo_height()
        self._menu.tk_popup(x, y)
    
    def _build_logged_in_menu(self):
        """构建已登录菜单"""
        # 显示地址
        self._menu.add_command(
            label=f"📍 {self.user_manager.short_address}",
            state="disabled"
        )
        self._menu.add_separator()
        
        # 复制地址
        self._menu.add_command(
            label="📋 复制地址",
            command=self._copy_address
        )
        
        # 账户信息
        self._menu.add_command(
            label="📊 账户信息",
            command=self._show_account_info
        )
        
        # 查看/备份助记词
        self._menu.add_command(
            label="🔑 备份助记词",
            command=self._backup_mnemonic
        )
        
        # 导出账户
        self._menu.add_command(
            label="📤 导出账户",
            command=self._export_account
        )
        
        self._menu.add_separator()
        
        # 消息签名
        self._menu.add_command(
            label="✍️ 消息签名",
            command=self._show_message_sign
        )
        
        # 签名当前代码
        self._menu.add_command(
            label="📝 签名当前代码",
            command=self._sign_current_code
        )
        
        # 验证代码签名
        self._menu.add_command(
            label="✅ 验证代码签名",
            command=self._verify_code_signature
        )
        
        # 消息加密
        self._menu.add_command(
            label="🔐 消息加密",
            command=self._show_message_crypto
        )
        
        self._menu.add_separator()
        
        # 高级选项
        self._menu.add_command(
            label="📥 导入其他身份",
            command=self._import_identity
        )
        
        self._menu.add_separator()
        
        # 锁定（仅非默认密码时显示）
        if not self.user_manager.is_using_default_password:
            self._menu.add_command(
                label="🔒 锁定",
                command=self._logout
            )
        
        # 删除账号
        self._menu.add_command(
            label="🗑️ 删除账号",
            command=self._delete_user
        )
        
        self._menu.add_separator()
        
        # 用户系统介绍
        self._menu.add_command(
            label="ℹ️ 用户系统介绍",
            command=self._show_about
        )
    
    def _build_locked_menu(self):
        """构建锁定状态菜单"""
        self._menu.add_command(
            label="🔓 解锁登录",
            command=self._login
        )
        self._menu.add_separator()
        self._menu.add_command(
            label="🗑️ 删除用户",
            command=self._delete_user
        )
        self._menu.add_separator()
        self._menu.add_command(
            label="ℹ️ 用户系统介绍",
            command=self._show_about
        )
    
    def _build_no_user_menu(self):
        """构建无用户菜单"""
        self._menu.add_command(
            label="✨ 创建新身份",
            command=self._create_new_identity
        )
        self._menu.add_command(
            label="📥 导入已有身份",
            command=self._import_identity
        )
        self._menu.add_separator()
        self._menu.add_command(
            label="ℹ️ 用户系统介绍",
            command=self._show_about
        )
    
    def _create_new_identity(self):
        """创建新身份"""
        if self.user_manager.auto_create_user():
            self._update_button_tooltip()
            messagebox.showinfo(
                "创建成功",
                f"已创建新身份\n\n地址: {self.user_manager.short_address}",
                parent=get_workbench()
            )
        else:
            messagebox.showerror("错误", "创建失败", parent=get_workbench())
    
    def _import_identity(self):
        """导入已有身份"""
        dialog = ImportIdentityDialog(get_workbench(), self.user_manager)
        if dialog.result:
            self._update_button_tooltip()
    
    def _login(self):
        """登录"""
        password = simpledialog.askstring(
            "解锁",
            "请输入密码:",
            show="*",
            parent=get_workbench()
        )
        if password:
            if self.user_manager.login(password):
                self._update_button_tooltip()
                messagebox.showinfo(
                    "登录成功",
                    f"欢迎回来！\n{self.user_manager.short_address}",
                    parent=get_workbench()
                )
            else:
                messagebox.showerror(
                    "登录失败",
                    "密码错误",
                    parent=get_workbench()
                )
    
    def _logout(self):
        """退出登录"""
        self.user_manager.logout()
        self._update_button_tooltip()
    
    def _copy_address(self):
        """复制地址"""
        try:
            wb = get_workbench()
            wb.clipboard_clear()
            wb.clipboard_append(self.user_manager.address)
            wb.update()
            messagebox.showinfo("复制成功", "地址已复制到剪贴板", parent=wb)
        except Exception as e:
            logger.error(f"Failed to copy address: {e}")
            messagebox.showerror("复制失败", str(e), parent=get_workbench())
    
    def _backup_mnemonic(self):
        """备份助记词（如果是默认密码，先设置新密码）"""
        if self.user_manager.is_using_default_password:
            # 显示助记词并要求设置密码
            dialog = BackupMnemonicDialog(get_workbench(), self.user_manager)
            if dialog.result:
                self._update_button_tooltip()
        else:
            # 已设置密码，需验证后查看
            password = simpledialog.askstring(
                "安全验证",
                "请输入密码以查看助记词:",
                show="*",
                parent=get_workbench()
            )
            if not password:
                return
            
            # 验证密码
            try:
                from aeknow.wallet import MnemonicWallet
                MnemonicWallet.from_keystore(self.user_manager.keystore_path, password)
            except:
                messagebox.showerror("错误", "密码错误", parent=get_workbench())
                return
            
            # 显示助记词
            MnemonicDisplayDialog(get_workbench(), self.user_manager.mnemonic)
    
    def _export_account(self):
        """导出账户"""
        from tkinter import filedialog
        
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON 文件", "*.json"), ("所有文件", "*.*")],
            initialfile=f"{self.user_manager.short_address}.json",
            parent=get_workbench()
        )
        if path:
            try:
                import shutil
                shutil.copy(self.user_manager.keystore_path, path)
                messagebox.showinfo(
                    "导出成功",
                    f"已导出到:\n{path}",
                    parent=get_workbench()
                )
            except Exception as e:
                messagebox.showerror("导出失败", str(e), parent=get_workbench())
    
    def _delete_user(self):
        """删除用户"""
        if messagebox.askyesno(
            "确认删除",
            "确定要删除用户吗？\n\n⚠️ 如果您没有备份助记词，将无法恢复！",
            parent=get_workbench()
        ):
            try:
                if os.path.exists(self.user_manager.keystore_path):
                    os.remove(self.user_manager.keystore_path)
                if os.path.exists(self.user_manager.metadata_path):
                    os.remove(self.user_manager.metadata_path)
                self.user_manager.logout()
                self._update_button_tooltip()
                messagebox.showinfo("已删除", "用户已删除", parent=get_workbench())
            except Exception as e:
                messagebox.showerror("删除失败", str(e), parent=get_workbench())
    
    def _show_message_sign(self):
        """显示消息签名窗口"""
        MessageSignDialog(get_workbench(), self.user_manager)
    
    def _show_message_crypto(self):
        """显示消息加密窗口"""
        MessageCryptoDialog(get_workbench(), self.user_manager)
    
    def _show_account_info(self):
        """显示账户信息窗口"""
        AccountInfoDialog(get_workbench(), self.user_manager)
    
    def _show_about(self):
        """显示用户系统介绍窗口"""
        UserSystemAboutDialog(get_workbench())
    
    def _sign_current_code(self):
        """签名当前编辑器中的代码"""
        from hashlib import blake2b
        import base58
        
        wb = get_workbench()
        editor = wb.get_editor_notebook().get_current_editor()
        
        if not editor:
            messagebox.showwarning("无代码", "请先打开一个代码文件", parent=wb)
            return
        
        # 获取代码内容
        code_view = editor.get_text_widget()
        code = code_view.get("1.0", "end-1c")
        
        if not code.strip():
            messagebox.showwarning("无代码", "当前文件没有代码内容", parent=wb)
            return
        
        # 检查是否已经签名
        has_signature = "# ========== PYSTART CODE SIGNATURE ==========" in code or "# ========== CODE SIGNATURE ==========" in code
        if has_signature:
            if not messagebox.askyesno(
                "已有签名",
                "代码已包含签名信息\n\n是否移除旧签名并重新签名？",
                parent=wb
            ):
                return
            # 移除旧签名
            sig_start = code.find("\n# ========== PYSTART CODE SIGNATURE ==========")
            if sig_start == -1:
                sig_start = code.find("# ========== PYSTART CODE SIGNATURE ==========")
            if sig_start == -1:
                sig_start = code.find("\n# ========== CODE SIGNATURE ==========")
            if sig_start == -1:
                sig_start = code.find("# ========== CODE SIGNATURE ==========")
            if sig_start != -1:
                code = code[:sig_start].rstrip()
        
        # 计算代码哈希
        code_bytes = code.encode('utf-8')
        code_hash = blake2b(code_bytes, digest_size=32).digest()
        code_hash_hex = code_hash.hex()
        
        # 签名
        try:
            account = self.user_manager._wallet.account
            signature = account.sign(code_hash)
            signature_b58 = base58.b58encode(signature).decode('utf-8')
        except Exception as e:
            messagebox.showerror("签名失败", str(e), parent=wb)
            return
        
        # 生成签名注释块
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        signature_block = f'''

# ========== PYSTART CODE SIGNATURE ==========
# Signer: {self.user_manager.address}
# Time: {timestamp}
# Hash: {code_hash_hex}
# Signature: sg_{signature_b58}
# Method: blake2b-ed25519
# Signed with PyStart IDE (https://github.com/aeknow/PyStart)
# ============================================='''
        
        # 在代码末尾添加签名
        new_code = code + signature_block
        
        # 更新编辑器内容
        code_view.delete("1.0", "end")
        code_view.insert("1.0", new_code)
        
        # 标记文件已修改
        editor.get_text_widget().edit_modified(True)
        
        messagebox.showinfo(
            "PyStart 签名成功",
            f"代码已签名！\n\n签名者: {self.user_manager.short_address}\n哈希: {code_hash_hex[:16]}...\n\n签名信息已添加到代码末尾\n分享给他人即可验证代码来源",
            parent=wb
        )
    
    def _verify_code_signature(self):
        """验证当前代码的签名"""
        from hashlib import blake2b
        import base58
        import re
        
        wb = get_workbench()
        editor = wb.get_editor_notebook().get_current_editor()
        
        if not editor:
            messagebox.showwarning("无代码", "请先打开一个代码文件", parent=wb)
            return
        
        # 获取代码内容
        code_view = editor.get_text_widget()
        code = code_view.get("1.0", "end-1c")
        
        if not code.strip():
            messagebox.showwarning("无代码", "当前文件没有代码内容", parent=wb)
            return
        
        # 检查是否有签名块
        if "# ========== PYSTART CODE SIGNATURE ==========" not in code and "# ========== CODE SIGNATURE ==========" not in code:
            messagebox.showinfo("无签名", "当前代码没有 PyStart 签名信息", parent=wb)
            return
        
        try:
            # 提取签名信息
            signer_match = re.search(r'# Signer: (ak_[a-zA-Z0-9]+)', code)
            hash_match = re.search(r'# Hash: ([a-fA-F0-9]+)', code)
            time_match = re.search(r'# Time: ([^\n]+)', code)
            method_match = re.search(r'# Method: ([^\n]+)', code)
            sig_match = re.search(r'# Signature: sg_([a-zA-Z0-9]+)', code)
            if not sig_match:
                # 兼容旧格式（无 sg_ 前缀）
                sig_match = re.search(r'# Signature: ([a-zA-Z0-9]+)', code)
            
            if not all([signer_match, hash_match, sig_match]):
                messagebox.showerror("格式错误", "签名块格式不完整", parent=wb)
                return
            
            signer_address = signer_match.group(1)
            claimed_hash = hash_match.group(1)
            signature_b58 = sig_match.group(1)
            sign_time = time_match.group(1) if time_match else "未知"
            sign_method = method_match.group(1) if method_match else "blake2b-ed25519"
            
            # 移除签名块，获取原始代码
            sig_start = code.find("\n# ========== PYSTART CODE SIGNATURE ==========")
            if sig_start == -1:
                sig_start = code.find("# ========== PYSTART CODE SIGNATURE ==========")
            if sig_start == -1:
                sig_start = code.find("\n# ========== CODE SIGNATURE ==========")
            if sig_start == -1:
                sig_start = code.find("# ========== CODE SIGNATURE ==========")
            
            original_code = code[:sig_start].rstrip()
            
            # 重新计算哈希
            code_bytes = original_code.encode('utf-8')
            actual_hash = blake2b(code_bytes, digest_size=32).hexdigest()
            
            # 验证哈希是否一致
            hash_valid = (actual_hash == claimed_hash)
            
            if not hash_valid:
                # 哈希不匹配，代码已被篡改
                SignatureVerifyResultDialog(
                    wb,
                    success=False,
                    error_type="hash_mismatch",
                    signer=signer_address,
                    sign_time=sign_time,
                    sign_method=sign_method,
                    claimed_hash=claimed_hash,
                    actual_hash=actual_hash,
                    signature=signature_b58
                )
                return
            
            # 验证签名
            import nacl.exceptions
            
            # 解码签名
            signature = base58.b58decode(signature_b58)
            hash_bytes = bytes.fromhex(claimed_hash)
            
            # 从地址提取公钥并验证
            try:
                from nacl.signing import VerifyKey
                from nacl.encoding import RawEncoder
                
                pubkey_bytes = base58.b58decode_check(signer_address[3:])
                verify_key = VerifyKey(pubkey_bytes, encoder=RawEncoder)
                verify_key.verify(hash_bytes, signature)
                
                # 验证成功
                SignatureVerifyResultDialog(
                    wb,
                    success=True,
                    signer=signer_address,
                    sign_time=sign_time,
                    sign_method=sign_method,
                    claimed_hash=claimed_hash,
                    actual_hash=actual_hash,
                    signature=signature_b58
                )
                
            except nacl.exceptions.BadSignatureError:
                # 签名无效
                SignatureVerifyResultDialog(
                    wb,
                    success=False,
                    error_type="bad_signature",
                    signer=signer_address,
                    sign_time=sign_time,
                    sign_method=sign_method,
                    claimed_hash=claimed_hash,
                    actual_hash=actual_hash,
                    signature=signature_b58
                )
                
        except Exception as e:
            messagebox.showerror("验证失败", f"验证过程出错: {e}", parent=wb)


class SignatureVerifyResultDialog(tk.Toplevel):
    """签名验证结果对话框"""
    
    def __init__(self, parent, success: bool, signer: str, sign_time: str, 
                 sign_method: str, claimed_hash: str, actual_hash: str, 
                 signature: str, error_type: str = None):
        super().__init__(parent)
        self.success = success
        self.signer = signer
        self.sign_time = sign_time
        self.sign_method = sign_method
        self.claimed_hash = claimed_hash
        self.actual_hash = actual_hash
        self.signature = signature
        self.error_type = error_type
        
        if success:
            self.title("✓ PyStart 验证成功")
        else:
            self.title("✗ PyStart 验证失败")
        
        self.geometry("700x580")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        self._create_widgets()
        
        # 居中显示
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
    
    def _create_widgets(self):
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 结果标题
        if self.success:
            ttk.Label(
                frame,
                text="✅ 代码签名验证通过",
                font=("TkDefaultFont", 14, "bold"),
                foreground="green"
            ).pack(pady=(0, 5))
            ttk.Label(
                frame,
                text="代码未被篡改，签名真实有效",
                foreground="green"
            ).pack(pady=(0, 15))
        else:
            ttk.Label(
                frame,
                text="❌ 代码签名验证失败",
                font=("TkDefaultFont", 14, "bold"),
                foreground="red"
            ).pack(pady=(0, 5))
            if self.error_type == "hash_mismatch":
                ttk.Label(
                    frame,
                    text="代码已被篡改！哈希值不匹配",
                    foreground="red"
                ).pack(pady=(0, 15))
            else:
                ttk.Label(
                    frame,
                    text="签名无效！与声称的签名者不匹配",
                    foreground="red"
                ).pack(pady=(0, 15))
        
        # 签名者信息
        signer_frame = ttk.LabelFrame(frame, text="👤 签名者信息", padding=10)
        signer_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(signer_frame, text="地址:", font=("TkDefaultFont", 9, "bold")).grid(row=0, column=0, sticky=tk.W, pady=2)
        signer_entry = ttk.Entry(signer_frame, width=62)
        signer_entry.insert(0, self.signer)
        signer_entry.config(state="readonly")
        signer_entry.grid(row=0, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
        ttk.Label(signer_frame, text="签名时间:", font=("TkDefaultFont", 9, "bold")).grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Label(signer_frame, text=self.sign_time).grid(row=1, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
        ttk.Label(signer_frame, text="签名算法:", font=("TkDefaultFont", 9, "bold")).grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Label(signer_frame, text=self.sign_method).grid(row=2, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
        # 签名详情
        sig_frame = ttk.LabelFrame(frame, text="🔐 签名详情", padding=10)
        sig_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 哈希值
        ttk.Label(sig_frame, text="代码哈希:", font=("TkDefaultFont", 9, "bold")).pack(anchor=tk.W)
        hash_text = tk.Text(sig_frame, height=2, width=72, wrap=tk.CHAR)
        hash_text.insert("1.0", self.claimed_hash)
        hash_text.config(state="disabled")
        hash_text.pack(fill=tk.X, pady=(2, 8))
        
        # 如果哈希不匹配，显示实际哈希
        if self.error_type == "hash_mismatch":
            ttk.Label(sig_frame, text="实际哈希:", font=("TkDefaultFont", 9, "bold"), foreground="red").pack(anchor=tk.W)
            actual_hash_text = tk.Text(sig_frame, height=2, width=72, wrap=tk.CHAR)
            actual_hash_text.insert("1.0", self.actual_hash)
            actual_hash_text.config(state="disabled")
            actual_hash_text.pack(fill=tk.X, pady=(2, 8))
        
        # 签名值
        ttk.Label(sig_frame, text="签名值:", font=("TkDefaultFont", 9, "bold")).pack(anchor=tk.W)
        sig_text = tk.Text(sig_frame, height=3, width=72, wrap=tk.CHAR)
        sig_text.insert("1.0", f"sg_{self.signature}")
        sig_text.config(state="disabled")
        sig_text.pack(fill=tk.X, pady=(2, 0))
        
        # 底部区域
        bottom_frame = ttk.Frame(frame)
        bottom_frame.pack(fill=tk.X, pady=(15, 0))
        
        # 品牌标语
        ttk.Label(
            bottom_frame,
            text="“信任来自密码学，而非平台” - PyStart",
            foreground="gray",
            font=("TkDefaultFont", 9)
        ).pack(side=tk.LEFT)
        
        ttk.Button(
            bottom_frame,
            text="确定",
            command=self.destroy,
            width=10
        ).pack(side=tk.RIGHT)


class BackupMnemonicDialog(tk.Toplevel):
    """备份助记词对话框（首次备份时设置密码）"""
    
    def __init__(self, parent, user_manager: UserManager):
        super().__init__(parent)
        self.user_manager = user_manager
        self.result = False
        
        self.title("备份助记词")
        self.geometry("860x660")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        self._create_widgets()
        
        # 居中显示
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
        
        self.wait_window(self)
    
    def _create_widgets(self):
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 警告
        ttk.Label(
            frame,
            text="⚠️ 请备份您的助记词\n这是恢复身份的唯一凭证，请用纸笔抄写并妙善保管",
            foreground="red",
            justify=tk.CENTER,
            font=("TkDefaultFont", 11)
        ).pack(pady=(0, 15))
        
        # 助记词显示
        words_frame = ttk.LabelFrame(frame, text="您的助记词", padding=15)
        words_frame.pack(fill=tk.BOTH, expand=True)
        
        words = self.user_manager.mnemonic.split()
        inner_frame = ttk.Frame(words_frame)
        inner_frame.pack(expand=True)
        
        cols = 4
        for i, word in enumerate(words):
            row = i // cols
            col = i % cols
            ttk.Label(
                inner_frame,
                text=f"{i+1}. {word}",
                font=("Consolas", 12),
                padding=(15, 8)
            ).grid(row=row, column=col, sticky=tk.W)
        
        # 密码设置
        pwd_frame = ttk.LabelFrame(frame, text="设置保护密码", padding=10)
        pwd_frame.pack(fill=tk.X, pady=(15, 0))
        
        ttk.Label(pwd_frame, text="设置密码（用于保护您的身份）:").pack(anchor=tk.W)
        self._password_entry = ttk.Entry(pwd_frame, show="*", width=30)
        self._password_entry.pack(fill=tk.X, pady=(5, 10))
        
        ttk.Label(pwd_frame, text="确认密码:").pack(anchor=tk.W)
        self._confirm_entry = ttk.Entry(pwd_frame, show="*", width=30)
        self._confirm_entry.pack(fill=tk.X, pady=(5, 0))
        
        # 按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(15, 0))
        
        ttk.Button(
            btn_frame,
            text="复制助记词",
            command=self._copy_mnemonic
        ).pack(side=tk.LEFT)
        
        ttk.Button(
            btn_frame,
            text="取消",
            command=self.destroy
        ).pack(side=tk.RIGHT, padx=(10, 0))
        
        ttk.Button(
            btn_frame,
            text="已备份，保存 ✓",
            command=self._save
        ).pack(side=tk.RIGHT)
        
        self._password_entry.focus_set()
    
    def _copy_mnemonic(self):
        """复制助记词"""
        try:
            self.clipboard_clear()
            self.clipboard_append(self.user_manager.mnemonic)
            self.update()
            messagebox.showinfo("复制成功", "助记词已复制到剪贴板", parent=self)
        except Exception as e:
            messagebox.showerror("复制失败", str(e), parent=self)
    
    def _save(self):
        """保存并设置新密码"""
        password = self._password_entry.get()
        confirm = self._confirm_entry.get()
        
        if not password:
            messagebox.showerror("错误", "请输入密码", parent=self)
            return
        
        if len(password) < 6:
            messagebox.showerror("错误", "密码至少 6 位", parent=self)
            return
        
        if password != confirm:
            messagebox.showerror("错误", "两次密码不一致", parent=self)
            return
        
        # 更新密码
        if self.user_manager.change_password(password):
            self.result = True
            messagebox.showinfo(
                "备份成功",
                "助记词已备份，密码已设置\n\n请妙善保管您的助记词和密码",
                parent=self
            )
            self.destroy()
        else:
            messagebox.showerror("错误", "保存失败", parent=self)


class ImportIdentityDialog(tk.Toplevel):
    """导入已有身份对话框 - 支持助记词和 Keystore"""
    
    def __init__(self, parent, user_manager: UserManager):
        super().__init__(parent)
        self.user_manager = user_manager
        self.result = False
        self._mnemonic = None
        
        self.title("导入已有身份")
        self.geometry("650x520")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        self._container = ttk.Frame(self, padding=20)
        self._container.pack(fill=tk.BOTH, expand=True)
        
        self._show_choose_method()
        
        # 居中显示
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
        
        self.wait_window(self)
    
    def _clear_container(self):
        """清空容器"""
        for widget in self._container.winfo_children():
            widget.destroy()
    
    def _show_choose_method(self):
        """选择导入方式"""
        self._clear_container()
        
        # 标题
        ttk.Label(
            self._container,
            text="选择导入方式",
            font=("TkDefaultFont", 14, "bold")
        ).pack(pady=(0, 20))
        
        ttk.Label(
            self._container,
            text="请选择您要使用的导入方式",
            justify=tk.CENTER
        ).pack(pady=(0, 30))
        
        # 导入方式按钮
        btn_frame = ttk.Frame(self._container)
        btn_frame.pack(fill=tk.X, padx=50)
        
        # 助记词导入
        mnemonic_frame = ttk.LabelFrame(btn_frame, text="📝 助记词导入", padding=15)
        mnemonic_frame.pack(fill=tk.X, pady=10)
        ttk.Label(mnemonic_frame, text="使用 12 或 24 个助记词单词恢复身份").pack(anchor=tk.W)
        ttk.Button(mnemonic_frame, text="输入助记词 →", 
                   command=self._show_mnemonic_input).pack(anchor=tk.E, pady=(10, 0))
        
        # Keystore 导入
        keystore_frame = ttk.LabelFrame(btn_frame, text="📁 Keystore 导入", padding=15)
        keystore_frame.pack(fill=tk.X, pady=10)
        ttk.Label(keystore_frame, text="从 Keystore 文件恢复身份").pack(anchor=tk.W)
        ttk.Button(keystore_frame, text="选择文件 →", 
                   command=self._import_keystore).pack(anchor=tk.E, pady=(10, 0))
        
        # 取消按钮
        ttk.Button(
            self._container,
            text="取消",
            command=self.destroy
        ).pack(side=tk.BOTTOM, anchor=tk.E)
    
    def _show_mnemonic_input(self):
        """步骤 1: 输入助记词"""
        self._clear_container()
        
        # 标题
        ttk.Label(
            self._container,
            text="步骤 1/2: 输入助记词",
            font=("TkDefaultFont", 14, "bold")
        ).pack(pady=(0, 15))
        
        ttk.Label(
            self._container,
            text="请输入您的 12 或 24 个助记词单词，用空格分隔",
            justify=tk.CENTER
        ).pack(pady=(0, 15))
        
        # 助记词输入框
        self._mnemonic_text = tk.Text(
            self._container, 
            height=5, 
            width=60,
            font=("Consolas", 11),
            wrap=tk.WORD
        )
        self._mnemonic_text.pack(fill=tk.X, pady=15)
        
        # 按钮
        btn_frame = ttk.Frame(self._container)
        btn_frame.pack(fill=tk.X, pady=(15, 0))
        
        ttk.Button(
            btn_frame,
            text="← 返回",
            command=self._show_choose_method
        ).pack(side=tk.LEFT)
        
        ttk.Button(
            btn_frame,
            text="取消",
            command=self.destroy
        ).pack(side=tk.RIGHT, padx=(10, 0))
        
        ttk.Button(
            btn_frame,
            text="验证并继续 →",
            command=self._validate_and_next
        ).pack(side=tk.RIGHT)
        
        self._mnemonic_text.focus_set()
    
    def _validate_and_next(self):
        """验证助记词并进入下一步"""
        mnemonic = self._mnemonic_text.get("1.0", tk.END).strip()
        
        if not mnemonic:
            messagebox.showerror("错误", "请输入助记词", parent=self)
            return
        
        words = mnemonic.split()
        if len(words) not in [12, 24]:
            messagebox.showerror("错误", f"助记词必须是 12 或 24 个单词\n当前: {len(words)} 个", parent=self)
            return
        
        # 验证助记词是否有效
        try:
            from aeknow.wallet import MnemonicWallet
            wallet = MnemonicWallet.from_mnemonic(mnemonic)
            self._mnemonic = mnemonic
            self._show_set_password()
        except Exception as e:
            messagebox.showerror("错误", f"助记词无效\n{str(e)}", parent=self)
    
    def _show_set_password(self):
        """步骤 2: 设置密码"""
        self._clear_container()
        
        # 标题
        ttk.Label(
            self._container,
            text="步骤 2/2: 设置密码",
            font=("TkDefaultFont", 14, "bold")
        ).pack(pady=(0, 20))
        
        ttk.Label(
            self._container,
            text="设置一个密码来保护您的身份",
            justify=tk.CENTER
        ).pack(pady=(0, 20))
        
        # 密码输入
        form_frame = ttk.Frame(self._container)
        form_frame.pack(fill=tk.X, padx=50)
        
        ttk.Label(form_frame, text="设置密码:").pack(anchor=tk.W)
        self._password_entry = ttk.Entry(form_frame, show="*", width=40, font=("TkDefaultFont", 12))
        self._password_entry.pack(fill=tk.X, pady=(5, 15))
        
        ttk.Label(form_frame, text="确认密码:").pack(anchor=tk.W)
        self._confirm_entry = ttk.Entry(form_frame, show="*", width=40, font=("TkDefaultFont", 12))
        self._confirm_entry.pack(fill=tk.X, pady=(5, 20))
        
        # 按钮
        btn_frame = ttk.Frame(self._container)
        btn_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Button(
            btn_frame,
            text="← 返回上一步",
            command=self._show_mnemonic_input
        ).pack(side=tk.LEFT)
        
        ttk.Button(
            btn_frame,
            text="取消",
            command=self.destroy
        ).pack(side=tk.RIGHT, padx=(10, 0))
        
        ttk.Button(
            btn_frame,
            text="完成导入 ✓",
            command=self._finish_mnemonic
        ).pack(side=tk.RIGHT)
        
        self._password_entry.focus_set()
    
    def _finish_mnemonic(self):
        """完成助记词导入"""
        password = self._password_entry.get()
        confirm = self._confirm_entry.get()
        
        if not password:
            messagebox.showerror("错误", "请输入密码", parent=self)
            return
        
        if len(password) < 6:
            messagebox.showerror("错误", "密码至少 6 位", parent=self)
            return
        
        if password != confirm:
            messagebox.showerror("错误", "两次密码不一致", parent=self)
            return
        
        # 保存用户
        if self.user_manager.import_from_mnemonic(self._mnemonic, password):
            self.result = True
            messagebox.showinfo(
                "导入成功",
                f"您的身份已导入！\n\n地址: {self.user_manager.short_address}",
                parent=self
            )
            self.destroy()
        else:
            messagebox.showerror("错误", "导入失败", parent=self)
    
    def _import_keystore(self):
        """导入 Keystore 文件"""
        from tkinter import filedialog
        
        file_path = filedialog.askopenfilename(
            title="选择 Keystore 文件",
            filetypes=[
                ("JSON 文件", "*.json"),
                ("所有文件", "*.*")
            ],
            parent=self
        )
        if not file_path:
            return
        
        # 请求密码
        password = simpledialog.askstring(
            "Keystore 密码",
            "请输入 Keystore 文件的密码:",
            show="*",
            parent=self
        )
        if password is None:
            return
        
        try:
            # 尝试加载 Keystore（支持新版 HD 钱包和旧版 SDK 格式）
            import json
            with open(file_path, 'r') as f:
                keystore_data = json.load(f)
            
            secret_type = keystore_data.get('crypto', {}).get('secret_type', '')
            
            if secret_type == 'ed25519-bip39-mnemonic':
                # 新版 HD 钱包格式
                from aeknow.wallet import MnemonicWallet
                wallet = MnemonicWallet.from_keystore(file_path, password)
                self.user_manager._wallet = wallet
            else:
                # 旧版 SDK 格式（ed25519）- 没有助记词
                from aeknow.signing import Account
                account = Account.from_keystore(file_path, password)
                # 创建一个简化的 wallet 对象
                class LegacyWallet:
                    def __init__(self, acc):
                        self.account = acc
                        self._mnemonic = None
                    @property
                    def address(self):
                        return self.account.get_address()
                    @property
                    def mnemonic(self):
                        return None  # 旧版格式没有助记词
                    def save_keystore(self, path, pwd):
                        self.account.save_to_keystore_file(path, pwd)
                
                self.user_manager._wallet = LegacyWallet(account)
            
            # 复制到用户目录
            import shutil
            shutil.copy(file_path, self.user_manager.keystore_path)
            
            # 设置状态
            self.user_manager._is_default_password = False
            
            # 保存元数据
            self.user_manager._metadata = {
                "address": self.user_manager._wallet.address,
                "imported_at": self.user_manager._get_timestamp(),
                "default_password": False,
                "legacy_format": (secret_type != 'ed25519-bip39-mnemonic')  # 标记旧版格式
            }
            self.user_manager._save_metadata()
            
            self.result = True
            
            # 旧版格式提示
            if secret_type != 'ed25519-bip39-mnemonic':
                messagebox.showinfo(
                    "导入成功",
                    f"您的身份已导入！\n\n地址: {self.user_manager.short_address}\n\n⚠️ 注意：这是旧版 SDK 格式，没有助记词",
                    parent=self
                )
            else:
                messagebox.showinfo(
                    "导入成功",
                    f"您的身份已导入！\n\n地址: {self.user_manager.short_address}",
                    parent=self
                )
            self.destroy()
            
        except Exception as e:
            error_msg = str(e)
            if "Decryption failed" in error_msg or "verification" in error_msg:
                messagebox.showerror("密码错误", "密码不正确，请重新输入", parent=self)
            else:
                messagebox.showerror("导入失败", f"无法加载 Keystore:\n{error_msg}", parent=self)


class MnemonicDisplayDialog(tk.Toplevel):
    """助记词显示对话框（只读）"""
    
    def __init__(self, parent, mnemonic: str):
        super().__init__(parent)
        self.mnemonic = mnemonic
        
        self.title("您的助记词")
        self.geometry("650x380")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        self._create_widgets()
        
        # 居中显示
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
    
    def _create_widgets(self):
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 警告
        ttk.Label(
            frame,
            text="⚠️ 请妙善保管，不要泄露给他人",
            foreground="red"
        ).pack(pady=(0, 15))
        
        # 助记词显示
        words_frame = ttk.LabelFrame(frame, text="助记词", padding=15)
        words_frame.pack(fill=tk.BOTH, expand=True)
        
        words = self.mnemonic.split()
        inner_frame = ttk.Frame(words_frame)
        inner_frame.pack(expand=True)
        
        cols = 4
        for i, word in enumerate(words):
            row = i // cols
            col = i % cols
            ttk.Label(
                inner_frame,
                text=f"{i+1}. {word}",
                font=("Consolas", 12),
                padding=(15, 8)
            ).grid(row=row, column=col, sticky=tk.W)
        
        # 按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(15, 0))
        
        ttk.Button(
            btn_frame,
            text="复制助记词",
            command=self._copy_mnemonic
        ).pack(side=tk.LEFT)
        
        ttk.Button(
            btn_frame,
            text="关闭",
            command=self.destroy
        ).pack(side=tk.RIGHT)
    
    def _copy_mnemonic(self):
        """复制助记词"""
        try:
            self.clipboard_clear()
            self.clipboard_append(self.mnemonic)
            self.update()
            messagebox.showinfo("复制成功", "助记词已复制到剪贴板", parent=self)
        except Exception as e:
            messagebox.showerror("复制失败", str(e), parent=self)


class MessageSignDialog(tk.Toplevel):
    """
    消息签名对话框
    参考 login_sign_tk.py，支持网站登录签名
    """
    
    # 签名方式
    METHOD_DIRECT = 'direct'       # 方式A: 直接签名
    METHOD_PREFIXED = 'prefixed'   # 方式B: 带前缀签名
    METHOD_HASHED = 'hashed'       # 方式C: 哈希签名
    
    def __init__(self, parent, user_manager: UserManager):
        super().__init__(parent)
        self.user_manager = user_manager
        
        self.title("消息签名")
        self.geometry("850x888")
        self.minsize(800, 800)
        self.transient(parent)
        
        self._create_widgets()
        
        # 居中显示
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
    
    def _create_widgets(self):
        # 创建标签页
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 签名页
        sign_frame = ttk.Frame(notebook, padding=15)
        notebook.add(sign_frame, text=" ✅ 签名 ")
        self._create_sign_tab(sign_frame)
        
        # 验证页
        verify_frame = ttk.Frame(notebook, padding=15)
        notebook.add(verify_frame, text=" 🔍 验证 ")
        self._create_verify_tab(verify_frame)
    
    def _create_sign_tab(self, parent):
        """创建签名标签页"""
        # 当前账户
        info_frame = ttk.LabelFrame(parent, text="当前账户", padding=5)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        self._address_label = ttk.Label(info_frame, text=self.user_manager.address, 
                                         font=("Consolas", 10), foreground="blue")
        self._address_label.pack(fill=tk.X)
        
        btn_frame = ttk.Frame(info_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="复制地址", command=self._copy_address).pack(side=tk.LEFT)
        
        # 待签名消息区域
        msg_frame = ttk.LabelFrame(parent, text="待签名消息", padding=10)
        msg_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 快捷操作按钮
        gen_frame = ttk.Frame(msg_frame)
        gen_frame.pack(fill=tk.X, pady=5)
        ttk.Label(gen_frame, text="快捷:").pack(side=tk.LEFT)
        ttk.Button(gen_frame, text="生成登录挑战", 
                   command=lambda: self._generate_challenge('simple')).pack(side=tk.LEFT, padx=2)
        ttk.Button(gen_frame, text="生成标准挑战", 
                   command=lambda: self._generate_challenge('standard')).pack(side=tk.LEFT, padx=2)
        ttk.Button(gen_frame, text="粘贴", 
                   command=self._paste_challenge).pack(side=tk.LEFT, padx=2)
        ttk.Button(gen_frame, text="清空", 
                   command=lambda: self._challenge_text.delete('1.0', tk.END)).pack(side=tk.LEFT, padx=2)
        
        ttk.Label(msg_frame, text="输入任意消息或使用上方快捷按钮生成:").pack(anchor=tk.W)
        self._challenge_text = tk.Text(msg_frame, height=4, font=("TkDefaultFont", 11))
        self._challenge_text.pack(fill=tk.BOTH, expand=True)
        
        # 签名方式选择
        method_frame = ttk.LabelFrame(parent, text="签名方式", padding=10)
        method_frame.pack(fill=tk.X, pady=5)
        
        self._sign_method = tk.StringVar(value=self.METHOD_HASHED)
        ttk.Radiobutton(method_frame, text="A: 直接签名", 
                        variable=self._sign_method, value=self.METHOD_DIRECT).pack(side=tk.LEFT, padx=(0, 15))
        ttk.Radiobutton(method_frame, text="B: 带AE前缀", 
                        variable=self._sign_method, value=self.METHOD_PREFIXED).pack(side=tk.LEFT, padx=15)
        ttk.Radiobutton(method_frame, text="C: Blake2b哈希 (推荐)", 
                        variable=self._sign_method, value=self.METHOD_HASHED).pack(side=tk.LEFT, padx=15)
        
        # 签名按钮
        ttk.Button(parent, text="执行签名", command=self._do_sign).pack(anchor=tk.W, pady=5)
        
        # 签名结果
        result_frame = ttk.LabelFrame(parent, text="签名结果", padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # sg_签名
        row1 = ttk.Frame(result_frame)
        row1.pack(fill=tk.X, pady=2)
        ttk.Label(row1, text="sg_签名:", width=12).pack(side=tk.LEFT)
        self._sig_sg_var = tk.StringVar()
        ttk.Entry(row1, textvariable=self._sig_sg_var, state='readonly', 
                  font=("Consolas", 9)).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(row1, text="复制", 
                   command=lambda: self._copy_text(self._sig_sg_var.get())).pack(side=tk.LEFT)
        
        # Hex签名
        row2 = ttk.Frame(result_frame)
        row2.pack(fill=tk.X, pady=2)
        ttk.Label(row2, text="Hex签名:", width=12).pack(side=tk.LEFT)
        self._sig_hex_var = tk.StringVar()
        ttk.Entry(row2, textvariable=self._sig_hex_var, state='readonly', 
                  font=("Consolas", 9)).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(row2, text="复制", 
                   command=lambda: self._copy_text(self._sig_hex_var.get())).pack(side=tk.LEFT)
        
        # 消息哈希
        row3 = ttk.Frame(result_frame)
        row3.pack(fill=tk.X, pady=2)
        ttk.Label(row3, text="消息哈希:", width=12).pack(side=tk.LEFT)
        self._msg_hash_var = tk.StringVar()
        ttk.Entry(row3, textvariable=self._msg_hash_var, state='readonly', 
                  font=("Consolas", 9)).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(row3, text="复制", 
                   command=lambda: self._copy_text(self._msg_hash_var.get())).pack(side=tk.LEFT)
        
        # 登录字符串
        login_frame = ttk.LabelFrame(result_frame, text="登录字符串 (address|signature) - 用于网站登录", padding=5)
        login_frame.pack(fill=tk.X, pady=10)
        
        self._login_string_var = tk.StringVar()
        ttk.Entry(login_frame, textvariable=self._login_string_var, state='readonly', 
                  font=("Consolas", 9)).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(login_frame, text="复制", 
                   command=lambda: self._copy_text(self._login_string_var.get())).pack(side=tk.LEFT, padx=5)
    
    def _create_verify_tab(self, parent):
        """创建验证标签页"""
        # 解析登录字符串
        parse_frame = ttk.LabelFrame(parent, text="快捷解析", padding=10)
        parse_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(parse_frame, text="登录字符串 (address|signature):").pack(anchor=tk.W)
        parse_row = ttk.Frame(parse_frame)
        parse_row.pack(fill=tk.X, pady=5)
        self._parse_login_var = tk.StringVar()
        ttk.Entry(parse_row, textvariable=self._parse_login_var, 
                  font=("Consolas", 10)).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(parse_row, text="解析", command=self._parse_login_string).pack(side=tk.LEFT, padx=5)
        ttk.Button(parse_row, text="粘贴", command=self._paste_login_string).pack(side=tk.LEFT)
        
        # 验证输入
        input_frame = ttk.LabelFrame(parent, text="验证输入", padding=10)
        input_frame.pack(fill=tk.BOTH, expand=True)
        
        # 地址
        addr_row = ttk.Frame(input_frame)
        addr_row.pack(fill=tk.X, pady=5)
        ttk.Label(addr_row, text="签名者地址 (ak_...):").pack(side=tk.LEFT)
        self._verify_addr_var = tk.StringVar()
        ttk.Entry(addr_row, textvariable=self._verify_addr_var, 
                  font=("Consolas", 10)).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(addr_row, text="粘贴", 
                   command=lambda: self._paste_to_var(self._verify_addr_var)).pack(side=tk.LEFT)
        
        # 消息
        ttk.Label(input_frame, text="原始消息:").pack(anchor=tk.W)
        self._verify_msg_text = tk.Text(input_frame, height=4, font=("TkDefaultFont", 11))
        self._verify_msg_text.pack(fill=tk.X, pady=5)
        
        # 签名
        sig_row = ttk.Frame(input_frame)
        sig_row.pack(fill=tk.X, pady=5)
        ttk.Label(sig_row, text="签名 (sg_xxx 或 hex):").pack(side=tk.LEFT)
        self._verify_sig_var = tk.StringVar()
        ttk.Entry(sig_row, textvariable=self._verify_sig_var, 
                  font=("Consolas", 10)).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(sig_row, text="粘贴", 
                   command=lambda: self._paste_to_var(self._verify_sig_var)).pack(side=tk.LEFT)
        
        # 按钮
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, pady=10)
        ttk.Button(btn_frame, text="验证签名", command=self._do_verify).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="清空", command=self._clear_verify).pack(side=tk.LEFT)
        
        # 结果
        result_frame = ttk.LabelFrame(parent, text="验证结果", padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True)
        
        self._verify_result_text = tk.Text(result_frame, height=6, state=tk.DISABLED, 
                                            font=("TkDefaultFont", 11))
        self._verify_result_text.pack(fill=tk.BOTH, expand=True)
    
    def _generate_challenge(self, mode: str):
        """生成挑战消息"""
        import time
        import secrets
        
        nonce = secrets.token_hex(8 if mode == 'simple' else 16)
        timestamp = int(time.time())
        
        if mode == 'simple':
            challenge = f"AEKnow Login\nNonce: {nonce}\nTime: {timestamp}"
        else:
            challenge = f"AEKnow Login Challenge\nAddress: {self.user_manager.address}\nNonce: {nonce}\nTimestamp: {timestamp}"
        
        self._challenge_text.delete('1.0', tk.END)
        self._challenge_text.insert('1.0', challenge)
    
    def _paste_challenge(self):
        """粘贴挑战"""
        try:
            text = self.clipboard_get()
            self._challenge_text.delete('1.0', tk.END)
            self._challenge_text.insert('1.0', text)
        except:
            pass
    
    def _do_sign(self):
        """执行签名"""
        import hashlib
        import base58
        
        message = self._challenge_text.get('1.0', tk.END).strip()
        if not message:
            messagebox.showwarning("提示", "请输入要签名的消息", parent=self)
            return
        
        method = self._sign_method.get()
        
        try:
            account = self.user_manager._wallet.account
            msg_bytes = message.encode('utf-8')
            
            # 计算消息哈希
            msg_hash = hashlib.blake2b(msg_bytes, digest_size=32).digest()
            
            # 根据方式准备签名数据
            if method == self.METHOD_DIRECT:
                sign_data = msg_bytes
            elif method == self.METHOD_PREFIXED:
                prefix = b'aeternity Signed Message:\n' + len(msg_bytes).to_bytes(4, 'big')
                sign_data = prefix + msg_bytes
            else:  # METHOD_HASHED
                sign_data = msg_hash
            
            # 执行签名
            signature = account.sign(sign_data)
            
            # 编码为 sg_xxx 格式
            sig_sg = "sg_" + base58.b58encode_check(signature).decode()
            sig_hex = signature.hex()
            
            # 显示结果
            self._sig_sg_var.set(sig_sg)
            self._sig_hex_var.set(sig_hex)
            self._msg_hash_var.set(msg_hash.hex())
            self._login_string_var.set(f"{self.user_manager.address}|{sig_sg}")
            
            messagebox.showinfo("签名成功", 
                f"签名方式: {method}\n可复制签名结果使用", parent=self)
            
        except Exception as e:
            messagebox.showerror("签名失败", str(e), parent=self)
    
    def _parse_login_string(self):
        """解析登录字符串"""
        login_str = self._parse_login_var.get().strip()
        if '|' in login_str:
            parts = login_str.split('|', 1)
            self._verify_addr_var.set(parts[0])
            self._verify_sig_var.set(parts[1])
    
    def _paste_login_string(self):
        """粘贴登录字符串"""
        try:
            self._parse_login_var.set(self.clipboard_get())
        except:
            pass
    
    def _do_verify(self):
        """验证签名 (尝试所有三种方式)"""
        import hashlib
        import base58
        import nacl.signing
        import nacl.exceptions
        
        address = self._verify_addr_var.get().strip()
        message = self._verify_msg_text.get('1.0', tk.END).strip()
        signature = self._verify_sig_var.get().strip()
        
        if not all([address, message, signature]):
            messagebox.showwarning("提示", "请填写完整的验证信息", parent=self)
            return
        
        try:
            # 解析公钥
            public_key = base58.b58decode_check(address[3:])
            verify_key = nacl.signing.VerifyKey(public_key)
            
            # 解析签名
            if signature.startswith("sg_"):
                sig_bytes = base58.b58decode_check(signature[3:])
            else:
                sig_bytes = bytes.fromhex(signature)
            
            msg_bytes = message.encode('utf-8')
            result = {'valid': False, 'method': None}
            
            # 方式A: 直接签名
            try:
                verify_key.verify(msg_bytes, sig_bytes)
                result = {'valid': True, 'method': 'direct (直接签名)'}
            except nacl.exceptions.BadSignatureError:
                pass
            
            # 方式B: 带前缀
            if not result['valid']:
                try:
                    prefix = b"aeternity Signed Message:\n" + len(msg_bytes).to_bytes(4, 'big')
                    verify_key.verify(prefix + msg_bytes, sig_bytes)
                    result = {'valid': True, 'method': 'prefixed (带AE前缀)'}
                except nacl.exceptions.BadSignatureError:
                    pass
            
            # 方式C: Blake2b 哈希
            if not result['valid']:
                try:
                    msg_hash = hashlib.blake2b(msg_bytes, digest_size=32).digest()
                    verify_key.verify(msg_hash, sig_bytes)
                    result = {'valid': True, 'method': 'hashed (Blake2b哈希)'}
                except nacl.exceptions.BadSignatureError:
                    pass
            
            # 显示结果
            self._verify_result_text.config(state=tk.NORMAL)
            self._verify_result_text.delete('1.0', tk.END)
            
            if result['valid']:
                text = f"✅ 签名有效!\n\n签名方式: {result['method']}\n验证通过，消息确实由该地址签名。"
                self._verify_result_text.insert('1.0', text)
            else:
                text = "❌ 签名无效!\n\n签名验证失败，消息可能被篡改或签名者地址不匹配。"
                self._verify_result_text.insert('1.0', text)
            
            self._verify_result_text.config(state=tk.DISABLED)
            
        except Exception as e:
            self._verify_result_text.config(state=tk.NORMAL)
            self._verify_result_text.delete('1.0', tk.END)
            self._verify_result_text.insert('1.0', f"❌ 验证失败: {str(e)}")
            self._verify_result_text.config(state=tk.DISABLED)
    
    def _clear_verify(self):
        """清空验证"""
        self._parse_login_var.set('')
        self._verify_addr_var.set('')
        self._verify_msg_text.delete('1.0', tk.END)
        self._verify_sig_var.set('')
        self._verify_result_text.config(state=tk.NORMAL)
        self._verify_result_text.delete('1.0', tk.END)
        self._verify_result_text.config(state=tk.DISABLED)
    
    def _copy_address(self):
        """复制地址"""
        self._copy_text(self.user_manager.address)
    
    def _copy_text(self, text: str):
        """复制文本"""
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            self.update()
    
    def _paste_to_var(self, var: tk.StringVar):
        """粘贴到变量"""
        try:
            var.set(self.clipboard_get())
        except:
            pass


class MessageCryptoDialog(tk.Toplevel):
    """
    消息加密对话框
    参考 crypto_tk.py，支持 SealedBox 和 Box 加密
    """
    
    def __init__(self, parent, user_manager: UserManager):
        super().__init__(parent)
        self.user_manager = user_manager
        
        self.title("消息加密")
        self.geometry("850x888")
        self.minsize(800, 850)
        self.transient(parent)
        
        self._create_widgets()
        
        # 居中显示
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
    
    def _create_widgets(self):
        # 创建标签页
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 加密页
        encrypt_frame = ttk.Frame(notebook, padding=15)
        notebook.add(encrypt_frame, text=" 🔒 加密 ")
        self._create_encrypt_tab(encrypt_frame)
        
        # 解密页
        decrypt_frame = ttk.Frame(notebook, padding=15)
        notebook.add(decrypt_frame, text=" 🔓 解密 ")
        self._create_decrypt_tab(decrypt_frame)
        
        # 密钥信息页
        keyinfo_frame = ttk.Frame(notebook, padding=15)
        notebook.add(keyinfo_frame, text=" 🔑 密钥信息 ")
        self._create_keyinfo_tab(keyinfo_frame)
    
    def _create_encrypt_tab(self, parent):
        """创建加密标签页"""
        # 当前账户
        info_frame = ttk.LabelFrame(parent, text="当前账户", padding=5)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        addr_row = ttk.Frame(info_frame)
        addr_row.pack(fill=tk.X)
        ttk.Label(addr_row, text=self.user_manager.address, 
                  font=("Consolas", 10), foreground="blue").pack(side=tk.LEFT)
        ttk.Button(addr_row, text="复制我的地址", 
                   command=self._copy_my_address).pack(side=tk.RIGHT)
        
        # 加密模式
        mode_frame = ttk.LabelFrame(parent, text="加密模式", padding=10)
        mode_frame.pack(fill=tk.X, pady=5)
        
        self._encrypt_mode = tk.StringVar(value='sealed')
        sealed_frame = ttk.Frame(mode_frame)
        sealed_frame.pack(fill=tk.X)
        ttk.Radiobutton(sealed_frame, text="SealedBox (匿名加密)", 
                        variable=self._encrypt_mode, value='sealed').pack(side=tk.LEFT)
        ttk.Label(sealed_frame, text="- 只需接收方地址，接收方无法知道发送者", 
                  foreground="gray").pack(side=tk.LEFT, padx=10)
        
        box_frame = ttk.Frame(mode_frame)
        box_frame.pack(fill=tk.X)
        ttk.Radiobutton(box_frame, text="Box (双向认证加密)", 
                        variable=self._encrypt_mode, value='box').pack(side=tk.LEFT)
        ttk.Label(box_frame, text="- 双方可验证对方身份", 
                  foreground="gray").pack(side=tk.LEFT, padx=10)
        
        # 接收方地址
        recipient_frame = ttk.Frame(parent)
        recipient_frame.pack(fill=tk.X, pady=5)
        ttk.Label(recipient_frame, text="接收方地址 (ak_...):").pack(side=tk.LEFT)
        self._recipient_var = tk.StringVar()
        ttk.Entry(recipient_frame, textvariable=self._recipient_var, 
                  font=("Consolas", 10)).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(recipient_frame, text="粘贴", 
                   command=lambda: self._paste_to_var(self._recipient_var)).pack(side=tk.LEFT)
        
        # 消息输入
        msg_frame = ttk.LabelFrame(parent, text="要加密的消息", padding=10)
        msg_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self._plaintext_text = tk.Text(msg_frame, height=6, font=("TkDefaultFont", 11))
        self._plaintext_text.pack(fill=tk.BOTH, expand=True)
        
        # 按钮
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="加密", command=self._do_encrypt).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="清空", 
                   command=lambda: self._plaintext_text.delete('1.0', tk.END)).pack(side=tk.LEFT)
        
        # 密文结果
        result_frame = ttk.LabelFrame(parent, text="加密结果 (Base64)", padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self._ciphertext_text = tk.Text(result_frame, height=5, font=("Consolas", 10), 
                                         state=tk.DISABLED)
        self._ciphertext_text.pack(fill=tk.BOTH, expand=True)
        
        result_btn_frame = ttk.Frame(result_frame)
        result_btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(result_btn_frame, text="复制密文", 
                   command=self._copy_ciphertext).pack(side=tk.LEFT, padx=5)
        ttk.Button(result_btn_frame, text="清空结果", 
                   command=self._clear_ciphertext).pack(side=tk.LEFT)
    
    def _create_decrypt_tab(self, parent):
        """创建解密标签页"""
        # 当前账户
        info_frame = ttk.LabelFrame(parent, text="当前账户 (接收方)", padding=5)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(info_frame, text=self.user_manager.address, 
                  font=("Consolas", 10), foreground="blue").pack(fill=tk.X)
        
        # 解密模式
        mode_frame = ttk.LabelFrame(parent, text="解密模式", padding=10)
        mode_frame.pack(fill=tk.X, pady=5)
        
        self._decrypt_mode = tk.StringVar(value='sealed')
        ttk.Radiobutton(mode_frame, text="SealedBox 解密 (匿名)", 
                        variable=self._decrypt_mode, value='sealed',
                        command=self._on_decrypt_mode_change).pack(anchor=tk.W)
        ttk.Radiobutton(mode_frame, text="Box 解密 (需验证发送方)", 
                        variable=self._decrypt_mode, value='box',
                        command=self._on_decrypt_mode_change).pack(anchor=tk.W)
        
        # 发送方地址 (Box 模式)
        self._sender_frame = ttk.Frame(parent)
        self._sender_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(self._sender_frame, text="发送方地址 (ak_...) - 仅 Box 模式:").pack(side=tk.LEFT)
        self._sender_var = tk.StringVar()
        ttk.Entry(self._sender_frame, textvariable=self._sender_var, 
                  font=("Consolas", 10)).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(self._sender_frame, text="粘贴", 
                   command=lambda: self._paste_to_var(self._sender_var)).pack(side=tk.LEFT)
        
        self._sender_frame.pack_forget()  # 初始隐藏
        
        # 密文输入
        cipher_frame = ttk.LabelFrame(parent, text="密文 (Base64)", padding=10)
        cipher_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self._cipher_input_text = tk.Text(cipher_frame, height=5, font=("Consolas", 10))
        self._cipher_input_text.pack(fill=tk.BOTH, expand=True)
        
        cipher_btn_frame = ttk.Frame(cipher_frame)
        cipher_btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(cipher_btn_frame, text="粘贴密文", 
                   command=self._paste_cipher).pack(side=tk.LEFT, padx=5)
        
        # 按钮
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="解密", command=self._do_decrypt).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="清空", command=self._clear_decrypt).pack(side=tk.LEFT)
        
        # 明文结果
        result_frame = ttk.LabelFrame(parent, text="解密结果", padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self._decrypted_text = tk.Text(result_frame, height=6, font=("TkDefaultFont", 11), 
                                        state=tk.DISABLED)
        self._decrypted_text.pack(fill=tk.BOTH, expand=True)
        
        ttk.Button(result_frame, text="复制明文", 
                   command=self._copy_decrypted).pack(anchor=tk.W, pady=5)
    
    def _create_keyinfo_tab(self, parent):
        """创建密钥信息标签页"""
        info_text = tk.Text(parent, font=("Consolas", 10))
        info_text.pack(fill=tk.BOTH, expand=True)
        
        try:
            from aeknow.crypto import get_key_info
            account = self.user_manager._wallet.account
            key_info = get_key_info(account)
            
            # 获取私钥 (hex)
            ed25519_private = account.signing_key.encode().hex()
            
            info = f"""===========================================================
  密钥信息
===========================================================

账户地址:
  {key_info['address']}

-----------------------------------------------------------
  ED25519 密钥 (用于签名)
-----------------------------------------------------------

公钥 (hex):
  {key_info['ed25519_public']}

-----------------------------------------------------------
  X25519 密钥 (用于加密 - 转换后)
-----------------------------------------------------------

公钥 (hex):
  {key_info['x25519_public']}

===========================================================
  说明
===========================================================

ED25519: 用于数字签名 (签名/验证)
X25519:  用于密钥交换和加密 (NaCl Box/SealedBox)

密钥转换: ED25519 → X25519 (单向转换)
"""
            info_text.insert('1.0', info)
        except Exception as e:
            info_text.insert('1.0', f"获取密钥信息失败: {e}")
        
        info_text.config(state=tk.DISABLED)
    
    def _on_decrypt_mode_change(self):
        """解密模式切换"""
        if self._decrypt_mode.get() == 'box':
            self._sender_frame.pack(fill=tk.X, pady=5)
        else:
            self._sender_frame.pack_forget()
    
    def _do_encrypt(self):
        """执行加密"""
        recipient = self._recipient_var.get().strip()
        plaintext = self._plaintext_text.get('1.0', tk.END).strip()
        mode = self._encrypt_mode.get()
        
        if not recipient:
            messagebox.showwarning("提示", "请输入接收方地址", parent=self)
            return
        if not plaintext:
            messagebox.showwarning("提示", "请输入要加密的消息", parent=self)
            return
        
        try:
            from aeknow.crypto import MessageCrypto
            
            crypto = MessageCrypto.from_account(self.user_manager._wallet.account)
            
            if mode == 'sealed':
                ciphertext = crypto.sealed_encrypt(plaintext, recipient)
                mode_name = "SealedBox (匿名)"
            else:
                ciphertext = crypto.box_encrypt(plaintext, recipient)
                mode_name = "Box (双向认证)"
            
            # 显示结果
            self._ciphertext_text.config(state=tk.NORMAL)
            self._ciphertext_text.delete('1.0', tk.END)
            self._ciphertext_text.insert('1.0', ciphertext)
            self._ciphertext_text.config(state=tk.DISABLED)
            
            messagebox.showinfo("加密成功", f"模式: {mode_name}", parent=self)
            
        except Exception as e:
            messagebox.showerror("加密失败", str(e), parent=self)
    
    def _do_decrypt(self):
        """执行解密"""
        ciphertext = self._cipher_input_text.get('1.0', tk.END).strip()
        mode = self._decrypt_mode.get()
        sender = self._sender_var.get().strip()
        
        if not ciphertext:
            messagebox.showwarning("提示", "请输入密文", parent=self)
            return
        if mode == 'box' and not sender:
            messagebox.showwarning("提示", "Box 模式需要输入发送方地址", parent=self)
            return
        
        try:
            from aeknow.crypto import MessageCrypto
            
            crypto = MessageCrypto.from_account(self.user_manager._wallet.account)
            
            if mode == 'sealed':
                plaintext = crypto.sealed_decrypt(ciphertext)
                mode_name = "SealedBox"
            else:
                plaintext = crypto.box_decrypt(ciphertext, sender)
                mode_name = "Box (已验证)"
            
            # 显示结果
            self._decrypted_text.config(state=tk.NORMAL)
            self._decrypted_text.delete('1.0', tk.END)
            self._decrypted_text.insert('1.0', plaintext)
            self._decrypted_text.config(state=tk.DISABLED)
            
            messagebox.showinfo("解密成功", f"模式: {mode_name}", parent=self)
            
        except Exception as e:
            messagebox.showerror("解密失败", str(e), parent=self)
    
    def _copy_my_address(self):
        """复制我的地址"""
        self.clipboard_clear()
        self.clipboard_append(self.user_manager.address)
        self.update()
    
    def _copy_ciphertext(self):
        """复制密文"""
        ct = self._ciphertext_text.get('1.0', tk.END).strip()
        if ct:
            self.clipboard_clear()
            self.clipboard_append(ct)
            self.update()
            messagebox.showinfo("复制成功", "密文已复制到剪贴板", parent=self)
    
    def _clear_ciphertext(self):
        """清空密文结果"""
        self._ciphertext_text.config(state=tk.NORMAL)
        self._ciphertext_text.delete('1.0', tk.END)
        self._ciphertext_text.config(state=tk.DISABLED)
    
    def _copy_decrypted(self):
        """复制明文"""
        pt = self._decrypted_text.get('1.0', tk.END).strip()
        if pt:
            self.clipboard_clear()
            self.clipboard_append(pt)
            self.update()
            messagebox.showinfo("复制成功", "明文已复制到剪贴板", parent=self)
    
    def _paste_cipher(self):
        """粘贴密文"""
        try:
            text = self.clipboard_get()
            self._cipher_input_text.delete('1.0', tk.END)
            self._cipher_input_text.insert('1.0', text)
        except:
            pass
    
    def _clear_decrypt(self):
        """清空解密"""
        self._sender_var.set('')
        self._cipher_input_text.delete('1.0', tk.END)
        self._decrypted_text.config(state=tk.NORMAL)
        self._decrypted_text.delete('1.0', tk.END)
        self._decrypted_text.config(state=tk.DISABLED)
    
    def _paste_to_var(self, var: tk.StringVar):
        """粘贴到变量"""
        try:
            var.set(self.clipboard_get())
        except:
            pass


class AccountInfoDialog(tk.Toplevel):
    """账户信息对话框 - 动态显示所有网络的资产信息"""
    
    # API 端点 (调试模式：使用本地测试服务器)
    #API_BASE = "http://192.168.3.227/api/v1"
    #API_BASE = "http://127.0.0.1:8001/api/v1"
    API_BASE = "https://www.aeknow.org/api/v1"  # 生产环境
    API_CHALLENGE = f"{API_BASE}/auth/challenge"
    API_VERIFY = f"{API_BASE}/auth/verify"
    API_ASSETS = f"{API_BASE}/assets/account"
    
    # Aeternity AEX2 签名前缀
    AE_PREFIX = b'aeternity Signed Message:\n'
    
    # 网络显示名称和图标映射
    NETWORK_DISPLAY = {
        'mainnet': ('🔵 主网 Mainnet', 'ae_mainnet'),
        'testnet': ('🟡 测试网 Testnet', 'ae_uat'),
        'hc_liu': ('🟢 HC Liu', 'hc_liu'),
    }
    
    def __init__(self, parent, user_manager: UserManager):
        super().__init__(parent)
        self.user_manager = user_manager
        self._api_token = None  # 缓存 API Token
        
        # 缓存数据和UI引用
        self._network_data = {}  # {network_id: data}
        self._network_ui = {}    # {network_id: {balance_var, detail_var, tree, stats_var, frame}}
        
        self.title("账户信息")
        self.geometry("1150x700")
        self.minsize(1000, 600)
        self.transient(parent)
        
        self._create_base_widgets()
        self._load_account_data()
        
        # 居中显示
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
    
    def _create_base_widgets(self):
        """创建基础UI框架"""
        self._main_frame = ttk.Frame(self, padding=15)
        self._main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 顶部：地址信息和操作按钮
        addr_frame = ttk.LabelFrame(self._main_frame, text="账户地址", padding=10)
        addr_frame.pack(fill=tk.X, pady=(0, 10))
        
        addr_row = ttk.Frame(addr_frame)
        addr_row.pack(fill=tk.X)
        self._addr_label = ttk.Label(addr_row, text=self.user_manager.address, 
                                      font=("Consolas", 10), foreground="blue")
        self._addr_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 操作按钮组（右侧）
        ttk.Button(addr_row, text="🔄 刷新", command=self._refresh_data).pack(side=tk.RIGHT, padx=5)
        ttk.Button(addr_row, text="📋 复制", command=self._copy_address).pack(side=tk.RIGHT, padx=5)
        ttk.Button(addr_row, text="🌐 浏览器查看", command=self._open_explorer).pack(side=tk.RIGHT)
        
        # 网络标签页容器
        self._notebook_frame = ttk.Frame(self._main_frame)
        self._notebook_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 初始加载提示
        self._loading_label = ttk.Label(self._notebook_frame, 
                                         text="正在加载账户数据...",
                                         font=("TkDefaultFont", 12))
        self._loading_label.pack(expand=True)
        
        # 底部状态栏
        btn_frame = ttk.Frame(self._main_frame)
        btn_frame.pack(fill=tk.X, pady=(5, 0))
        
        self._status_var = tk.StringVar(value="")
        ttk.Label(btn_frame, textvariable=self._status_var, foreground="gray").pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="关闭", command=self.destroy).pack(side=tk.RIGHT)
    
    def _refresh_data(self):
        """刷新数据 - 重新获取API并更新UI"""
        self._status_var.set("正在刷新...")
        self._load_account_data()
    
    def _safe_set_status(self, message: str):
        """安全设置状态栏（检查窗口存在）"""
        if self.winfo_exists():
            self._status_var.set(message)
    
    def _load_account_data(self):
        """从 API 加载账户数据"""
        self._status_var.set("正在加载数据...")
        
        # 异步加载
        import threading
        threading.Thread(target=self._fetch_and_update, daemon=True).start()
    
    def _get_account(self):
        """获取用户的 Account 对象"""
        wallet = self.user_manager._wallet
        if wallet is None:
            return None
        
        # 新版 MnemonicWallet 有 account 属性
        if hasattr(wallet, 'account'):
            return wallet.account
        # 旧版 LegacyWallet 有 account 属性
        if hasattr(wallet, 'account'):
            return wallet.account
        return None
    
    def _sign_challenge(self, challenge: str) -> str:
        """
        对挑战码进行签名
        
        :param challenge: 挑战码字符串
        :return: sg_xxx 格式的签名
        """
        import base58
        
        account = self._get_account()
        if not account:
            raise ValueError("无法获取账户")
        
        # Aeternity 签名格式: prefix + length(4 bytes, big-endian) + message
        message_bytes = challenge.encode('utf-8')
        length_bytes = len(message_bytes).to_bytes(4, 'big')
        full_message = self.AE_PREFIX + length_bytes + message_bytes
        
        # 调试日志
        logger.info(f"[AUTH DEBUG] Challenge length: {len(message_bytes)}")
        logger.info(f"[AUTH DEBUG] Full message (hex): {full_message.hex()}")
        
        # 签名
        signature = account.sign(full_message)
        
        # 编码为 sg_xxx 格式
        sig_encoded = "sg_" + base58.b58encode_check(signature).decode()
        logger.info(f"[AUTH DEBUG] Signature: {sig_encoded}")
        
        return sig_encoded
    
    def _get_api_token(self) -> str:
        """
        获取 API Token（签名挑战认证流程）
        
        :return: API Token
        :raises: Exception 如果认证失败
        """
        import urllib.request
        import json
        
        address = self.user_manager.address
        logger.info(f"[AUTH DEBUG] ========== 开始签名认证 ==========")
        logger.info(f"[AUTH DEBUG] Address: {address}")
        logger.info(f"[AUTH DEBUG] API Base: {self.API_BASE}")
        
        # 1. 获取挑战码
        challenge_url = f"{self.API_CHALLENGE}?address={address}"
        logger.info(f"[AUTH DEBUG] Step 1: GET {challenge_url}")
        req = urllib.request.Request(challenge_url, headers={'User-Agent': 'PyStart/1.0'})
        
        with urllib.request.urlopen(req, timeout=15) as response:
            response_text = response.read().decode('utf-8')
            logger.info(f"[AUTH DEBUG] Challenge response: {response_text}")
            result = json.loads(response_text)
        
        if not result.get('success'):
            raise ValueError(result.get('detail', '获取挑战码失败'))
        
        challenge_data = result['data']
        challenge_id = challenge_data['challenge_id']
        challenge = challenge_data['challenge']
        logger.info(f"[AUTH DEBUG] Challenge ID: {challenge_id}")
        
        # 2. 签名挑战码
        logger.info(f"[AUTH DEBUG] Step 2: Signing challenge...")
        signature = self._sign_challenge(challenge)
        
        # 3. 验证签名获取 Token
        verify_payload = {
            'challenge_id': challenge_id,
            'address': address,
            'signature': signature
        }
        verify_data = json.dumps(verify_payload).encode('utf-8')
        
        logger.info(f"[AUTH DEBUG] Step 3: POST {self.API_VERIFY}")
        logger.info(f"[AUTH DEBUG] Verify payload: {json.dumps(verify_payload, indent=2)}")
        
        req = urllib.request.Request(
            self.API_VERIFY,
            data=verify_data,
            headers={
                'User-Agent': 'PyStart/1.0',
                'Content-Type': 'application/json'
            },
            method='POST'
        )
        
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                response_text = response.read().decode('utf-8')
                logger.info(f"[AUTH DEBUG] Verify response: {response_text}")
                result = json.loads(response_text)
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else 'No body'
            logger.error(f"[AUTH DEBUG] HTTP Error {e.code}: {error_body}")
            raise ValueError(f"HTTP {e.code}: {error_body}")
        
        if not result.get('success'):
            error_detail = result.get('detail', '签名验证失败')
            logger.error(f"[AUTH DEBUG] Verify failed: {error_detail}")
            raise ValueError(error_detail)
        
        api_token = result['data']['api_token']
        logger.info(f"[AUTH DEBUG] ========== 认证成功 ==========")
        logger.info(f"[AUTH DEBUG] API Token: {api_token[:20]}...")
        return api_token
    
    def _fetch_and_update(self):
        """获取数据并更新 UI"""
        import urllib.request
        import json
        
        address = self.user_manager.address
        
        try:
            # 1. 先获取 API Token（如果没有缓存）
            if not self._api_token:
                self.after(0, lambda: self._safe_set_status("正在进行签名认证..."))
                self._api_token = self._get_api_token()
            
            # 2. 用 Token 访问 API
            self.after(0, lambda: self._safe_set_status("正在获取资产数据..."))
            api_url = f"{self.API_ASSETS}/{address}"
            req = urllib.request.Request(
                api_url, 
                headers={
                    'User-Agent': 'PyStart/1.0',
                    'Authorization': f'Bearer {self._api_token}'
                }
            )
            
            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            if data.get('success'):
                # 获取所有有数据的网络
                networks_data = data.get('data', {})
                self._network_data = networks_data
                
                # 在主线程更新UI
                self.after(0, lambda: self._rebuild_network_tabs(networks_data))
                self.after(0, lambda: self._safe_set_status(f"数据已更新 ({len(networks_data)} 个网络)"))
            else:
                error_msg = data.get('detail', data.get('message', '未知错误'))
                # Token 可能已过期，清除缓存
                if 'token' in error_msg.lower() or 'auth' in error_msg.lower():
                    self._api_token = None
                self.after(0, lambda: self._show_error(f"API 错误: {error_msg}"))
                
        except Exception as e:
            error_msg = str(e)[:80]
            # Token 相关错误清除缓存
            if 'token' in error_msg.lower() or 'auth' in error_msg.lower() or '401' in error_msg:
                self._api_token = None
            self.after(0, lambda: self._show_error(f"加载失败: {error_msg}"))
    
    def _show_error(self, message: str):
        """显示错误信息"""
        # 检查窗口是否仍然存在
        if not self.winfo_exists():
            return
        self._status_var.set(message)
        # 清空notebook并显示错误
        for widget in self._notebook_frame.winfo_children():
            widget.destroy()
        ttk.Label(self._notebook_frame, text=f"❌ {message}", 
                  foreground="red", font=("TkDefaultFont", 11)).pack(expand=True)
    
    def _rebuild_network_tabs(self, networks_data: dict):
        """根据数据重建网络标签页"""
        # 检查窗口是否仍然存在
        if not self.winfo_exists():
            return
        # 清空现有标签页
        for widget in self._notebook_frame.winfo_children():
            widget.destroy()
        self._network_ui.clear()
        
        # 过滤有效网络（有AE余额或有Token的网络）
        valid_networks = []
        for network_id, data in networks_data.items():
            ae_data = data.get('ae', {})
            tokens = data.get('tokens', [])
            balance = ae_data.get('balance_ae', 0) or 0
            
            # 只有有余额或有Token的网络才显示
            if balance > 0 or len(tokens) > 0:
                valid_networks.append((network_id, data))
        
        if not valid_networks:
            ttk.Label(self._notebook_frame, text="该账户在所有网络上暂无资产", 
                      font=("TkDefaultFont", 11)).pack(expand=True)
            return
        
        # 创建Notebook
        notebook = ttk.Notebook(self._notebook_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # 网络排序优先级
        network_order = ['mainnet', 'testnet', 'hc_liu']
        
        def sort_key(item):
            network_id = item[0]
            if network_id in network_order:
                return network_order.index(network_id)
            return 999  # 未知网络排在最后
        
        valid_networks.sort(key=sort_key)
        
        # 为每个有效网络创建标签页
        for network_id, data in valid_networks:
            self._create_network_tab(notebook, network_id, data)
    
    def _get_network_display_name(self, network_id: str) -> str:
        """获取网络的显示名称"""
        if network_id in self.NETWORK_DISPLAY:
            return self.NETWORK_DISPLAY[network_id][0]
        # 未知网络，使用ID生成名称
        return f"🔘 {network_id.replace('_', ' ').title()}"
    
    def _create_network_tab(self, notebook: ttk.Notebook, network_id: str, data: dict):
        """创建单个网络的标签页"""
        frame = ttk.Frame(notebook, padding=10)
        display_name = self._get_network_display_name(network_id)
        notebook.add(frame, text=f" {display_name} ")
        
        # 网络信息（如果有）
        network_info = data.get('network', {})
        if network_info:
            info_text = network_info.get('name', network_id)
            ttk.Label(frame, text=f"网络: {info_text}", foreground="gray").pack(anchor=tk.W)
        
        # AE 余额区域
        ae_frame = ttk.LabelFrame(frame, text="💰 主币余额", padding=10)
        ae_frame.pack(fill=tk.X, pady=(5, 10))
        
        balance_row = ttk.Frame(ae_frame)
        balance_row.pack(fill=tk.X)
        
        ae_data = data.get('ae', {})
        balance_ae = ae_data.get('balance_ae', 0) or 0
        symbol = ae_data.get('symbol', 'AE')
        nonce = ae_data.get('nonce', 0)
        
        balance_var = tk.StringVar(value=f"{balance_ae:,.6f} {symbol}")
        ttk.Label(balance_row, textvariable=balance_var, 
                  font=("TkDefaultFont", 16, "bold")).pack(side=tk.LEFT)
        
        detail_var = tk.StringVar(value=f"Nonce: {nonce}")
        ttk.Label(balance_row, textvariable=detail_var, foreground="gray").pack(side=tk.LEFT, padx=15)
        
        # Token 列表区域
        tokens = data.get('tokens', [])
        
        token_frame = ttk.LabelFrame(frame, text=f"🪙 Token 资产 ({len(tokens)})", padding=10)
        token_frame.pack(fill=tk.BOTH, expand=True)
        
        if tokens:
            # 创建 Treeview
            columns = ('symbol', 'name', 'balance', 'verified')
            tree = ttk.Treeview(token_frame, columns=columns, show='headings', height=12)
            
            tree.heading('symbol', text='Symbol')
            tree.heading('name', text='Token Name')
            tree.heading('balance', text='Balance')
            tree.heading('verified', text='状态')
            
            tree.column('symbol', width=80, anchor=tk.CENTER)
            tree.column('name', width=200, anchor=tk.W)
            tree.column('balance', width=180, anchor=tk.E)
            tree.column('verified', width=80, anchor=tk.CENTER)
            
            scrollbar = ttk.Scrollbar(token_frame, orient=tk.VERTICAL, command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # 填充Token数据
            self._populate_tokens(tree, tokens)
            
            # 统计信息
            verified_count = sum(1 for t in tokens if t.get('verified', False))
            stats_var = tk.StringVar(value=f"共 {len(tokens)} 种 Token，其中 {verified_count} 种已验证")
            ttk.Label(frame, textvariable=stats_var, foreground="gray").pack(anchor=tk.W, pady=(5, 0))
        else:
            ttk.Label(token_frame, text="暂无 Token 资产", foreground="gray").pack(expand=True)
        
        # 保存UI引用
        self._network_ui[network_id] = {
            'frame': frame,
            'balance_var': balance_var,
            'detail_var': detail_var,
        }
    
    def _populate_tokens(self, tree: ttk.Treeview, tokens: list):
        """填充Token列表数据"""
        # 按 verified 排序（verified 在前），然后按余额排序
        sorted_tokens = sorted(tokens, key=lambda t: (not t.get('verified', False), -float(t.get('balance', 0))))
        
        for token in sorted_tokens:
            symbol = token.get('symbol', 'Unknown')
            name = token.get('name', 'Unknown')
            balance = token.get('balance', 0)
            decimals = token.get('decimals', 18)
            verified = token.get('verified', False)
            
            # 格式化余额
            try:
                balance_num = float(balance) / (10 ** decimals)
                if balance_num >= 1e9:
                    balance_str = f"{balance_num:.2e}"
                elif balance_num >= 1000000:
                    balance_str = f"{balance_num:,.0f}"
                elif balance_num >= 1:
                    balance_str = f"{balance_num:,.4f}"
                else:
                    balance_str = f"{balance_num:.8f}"
            except:
                balance_str = str(balance)
            
            status = "✅ 已验证" if verified else "⚪ 未验证"
            tree.insert('', tk.END, values=(symbol, name, balance_str, status))
    
    def _copy_address(self):
        """复制地址"""
        self.clipboard_clear()
        self.clipboard_append(self.user_manager.address)
        self.update()
        messagebox.showinfo("复制成功", "地址已复制到剪贴板", parent=self)
    
    def _open_explorer(self):
        """在浏览器中打开账户详情"""
        import webbrowser
        url = f"https://www.aeknow.org/address/wallet/{self.user_manager.address}"
        webbrowser.open(url)


class UserSystemAboutDialog(tk.Toplevel):
    """用户系统介绍对话框"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.title("用户系统介绍")
        self.geometry("700x650")
        self.resizable(False, False)
        self.transient(parent)
        
        self._create_widgets()
        
        # 居中显示
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
    
    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(title_frame, text="👤 PyStart 用户系统", 
                  font=("TkDefaultFont", 16, "bold")).pack(side=tk.LEFT)
        ttk.Label(title_frame, text="去中心化身份管理", 
                  foreground="gray").pack(side=tk.LEFT, padx=10)
        
        # 内容区域（可滚动）
        self._canvas = tk.Canvas(main_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self._canvas.yview)
        scrollable_frame = ttk.Frame(self._canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all"))
        )
        
        self._canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        self._canvas.configure(yscrollcommand=scrollbar.set)
        
        # 鼠标滚轮支持（只绑定到窗口和canvas，不用bind_all）
        self._canvas.bind("<MouseWheel>", self._on_mousewheel)
        self._canvas.bind("<Enter>", lambda e: self._canvas.focus_set())
        self.bind("<MouseWheel>", self._on_mousewheel)
        
        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 填充内容
        self._create_content(scrollable_frame)
        
        # 底部按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(15, 0))
        
        ttk.Button(btn_frame, text="了解更多", command=self._open_docs).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="关闭", command=self.destroy).pack(side=tk.RIGHT)
    
    def _on_mousewheel(self, event):
        """鼠标滚轮事件"""
        if self.winfo_exists() and self._canvas.winfo_exists():
            self._canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def _create_content(self, parent):
        """创建介绍内容"""
        
        # === 什么是用户系统 ===
        self._add_section(parent, "🌟 什么是用户系统？", [
            "PyStart 用户系统是一个基于区块链技术的去中心化身份管理系统。",
            "",
            "• 您的身份由 12 个助记词生成，完全由您掌控",
            "• 无需注册账号、无需验证手机或邮箱",
            "• 没有中心服务器，无法被封禁或审查",
            "• 助记词是您身份的唯一凭证，请妥善保管",
        ])
        
        # === 核心功能 ===
        self._add_section(parent, "🛠️ 核心功能", [
            "▶ 身份管理",
            "   创建、导入、导出和备份您的数字身份",
            "",
            "▶ 账户信息",
            "   查看多链资产余额（主网、测试网等）",
            "",
            "▶ 代码签名",
            "   为代码添加数字签名，证明代码来源和完整性",
            "",
            "▶ 消息签名",
            "   用于网站登录或身份验证的数字签名",
            "",
            "▶ 消息加密",
            "   端到端加密通信，只有收件人能解密",
        ])
        
        # === 安全说明 ===
        self._add_section(parent, "🔒 安全说明", [
            "• 助记词是您身份的唯一凭证，丢失无法找回",
            "• 请用纸笔抷写助记词，不要截图或存在电脑",
            "• 不要将助记词告诉任何人，包括 PyStart 开发者",
            "• Keystore 文件可以备份，但需配合密码使用",
            "• 建议在备份助记词后设置一个强密码",
        ])
        
        # === 技术特点 ===
        self._add_section(parent, "⚙️ 技术特点", [
            "• BIP39 助记词标准，兼容主流钱包",
            "• ED25519 签名算法，安全高效",
            "• X25519 加密算法，端到端加密",
            "• Blake2b 哈希算法，快速可靠",
            "• 本地存储，数据不上传",
        ])
        
        # === 常见问答 ===
        self._add_section(parent, "❓ 常见问答", [
            "Q: 忘记密码怎么办？",
            "A: 如果有助记词，可以删除当前用户后重新导入",
            "",
            "Q: 助记词丢失了怎么办？",
            "A: 无法找回，这是去中心化的代价。请务必备份！",
            "",
            "Q: 可以在其他设备上使用同一身份吗？",
            "A: 可以，通过助记词或 Keystore 文件导入即可",
        ])
        
        # === 关于 ===
        about_frame = ttk.Frame(parent)
        about_frame.pack(fill=tk.X, pady=(15, 5), padx=5)
        
        ttk.Label(about_frame, 
                  text="PyStart 用户系统基于 Aeternity 区块链技术",
                  foreground="gray").pack(anchor=tk.W)
        ttk.Label(about_frame, 
                  text="\"信任来自密码学，而非平台\" - PyStart",
                  foreground="gray", font=("TkDefaultFont", 9, "italic")).pack(anchor=tk.W, pady=(5, 0))
    
    def _add_section(self, parent, title: str, lines: list):
        """添加一个内容区块"""
        frame = ttk.LabelFrame(parent, text=title, padding=10)
        frame.pack(fill=tk.X, pady=(0, 10), padx=5)
        
        for line in lines:
            if line == "":
                ttk.Label(frame, text="").pack(anchor=tk.W)  # 空行
            else:
                ttk.Label(frame, text=line, wraplength=600, justify=tk.LEFT).pack(anchor=tk.W)
    
    def _open_docs(self):
        """打开文档页面"""
        import webbrowser
        webbrowser.open("https://github.com/AEKnow/PyStart")


# 全局 UI 实例
_user_ui = None


def load_plugin():
    """插件加载入口"""
    global _user_ui
    
    def setup_ui():
        global _user_ui
        _user_ui = UserSystemUI()
        _user_ui.setup_toolbar_button()
    
    # 在 workbench 准备好后设置 UI
    get_workbench().bind("WorkbenchReady", lambda e: setup_ui(), True)

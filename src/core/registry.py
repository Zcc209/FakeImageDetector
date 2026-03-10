# src/core/registry.py

# 儲存所有註冊模組的字典
_MODULES = {}

def register_module(name: str):
    """
    模組註冊裝飾器。
    B組與C組只要在他們的函數上方加上 @register_module("名稱")，
    系統就會自動把它加進註冊表，完全不需要去 main.py 裡面改 import。
    """
    def decorator(func):
        _MODULES[name] = func
        return func
    return decorator

def get_module(name: str):
    """透過名稱從註冊表中取出模組函數"""
    if name not in _MODULES:
        raise ValueError(f"⚠️ 模組 '{name}' 尚未註冊！請檢查是否有 import 該模組。")
    return _MODULES[name]

def list_modules() -> list:
    """列出目前已註冊的所有模組 (Debug 用)"""
    return list(_MODULES.keys())
# 交通違規檢舉自動化工具

這是一個用於台中市交通違規檢舉的自動化工具，支援自動驗證碼識別、表單自動填寫和檔案上傳。

> ⚠️ 溫馨警示
> 
> 本工具為 **高度客製化的自動化工具**，目前仍處於開發/測試階段。  
> **不建議個人使用**


## 系統需求

- Python 3.9+
- Tesseract OCR 引擎

## 專案結構
```
TrafficViolaction-Push/
├── traffic_violation/          # 核心模組
│   ├── __init__.py            # 模組初始化
│   ├── core.py                # 主要功能實作
│   ├── models.py              # 資料模型
│   └── exceptions.py          # 自訂例外
├── examples/                   # 使用範例
│   └── standalone.py          # CLI 範例
├── debug_ocr.py               # OCR 除錯工具
└── README.md                  # 說明文件
```

## 安裝說明

### 1. 安裝 Tesseract OCR

#### Arch Linux
```bash
sudo pacman -S tesseract tesseract-data-chi_tra
```

#### Ubuntu/Debian
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-chi-tra
```

#### macOS
```bash
brew install tesseract tesseract-lang
```

### 2. 安裝 Python 套件

使用 uv（推薦）：
```bash
uv sync
```

或使用 pip：
```bash
pip install -e .
```

## How to simple use

```bash
uv run python examples/standalone.py
```

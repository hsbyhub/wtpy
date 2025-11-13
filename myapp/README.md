# MyApp - WonderTrader Python 量化交易应用

## 快速开始

### 前置要求

- Python >= 3.8
- [uv](https://github.com/astral-sh/uv) (推荐) 或 pip

### 安装 uv (如果还没有)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# 或使用 Homebrew
brew install uv
```

## 初始化项目（仅安装依赖，不打包）

### 方法一：使用 uv（推荐）

```bash
# 1. 克隆或进入项目目录
cd myapp

# 2. 创建虚拟环境
uv venv

# 3. 激活虚拟环境
source .venv/bin/activate  # macOS/Linux
# 或 .venv\Scripts\activate  # Windows

# 4. 安装依赖（使用国内镜像源加速）
uv pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 5. 验证安装
python src/main.py --help
```

### 方法二：使用标准 venv + pip

```bash
# 1. 进入项目目录
cd myapp

# 2. 创建虚拟环境
python3 -m venv .venv

# 3. 激活虚拟环境
source .venv/bin/activate

# 4. 升级 pip
pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple

# 5. 安装依赖
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 6. 验证安装
python src/main.py --help
```

## 一键初始化脚本

项目根目录提供了 `setup.sh` 脚本，可以直接运行：

```bash
chmod +x setup.sh
./setup.sh
```

## 使用项目

### 运行回测

```bash
python src/main.py cta_stk_bt
```

### 下载K线数据

```bash
# 下载5分钟K线数据
python src/main.py download_bars --code="SSE.STK.600008" --period="min5"

# 下载日线数据
python src/main.py download_bars --code="SSE.STK.600008" --period="day"
```

### 查看帮助

```bash
python src/main.py --help
python src/main.py download_bars --help
```

## 项目结构

```
myapp/
├── src/                    # 源代码目录
│   ├── main.py            # 主程序入口
│   ├── common/            # 配置文件目录
│   └── strategy/          # 策略目录
├── requirements.txt        # Python 依赖列表
├── pyproject.toml         # 项目配置（用于打包，可选）
└── README.md              # 本文件
```

## 常见问题

### 1. 虚拟环境找不到 Python

```bash
# 删除旧环境重新创建
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
```

### 2. 安装依赖很慢

使用国内镜像源：
```bash
uv pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 3. wtpy 安装失败

如果 `wtpy` 不在 PyPI 上，需要从本地安装：
```bash
# 先安装其他依赖
pip install -r requirements.txt --no-deps

# 然后从父目录安装 wtpy
pip install -e ../  # 在 wtpy 项目根目录执行
```

## 开发环境设置（可选）

如果需要开发工具（测试、格式化等）：

```bash
# 使用 uv
uv pip install -e ".[dev]"

# 或使用 pip
pip install -e ".[dev]"
```

## 注意事项

- 本项目**不需要打包**，直接运行 `python src/main.py` 即可
- 虚拟环境目录 `.venv/` 已添加到 `.gitignore`，不会提交到 Git
- 数据文件（`storage/`, `outputs/`）也不会提交到 Git


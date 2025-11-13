import os
import sys

def silence_output():
    # 打开 /dev/null
    devnull_fd = os.open(os.devnull, os.O_RDWR)

    # 将 fd 1(stdout) 和 fd 2(stderr) 重定向到 /dev/null
    os.dup2(devnull_fd, 1)
    os.dup2(devnull_fd, 2)

    # 可选：替换 Python 层的 sys.stdout/sys.stderr，避免 Python 层缓冲等问题
    import io
    sys.stdout = io.TextIOWrapper(os.fdopen(1, "wb"), encoding="utf-8", line_buffering=True)
    sys.stderr = io.TextIOWrapper(os.fdopen(2, "wb"), encoding="utf-8", line_buffering=True)

    # 可选：如果使用 logging 模块，禁用或设置更高等级
    import logging
    logging.getLogger().handlers = []
    logging.getLogger().setLevel(logging.CRITICAL + 1)
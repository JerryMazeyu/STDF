import os
import sys
import signal
import logging
from app import run_server

def signal_handler(signum, frame):
    """处理退出信号"""
    logging.info("正在关闭服务器...")
    sys.exit(0)

if __name__ == "__main__":
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 运行服务器
        run_server()
    except KeyboardInterrupt:
        logging.info("服务器被用户中断")
    except Exception as e:
        logging.error(f"服务器异常退出: {str(e)}")
        sys.exit(1) 
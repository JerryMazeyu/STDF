import sys
import os
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QThread
from App.views.main_window import MainWindow

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def exception_hook(exctype, value, traceback):
    """捕获未处理的异常"""
    logger.error('未捕获的异常:', exc_info=(exctype, value, traceback))
    sys.__excepthook__(exctype, value, traceback)

def main():
    try:
        # 设置异常钩子
        sys.excepthook = exception_hook
        
        # 设置高DPI支持
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
        
        # 创建应用实例
        app = QApplication(sys.argv)
        
        # 设置应用样式
        app.setStyle('Fusion')
        
        # 创建主窗口
        logger.info("正在启动主窗口...")
        window = MainWindow()
        window.show()
        
        logger.info("应用程序启动完成")
        sys.exit(app.exec_())
        
    except Exception as e:
        logger.error(f"应用程序启动失败: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main() 
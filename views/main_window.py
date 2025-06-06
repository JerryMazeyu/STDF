import sys
import os
import logging
import time
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, 
                            QVBoxLayout, QPushButton, QStackedWidget, QProgressBar,
                            QLabel, QSplashScreen, QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QPalette, QColor, QPixmap

# 添加父目录到系统路径
current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.dirname(os.path.dirname(current_dir))
if app_dir not in sys.path:
    sys.path.append(app_dir)

from App.views.tabs.tab1 import Tab1Widget
from App.views.tabs.tab2 import Tab2Widget
from App.views.tabs.tab3 import Tab3Widget
from App.views.tabs.tab4 import Tab4Widget
from App.utils.api_client import APIClient

logger = logging.getLogger(__name__)

class LoadingThread(QThread):
    """加载线程"""
    progress = pyqtSignal(int)
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, api_client):
        super().__init__()
        self.api_client = api_client
        self.max_retries = 3
        self.retry_delay = 2  # 秒
        
    def check_server_connection(self) -> bool:
        """检查服务器连接"""
        retries = 0
        while retries < self.max_retries:
            try:
                response = self.api_client.get_pid()
                if response['status'] == 'success':
                    logger.info(f"成功连接到服务器，PID: {response.get('pid')}")
                    return True
                else:
                    logger.warning(f"服务器返回错误: {response.get('message')}")
            except Exception as e:
                logger.warning(f"连接服务器失败 (尝试 {retries + 1}/{self.max_retries}): {str(e)}")
            
            retries += 1
            if retries < self.max_retries:
                time.sleep(self.retry_delay)
                
        return False
        
    def run(self):
        try:
            # 检查后端服务器连接
            self.progress.emit(20)
            if not self.check_server_connection():
                raise Exception("无法连接到后端服务器")
            
            # 检查系统资源
            self.progress.emit(40)
            response = self.api_client.get_cpu_usage()
            if response['status'] == 'success':
                logger.info(f"CPU使用率: {response.get('cpu_percent')}%")
            
            # 检查GPU状态
            self.progress.emit(60)
            response = self.api_client.get_gpu_usage()
            if response['status'] == 'success':
                logger.info(f"GPU状态: {response.get('gpu_info')}")
            
            # 检查静态数据
            self.progress.emit(80)
            response = self.api_client.get_static_data()
            if response['status'] == 'success':
                logger.info(f"找到 {len(response.get('data', []))} 个图像文件")
            
            # 完成初始化
            self.progress.emit(100)
            self.finished.emit()
            
        except Exception as e:
            logger.error(f"初始化失败: {str(e)}", exc_info=True)
            self.error.emit(str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.api_client = APIClient(max_retries=3)  # 设置API客户端重试次数
        self.initUI()
        
    def initUI(self):
        # 设置窗口标题和大小
        self.setWindowTitle('残余物检测系统')
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建主窗口部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # 主布局
        main_layout = QVBoxLayout(main_widget)
        
        # 导航按钮布局
        nav_layout = QHBoxLayout()
        
        # 创建导航按钮
        self.tab1_btn = QPushButton("特征提取")
        self.tab2_btn = QPushButton("特征图")
        self.tab3_btn = QPushButton("图片管理")
        self.tab4_btn = QPushButton("残余物检测")
        
        # 设置按钮样式和尺寸
        for btn in [self.tab1_btn, self.tab2_btn, self.tab3_btn, self.tab4_btn]:
            btn.setMinimumSize(120, 40)
            btn.setStyleSheet("QPushButton { font-size: 14px; }")
            btn.setEnabled(False)  # 初始禁用按钮
        
        # 将按钮添加到导航布局
        nav_layout.addWidget(self.tab1_btn)
        nav_layout.addWidget(self.tab2_btn)
        nav_layout.addWidget(self.tab3_btn)
        nav_layout.addWidget(self.tab4_btn)
        nav_layout.addStretch()
        
        # 创建堆叠部件用于页面切换
        self.stacked_widget = QStackedWidget()
        
        # 创建加载页面
        self.loading_page = QWidget()
        loading_layout = QVBoxLayout(self.loading_page)
        loading_layout.addStretch()
        
        # 添加加载提示
        self.loading_label = QLabel("正在初始化...")
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setStyleSheet("font-size: 16px;")
        loading_layout.addWidget(self.loading_label)
        
        # 添加进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        loading_layout.addWidget(self.progress_bar)
        
        # 添加重试按钮（初始隐藏）
        self.retry_btn = QPushButton("重试")
        self.retry_btn.clicked.connect(self.retry_initialization)
        self.retry_btn.hide()
        loading_layout.addWidget(self.retry_btn)
        
        loading_layout.addStretch()
        
        # 将加载页面添加到堆叠部件
        self.stacked_widget.addWidget(self.loading_page)
        
        # 将导航布局和堆叠部件添加到主布局
        main_layout.addLayout(nav_layout)
        main_layout.addWidget(self.stacked_widget)
        
        # 启动加载线程
        self.start_initialization()
        
    def start_initialization(self):
        """启动初始化过程"""
        self.loading_thread = LoadingThread(self.api_client)
        self.loading_thread.progress.connect(self.update_progress)
        self.loading_thread.finished.connect(self.init_tabs)
        self.loading_thread.error.connect(self.show_error)
        self.loading_thread.start()
        self.retry_btn.hide()
        self.loading_label.setText("正在初始化...")
        self.loading_label.setStyleSheet("font-size: 16px;")
        
    def retry_initialization(self):
        """重试初始化"""
        self.start_initialization()
        
    def update_progress(self, value):
        """更新进度条"""
        self.progress_bar.setValue(value)
        
    def show_error(self, message):
        """显示错误信息"""
        self.loading_label.setText(f"错误: {message}")
        self.loading_label.setStyleSheet("font-size: 16px; color: red;")
        self.retry_btn.show()
        
        # 显示错误对话框
        QMessageBox.warning(
            self,
            "初始化错误",
            f"初始化过程中出现错误：\n{message}\n\n请检查后端服务器是否正在运行。"
        )
        
    def init_tabs(self):
        """初始化标签页"""
        try:
            logger.info("正在初始化标签页...")
            
            # 创建标签页
            self.tab1 = Tab1Widget()
            self.tab2 = Tab2Widget()
            self.tab3 = Tab3Widget()
            self.tab4 = Tab4Widget()
            
            # 连接Tab1和Tab2的信号
            self.tab1.analysis_started.connect(self.on_analysis_started)
            self.tab1.analysis_completed.connect(self.on_analysis_completed)
            
            # 将标签页添加到堆叠部件
            self.stacked_widget.addWidget(self.tab1)
            self.stacked_widget.addWidget(self.tab2)
            self.stacked_widget.addWidget(self.tab3)
            self.stacked_widget.addWidget(self.tab4)
            
            # 连接按钮信号到槽函数
            self.tab1_btn.clicked.connect(self.show_tab1)
            self.tab2_btn.clicked.connect(self.show_tab2)
            self.tab3_btn.clicked.connect(self.show_tab3)
            self.tab4_btn.clicked.connect(self.show_tab4)
            
            # 启用按钮
            for btn in [self.tab1_btn, self.tab2_btn, self.tab3_btn, self.tab4_btn]:
                btn.setEnabled(True)
            
            # 显示第一个标签页
            self.show_tab1()
            logger.info("标签页初始化完成")
            
        except Exception as e:
            logger.error(f"标签页初始化失败: {str(e)}", exc_info=True)
            self.show_error(f"标签页初始化失败: {str(e)}")
    
    def show_tab1(self):
        self.stacked_widget.setCurrentWidget(self.tab1)
        self.update_button_styles(self.tab1_btn)
    
    def show_tab2(self):
        self.stacked_widget.setCurrentWidget(self.tab2)
        self.update_button_styles(self.tab2_btn)
    
    def show_tab3(self):
        self.stacked_widget.setCurrentWidget(self.tab3)
        self.update_button_styles(self.tab3_btn)
    
    def show_tab4(self):
        self.stacked_widget.setCurrentWidget(self.tab4)
        self.update_button_styles(self.tab4_btn)
    
    def update_button_styles(self, active_btn):
        """更新按钮样式"""
        for btn in [self.tab1_btn, self.tab2_btn, self.tab3_btn, self.tab4_btn]:
            if btn == active_btn:
                btn.setStyleSheet(
                    "QPushButton { background-color: #4CAF50; color: white; font-size: 14px; }"
                )
            else:
                btn.setStyleSheet("QPushButton { font-size: 14px; }")
    
    def on_analysis_started(self, image_path):
        """当开始分析图像时切换到Tab2"""
        self.show_tab2()
    
    def on_analysis_completed(self, features):
        """当分析完成时更新特征图"""
        self.tab2.update_feature_maps(features)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

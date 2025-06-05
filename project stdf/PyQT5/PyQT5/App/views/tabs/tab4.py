from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                           QLabel, QPushButton, QListWidget, QFileDialog,
                           QSplitter, QFrame, QComboBox, QProgressBar,
                           QMessageBox, QGroupBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap
import os
from datetime import datetime
from ...utils.api_client import APIClient
import time

class Tab4Widget(QWidget):
    def __init__(self):
        super().__init__()
        self.api_client = APIClient()
        self.current_image = None
        self.image_series = []
        self.last_alert_check = 0  # 上次检查报警的时间
        self.alert_check_interval = 5  # 报警检查间隔（秒）
        self.initUI()
        
    def initUI(self):
        # 创建主布局
        main_layout = QVBoxLayout(self)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧面板 - 图片列表和控制
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # 图片导入控制
        import_group = QGroupBox("图片导入")
        import_layout = QVBoxLayout(import_group)
        
        # 添加图片按钮
        self.import_btn = QPushButton('导入图片')
        self.import_btn.clicked.connect(self.import_images)
        import_layout.addWidget(self.import_btn)
        
        # 图片列表
        self.image_list = QListWidget()
        self.image_list.itemClicked.connect(self.show_image)
        import_layout.addWidget(self.image_list)
        
        left_layout.addWidget(import_group)
        
        # 模型控制
        model_group = QGroupBox("模型控制")
        model_layout = QVBoxLayout(model_group)
        
        # 模型选择
        self.model_combo = QComboBox()
        self.model_combo.addItems(['模型1', '模型2', '模型3'])
        model_layout.addWidget(self.model_combo)
        
        # 检测按钮
        self.detect_btn = QPushButton('执行检测')
        self.detect_btn.clicked.connect(self.run_detection)
        model_layout.addWidget(self.detect_btn)
        
        # 趋势预测按钮
        self.trend_btn = QPushButton('趋势预测')
        self.trend_btn.clicked.connect(self.run_trend_prediction)
        model_layout.addWidget(self.trend_btn)
        
        left_layout.addWidget(model_group)
        
        # 中间面板 - 图片显示
        middle_panel = QWidget()
        middle_layout = QVBoxLayout(middle_panel)
        
        # 图片显示区域
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(500, 400)
        middle_layout.addWidget(self.image_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        middle_layout.addWidget(self.progress_bar)
        
        # 右侧面板 - 结果显示
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # 检测结果
        result_group = QGroupBox("检测结果")
        result_layout = QVBoxLayout(result_group)
        
        self.result_label = QLabel("等待检测...")
        result_layout.addWidget(self.result_label)
        
        right_layout.addWidget(result_group)
        
        # 趋势预测结果
        trend_group = QGroupBox("趋势预测")
        trend_layout = QVBoxLayout(trend_group)
        
        self.trend_label = QLabel("等待预测...")
        trend_layout.addWidget(self.trend_label)
        
        right_layout.addWidget(trend_group)
        
        # 系统监控
        monitor_group = QGroupBox("系统监控")
        monitor_layout = QVBoxLayout(monitor_group)
        
        self.pid_label = QLabel("PID: --")
        self.cpu_label = QLabel("CPU: --")
        self.gpu_label = QLabel("GPU: --")
        
        monitor_layout.addWidget(self.pid_label)
        monitor_layout.addWidget(self.cpu_label)
        monitor_layout.addWidget(self.gpu_label)
        
        right_layout.addWidget(monitor_group)
        
        # 添加面板到分割器
        splitter.addWidget(left_panel)
        splitter.addWidget(middle_panel)
        splitter.addWidget(right_panel)
        
        # 设置分割器的初始大小
        splitter.setSizes([200, 500, 200])
        
        # 将分割器添加到主布局
        main_layout.addWidget(splitter)
        
        # 设置定时器更新系统监控信息
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_system_info)
        self.timer.start(2000)  # 每2秒更新一次
        
    def import_images(self):
        """导入图片"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择图片",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        
        if files:
            self.image_list.clear()
            self.image_series = files
            for file_path in files:
                self.image_list.addItem(os.path.basename(file_path))
    
    def show_image(self, item):
        """显示选中的图片"""
        for image_path in self.image_series:
            if os.path.basename(image_path) == item.text():
                self.current_image = image_path
                pixmap = QPixmap(image_path)
                scaled_pixmap = pixmap.scaled(
                    self.image_label.width() - 20,
                    self.image_label.height() - 20,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.image_label.setPixmap(scaled_pixmap)
                break
    
    def run_detection(self):
        """执行残余物检测"""
        if not self.current_image:
            QMessageBox.warning(self, "警告", "请先选择图片！")
            return
            
        try:
            # 执行检测
            response = self.api_client.inference(
                self.current_image,
                self.model_combo.currentText()
            )
            
            if response['status'] == 'success':
                results = response['results']
                result_text = f"检测结果：{'有' if results['detected'] else '无'}残余物\n"
                result_text += f"置信度：{results['confidence']:.2%}"
                self.result_label.setText(result_text)
            else:
                raise Exception(response['message'])
                
        except Exception as e:
            QMessageBox.warning(self, "错误", f"检测失败：{str(e)}")
    
    def run_trend_prediction(self):
        """执行趋势预测"""
        if len(self.image_series) < 2:
            QMessageBox.warning(self, "警告", "趋势预测需要至少2张图片！")
            return
            
        try:
            # 执行趋势预测
            response = self.api_client.check_trend(self.image_series)
            
            if response['status'] == 'success':
                result = response['result']
                trend_text = f"褶皱状态：{'扩大' if result['expanding'] else '稳定'}\n"
                trend_text += f"变化率：{result['rate']:.2%}"
                self.trend_label.setText(trend_text)
            else:
                raise Exception(response['message'])
                
        except Exception as e:
            QMessageBox.warning(self, "错误", f"预测失败：{str(e)}")
    
    def update_system_info(self):
        """更新系统监控信息"""
        try:
            current_time = time.time()
            
            # 获取PID（只在第一次获取）
            if not hasattr(self, 'pid_cached'):
                pid_response = self.api_client.get_pid()
                if pid_response['status'] == 'success':
                    self.pid_label.setText(f"PID: {pid_response['pid']}")
                    self.pid_cached = True
            
            # 获取CPU使用率
            cpu_response = self.api_client.get_cpu_usage()
            if cpu_response['status'] == 'success':
                self.cpu_label.setText(f"CPU: {cpu_response['cpu_percent']}%")
            
            # 获取GPU使用率
            gpu_response = self.api_client.get_gpu_usage()
            if gpu_response['status'] == 'success':
                gpu_info = gpu_response['gpu_info']
                self.gpu_label.setText(
                    f"GPU: {gpu_info['gpu_percent']}% "
                    f"({gpu_info['memory_used']}MB)"
                )
            
            # 每5秒检查一次报警状态
            if current_time - self.last_alert_check >= self.alert_check_interval:
                alert_response = self.api_client.check_alert()
                if alert_response['status'] == 'success':
                    alert_info = alert_response['alert_info']
                    if alert_info['alert']:
                        QMessageBox.warning(self, "警告", f"系统报警：{alert_info['reason']}")
                self.last_alert_check = current_time
                    
        except Exception as e:
            print(f"更新系统信息失败：{str(e)}")
            
    def showEvent(self, event):
        """当标签页显示时启动定时器"""
        super().showEvent(event)
        self.timer.start(2000)  # 每2秒更新一次
        
    def hideEvent(self, event):
        """当标签页隐藏时停止定时器"""
        super().hideEvent(event)
        self.timer.stop()  # 停止更新

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    window = Tab4Widget()
    window.show()
    sys.exit(app.exec_()) 
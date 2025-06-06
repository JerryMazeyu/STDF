import sys
import psutil
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QLabel, QFrame, QGridLayout, QSizePolicy)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QImage, QPainter, QColor, QBrush
import numpy as np

class Tab2Widget(QWidget):
    def __init__(self):
        super().__init__()
        self.monitoring = False
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_monitoring)
        self.initUI()
        
    def initUI(self):
        # 主布局
        main_layout = QVBoxLayout(self)
        
        # 创建内容区域布局
        content_layout = QHBoxLayout()
        
        # 左侧信息面板
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # 系统信息显示
        info_frame = QFrame()
        info_frame.setFrameShape(QFrame.Box)
        info_frame.setLineWidth(1)
        info_layout = QVBoxLayout(info_frame)
        
        # PID信息
        self.pid_label = QLabel("PID号: --")
        self.pid_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        
        # CPU使用率
        self.cpu_label = QLabel("CPU占用: --")
        self.cpu_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        
        # GPU使用率
        self.gpu_label = QLabel("GPU占用: --")
        self.gpu_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        
        # 添加信息标签到布局
        info_layout.addWidget(self.pid_label)
        info_layout.addWidget(self.cpu_label)
        info_layout.addWidget(self.gpu_label)
        
        # 控制按钮
        control_layout = QHBoxLayout()
        self.start_btn = QPushButton("开始监测")
        self.start_btn.setMinimumHeight(40)
        self.stop_btn = QPushButton("结束")
        self.stop_btn.setMinimumHeight(40)
        self.stop_btn.setEnabled(False)
        
        # 连接按钮信号
        self.start_btn.clicked.connect(self.start_monitoring)
        self.stop_btn.clicked.connect(self.stop_monitoring)
        
        # 添加按钮到布局
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.stop_btn)
        
        # 将信息框和控制按钮添加到左侧面板
        left_layout.addWidget(info_frame)
        left_layout.addLayout(control_layout)
        left_layout.addStretch()
        
        # 设置左侧面板的固定宽度
        left_panel.setFixedWidth(250)
        
        # 右侧特征图显示区域
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # 特征图标题
        feature_title = QLabel("特征图")
        feature_title.setAlignment(Qt.AlignCenter)
        feature_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        # 特征图网格
        feature_grid = QGridLayout()
        
        # 创建4个特征图框
        self.feature_frames = []
        self.layer_names = ['layer1', 'layer2', 'layer3', 'layer4']
        positions = [(0, 0), (0, 1), (1, 0), (1, 1)]
        for i, (pos, name) in enumerate(zip(positions, self.layer_names)):
            frame = FeatureFrame(name)
            self.feature_frames.append(frame)
            feature_grid.addWidget(frame, *pos)
        
        # 将标题和特征图网格添加到右侧布局
        right_layout.addWidget(feature_title)
        right_layout.addLayout(feature_grid)
        
        # 将左右面板添加到内容布局
        content_layout.addWidget(left_panel)
        content_layout.addWidget(right_panel, 1)  # 右侧占据更多空间
        
        # 将内容布局添加到主布局
        main_layout.addLayout(content_layout)
    
    def start_monitoring(self):
        self.monitoring = True
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        
        # 更新PID
        self.pid_label.setText(f"PID号: {os.getpid()}")
        
        # 启动定时器更新监控数据
        self.timer.start(1000)  # 每秒更新一次
    
    def stop_monitoring(self):
        self.monitoring = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.timer.stop()
        
        # 重置信息
        self.pid_label.setText("PID号: --")
        self.cpu_label.setText("CPU占用: --")
        self.gpu_label.setText("GPU占用: --")
    
    def update_monitoring(self):
        if not self.monitoring:
            return
            
        # 更新CPU使用率
        cpu_percent = psutil.cpu_percent()
        self.cpu_label.setText(f"CPU占用: {cpu_percent}%")
        
        # 更新GPU使用率（如果有CUDA）
        if hasattr(self, 'last_gpu_percent'):
            gpu_percent = self.last_gpu_percent
        else:
            gpu_percent = 0
        self.gpu_label.setText(f"GPU占用: {gpu_percent}%")
    
    def update_feature_maps(self, features):
        """更新特征图显示"""
        self.start_monitoring()  # 开始监控
        
        # 更新每个特征图
        for frame, layer_name in zip(self.feature_frames, self.layer_names):
            if layer_name in features:
                frame.update_feature_map(features[layer_name])


class FeatureFrame(QFrame):
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.setFrameShape(QFrame.Box)
        self.setLineWidth(1)
        self.setMinimumSize(150, 150)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 创建布局
        layout = QVBoxLayout(self)
        
        # 显示层名称
        self.name_label = QLabel(self.name)
        self.name_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.name_label)
        
        # 特征图显示标签
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.image_label)
    
    def update_feature_map(self, feature_map):
        """更新特征图显示"""
        if feature_map is None:
            return
            
        # 将numpy数组转换为QImage
        height, width = feature_map.shape
        bytes_per_line = width
        image = QImage(feature_map.data, width, height, bytes_per_line, QImage.Format_Grayscale8)
        
        # 创建QPixmap并显示
        pixmap = QPixmap.fromImage(image)
        scaled_pixmap = pixmap.scaled(
            self.image_label.width(),
            self.image_label.height(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.image_label.setPixmap(scaled_pixmap)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Tab2Widget()
    window.show()
    sys.exit(app.exec_())

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                           QLabel, QPushButton, QListWidget, QFileDialog,
                           QSplitter, QFrame)
from PyQt5.QtCore import Qt, QDateTime, QSize
from PyQt5.QtGui import QIcon, QPixmap
import os
from datetime import datetime

class Tab3Widget(QWidget):
    def __init__(self):
        super().__init__()
        self.image_list = []
        self.initUI()
        
    def initUI(self):
        # 创建主布局
        main_layout = QVBoxLayout(self)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧面板
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # 创建顶部工具栏
        toolbar = QHBoxLayout()
        
        # 添加图片按钮
        self.add_btn = QPushButton('添加图片')
        self.add_btn.setMinimumHeight(40)
        self.add_btn.clicked.connect(self.add_images)
        toolbar.addWidget(self.add_btn)
        
        # 清空列表按钮
        self.clear_btn = QPushButton('清空列表')
        self.clear_btn.setMinimumHeight(40)
        self.clear_btn.clicked.connect(self.clear_list)
        toolbar.addWidget(self.clear_btn)
        
        # 排序按钮
        self.sort_btn = QPushButton('时间排序')
        self.sort_btn.setMinimumHeight(40)
        self.sort_btn.clicked.connect(self.sort_by_time)
        toolbar.addWidget(self.sort_btn)
        
        left_layout.addLayout(toolbar)
        
        # 创建图片列表
        self.image_list_widget = QListWidget()
        self.image_list_widget.setMinimumWidth(300)
        self.image_list_widget.itemClicked.connect(self.show_image_details)
        left_layout.addWidget(self.image_list_widget)
        
        # 右侧图片预览面板
        right_panel = QFrame()
        right_panel.setFrameShape(QFrame.Box)
        right_panel.setLineWidth(1)
        right_layout = QVBoxLayout(right_panel)
        
        # 预览标题
        preview_title = QLabel("图片预览")
        preview_title.setAlignment(Qt.AlignCenter)
        preview_title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        right_layout.addWidget(preview_title)
        
        # 图片预览区域
        self.detail_label = QLabel()
        self.detail_label.setAlignment(Qt.AlignCenter)
        self.detail_label.setMinimumSize(500, 400)
        right_layout.addWidget(self.detail_label)
        
        # 图片信息标签
        self.info_label = QLabel()
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("font-size: 12px; color: #666;")
        right_layout.addWidget(self.info_label)
        
        # 添加左右面板到分割器
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        
        # 设置分割器的初始大小
        splitter.setSizes([300, 700])
        
        # 将分割器添加到主布局
        main_layout.addWidget(splitter)
        
    def add_images(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择图片",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        
        for file_path in files:
            file_info = {
                'path': file_path,
                'name': os.path.basename(file_path),
                'time': os.path.getmtime(file_path),
                'size': os.path.getsize(file_path)
            }
            self.image_list.append(file_info)
            self.image_list_widget.addItem(file_info['name'])
            
    def clear_list(self):
        self.image_list.clear()
        self.image_list_widget.clear()
        self.detail_label.clear()
        self.info_label.clear()
        
    def sort_by_time(self):
        self.image_list.sort(key=lambda x: x['time'])
        self.image_list_widget.clear()
        for image in self.image_list:
            self.image_list_widget.addItem(image['name'])
            
    def show_image_details(self, item):
        for image in self.image_list:
            if image['name'] == item.text():
                # 显示图片
                pixmap = QPixmap(image['path'])
                scaled_pixmap = pixmap.scaled(
                    self.detail_label.width() - 20,
                    self.detail_label.height() - 20,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.detail_label.setPixmap(scaled_pixmap)
                
                # 显示图片信息
                time_str = datetime.fromtimestamp(image['time']).strftime('%Y-%m-%d %H:%M:%S')
                size_mb = image['size'] / (1024 * 1024)
                info_text = f"文件名: {image['name']}\n"
                info_text += f"创建时间: {time_str}\n"
                info_text += f"文件大小: {size_mb:.2f} MB\n"
                info_text += f"分辨率: {pixmap.width()} x {pixmap.height()}"
                self.info_label.setText(info_text)
                break

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = Tab3Widget()
    window.show()
    sys.exit(app.exec_())

import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QLabel, QFrame, QCheckBox, QGroupBox, 
                            QFileDialog, QSizePolicy, QMessageBox, QListWidget,
                            QSplitter, QComboBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage
import os
import sys

# 添加父目录到系统路径
current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if app_dir not in sys.path:
    sys.path.append(app_dir)

from App.models.model_manager import ModelManager

class Tab1Widget(QWidget):
    # 添加信号
    analysis_started = pyqtSignal(str)  # 发送图像路径
    analysis_completed = pyqtSignal(dict)  # 发送特征图数据

    def __init__(self):
        super().__init__()
        self.current_image_path = None
        self.image_list = []  # 存储所有导入的图片路径
        self.model_manager = None  # 稍后初始化
        self.initUI()
        
    def initUI(self):
        # 主布局
        main_layout = QHBoxLayout(self)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧面板 - 图片列表
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # 按钮组
        button_layout = QHBoxLayout()
        
        # 导入按钮
        self.import_btn = QPushButton("导入图像")
        self.import_btn.setMinimumHeight(40)
        self.import_btn.clicked.connect(self.import_images)
        button_layout.addWidget(self.import_btn)
        
        # 清空按钮
        self.clear_btn = QPushButton("清空列表")
        self.clear_btn.setMinimumHeight(40)
        self.clear_btn.clicked.connect(self.clear_list)
        button_layout.addWidget(self.clear_btn)
        
        left_layout.addLayout(button_layout)
        
        # 图片列表
        self.image_list_widget = QListWidget()
        self.image_list_widget.setMinimumWidth(200)
        self.image_list_widget.itemClicked.connect(self.show_selected_image)
        left_layout.addWidget(self.image_list_widget)
        
        # 中间部分 - 图像显示区域
        middle_panel = QWidget()
        middle_layout = QVBoxLayout(middle_panel)
        
        self.image_frame = QFrame()
        self.image_frame.setFrameShape(QFrame.Box)
        self.image_frame.setLineWidth(1)
        self.image_frame.setMinimumSize(500, 500)
        self.image_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 图像显示标签
        image_layout = QVBoxLayout(self.image_frame)
        self.image_label = QLabel("请导入图像")
        self.image_label.setAlignment(Qt.AlignCenter)
        image_layout.addWidget(self.image_label)
        
        middle_layout.addWidget(self.image_frame)
        
        # 右侧控制面板
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_panel.setFixedWidth(200)
        
        # 创建模型选择框
        model_group = QGroupBox("选择模型")
        model_layout = QVBoxLayout(model_group)
        
        # 添加模型选择下拉框
        self.model_combo = QComboBox()
        self.model_combo.addItems(ModelManager.get_available_models())
        self.model_combo.currentTextChanged.connect(self.on_model_changed)
        model_layout.addWidget(self.model_combo)
        
        # 添加预训练模型选项
        self.pretrained_cb = QCheckBox("使用预训练权重")
        self.pretrained_cb.setChecked(True)
        model_layout.addWidget(self.pretrained_cb)
        
        # 添加自定义权重加载按钮
        self.load_weights_btn = QPushButton("加载自定义权重")
        self.load_weights_btn.clicked.connect(self.load_custom_weights)
        model_layout.addWidget(self.load_weights_btn)
        
        # 分析按钮
        self.analyze_btn = QPushButton("分析图像")
        self.analyze_btn.setMinimumHeight(40)
        self.analyze_btn.setEnabled(False)  # 初始禁用
        self.analyze_btn.clicked.connect(self.analyze_image)
        
        # 添加预测结果显示区域
        self.prediction_label = QLabel()
        self.prediction_label.setAlignment(Qt.AlignCenter)
        self.prediction_label.setWordWrap(True)
        self.prediction_label.setStyleSheet("font-size: 12px; color: #666;")
        
        # 添加元素到右侧布局
        right_layout.addWidget(model_group)
        right_layout.addWidget(self.analyze_btn)
        right_layout.addWidget(self.prediction_label)
        right_layout.addStretch()
        
        # 将面板添加到分割器
        splitter.addWidget(left_panel)
        splitter.addWidget(middle_panel)
        splitter.addWidget(right_panel)
        
        # 设置分割器的初始大小
        splitter.setSizes([200, 600, 200])
        
        # 将分割器添加到主布局
        main_layout.addWidget(splitter)
        
        # 初始化模型
        self.on_model_changed(self.model_combo.currentText())
    
    def import_images(self):
        options = QFileDialog.Options()
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择图像文件", "", 
            "图像文件 (*.png *.jpg *.jpeg *.bmp);;所有文件 (*)", 
            options=options
        )
        
        if files:
            self.image_list.extend(files)
            self.image_list_widget.clear()
            for file_path in self.image_list:
                self.image_list_widget.addItem(os.path.basename(file_path))
            
            # 显示第一张图片
            if not self.current_image_path:
                self.current_image_path = files[0]
                self.show_image(files[0])
    
    def clear_list(self):
        self.image_list.clear()
        self.image_list_widget.clear()
        self.current_image_path = None
        self.image_label.setText("请导入图像")
        self.image_label.setPixmap(QPixmap())  # 清除图片
        self.analyze_btn.setEnabled(False)
    
    def show_selected_image(self, item):
        """当在列表中选择图片时显示"""
        for image_path in self.image_list:
            if os.path.basename(image_path) == item.text():
                self.current_image_path = image_path
                self.show_image(image_path)
                break
    
    def show_image(self, file_path):
        """显示指定路径的图片"""
        pixmap = QPixmap(file_path)
        if not pixmap.isNull():
            # 调整图像大小以适应框架，保持纵横比
            scaled_pixmap = pixmap.scaled(
                self.image_frame.width() - 20, 
                self.image_frame.height() - 20,
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
            self.image_label.setText("")  # 清除默认文本
            self.analyze_btn.setEnabled(True)  # 启用分析按钮
        else:
            self.image_label.setText("图像加载失败")
            self.analyze_btn.setEnabled(False)
    
    def on_model_changed(self, model_name):
        """当选择的模型改变时调用"""
        self.model_manager = ModelManager(
            model_name=model_name,
            pretrained=self.pretrained_cb.isChecked()
        )
    
    def load_custom_weights(self):
        """加载自定义权重文件"""
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择权重文件",
            "",
            "PyTorch权重文件 (*.pth);;所有文件 (*)",
            options=options
        )
        
        if file_path:
            try:
                self.model_manager.load_weights(file_path)
                QMessageBox.information(self, "成功", "权重加载成功！")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"加载权重文件时出错：{str(e)}")
    
    def analyze_image(self):
        if not self.current_image_path:
            return
            
        try:
            # 发送开始分析信号
            self.analysis_started.emit(self.current_image_path)
            
            # 处理图像获取特征图和预测结果
            results = self.model_manager.process_image(self.current_image_path)
            
            # 发送完成信号和特征图数据
            self.analysis_completed.emit(results['features'])
            
            # 显示预测结果
            probs = results['predictions']['probabilities']
            classes = results['predictions']['classes']
            
            # 显示前5个预测结果
            result_text = "预测结果：\n"
            for prob, class_idx in zip(probs, classes):
                result_text += f"类别 {class_idx}: {prob*100:.2f}%\n"
            self.prediction_label.setText(result_text)
            
            QMessageBox.information(self, "分析完成", "图像分析已完成！")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"分析过程中出现错误：{str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Tab1Widget()
    window.show()
    sys.exit(app.exec_())
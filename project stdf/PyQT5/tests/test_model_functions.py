import unittest
import os
import sys
from pathlib import Path
import json
import threading
import time
import numpy as np
from PIL import Image
import io

# 添加项目根目录到系统路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.append(str(project_root))

from PyQT5.server.app import app
from PyQT5.App.utils.api_client import APIClient

class TestModelFunctions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        # 启动Flask服务器
        def run_flask():
            app.run(port=5000)
        
        cls.flask_thread = threading.Thread(target=run_flask, daemon=True)
        cls.flask_thread.start()
        time.sleep(1)  # 等待服务器启动
        
        cls.api_client = APIClient()
        
        # 创建测试数据目录
        cls.test_data_dir = os.path.join(current_dir, 'test_data')
        os.makedirs(cls.test_data_dir, exist_ok=True)
        
        # 创建测试模型目录
        cls.test_model_dir = os.path.join(cls.test_data_dir, 'models')
        os.makedirs(cls.test_model_dir, exist_ok=True)
        
        # 创建虚拟测试图片
        cls.test_images = cls._create_test_images()
        
        # 创建虚拟模型文件
        cls.test_model_path = os.path.join(cls.test_model_dir, 'test_model.pth')
        with open(cls.test_model_path, 'wb') as f:
            # 创建一个简单的PyTorch模型结构
            dummy_model = {
                'state_dict': {
                    'conv1.weight': np.random.rand(64, 3, 3, 3).astype(np.float32),
                    'conv1.bias': np.random.rand(64).astype(np.float32),
                    'fc.weight': np.random.rand(1000, 64).astype(np.float32),
                    'fc.bias': np.random.rand(1000).astype(np.float32)
                }
            }
            np.save(f, dummy_model)

    @classmethod
    def _create_test_images(cls):
        """创建测试图片"""
        images = []
        # 创建3张测试图片：正常、有褶皱、有残余物
        for i, condition in enumerate(['normal', 'wrinkle', 'residue']):
            # 创建一个224x224的随机图片（标准输入尺寸）
            img_array = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
            
            # 添加特定的模式
            if condition == 'wrinkle':
                # 添加一条对角线模拟褶皱
                for j in range(224):
                    img_array[j, j] = [255, 255, 255]
            elif condition == 'residue':
                # 添加一个白色方块模拟残余物
                img_array[90:134, 90:134] = [255, 255, 255]
            
            # 保存图片
            img = Image.fromarray(img_array)
            img_path = os.path.join(cls.test_data_dir, f'test_{condition}.jpg')
            img.save(img_path)
            images.append(img_path)
        return images

    def setUp(self):
        """每个测试用例开始前执行"""
        # 确保模型已加载
        response = self.api_client.load_model(
            model_path=self.test_model_path,
            model_type='residue_detection'
        )
        self.assertEqual(response['status'], 'success', "模型加载失败")

    def test_model_check_and_load(self):
        """测试模型检查和加载功能"""
        # 测试模型路径检查
        response = self.api_client.check_model(self.test_model_path)
        self.assertEqual(response['status'], 'success')
        self.assertTrue(response.get('exists', False), "模型文件应该存在")
        
        # 测试模型加载
        response = self.api_client.load_model(
            model_path=self.test_model_path,
            model_type='residue_detection'
        )
        self.assertEqual(response['status'], 'success')
        self.assertTrue(response.get('loaded', False), "模型应该成功加载")

    def test_inference(self):
        """测试模型推理功能"""
        # 测试单图推理
        response = self.api_client.inference(
            image_path=self.test_images[0],
            model_path=self.test_model_path
        )
        self.assertEqual(response['status'], 'success')
        self.assertIn('results', response)
        self.assertIn('confidence', response['results'])
        
        # 测试异步推理
        response = self.api_client.inference_async(
            image_path=self.test_images[1],
            model_path=self.test_model_path
        )
        self.assertEqual(response['status'], 'success')
        self.assertIn('task_id', response)
        
        # 测试多模型集成推理
        response = self.api_client.detection(
            image_path=self.test_images[2],
            model_paths=[self.test_model_path]
        )
        self.assertEqual(response['status'], 'success')
        self.assertIn('results', response)
        self.assertIn('ensemble_result', response['results'])

    def test_trend_prediction(self):
        """测试趋势预测功能"""
        # 测试褶皱趋势预测
        image_series = self.test_images
        response = self.api_client.check_trend(image_series)
        self.assertEqual(response['status'], 'success')
        self.assertIn('result', response)
        self.assertIn('expanding', response['result'])
        
        # 测试趋势推理
        test_data = {
            'image_series': image_series,
            'timestamps': [time.time() - i * 3600 for i in range(len(image_series))]
        }
        response = self.api_client.trend_inference(test_data)
        self.assertEqual(response['status'], 'success')

    def test_monitoring(self):
        """测试监控功能"""
        # 测试特征图获取
        response = self.api_client.get_feature_map(
            model_name='test_model',
            layer_name='conv1'
        )
        self.assertEqual(response['status'], 'success')
        self.assertIn('feature_map', response)
        
        # 测试系统监控
        response = self.api_client.get_pid()
        self.assertEqual(response['status'], 'success')
        self.assertIn('pid', response)
        
        response = self.api_client.get_cpu_usage()
        self.assertEqual(response['status'], 'success')
        self.assertIn('cpu_percent', response)
        
        response = self.api_client.get_gpu_usage()
        self.assertEqual(response['status'], 'success')
        self.assertIn('gpu_info', response)
        
        # 测试报警功能
        response = self.api_client.check_alert()
        self.assertEqual(response['status'], 'success')

    def test_signal_transmission(self):
        """测试信号传输功能"""
        signal_data = {
            'signal_type': 'alert',
            'message': 'Residue detected',
            'timestamp': time.time(),
            'data': {
                'confidence': 0.95,
                'location': [100, 100, 150, 150],
                'type': 'residue'
            }
        }
        response = self.api_client.send_signal(signal_data)
        self.assertEqual(response['status'], 'success')
        self.assertTrue(response.get('received', False), "信号应该被成功接收")

    @classmethod
    def tearDownClass(cls):
        """测试类结束后清理"""
        # 删除测试数据目录
        import shutil
        if os.path.exists(cls.test_data_dir):
            shutil.rmtree(cls.test_data_dir)

if __name__ == '__main__':
    unittest.main() 
import unittest
import os
import sys
from pathlib import Path
import json
import threading
import time

# 添加项目根目录到系统路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.append(str(project_root))

from PyQT5.server.app import app
from PyQT5.App.utils.api_client import APIClient

class TestDataCollection(unittest.TestCase):
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
        
        # 创建测试图片
        cls.test_image_paths = []
        for i in range(3):
            test_image_path = os.path.join(cls.test_data_dir, f'test_image_{i}.jpg')
            # 创建空白测试图片文件
            with open(test_image_path, 'w') as f:
                f.write('')
            cls.test_image_paths.append(test_image_path)

    def setUp(self):
        """每个测试用例开始前执行"""
        pass

    def test_get_static_data(self):
        """测试获取图像路径数据"""
        # 使用API客户端
        response = self.api_client.get_static_data()
        self.assertEqual(response['status'], 'success')
        self.assertIsInstance(response.get('data', []), list)

    def test_get_rtsp_data(self):
        """测试获取RTSP流数据"""
        # 测试有效的RTSP URL
        valid_rtsp_url = "rtsp://example.com/stream1"
        response = self.api_client.get_rtsp_data(valid_rtsp_url)
        self.assertEqual(response['status'], 'success')
        self.assertEqual(response['url'], valid_rtsp_url)

    def test_image_info_cache(self):
        """测试图像信息缓存功能"""
        # 测试有效的图像路径
        if self.test_image_paths:
            test_path = self.test_image_paths[0]
            from PyQT5.server.app import get_image_info
            
            # 第一次调用
            info1 = get_image_info(test_path)
            self.assertIsNotNone(info1)
            self.assertEqual(info1['path'], test_path)
            
            # 第二次调用（应该从缓存获取）
            info2 = get_image_info(test_path)
            self.assertEqual(info1, info2)
        
        # 测试无效的图像路径
        invalid_path = os.path.join(self.test_data_dir, 'nonexistent.jpg')
        info = get_image_info(invalid_path)
        self.assertIsNone(info)

    def test_api_client_connection(self):
        """测试API客户端连接"""
        # 测试默认连接
        self.assertIsNotNone(self.api_client)
        
        # 测试自定义基础URL
        custom_client = APIClient(base_url="http://localhost:5001")
        self.assertEqual(custom_client.base_url, "http://localhost:5001")
        
        # 测试重试机制
        custom_client = APIClient(max_retries=5)
        self.assertEqual(custom_client.max_retries, 5)

    @classmethod
    def tearDownClass(cls):
        """测试类结束后清理"""
        # 删除测试数据目录
        import shutil
        if os.path.exists(cls.test_data_dir):
            shutil.rmtree(cls.test_data_dir)

if __name__ == '__main__':
    unittest.main() 
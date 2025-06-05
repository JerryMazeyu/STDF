import requests
import json
import time
import logging
from typing import Dict, List, Union, Optional
from requests.exceptions import RequestException, Timeout, ConnectionError

logger = logging.getLogger(__name__)

class APIClient:
    def __init__(self, base_url: str = "http://localhost:5000", max_retries: int = 3):
        self.base_url = base_url
        self.timeout = 3  # 设置3秒超时
        self.max_retries = max_retries
        self.retry_delay = 1  # 重试延迟（秒）
        
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """发送请求并处理重试逻辑"""
        url = f"{self.base_url}{endpoint}"
        retries = 0
        last_error = None
        
        while retries < self.max_retries:
            try:
                if 'timeout' not in kwargs:
                    kwargs['timeout'] = self.timeout
                    
                response = requests.request(method, url, **kwargs)
                response.raise_for_status()
                return response.json()
                
            except Timeout as e:
                last_error = '服务器响应超时'
                logger.warning(f"请求超时 (尝试 {retries + 1}/{self.max_retries}): {endpoint}")
            except ConnectionError as e:
                last_error = '无法连接到服务器'
                logger.warning(f"连接错误 (尝试 {retries + 1}/{self.max_retries}): {endpoint}")
            except RequestException as e:
                last_error = f'请求错误: {str(e)}'
                logger.warning(f"请求异常 (尝试 {retries + 1}/{self.max_retries}): {endpoint}")
            except Exception as e:
                last_error = str(e)
                logger.error(f"未知错误 (尝试 {retries + 1}/{self.max_retries}): {endpoint}", exc_info=True)
            
            retries += 1
            if retries < self.max_retries:
                time.sleep(self.retry_delay)
        
        logger.error(f"请求失败 {endpoint}: {last_error}")
        return {'status': 'error', 'message': last_error}
    
    def _get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """发送GET请求"""
        return self._request('GET', endpoint, params=params)
    
    def _post(self, endpoint: str, data: Dict) -> Dict:
        """发送POST请求"""
        return self._request('POST', endpoint, json=data)
    
    # 1. 数据采集接口
    def get_static_data(self) -> Dict:
        """获取图像路径数据"""
        return self._get('/api/data/get_static_data')
    
    def get_rtsp_data(self, rtsp_url: str) -> Dict:
        """获取图像rtsp流数据"""
        return self._post('/api/data/get_rtsp_data', {'rtsp_url': rtsp_url})
    
    # 2. 模型接口
    def check_model(self, model_path: str) -> Dict:
        """检查模型路径是否存在"""
        return self._post('/api/model/check', {'model_path': model_path})
    
    def load_model(self, model_path: str, model_type: str) -> Dict:
        """加载模型"""
        return self._post('/api/data/load_model', {
            'model_path': model_path,
            'model_type': model_type
        })
    
    # 3. 残余物检测接口
    def inference(self, image_path: str, model_path: str) -> Dict:
        """执行模型推理"""
        return self._post('/api/detection/inference', {
            'image_path': image_path,
            'model_path': model_path
        })
    
    def inference_async(self, image_path: str, model_path: str) -> Dict:
        """异步推理"""
        return self._post('/api/detection/inference_async', {
            'image_path': image_path,
            'model_path': model_path
        })
    
    def detection(self, image_path: str, model_paths: List[str]) -> Dict:
        """集成多模型推理结果"""
        return self._post('/api/detection/detection', {
            'image_path': image_path,
            'model_paths': model_paths
        })
    
    # 4. 趋势预测接口
    def trend_inference(self, data: Dict) -> Dict:
        """执行趋势预测"""
        return self._post('/api/stp/inference', {'data': data})
    
    def check_trend(self, image_series: List[str]) -> Dict:
        """推理是否褶皱扩大"""
        return self._post('/api/stp/trend', {'image_series': image_series})
    
    # 5. 残余物哨兵接口
    def get_feature_map(self, model_name: str, layer_name: str) -> Dict:
        """查看模型中间表征运行"""
        return self._get('/api/monitor/feature_map', {
            'model_name': model_name,
            'layer_name': layer_name
        })
    
    def get_pid(self) -> Dict:
        """查看程序运行PID号"""
        return self._get('/api/monitor/pid')
    
    def get_cpu_usage(self) -> Dict:
        """查看CPU占用"""
        return self._get('/api/monitor/cpu')
    
    def get_gpu_usage(self) -> Dict:
        """查看GPU占用"""
        return self._get('/api/monitor/gpu')
    
    def check_alert(self) -> Dict:
        """是否报警"""
        return self._get('/api/monitor/alert')
    
    # 6. 信号传输接口
    def send_signal(self, signal_data: Dict) -> Dict:
        """向指定管道传输socket信号"""
        return self._post('/api/signal/send', signal_data) 
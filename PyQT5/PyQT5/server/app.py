import sys
import os
import logging
from flask import Flask, jsonify, request
import torch
import psutil
import asyncio
import json
from datetime import datetime
from functools import lru_cache
import threading
import time

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 获取项目根目录
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 全局变量
MODEL_PATH = os.path.join(ROOT_DIR, "models")
STATIC_DATA_PATH = os.path.join(ROOT_DIR, "data", "images")
loaded_models = {}

# 缓存系统信息
system_info = {
    'cpu_percent': 0,
    'gpu_info': {'gpu_percent': 0, 'memory_used': 0},
    'last_update': 0
}

def update_system_info():
    """后台更新系统信息"""
    while True:
        try:
            system_info['cpu_percent'] = psutil.cpu_percent()
            
            # GPU信息获取
            if torch.cuda.is_available():
                try:
                    # 获取第一个GPU的信息
                    gpu_percent = torch.cuda.utilization_percent()
                    memory_used = torch.cuda.memory_allocated() / (1024 * 1024)  # 转换为MB
                    system_info['gpu_info'] = {
                        'gpu_percent': gpu_percent,
                        'memory_used': memory_used
                    }
                except Exception as e:
                    logger.warning(f"获取GPU信息失败: {str(e)}")
                    system_info['gpu_info'] = {'gpu_percent': 0, 'memory_used': 0}
            else:
                system_info['gpu_info'] = {'gpu_percent': 0, 'memory_used': 0}
                
            system_info['last_update'] = time.time()
            
        except Exception as e:
            logger.error(f"更新系统信息失败：{str(e)}")
        time.sleep(1)  # 每秒更新一次

def init_server():
    """初始化服务器"""
    try:
        # 创建必要的目录
        os.makedirs(MODEL_PATH, exist_ok=True)
        os.makedirs(STATIC_DATA_PATH, exist_ok=True)
        
        # 启动后台更新线程
        update_thread = threading.Thread(target=update_system_info, daemon=True)
        update_thread.start()
        
        logger.info(f"服务器初始化完成")
        logger.info(f"模型目录: {MODEL_PATH}")
        logger.info(f"数据目录: {STATIC_DATA_PATH}")
        
    except Exception as e:
        logger.error(f"服务器初始化失败: {str(e)}")
        sys.exit(1)

# 创建Flask应用
app = Flask(__name__)

@lru_cache(maxsize=100)
def get_image_info(file_path):
    """缓存图像信息"""
    try:
        return {
            'path': file_path,
            'name': os.path.basename(file_path),
            'time': os.path.getmtime(file_path),
            'size': os.path.getsize(file_path)
        }
    except Exception as e:
        logger.error(f"获取图像信息失败: {str(e)}")
        return None

# 1. 数据采集接口
@app.route('/api/data/get_static_data', methods=['GET'])
def get_static_data():
    """获取图像路径数据"""
    try:
        images = []
        if os.path.exists(STATIC_DATA_PATH):
            for file in os.listdir(STATIC_DATA_PATH):
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    file_path = os.path.join(STATIC_DATA_PATH, file)
                    image_info = get_image_info(file_path)
                    if image_info:
                        images.append(image_info)
        return jsonify({'status': 'success', 'data': images})
    except Exception as e:
        logger.error(f"获取静态数据失败: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/data/get_rtsp_data', methods=['POST'])
def get_rtsp_data():
    """获取图像rtsp流数据"""
    try:
        rtsp_url = request.json.get('rtsp_url')
        # 这里添加RTSP流处理逻辑
        return jsonify({'status': 'success', 'url': rtsp_url})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# 2. 模型接口
@app.route('/api/model/check', methods=['POST'])
def check_model():
    """检查模型路径是否存在"""
    try:
        model_path = request.json.get('model_path')
        exists = os.path.exists(os.path.join(MODEL_PATH, model_path))
        return jsonify({'status': 'success', 'exists': exists})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/data/load_model', methods=['POST'])
def load_model():
    """加载模型"""
    try:
        model_path = request.json.get('model_path')
        model_type = request.json.get('model_type')
        if model_path not in loaded_models:
            # 这里添加模型加载逻辑
            loaded_models[model_path] = {'type': model_type, 'loaded_time': datetime.now()}
        return jsonify({'status': 'success', 'model_info': loaded_models[model_path]})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# 3. 残余物检测接口
@app.route('/api/detection/inference', methods=['POST'])
def inference():
    """执行模型推理"""
    try:
        image_path = request.json.get('image_path')
        model_path = request.json.get('model_path')
        # 这里添加推理逻辑
        results = {'detected': True, 'confidence': 0.95}
        return jsonify({'status': 'success', 'results': results})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/detection/inference_async', methods=['POST'])
async def inference_async():
    """异步推理"""
    try:
        image_path = request.json.get('image_path')
        model_path = request.json.get('model_path')
        # 这里添加异步推理逻辑
        await asyncio.sleep(1)  # 模拟异步处理
        results = {'detected': True, 'confidence': 0.95}
        return jsonify({'status': 'success', 'results': results})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/detection/detection', methods=['POST'])
def detection():
    """集成多模型推理结果"""
    try:
        image_path = request.json.get('image_path')
        model_paths = request.json.get('model_paths')
        # 这里添加多模型集成逻辑
        results = {'ensemble_result': True, 'confidence': 0.98}
        return jsonify({'status': 'success', 'results': results})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# 4. 趋势预测接口
@app.route('/api/stp/inference', methods=['POST'])
def trend_inference():
    """执行趋势预测"""
    try:
        data = request.json.get('data')
        # 这里添加趋势预测逻辑
        prediction = {'trend': 'increasing', 'probability': 0.85}
        return jsonify({'status': 'success', 'prediction': prediction})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/stp/trend', methods=['POST'])
def check_trend():
    """推理是否褶皱扩大"""
    try:
        image_series = request.json.get('image_series')
        # 这里添加褶皱分析逻辑
        result = {'expanding': True, 'rate': 0.15}
        return jsonify({'status': 'success', 'result': result})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# 5. 残余物哨兵接口
@app.route('/api/monitor/feature_map', methods=['GET'])
def get_feature_map():
    """查看模型中间表征运行"""
    try:
        model_name = request.args.get('model_name')
        layer_name = request.args.get('layer_name')
        # 这里添加特征图获取逻辑
        feature_map = {'shape': [64, 64], 'data': []}
        return jsonify({'status': 'success', 'feature_map': feature_map})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/monitor/pid', methods=['GET'])
def get_pid():
    """查看程序运行PID号"""
    try:
        return jsonify({
            'status': 'success',
            'pid': os.getpid(),
            'server_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        logger.error(f"获取PID失败: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/monitor/cpu', methods=['GET'])
def get_cpu_usage():
    """查看CPU占用"""
    try:
        return jsonify({
            'status': 'success', 
            'cpu_percent': system_info['cpu_percent'],
            'server_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        logger.error(f"获取CPU使用率失败: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/monitor/gpu', methods=['GET'])
def get_gpu_usage():
    """查看GPU占用"""
    try:
        return jsonify({
            'status': 'success',
            'gpu_info': system_info['gpu_info'],
            'server_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        logger.error(f"获取GPU使用率失败: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/monitor/alert', methods=['GET'])
def check_alert():
    """是否报警"""
    try:
        # 这里添加报警检测逻辑
        alert_info = {'alert': False, 'reason': None}
        return jsonify({'status': 'success', 'alert_info': alert_info})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# 6. 信号传输接口
@app.route('/api/signal/send', methods=['POST'])
def send_signal():
    """向指定管道传输socket信号"""
    try:
        signal_data = request.json
        # 这里添加信号传输逻辑
        return jsonify({'status': 'success', 'message': 'Signal sent'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

def run_server():
    """运行服务器"""
    try:
        # 初始化服务器
        init_server()
        
        # 启动Flask服务器
        logger.info("正在启动Flask服务器...")
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,
            threaded=True,
            use_reloader=False  # 禁用重载器以避免创建多个后台线程
        )
    except Exception as e:
        logger.error(f"服务器启动失败: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    run_server() 
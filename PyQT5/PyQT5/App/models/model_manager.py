import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image
import numpy as np

class FeatureExtractor(nn.Module):
    def __init__(self, model_name='resnet18', pretrained=True, num_classes=1000):
        super().__init__()
        # 获取基础模型
        if model_name == 'resnet18':
            self.model = models.resnet18(pretrained=pretrained)
        elif model_name == 'resnet34':
            self.model = models.resnet34(pretrained=pretrained)
        elif model_name == 'resnet50':
            self.model = models.resnet50(pretrained=pretrained)
        elif model_name == 'vgg16':
            self.model = models.vgg16(pretrained=pretrained)
        else:
            raise ValueError(f"不支持的模型类型: {model_name}")
        
        # 修改最后的全连接层
        if isinstance(self.model, models.ResNet):
            in_features = self.model.fc.in_features
            self.model.fc = nn.Sequential(
                nn.Linear(in_features, 512),
                nn.ReLU(),
                nn.Dropout(0.5),
                nn.Linear(512, num_classes)
            )
        elif isinstance(self.model, models.VGG):
            in_features = self.model.classifier[-1].in_features
            self.model.classifier[-1] = nn.Sequential(
                nn.Linear(in_features, 512),
                nn.ReLU(),
                nn.Dropout(0.5),
                nn.Linear(512, num_classes)
            )
        
        self.model_name = model_name
        self.feature_maps = {}
        
        # 注册钩子来获取中间层特征图
        def hook_fn(name):
            def hook(module, input, output):
                self.feature_maps[name] = output.detach()
            return hook
        
        # 根据不同模型注册相应的钩子
        if isinstance(self.model, models.ResNet):
            self.model.layer1.register_forward_hook(hook_fn('layer1'))
            self.model.layer2.register_forward_hook(hook_fn('layer2'))
            self.model.layer3.register_forward_hook(hook_fn('layer3'))
            self.model.layer4.register_forward_hook(hook_fn('layer4'))
        elif isinstance(self.model, models.VGG):
            # VGG的特征提取层
            self.model.features[5].register_forward_hook(hook_fn('conv2'))
            self.model.features[10].register_forward_hook(hook_fn('conv3'))
            self.model.features[17].register_forward_hook(hook_fn('conv4'))
            self.model.features[24].register_forward_hook(hook_fn('conv5'))
        
    def forward(self, x):
        self.feature_maps.clear()
        return self.model(x)

class ModelManager:
    def __init__(self, model_name='resnet18', pretrained=True, num_classes=1000):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = FeatureExtractor(
            model_name=model_name,
            pretrained=pretrained,
            num_classes=num_classes
        ).to(self.device)
        self.model.eval()
        
        # 根据不同模型设置不同的预处理
        self.transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
    
    @staticmethod
    def get_available_models():
        """返回可用的模型列表"""
        return ['resnet18', 'resnet34', 'resnet50', 'vgg16']
    
    def process_image(self, image_path):
        """处理图像并返回特征图"""
        # 加载和预处理图像
        image = Image.open(image_path).convert('RGB')
        input_tensor = self.transform(image).unsqueeze(0).to(self.device)
        
        # 获取特征图
        with torch.no_grad():
            output = self.model(input_tensor)
            feature_maps = self.model.feature_maps
        
        # 处理特征图以便显示
        processed_features = {}
        for name, feature_map in feature_maps.items():
            # 选择第一个特征图的第一个通道
            feature = feature_map[0, 0].cpu().numpy()
            
            # 归一化到0-255范围
            feature = ((feature - feature.min()) / (feature.max() - feature.min()) * 255).astype(np.uint8)
            processed_features[name] = feature
        
        # 获取预测结果
        probabilities = torch.nn.functional.softmax(output[0], dim=0)
        top_prob, top_class = torch.topk(probabilities, 5)
        
        return {
            'features': processed_features,
            'predictions': {
                'probabilities': top_prob.cpu().numpy(),
                'classes': top_class.cpu().numpy()
            }
        }
    
    def load_weights(self, weights_path):
        """加载预训练权重"""
        self.model.load_state_dict(torch.load(weights_path, map_location=self.device))
        self.model.eval()
    
    def save_weights(self, weights_path):
        """保存模型权重"""
        torch.save(self.model.state_dict(), weights_path) 
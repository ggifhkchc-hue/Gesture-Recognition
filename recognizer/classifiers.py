# ==========================================
# 自定义模型分类器 (recognizer/classifiers.py)
# ==========================================

class CustomGestureClassifier:
    def __init__(self, model_path=None):
        self.model_path = model_path
        # 这里以后可以初始化 sklearn.svm 或 PyTorch 的 MLP 模型
        self.model = None
        self.is_loaded = False

    def load_model(self):
        """加载训练好的模型权重文件"""
        if self.model_path:
            print(f"[INFO] 正在加载自定义分类器模型: {self.model_path} ...")
            # example: self.model = joblib.load(self.model_path)
            self.is_loaded = True

    def predict(self, landmarks):
        """输入 21 个点坐标，输出预测的手势 ID"""
        if not self.is_loaded:
            return "UNKNOWN"
        
        # 提取特征数据并归一化
        # feature_vector = [lm.x for lm in landmarks] + [lm.y for lm in landmarks]
        # return self.model.predict([feature_vector])[0]
        return "UNKNOWN"
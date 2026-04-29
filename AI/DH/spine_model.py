import torch
import torch.nn as nn
import timm

# ---------------------------------------------------------
# 1. 모델 설계도 (Blueprint) 정의
# PyTorch의 .pth 파일은 '가중치 숫자'만 들어있기 때문에,
# 반드시 숫자가 들어갈 똑같은 모양의 '빈 껍데기(클래스)'가 필요합니다.
# ---------------------------------------------------------

class MRIConditionModel(nn.Module):
    def __init__(self, backbone='resnet18', num_conditions=3):
        super().__init__()
        # timm 라이브러리에서 사전 학습된 ResNet18 뼈대를 가져옵니다.
        self.backbone = timm.create_model(
            backbone,
            pretrained=False, # 가중치를 따로 덮어씌울 것이므로 False로 둡니다.
            in_chans=3,
            features_only=False,
            num_classes=0
        )
        self.num_features = self.backbone.num_features

        # 가져온 뼈대 끝에 9개의 결과(3가지 질환 * 3가지 심각도)를 출력하도록 머리를 붙입니다.
        self.classifier = nn.Sequential(
            nn.AdaptiveAvgPool2d((1, 1)),
            nn.Flatten(),
            nn.Linear(self.num_features, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(512, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, num_conditions * 3) # 최종 출력: 9
        )

    def forward(self, x):
        features = self.backbone.forward_features(x)
        x = self.classifier(features)
        return x

# ---------------------------------------------------------
# 2. 모델 로딩 함수 (외부에서 호출할 함수)
# ---------------------------------------------------------
def load_spine_model(weights_path='best_mri_model.pth'):
    """
    설계도를 바탕으로 빈 모델을 만들고, 다운로드한 가중치를 주입합니다.
    """
    try:
        # 내 컴퓨터에 GPU가 있으면 GPU를, 없으면 CPU를 사용하도록 설정
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"✅ 사용 중인 디바이스: {device}")

        # 1. 빈 모델 생성
        model = MRIConditionModel(backbone='resnet18', num_conditions=3)

        # 2. 가중치 파일(.pth) 불러오기
        checkpoint = torch.load(weights_path, map_location=device, weights_only=True)

        # 3. 빈 모델에 가중치 덮어씌우기
        model.load_state_dict(checkpoint['model_state_dict'])
        model.to(device)
        model.eval() # 평가(추론) 모드로 변경! (아주 중요함, 끄면 결과가 튀어요)

        print("✅ 모델 및 가중치 로딩 성공!")
        return model, device

    except Exception as e:
        print(f"❌ 모델 로딩 실패: {e}")
        return None, None

# ---------------------------------------------------------
# 3. 테스트 실행 (이 파일을 직접 실행했을 때만 동작)
# ---------------------------------------------------------
if __name__ == "__main__":
    # best_mri_model.pth 파일이 이 파이썬 파일과 같은 폴더에 있어야 합니다!
    my_model, my_device = load_spine_model('best_mri_model.pth')

    if my_model:
        print("🎉 모든 준비가 완료되었습니다! 이제 이미지를 넣을 수 있습니다.")
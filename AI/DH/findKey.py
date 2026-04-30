import torch

# 1. 일단 파일을 불러옵니다.
checkpoint = torch.load('best_mri_model.pth', map_location='cpu')

# 2. 어떤 키들이 있는지 확인합니다.
print("--- 가중치 파일 내부 구성 ---")
if isinstance(checkpoint, dict):
    print(f"발견된 키: {checkpoint.keys()}")
else:
    print("이 파일은 키가 없는 '순수 가중치 데이터(state_dict)' 자체입니다.")
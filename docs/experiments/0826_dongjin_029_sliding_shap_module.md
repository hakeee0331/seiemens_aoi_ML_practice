# 0826_dongjin_029_sliding_shap_module

- **연결된 노트북 경로**: `notebooks/0826_dongjin_029_sliding_shap_module.py`
- **상태**: 완료
- **실험 목적**: 028번 실험에서 작성된 실시간 Sliding Window 기반 Dynamic SHAP 계산 코드를 재사용 가능한 함수로 모듈화함. `src/` 폴더에 코드를 추가하지 않는 프로젝트 규칙을 준수하여 `notebooks/` 디렉토리에 위치시킴.
- **이전 실험 대비 주요 변경사항**:
  - `StreamingDynamicSHAPMonitor` 클래스의 실행 루프를 `calculate_sliding_shap` 함수로 분리.
  - Convergence 분석 로직을 `analyze_shap_convergence` 함수로 분리.
- **평가 방법과 주요 결과**: 해당 없음 (모듈화 목적)
- **결론과 다음 단계**: 다른 노트북에서 `from 0826_dongjin_029_sliding_shap_module import calculate_sliding_shap` 형태로 import하여 재사용 가능.
- **저장된 모델 경로**: 없음

# siemens_aoi

## 프로젝트 목표

팀원과 회의 후 구체적 사항 기록 예정

## 참여 방법

이 저장소는 사람과 에이전트가 함께 작업하는 2일간의 머신러닝 미니 프로젝트다. 탐색, 전처리, 학습 및 평가는 우선 노트북에서 수행한다.

작업을 시작하기 전에 `CONTRIBUTING.md`를 읽는다. 새 파일을 만들 때는 반드시 저장소의 동일 유형 example을 먼저 참고한다.

## GitHub 협업

- 새 작업은 GitHub Issue로 기록하고 제공된 작업 이슈 양식을 사용한다.
- 변경사항은 Pull Request로 공유하고 관련 Issue를 연결한다.
- 팀 공유용 협업 가이드는 `docs/project_status.html`에서 확인한다.
- 자세한 작성 규칙은 `CONTRIBUTING.md`에서 확인한다.

## 환경 설정

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
jupyter lab
```

노트북은 저장소 루트에서 Jupyter를 실행한 뒤 사용한다.

## 데이터

원본 데이터는 `data/raw/`에 둔다. 실제 데이터 파일은 Git에서 제외된다.

익명 컬럼과 데이터 구조를 기록할 때는 `docs/data_example.md`를 참고해 실제 데이터용 문서를 작성한다.

## 실험 추가 순서

1. example 노트북과 example 실험 문서를 읽는다.
2. `MMDD_작성자_실험번호_설명` 규칙으로 노트북을 생성한다.
3. 같은 stem으로 `docs/experiments/`에 설명 문서를 생성한다.
4. 노트북을 처음부터 끝까지 실행한다.
5. 실험 문서와 `docs/experiments/index.md`를 갱신한다.
6. 모델의 최종 Test 평가가 있으면 `docs/model_val.md`를 갱신한다.
7. 필요한 경우 같은 stem으로 모델을 `models/`에 저장한다.

세부 규칙은 `CONTRIBUTING.md`에서 확인한다.

## Example

- 노트북 example: `notebooks/0823_example_001_baseline.ipynb`
- 실험 문서 example: `docs/experiments/0823_example_001_baseline.md`
- 데이터 설명 example: `docs/data_example.md`

Example은 구조와 작성 형식을 보여주기 위해 합성 데이터를 사용한다. 실제 실험을 시작할 때 example 파일을 복사한 뒤 파일 이름, 데이터 로딩, 실험 내용과 결과를 실제 작업에 맞게 변경한다.

## 저장소 구조

```text
siemens_aoi/
├── README.md
├── CONTRIBUTING.md
├── AGENTS.md
├── requirements.txt
├── .gitignore
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   └── task.yml
│   └── pull_request_template.md
├── data/
│   └── raw/
│       └── .gitkeep
├── docs/
│   ├── project_status.html
│   ├── data_example.md
│   ├── model_val.md
│   └── experiments/
│       ├── index.md
│       └── 0823_example_001_baseline.md
├── notebooks/
│   └── 0823_example_001_baseline.ipynb
└── models/
    └── .gitkeep
```

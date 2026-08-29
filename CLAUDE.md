# manufacturing_AI — 프로젝트 지침

이 파일은 이 리포지토리에서 작업할 때 참고할 총괄 지침 문서다. 개별 데이터셋에 대해
새롭게 알게 되는 사실, 컬럼 의미, 주의사항 등은 이 파일에 직접 쓰지 말고
`docs/lsw/<데이터셋명>/notes.md` 에 정리하고, 여기서는 링크만 건다.

`docs/` 아래는 팀원별로 `docs/<본인 아이디>/` 하위에 각자의 노트를 둔다 (예: 이 파일을
쓰는 사람은 `docs/lsw/`). 다른 팀원의 개인 노트를 수정할 때는 먼저 확인을 구한다.

## 이 파일과 AGENTS.md / CONTRIBUTING.md의 관계

이 저장소의 작업 방식(브랜치 전략, 커밋 메시지, 노트북·실험 문서 작성 규칙,
`src/`·`results/`·`data/processed/`를 함부로 만들지 않는 것 등)에 대한 원본은
[AGENTS.md](AGENTS.md)와 [CONTRIBUTING.md](CONTRIBUTING.md)다. 이 CLAUDE.md는 그
규칙을 대체하지 않고, **데이터/프로젝트에 대해 새로 알게 된 지식을 누적 기록하는
용도**로만 사용한다. 작업 워크플로우 관련 결정은 항상 AGENTS.md/CONTRIBUTING.md를
따른다.

## 프로젝트 진행현황

- 최종 프로젝트 방향성과 확장 로드맵: [docs/lsw/project/scope_and_roadmap.md](docs/lsw/project/scope_and_roadmap.md)
  (Siemens AOI 데이터 기반 false call 감소 2차 판정기 PoC + 불균형/drift/라벨노이즈/
  비지도 이상탐지로의 scope 확장 계획)
- **새 세션은 여기부터 읽는다**: [docs/lsw/project/handoff.md](docs/lsw/project/handoff.md)
  — 지금까지 확정된 결론, 진행 중인 작업, 다음 할 일을 압축한 인수인계 문서.
  오래된 스냅샷일 수 있으니 실제 코드/커밋 상태와 다르면 최신 쪽을 따른다.

## 데이터셋 목록

### siemens_aoi_v2

- 위치: [data/raw/](data/raw/) (`dataset.csv`, `mapping.json` — Git에는 커밋되지 않음,
  `docs/data_example.md` 참고해서 실제 데이터 문서도 별도로 필요하면 작성)
- 상세 노트: [docs/lsw/siemens_aoi_v2/notes.md](docs/lsw/siemens_aoi_v2/notes.md)
- 한 줄 요약: Siemens AG 독일 SMT(표면실장) 생산라인의 AOI(자동광학검사) 실측 데이터.
  AOI가 불량으로 판정한 것 중 실제로는 정상인 "false call"을 가려내는 문제(false call
  reduction)를 다루는 공개 데이터셋(Data in Brief, 2024).

## 새 사실을 기록할 때 규칙

- 컬럼 의미, 데이터 특성, 논문/외부 자료에서 확인한 내용, 분석 중 발견한 이상치나
  주의사항 등은 모두 `docs/lsw/<데이터셋명>/notes.md`에 날짜와 함께 추가한다.
- 코드/구조에서 바로 파악 가능한 내용(파일 경로, 함수 목록 등)은 기록하지 않는다 —
  다시 탐색하면 되는 정보이기 때문. 기록 대상은 **외부에서 찾은 배경지식**,
  **분석으로만 알 수 있는 데이터 특성**, **재현하기 번거로운 결론** 위주로 한다.
- 데이터셋이 새로 추가되면 위 "데이터셋 목록" 섹션에 항목을 추가하고
  `docs/lsw/<데이터셋명>/notes.md`를 새로 만든다.

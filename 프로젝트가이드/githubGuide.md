# Git 사용 가이드

---

## 브랜치 전략

```
main      ── 최종 완성본. 직접 push 금지
  │
  ├── feature/brain        ← 뇌종양 담당
  ├── feature/skin         ← 피부 담당
  ├── feature/eyes         ← 안과 담당
  ├── feature/lumbarSpine  ← 척추 담당
  ├── feature/kidney       ← 신장 담당
  └── feature/colon        ← 대장암 담당
```

**규칙:** 각자 본인 `feature/모듈명` 브랜치에서만 작업. `main`에 직접 push 금지.
**로컬에는 feature 브랜치 하나만 사용합니다. 로컬 main 브랜치는 만들지 않아도 됩니다.**

`git branch` 입력 시 아래처럼 나오면 정상:
```
* feature/brain
```
`*` 옆에 있는 게 현재 사용 중인 브랜치.

**PR:** `feature/모듈명` → `main` 으로 Pull Request 생성.  
**CI:** PR 생성 또는 main push 시 자동으로 테스트 실행.

---

## 처음 한 번만 (프로젝트 받고 브랜치 만들기)

```cmd
git clone https://github.com/MadSadly/MediCore.git

git checkout -b feature/본인모듈명
git push -u origin feature/본인모듈명
```

---

## 매일 작업 시작할 때

```cmd
git pull origin main
```

> feature 브랜치에 있는 상태에서 바로 실행.
> origin/main의 최신 코드가 내 브랜치에 바로 반영됨.
> 로컬 main 브랜치로 이동할 필요 없음.

---

## 작업하고 저장할 때

```cmd
git add 파일명
git commit -m "작업 내용 설명"
git push origin feature/본인모듈명
```

파일 여러 개면:
```cmd
git add AI/DH/
git commit -m "뇌종양 모델 전처리 추가"
git push origin feature/brain
```

---

## 작업 완료 후 main에 합치기 (PR)

1. GitHub 웹사이트 접속
2. `feature/본인모듈` → `main` 으로 **Pull Request** 생성
3. 팀원 리뷰 후 Merge

---

## 자주 쓰는 명령어

| 명령어 | 하는 일 |
|--------|---------|
| `git status` | 현재 변경사항 확인 |
| `git branch` | 브랜치 목록 |
| `git pull origin main` | origin/main 최신 코드를 내 브랜치에 반영 |
| `git push origin 브랜치명` | GitHub에 올리기 |
| `git add 파일` | 커밋할 파일 선택 |
| `git commit -m "메시지"` | 저장 |
| `git log --oneline` | 커밋 히스토리 보기 |

---

## 충돌(Conflict) 났을 때

같은 파일을 두 명이 동시에 수정하면 발생.

```
<<<<<<< feature/brain
    내가 수정한 코드
=======
    조원이 수정한 코드
>>>>>>> main
```

파일 열어서 둘 중 하나 선택하거나 합친 뒤:
```cmd
git add .
git commit -m "충돌 해결"
```

> 각자 담당 폴더(AI/DH/, AI/GW/ 등)가 나뉘어 있어서 충돌 날 일은 거의 없음.

---

## 하루 흐름 요약

```
작업 시작 (feature/본인모듈 브랜치에서)
  → git pull origin main  ← 한 줄로 최신화 끝
  → 코드 작업
  → git add → git commit → git push origin feature/본인모듈명
  → 완료되면 GitHub에서 PR 생성 (feature → main)
```

<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GitHub로 프로젝트 & 포트폴리오 만들기 — 기본 설정과 사용법</title>
<style>
  :root {
    --bg: #0d1117; --panel: #161b22; --border: #30363d; --text: #e6edf3;
    --muted: #8b949e; --accent: #2f81f7; --green: #3fb950; --yellow: #d29922; --red: #f85149;
    --code-bg: #0b0f14;
  }
  * { box-sizing: border-box; }
  html { scroll-behavior: smooth; }
  body {
    margin: 0; background: var(--bg); color: var(--text);
    font-family: "Pretendard", "Noto Sans KR", -apple-system, "Segoe UI", sans-serif;
    line-height: 1.7; font-size: 16px;
  }
  .layout { display: grid; grid-template-columns: 260px 1fr; min-height: 100vh; }
  nav {
    position: sticky; top: 0; height: 100vh; overflow-y: auto;
    background: var(--panel); border-right: 1px solid var(--border); padding: 24px 18px;
  }
  nav h2 { font-size: 15px; margin: 0 0 12px; color: var(--muted); letter-spacing: .05em; }
  nav ol { padding-left: 20px; margin: 0; }
  nav li { margin: 6px 0; font-size: 14px; }
  nav a { color: var(--text); text-decoration: none; }
  nav a:hover { color: var(--accent); }
  main { max-width: 920px; padding: 40px 48px 120px; }
  header.hero { border-bottom: 1px solid var(--border); padding-bottom: 24px; margin-bottom: 32px; }
  header.hero h1 { font-size: 32px; margin: 0 0 8px; }
  header.hero p { color: var(--muted); margin: 0; }
  section { margin-bottom: 56px; scroll-margin-top: 20px; }
  h2 { font-size: 24px; border-bottom: 1px solid var(--border); padding-bottom: 8px; }
  h2 .num { color: var(--accent); margin-right: 8px; }
  h3 { font-size: 18px; margin-top: 28px; }
  a { color: var(--accent); }
  code { font-family: "JetBrains Mono", "D2Coding", Consolas, monospace; font-size: 0.9em; }
  p code, li code, td code { background: #262c36; padding: 2px 6px; border-radius: 4px; }
  .code {
    position: relative; background: var(--code-bg); border: 1px solid var(--border);
    border-radius: 8px; margin: 12px 0 18px;
  }
  .code .label {
    font-size: 12px; color: var(--muted); padding: 6px 14px; border-bottom: 1px solid var(--border);
  }
  .code pre { margin: 0; padding: 14px; overflow-x: auto; }
  .code button {
    position: absolute; top: 4px; right: 6px; background: #21262d; color: var(--text);
    border: 1px solid var(--border); border-radius: 6px; font-size: 12px; padding: 3px 10px; cursor: pointer;
  }
  .code button:hover { border-color: var(--accent); }
  .cm { color: #6e7681; }
  .callout { border-left: 4px solid var(--accent); background: #121d2f; padding: 12px 16px; border-radius: 6px; margin: 16px 0; }
  .callout.tip { border-color: var(--green); background: #0f1f14; }
  .callout.warn { border-color: var(--yellow); background: #231c0b; }
  .callout.danger { border-color: var(--red); background: #2a1114; }
  .callout strong:first-child { display: block; margin-bottom: 4px; }
  table { width: 100%; border-collapse: collapse; margin: 14px 0; font-size: 15px; }
  th, td { border: 1px solid var(--border); padding: 8px 12px; text-align: left; vertical-align: top; }
  th { background: var(--panel); }
  .flow { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin: 16px 0; }
  .flow span { background: var(--panel); border: 1px solid var(--border); border-radius: 20px; padding: 6px 14px; font-size: 14px; }
  .flow i { color: var(--muted); font-style: normal; }
  .checklist li { list-style: none; margin-left: -20px; }
  .checklist input { margin-right: 8px; transform: scale(1.15); }
  .badge { display: inline-block; font-size: 12px; padding: 1px 8px; border-radius: 10px; background: #1f6feb33; color: #79c0ff; margin-left: 6px; vertical-align: middle; }
  @media (max-width: 860px) {
    .layout { grid-template-columns: 1fr; }
    nav { position: static; height: auto; border-right: 0; border-bottom: 1px solid var(--border); }
    main { padding: 24px 18px 80px; }
  }
  @media print {
    nav, .code button { display: none; }
    .layout { display: block; }
    body { background: #fff; color: #000; }
  }
</style>
</head>
<body>
<div class="layout">
<nav>
  <h2>목차</h2>
  <ol>
    <li><a href="#overview">전체 흐름</a></li>
    <li><a href="#account">GitHub 계정 & 프로필</a></li>
    <li><a href="#git">Git 설치 & 초기 설정</a></li>
    <li><a href="#auth">인증 설정 (SSH / gh)</a></li>
    <li><a href="#repo">첫 저장소 만들기</a></li>
    <li><a href="#daily">매일 쓰는 명령어</a></li>
    <li><a href="#branch">브랜치 & Pull Request</a></li>
    <li><a href="#manage">Issues / Projects로 관리</a></li>
    <li><a href="#readme">포트폴리오용 README</a></li>
    <li><a href="#profile">프로필 README & 핀 고정</a></li>
    <li><a href="#pages">GitHub Pages 포트폴리오 사이트</a></li>
    <li><a href="#ros">ROS 2 프로젝트 팁</a></li>
    <li><a href="#trouble">자주 만나는 문제</a></li>
    <li><a href="#checklist">최종 체크리스트</a></li>
  </ol>
</nav>

<main>
<header class="hero">
  <h1>GitHub로 프로젝트하면서 포트폴리오 만들기</h1>
  <p>기본 설정 → 프로젝트 관리 → 포트폴리오로 보여주기까지, 순서대로 따라 하는 가이드 (Ubuntu 기준)</p>
</header>

<!-- 1 -->
<section id="overview">
  <h2><span class="num">1</span>전체 흐름</h2>
  <p>포트폴리오는 "프로젝트를 다 끝내고 정리"하는 게 아니라, <strong>프로젝트를 하는 동안 GitHub에 기록이 쌓이게</strong> 하는 것이 핵심입니다. 커밋 기록, 이슈, PR, README가 그대로 실력의 증거가 됩니다.</p>
  <div class="flow">
    <span>① 계정·프로필</span><i>→</i>
    <span>② Git 설정</span><i>→</i>
    <span>③ SSH 인증</span><i>→</i>
    <span>④ 저장소 생성</span><i>→</i>
    <span>⑤ 커밋·푸시 습관</span><i>→</i>
    <span>⑥ README 정리</span><i>→</i>
    <span>⑦ 프로필·Pages 공개</span>
  </div>
  <table>
    <tr><th>보는 사람</th><th>확인하는 것</th></tr>
    <tr><td>채용 담당자 (30초)</td><td>프로필 README, 고정(Pinned) 저장소 6개, 데모 GIF</td></tr>
    <tr><td>현업 개발자 (5분)</td><td>README 구조, 코드 구성, 커밋 메시지, 이슈/PR 흐름</td></tr>
    <tr><td>면접관</td><td>"왜 이렇게 설계했나" — 문제 해결 과정 기록 (Issues, 트러블슈팅 문서)</td></tr>
  </table>
</section>

<!-- 2 -->
<section id="account">
  <h2><span class="num">2</span>GitHub 계정 & 프로필 기본 설정</h2>
  <ol>
    <li><a href="https://github.com/signup" target="_blank">github.com/signup</a>에서 가입. <strong>사용자 이름(username)은 URL이 되므로</strong> 본명 기반의 깔끔한 이름 추천 (예: <code>kim-sewoong</code>, <code>swkim-dev</code>).</li>
    <li><strong>Settings → Profile</strong>: 프로필 사진, Name, Bio(한 줄 소개), 지역, 블로그/링크 입력.</li>
    <li><strong>Settings → Password and authentication</strong>: <strong>2단계 인증(2FA)</strong> 켜기 (기여 활동이 있는 계정은 사실상 필수).</li>
    <li><strong>Settings → Emails</strong>: "Keep my email addresses private" 체크 → 표시되는 <code>ID+username@users.noreply.github.com</code> 주소를 Git 설정에 사용하면 커밋에 개인 이메일이 노출되지 않습니다.</li>
  </ol>
  <div class="callout tip"><strong>팁</strong>Settings → Public profile에서 "Include private contributions on my profile"을 켜면, 비공개 저장소 작업도 잔디(contribution graph)에 표시됩니다.</div>
</section>

<!-- 3 -->
<section id="git">
  <h2><span class="num">3</span>Git 설치 & 초기 설정</h2>
  <p>이 PC에는 이미 Git 2.43이 설치되어 있지만, <strong>전역 사용자 설정은 아직 비어 있습니다</strong>. 아래를 한 번만 실행하세요.</p>
  <div class="code"><div class="label">bash — 설치 확인</div><pre><code>git --version            <span class="cm"># 없으면: sudo apt update && sudo apt install -y git</span></code></pre></div>
  <div class="code"><div class="label">bash — 사용자 정보 (커밋 작성자로 기록됨)</div><pre><code>git config --global user.name  "홍길동"
git config --global user.email "12345678+username@users.noreply.github.com"   <span class="cm"># GitHub 계정 이메일 또는 noreply 주소</span></code></pre></div>
  <div class="code"><div class="label">bash — 권장 기본값</div><pre><code>git config --global init.defaultBranch main     <span class="cm"># 새 저장소 기본 브랜치를 main으로</span>
git config --global core.editor "nano"           <span class="cm"># 또는 "code --wait" (VS Code)</span>
git config --global pull.rebase false            <span class="cm"># pull 시 merge 방식 (초보자에게 단순)</span>
git config --global core.autocrlf input          <span class="cm"># 줄바꿈 문제 방지 (Linux/Mac)</span>
git config --global color.ui auto

git config --global --list                       <span class="cm"># 설정 확인</span></code></pre></div>
</section>

<!-- 4 -->
<section id="auth">
  <h2><span class="num">4</span>인증 설정 — SSH 키 (추천) 또는 GitHub CLI</h2>
  <div class="callout warn"><strong>주의</strong>GitHub는 2021년부터 <code>git push</code> 시 <strong>계정 비밀번호 인증을 지원하지 않습니다</strong>. SSH 키나 토큰(gh CLI가 자동 처리)이 필요합니다.</div>

  <h3>방법 A. SSH 키 <span class="badge">추천</span></h3>
  <div class="code"><div class="label">bash — 1) 키 생성</div><pre><code>ssh-keygen -t ed25519 -C "github"     <span class="cm"># 엔터 3번 (경로 기본값, 암호는 선택)</span></code></pre></div>
  <div class="code"><div class="label">bash — 2) ssh-agent에 등록</div><pre><code>eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519</code></pre></div>
  <div class="code"><div class="label">bash — 3) 공개키 복사</div><pre><code>cat ~/.ssh/id_ed25519.pub      <span class="cm"># 출력된 한 줄(ssh-ed25519 ...) 전체를 복사</span></code></pre></div>
  <p>4) GitHub → <strong>Settings → SSH and GPG keys → New SSH key</strong> → Title(예: <code>ubuntu-desktop</code>), Key 칸에 붙여넣기 → Add.</p>
  <div class="code"><div class="label">bash — 5) 연결 테스트</div><pre><code>ssh -T git@github.com
<span class="cm"># "Hi username! You've successfully authenticated..." 나오면 성공</span></code></pre></div>
  <div class="callout danger"><strong>절대 금지</strong><code>id_ed25519</code>(개인키, .pub 없는 파일)는 누구에게도 보내거나 업로드하지 마세요. GitHub에 등록하는 것은 <code>.pub</code> 파일뿐입니다.</div>

  <h3>방법 B. GitHub CLI (<code>gh</code>)</h3>
  <p>터미널에서 저장소 생성, PR 생성까지 할 수 있어 편리합니다.</p>
  <div class="code"><div class="label">bash</div><pre><code>sudo apt install -y gh        <span class="cm"># Ubuntu 기본 저장소 버전</span>
gh auth login                 <span class="cm"># GitHub.com → SSH → 위에서 만든 키 선택 → 브라우저 로그인</span>
gh auth status</code></pre></div>
</section>

<!-- 5 -->
<section id="repo">
  <h2><span class="num">5</span>첫 저장소 만들기</h2>
  <h3>경우 1. GitHub에서 먼저 만들고 clone (가장 쉬움)</h3>
  <ol>
    <li>GitHub 우측 상단 <strong>+ → New repository</strong></li>
    <li>Repository name: 프로젝트를 설명하는 이름 (예: <code>turtlebot3-autonomous-track</code>)</li>
    <li>Description 한 줄 작성, <strong>Public</strong> 선택 (포트폴리오는 공개여야 보입니다)</li>
    <li><strong>Add a README</strong> 체크, <strong>.gitignore</strong> 템플릿 선택(Python, C++ 등), <strong>License</strong>는 보통 MIT</li>
  </ol>
  <div class="code"><div class="label">bash</div><pre><code>cd ~/projects
git clone git@github.com:username/turtlebot3-autonomous-track.git
cd turtlebot3-autonomous-track</code></pre></div>

  <h3>경우 2. 이미 작업 중인 로컬 폴더를 올리기</h3>
  <p>GitHub에서 <strong>빈 저장소</strong>(README·.gitignore 체크 해제)를 만든 뒤:</p>
  <div class="code"><div class="label">bash</div><pre><code>cd ~/my_project
git init
<span class="cm"># .gitignore 먼저 만들기! (빌드 결과물·비밀키가 올라가지 않도록)</span>
git add .
git status                    <span class="cm"># 올라갈 파일 목록 반드시 확인</span>
git commit -m "Initial commit"
git remote add origin git@github.com:username/my_project.git
git push -u origin main</code></pre></div>
  <div class="code"><div class="label">bash — gh CLI로 한 번에</div><pre><code>gh repo create my_project --public --source=. --remote=origin --push</code></pre></div>
</section>

<!-- 6 -->
<section id="daily">
  <h2><span class="num">6</span>매일 쓰는 명령어 (기본 사이클)</h2>
  <div class="flow">
    <span>pull (최신화)</span><i>→</i><span>코드 수정</span><i>→</i><span>status / diff</span><i>→</i><span>add</span><i>→</i><span>commit</span><i>→</i><span>push</span>
  </div>
  <div class="code"><div class="label">bash</div><pre><code>git pull                         <span class="cm"># 작업 시작 전 최신 상태로</span>
git status                       <span class="cm"># 무엇이 바뀌었나</span>
git diff                         <span class="cm"># 바뀐 내용 자세히</span>
git add src/controller.py        <span class="cm"># 커밋할 파일 선택 (전체: git add .)</span>
git commit -m "feat: 라인 추종 PID 제어기 추가"
git push                         <span class="cm"># GitHub에 업로드</span>

git log --oneline --graph -10    <span class="cm"># 최근 기록 보기</span></code></pre></div>

  <h3>좋은 커밋 메시지 규칙</h3>
  <p>"작게, 자주, 의미 있게" 커밋하세요. 커밋 기록 자체가 개발 과정을 보여주는 포트폴리오입니다.</p>
  <table>
    <tr><th>접두어</th><th>의미</th><th>예시</th></tr>
    <tr><td><code>feat</code></td><td>새 기능</td><td><code>feat: Nav2 waypoint 주행 노드 추가</code></td></tr>
    <tr><td><code>fix</code></td><td>버그 수정</td><td><code>fix: 라이다 프레임 TF 오류 수정</code></td></tr>
    <tr><td><code>docs</code></td><td>문서</td><td><code>docs: README에 실행 방법 추가</code></td></tr>
    <tr><td><code>refactor</code></td><td>구조 개선</td><td><code>refactor: 센서 처리 로직 클래스로 분리</code></td></tr>
    <tr><td><code>chore</code></td><td>설정·기타</td><td><code>chore: .gitignore에 build/ 추가</code></td></tr>
  </table>
  <div class="callout"><strong>되돌리기 기본</strong>
    <code>git restore 파일</code> — 수정 취소(커밋 전) ·
    <code>git restore --staged 파일</code> — add 취소 ·
    <code>git commit --amend</code> — 직전 커밋 메시지 수정(push 전에만) ·
    <code>git revert 커밋ID</code> — 이미 push한 커밋을 안전하게 되돌리기
  </div>
</section>

<!-- 7 -->
<section id="branch">
  <h2><span class="num">7</span>브랜치 & Pull Request</h2>
  <p>혼자 하는 프로젝트라도 <strong>기능별 브랜치 → PR → merge</strong> 흐름을 쓰면, "협업 프로세스를 이해한다"는 것을 보여줄 수 있습니다.</p>
  <div class="code"><div class="label">bash</div><pre><code>git switch -c feature/obstacle-avoidance   <span class="cm"># 새 브랜치 생성 + 이동</span>
<span class="cm"># ... 작업 & 커밋 ...</span>
git push -u origin feature/obstacle-avoidance

gh pr create --fill                        <span class="cm"># 또는 GitHub 웹에서 "Compare & pull request" 클릭</span>
gh pr merge --squash --delete-branch       <span class="cm"># 확인 후 병합</span>

git switch main
git pull</code></pre></div>
  <p>PR 본문에는 <strong>무엇을 / 왜 / 어떻게 테스트했는지</strong>, 가능하면 스크린샷·GIF를 붙이세요. <code>Closes #3</code>이라고 쓰면 병합 시 3번 이슈가 자동으로 닫힙니다.</p>
</section>

<!-- 8 -->
<section id="manage">
  <h2><span class="num">8</span>Issues / Projects / Milestones로 프로젝트 관리</h2>
  <table>
    <tr><th>기능</th><th>용도</th><th>포트폴리오 효과</th></tr>
    <tr><td><strong>Issues</strong></td><td>할 일, 버그, 아이디어를 하나씩 등록</td><td>문제 정의 → 해결 과정이 기록됨</td></tr>
    <tr><td><strong>Labels</strong></td><td><code>bug</code>, <code>feature</code>, <code>docs</code> 등 분류</td><td>체계적인 관리 인상</td></tr>
    <tr><td><strong>Milestones</strong></td><td>"v0.1 시뮬레이션 완료" 같은 단계 목표</td><td>일정 관리 능력</td></tr>
    <tr><td><strong>Projects</strong></td><td>칸반 보드 (Todo / In Progress / Done)</td><td>팀 프로젝트에서 역할 분담 증명</td></tr>
    <tr><td><strong>Releases</strong></td><td>완성 단계마다 태그(<code>v1.0.0</code>)와 변경 내역</td><td>"끝까지 완성했다"는 증거</td></tr>
    <tr><td><strong>Wiki / docs/</strong></td><td>설계 문서, 트러블슈팅 기록</td><td>면접에서 이야기할 소재</td></tr>
  </table>
  <div class="code"><div class="label">bash — 릴리스 만들기</div><pre><code>git tag -a v1.0.0 -m "첫 완성 버전"
git push origin v1.0.0
gh release create v1.0.0 --generate-notes</code></pre></div>
</section>

<!-- 9 -->
<section id="readme">
  <h2><span class="num">9</span>포트폴리오용 README 작성법</h2>
  <p>README는 저장소의 표지입니다. 아래 구조를 복사해서 채우세요.</p>
  <div class="code"><div class="label">README.md 템플릿</div><pre><code># 🤖 프로젝트 이름

> 한 줄 소개: 무엇을, 왜 만들었는지

![demo](docs/demo.gif)

## 📌 개요
- 기간: 2026.09 ~ 2026.11 (개인 / 팀 N명 — 내 역할: ○○)
- 목표: 해결하려는 문제

## 🛠 기술 스택
ROS 2 Humble · Python · C++ · Gazebo · Nav2

## ✨ 주요 기능
- 기능 1
- 기능 2

## 🏗 구조
(아키텍처 다이어그램 또는 노드/토픽 그래프 이미지)

## 🚀 실행 방법
```bash
git clone ...
colcon build
ros2 launch ...
```

## 🧩 트러블슈팅
| 문제 | 원인 | 해결 |
|------|------|------|
| ... | ... | ... |

## 📈 결과 & 배운 점
- 정량적 결과 (예: 주행 성공률 95%)
- 다음에 개선할 점</code></pre></div>
  <div class="callout tip"><strong>효과가 큰 3가지</strong>
    ① 맨 위 <strong>데모 GIF/영상</strong> (Peek, Kazam 등으로 녹화 → <code>docs/</code> 폴더에 저장) ·
    ② <strong>트러블슈팅 표</strong> — 면접 질문으로 직결 ·
    ③ <strong>실행 방법</strong>이 실제로 동작할 것
  </div>
  <p>저장소 메인 화면 우측 ⚙(About)에서 <strong>Description, Website, Topics</strong>(예: <code>ros2</code>, <code>robotics</code>, <code>turtlebot3</code>)도 꼭 채우세요. 검색과 첫인상에 영향을 줍니다.</p>
</section>

<!-- 10 -->
<section id="profile">
  <h2><span class="num">10</span>프로필 README & 대표 저장소 고정</h2>
  <h3>프로필 README (나만의 첫 화면)</h3>
  <ol>
    <li><strong>내 username과 똑같은 이름</strong>의 Public 저장소를 생성 (예: username이 <code>swkim-dev</code>면 저장소도 <code>swkim-dev</code>)</li>
    <li>"Add a README" 체크 → 생성하면 그 README가 프로필 맨 위에 표시됩니다.</li>
  </ol>
  <div class="code"><div class="label">프로필 README.md 예시</div><pre><code>## 안녕하세요, 로봇 소프트웨어 개발자 ○○○입니다 👋

- 🤖 관심 분야: 자율주행 로봇, ROS 2, 협동로봇 제어
- 🔭 현재: TurtleBot3 기반 자율주행 트랙 프로젝트 진행 중
- 📫 연락: (블로그/링크드인 링크)

### 🛠 Tech Stack
![ROS2](https://img.shields.io/badge/ROS2-22314E?logo=ros&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)
![C++](https://img.shields.io/badge/C++-00599C?logo=cplusplus&logoColor=white)

### 📂 대표 프로젝트
| 프로젝트 | 설명 |
|---|---|
| [turtlebot3-autonomous-track](링크) | Nav2 기반 커스텀 트랙 자율주행 |
| [cobot-pick-and-place](링크) | 협동로봇 픽앤플레이스 |</code></pre></div>
  <h3>Pinned 저장소</h3>
  <p>프로필 화면 → <strong>Customize your pins</strong> → 가장 자신 있는 저장소 최대 6개 선택. 완성도 높은 것만 고르고, 연습용 저장소는 고정하지 마세요.</p>
</section>

<!-- 11 -->
<section id="pages">
  <h2><span class="num">11</span>GitHub Pages로 포트폴리오 웹사이트 만들기</h2>
  <p>무료로 <code>https://username.github.io</code> 주소의 사이트를 만들 수 있습니다.</p>
  <ol>
    <li><strong><code>username.github.io</code></strong>라는 이름의 Public 저장소 생성 (username 부분은 본인 것으로 정확히)</li>
    <li>저장소에 <code>index.html</code> 추가 (아래 최소 예시 또는 무료 템플릿 활용)</li>
    <li><strong>Settings → Pages → Build and deployment</strong> → Source: <strong>Deploy from a branch</strong>, Branch: <code>main</code> / <code>/(root)</code> → Save</li>
    <li>1~2분 후 <code>https://username.github.io</code> 접속 확인</li>
  </ol>
  <div class="code"><div class="label">bash</div><pre><code>git clone git@github.com:username/username.github.io.git
cd username.github.io
<span class="cm"># index.html 작성 후</span>
git add . && git commit -m "feat: 포트폴리오 사이트 초안" && git push</code></pre></div>
  <div class="code"><div class="label">index.html 최소 예시</div><pre><code>&lt;!DOCTYPE html&gt;
&lt;html lang="ko"&gt;
&lt;head&gt;&lt;meta charset="UTF-8"&gt;&lt;title&gt;○○○ | Portfolio&lt;/title&gt;&lt;/head&gt;
&lt;body&gt;
  &lt;h1&gt;○○○ — Robotics Software Engineer&lt;/h1&gt;
  &lt;h2&gt;Projects&lt;/h2&gt;
  &lt;ul&gt;
    &lt;li&gt;&lt;a href="https://github.com/username/turtlebot3-autonomous-track"&gt;TurtleBot3 자율주행&lt;/a&gt; — Nav2, Gazebo&lt;/li&gt;
  &lt;/ul&gt;
&lt;/body&gt;
&lt;/html&gt;</code></pre></div>
  <div class="callout"><strong>프로젝트별 페이지도 가능</strong>일반 저장소에서도 Settings → Pages를 켜면 <code>https://username.github.io/저장소이름</code>으로 프로젝트 소개 페이지(또는 <code>docs/</code> 폴더)를 공개할 수 있습니다.</div>
</section>

<!-- 12 -->
<section id="ros">
  <h2><span class="num">12</span>ROS 2 워크스페이스 프로젝트 팁</h2>
  <p>ROS 2 프로젝트는 <strong>워크스페이스 전체가 아니라 <code>src/</code> 안의 패키지(또는 src 폴더)만</strong> 저장소로 관리하는 것이 일반적입니다. <code>build/ install/ log/</code>는 절대 올리지 마세요.</p>
  <div class="code"><div class="label">.gitignore (ROS 2 / Python / C++)</div><pre><code># colcon 빌드 결과물
build/
install/
log/

# Python
__pycache__/
*.pyc
.venv/

# 에디터 / OS
.vscode/
.idea/
*.swp
.DS_Store

# 대용량·비밀 파일
*.bag
*.db3
.env</code></pre></div>
  <div class="code"><div class="label">bash — 패키지 단위로 저장소 만들기</div><pre><code>cd ~/ros2_ws/src/my_robot_pkg
git init
<span class="cm"># 위 .gitignore 작성</span>
git add . && git commit -m "Initial commit: my_robot_pkg"
gh repo create my_robot_pkg --public --source=. --push</code></pre></div>
  <div class="callout tip"><strong>보여주기 좋은 자료</strong><code>rqt_graph</code> 노드 그래프 캡처, Gazebo/RViz 화면 녹화 GIF, launch 파일 구조 설명을 README에 넣으면 로봇 분야 포트폴리오로서 설득력이 크게 올라갑니다.</div>
</section>

<!-- 13 -->
<section id="trouble">
  <h2><span class="num">13</span>자주 만나는 문제</h2>
  <table>
    <tr><th>증상</th><th>원인 & 해결</th></tr>
    <tr><td><code>Permission denied (publickey)</code></td><td>SSH 키 미등록/미로드 → 4장 다시 확인, <code>ssh-add ~/.ssh/id_ed25519</code>, <code>ssh -T git@github.com</code></td></tr>
    <tr><td><code>Password authentication is not supported</code></td><td>HTTPS 주소 + 비밀번호 사용 중 → <code>git remote set-url origin git@github.com:username/repo.git</code></td></tr>
    <tr><td><code>! [rejected] ... (fetch first)</code></td><td>GitHub에 내 로컬에 없는 커밋이 있음 → <code>git pull</code> 후 다시 <code>git push</code></td></tr>
    <tr><td>pull 후 <code>CONFLICT</code></td><td>같은 곳을 양쪽에서 수정 → 파일 안의 <code>&lt;&lt;&lt;&lt;&lt;&lt;&lt;</code> ~ <code>&gt;&gt;&gt;&gt;&gt;&gt;&gt;</code> 구간을 직접 정리 → <code>git add</code> → <code>git commit</code></td></tr>
    <tr><td><code>file is larger than 100 MB</code></td><td>GitHub 단일 파일 제한 100MB → 커밋에서 제외하고 .gitignore 추가, 꼭 필요하면 Git LFS(<code>git lfs track "*.bag"</code>)</td></tr>
    <tr><td>빌드 폴더를 실수로 올림</td><td><code>.gitignore</code> 추가 후 <code>git rm -r --cached build install log</code> → 커밋</td></tr>
    <tr><td>API 키·비밀번호를 커밋함</td><td><strong>즉시 해당 키를 폐기/재발급</strong>하세요. 커밋을 지워도 기록·포크에 남을 수 있습니다.</td></tr>
  </table>
</section>

<!-- 14 -->
<section id="checklist">
  <h2><span class="num">14</span>최종 체크리스트</h2>
  <ul class="checklist">
    <li><label><input type="checkbox"> GitHub 가입, 프로필 사진·Bio 작성, 2FA 설정</label></li>
    <li><label><input type="checkbox"> <code>git config --global user.name / user.email</code> 설정</label></li>
    <li><label><input type="checkbox"> SSH 키 등록 & <code>ssh -T git@github.com</code> 성공</label></li>
    <li><label><input type="checkbox"> 프로젝트 저장소 생성 + <code>.gitignore</code> + LICENSE</label></li>
    <li><label><input type="checkbox"> 작업할 때마다 의미 있는 단위로 커밋 & 푸시</label></li>
    <li><label><input type="checkbox"> 기능은 브랜치 → PR → merge로 진행</label></li>
    <li><label><input type="checkbox"> Issues로 할 일·버그 기록, 완성 시 Release 생성</label></li>
    <li><label><input type="checkbox"> README: 데모 GIF, 기술 스택, 실행 방법, 트러블슈팅</label></li>
    <li><label><input type="checkbox"> 저장소 About에 Description·Topics 입력</label></li>
    <li><label><input type="checkbox"> 프로필 README(<code>username/username</code>) 작성</label></li>
    <li><label><input type="checkbox"> 대표 저장소 최대 6개 Pinned</label></li>
    <li><label><input type="checkbox"> (선택) <code>username.github.io</code> 포트폴리오 사이트 공개</label></li>
  </ul>
  <p style="color:var(--muted);font-size:14px;margin-top:32px">참고: <a href="https://docs.github.com/ko/get-started" target="_blank">GitHub Docs 시작하기</a> · <a href="https://docs.github.com/ko/pages" target="_blank">GitHub Pages 문서</a> · <a href="https://docs.github.com/ko/account-and-profile/setting-up-and-managing-your-github-profile/customizing-your-profile/managing-your-profile-readme" target="_blank">프로필 README 관리</a></p>
</section>
</main>
</div>

<script>
  // 코드 블록마다 복사 버튼 추가 (주석 포함 원문 복사)
  document.querySelectorAll('.code').forEach(block => {
    const btn = document.createElement('button');
    btn.textContent = '복사';
    btn.addEventListener('click', () => {
      const text = block.querySelector('pre').innerText;
      navigator.clipboard.writeText(text).then(() => {
        btn.textContent = '복사됨 ✓';
        setTimeout(() => (btn.textContent = '복사'), 1500);
      });
    });
    block.appendChild(btn);
  });
  // 체크리스트 상태 저장
  document.querySelectorAll('.checklist input').forEach((cb, i) => {
    const key = 'gh-guide-check-' + i;
    cb.checked = localStorage.getItem(key) === '1';
    cb.addEventListener('change', () => localStorage.setItem(key, cb.checked ? '1' : '0'));
  });
</script>
</body>
</html>

# 프로젝트 컨텍스트 및 배경 설명

## 프로젝트 개요

**제목**: DDoS Learning and Designing Platform for Open RAN-based 5G Systems

**원래 주제**: 5G base station attack and defence between CU and DU

**목적**: 오픈소스 프로젝트인 OAI 5G환경에서, F1 인터페이스를 통해 DDoS 공격, 공격 탐지와 방어를 구현/연구해보록 돕는 프로그램을 만드는 것

**대상 사용자**: 보안 학습자 (특히 입문자)

**선배 조언**: 학부생이 구현 가능한 수준에서 최대한 대중적인 툴을 사용

## 졸업 프로젝트 경진대회 정보

### 성적 계산 방식
- 전시회: 50% (외부 위원 채점)
- 지도교수: 50%

### 포스터 규정
- 크기: A1 (1장만)
- 포함 내용: 제목, 조원 학번, 이름, 지도교수
- 출력: 자체 출력 후 당일 현장에 가져가기

### 장소 정보
- 테이블 크기: 100cm x 75cm x 50cm
- 제공 장비: 테이블, 전원 콘센트

### 발표 시간
- 총 시간: 5분
  - 학생 발표: 3분
  - 심사위원 질문: 2분
- 참가팀이 많아 2개 그룹으로 나누어 진행
- 학생 발표 후 심사위원 질문 시작

## 프로토콜 활용 계획

각 모듈에 대해 다음 프로토콜들을 활용:

- **O-CU-CP**: RRC, PDCP
- **O-CU-UP**: SDAP, PDCP
- **O-DU**: RLC, MAC, PHY-high (Scrambling Modulation, Layer mapping, Precoding, RE mapping)

## 공격 방법론

### F1-C (Control)
- Massive UE connection
- UE context manage, RRC/PDCP signaling exchange
- Hand over, Tracking Area Update
- PDU Session, Bearer Flooding

### F1-U (Data)
- UDP Flood

### 공격 기능 강화 옵션

#### F1AP Vulnerability
- **Information sniffing**: IP/access permission 등을 얻어 공격 조건 완화
- **Fuzzing**: 다양한 입력 시도하여 크래시 유발, 제로데이 발견

#### Fast flux

#### 분산 공격 (DDoS 업그레이드)
- 봇넷 예시
- 다지역 다노드로 분산식 도스 공격 시뮬레이션

#### Auto mode

## 탐지 방법론

- **Get index**: 탐지되는 기준치
- **Graph layout**: GUI에서 그래프 레이아웃
- **Detect attack**: 허니팟 기법 등
- **Auto mode**

## 방어 방법론

- Filtering
- Rate Limiting / Throttling (dynamic)
- Dynamic allocation of DU by CU (disconnect/reboot)
- Self protection (RAN changes ip and reboot)
- Encryption/Authentication/Integrity
- Auto mode

## 사용 툴

### 검색 소스
- https://sectools.org

### GitHub 저장소
- https://github.com/asset-group/5ghoul-5g-nr-attacks
- https://github.com/asset-group/Sni5Gect-5GNR-sniffing-and-exploitation
- https://github.com/NewEraCracker/LOIC/
- https://github.com/DynamicDesignz/HOIC
- https://github.com/gkbrk/slowloris
- https://sourceforge.net/projects/r-u-dead-yet/
- https://github.com/Karlheinzniebuhr/torshammer

### 도구 목록
- trinoo
- TFN
- TFN2K
- Stacheldraht
- tcpdump
- Scapy
- hping3
- iperf3

**참고**: 가능하면 제일 유명한 툴들을 골라 사용하되 부족하면 깃헙에서 직접 찾아 사용할 것

## 참고 자료 및 링크

### O-RAN specifications

#### 보안 그룹
https://specifications.o-ran.org/specifications?QueryOptions=%7B%22SearchString%22%3Anull%2C%22DocumentTypeIds%22%3Anull%2C%22Version%22%3Anull%2C%22WorkGroupId%22%3A24%2C%22ReleaseId%22%3Anull%2C%22FeaturePackageId%22%3Anull%2C%22FileType%22%3Anull%2C%22ShowLatest%22%3Atrue%2C%22IsVisible%22%3Afalse%2C%22PublicationDateRange%22%3A%7B%22StartDate%22%3Anull%2C%22EndDate%22%3Anull%7D%7D

#### F1 인터페이스 그룹
https://specifications.o-ran.org/specifications?QueryOptions=%7B%22SearchString%22%3Anull%2C%22DocumentTypeIds%22%3Anull%2C%22Version%22%3Anull%2C%22WorkGroupId%22%3A11%2C%22ReleaseId%22%3Anull%2C%22FeaturePackageId%22%3Anull%2C%22FileType%22%3Anull%2C%22ShowLatest%22%3Atrue%2C%22IsVisible%22%3Afalse%2C%22PublicationDateRange%22%3A%7B%22StartDate%22%3Anull%2C%22EndDate%22%3Anull%7D%7D

### OAI github documents

#### OAI doc 폴더
https://gitlab.eurecom.fr/oai/openairinterface5g/-/tree/develop/doc

#### UE 디자인
https://gitlab.eurecom.fr/oai/openairinterface5g/-/blob/develop/doc/nr-ue-design.md

#### 멀티 UE
https://gitlab.eurecom.fr/oai/openairinterface5g/-/blob/develop/doc/NR_SA_Tutorial_OAI_multi_UE.md

#### F1 디자인
https://gitlab.eurecom.fr/oai/openairinterface5g/-/tree/develop/doc/F1AP

#### RRC 디자인
https://gitlab.eurecom.fr/oai/openairinterface5g/-/tree/develop/doc/RRC

#### E1 split 디자인
https://gitlab.eurecom.fr/oai/openairinterface5g/-/tree/develop/ci-scripts/yaml_files/5g_rfsimulator_e1

**참고**: 참고하면 좋을 자료, 링크이니 무조건 들어가서 내용 확인해볼 것

## 용어 정리

### 네트워크 유닛
- 기본 oai 네트워크 (CN, CUCP, CUUP, DU, UE)
- 공격자 (감염자 포함)
- 탐지자
- 방어자

### 액션 유닛
- 공격자 (감염자 포함)
- 탐지자
- 방어자

## 구현 세부사항

### UE 트래픽
기존 oai의 여러 UE가 5G를 사용하는 트래픽 시뮬레이션.

UE 종류:
- 위험 물질을 다루는 정밀 로봇팔
- 자율주행 차량
- 군사 드론
- 스마트폰
- 방송 카메라

### 대시보드
- 직관적이고 간단하게 조작 가능
- 네트워크 유닛의 모든 구성원을 토폴로지 관계로 볼 수 있음
- 기본 5G 시스템 조작 (부팅, 셧다운, 재부팅) 가능
- 시나리오 선택 가능
- 공격과 방어는 수동 모드 (파라미터 설정)와 자동 모드 (파라미터 프리셋) 두 가지
  - 파라미터: 공격할 노드 (CUCP, CUUP1, CUUP2, DU1, DU2, DU3), 공격할 방법, 방어 여부
  - 수동 모드: GUI에서의 선택에 따라 자동으로 완성되는 입력커맨드
  - 실행 방법:
    - 옵션 다 고른 후 GUI상의 실행하기 버튼 클릭
    - 복사해서 cli에 붙여넣기하여 수동입력도 가능

### 네트워크 유닛
기존 5G 시스템, 공격자, 감염자, 탐지자, 방어자는 각각 독립된 네임스페이스로 네트워크 분리.

#### 공격자
**감염자**:
- 공격자가 슬레이브로 사용할 봇넷을 네트워크 네임스페이스로 구현
- 웜으로 감염자끼리만 확산 감염되는 방식

**방법론**:
- **F1 setUp**: 시스템 연결 전/재부팅 시간에 공격
- **스캐피 속도 조절**: 스캐피 속도 조절해보기
- **sniffing**:
  - ARP로 아이피 얻기
  - 이미 가진 정보: 포트 번호
  - 반 가진 정보: 각 모듈 아이피 주소
  - 스니핑으로 얻은 정보는 info.txt에 저장

**공격 업그레이드**:
- ORAN CVE 찾기
- 크래쉬 일으키기: 어떤 패킷 보내서 리소스 충분할 때도 gnb를 망가뜨릴지
- high & low rate dos 사용 됐는지

#### 방어자
탐지자와 방어자는 서로 정보를 주고 받음.

### 시나리오
- 시나리오마다 다른 UE 사용
- UE는 공격 당할 시 어떤 오작동, 피해가 생기는지 애니메이션으로 실감나게 보여주기
- 배경: 원전, 도로, 지형 지도, 공공장소, 집회 현장 등
- 각 UE마다 LED 인디케이터로 네트워크 유닛 표시
  - 인디케이터 상태: 오프라인, 온라인, 서비스불가

### 통계 및 측정

#### 베이즈 테이블
- packet numbers로 구현
- 공격 전에 탐지하면 오탐 (false positive)
- 공격 후에 탐지하는데 정상을 오인하면 오탐 (false negative)
- 공격 후에 문제 있는 거만 골라 탐지하면 잘한 거 (true positive)
- 공격 후에 탐지 못 해내면 못한 거 (false negative)

#### 공격 효과 측정
- CPU 사용률: CU/DU 프로세서 부하
- 메모리 사용률: 시스템 메모리 소진 정도
- 네트워크 지연: F1 인터페이스 응답 시간
- 서비스 가용성: UE 연결 성공률
- 제약: 1-2개 파라미터로 충분히 가능하게, 10개+면 실행불가한 공격

#### 방어 효과 측정
- 탐지 정확도: False Positive/Negative 등 비율
- 응답 시간: 공격 탐지부터 대응까지의 시간
- 서비스 복구 시간: 공격 중단 후 정상화 시간
- 목표: 5개 다 막을 수 있으면 나이스

### 독창성
- feature.txt 읽어보고 독창성 평가하기
- 특별한 부분 필수, 프로그램 잘 돌아가는 게 다가 아님
- 독창적이라고 결론난 기능은 예시 연구나 논문 찾아보기

### 마무리
- 오프라인일 때 돌아가는지 테스트
- 재귀 있는지 체크
- 코드가 간단하게 소분된 구조인지 확인
- 컴파일해서 속도 높이기
- github 최종판 마감하기
  - 공격자, 감염자, 탐지자, 방어자 다 있는 버전
  - 탐지자와 방어자만 있는 비침습형 사이드카 컨테이너 추가 버전

## 논문 작성 가이드

### 앱스트랙 구조
1. 현 상황 / 중요성 / 문제의 원인
2. 그로 인해 발생한 문제 / 문제 정의 겸 연구 동기
3. 해결 방안 제시 / 방법론 요약
4. 기대 효과 / 실험 결과

### 개인적 경험담
내가 보안에 처음 입문할 때, 어디서부터 배워야 할지 모르겠어서 막막했는데, 만약 이런 이미 만들어진 코드를 직접 배울 수도 있고, 자유도도 높아서 내가 만든 코드도 적용해서 실험할 수 있는 플랫폼이 있었으면 좋겠다 생각했다. 나 같은 보안 입문자들에게 학습의 진입 장벽을 낮추는데 기여했다고 생각한다.

### F1 인터페이스 선택 이유
왜 하필 CU-DU 사이의 F1 인터페이스를 선택했는지:
- 5g ru는 소범위라 F1을 공격하면 광범위한 영역이 마비됨
- 집단 통제 가능성

### 논문 작성 요구사항
- 구조/도형/스크린샷 적극 활용
- technical하게 방법론 장단점 분석 (시간, 공간 복잡도, 수치화, 성능 점수, 유효 조건, 한계점)
- 어떤 학술적 방식으로, 어떤 툴을 사용하겠다는 결론에 이르렀는지

### Overleaf 작성 규칙
- 날짜.tex로 제목 설정
- 아티클 = 등호 위치 일치, ""따옴표 통일
- 검색 키워드만 {}
- ieee의 사이테이션 코드 스니펫 년도 외에도 월, 날짜 표기해야 함
- doi값 잘 찾기

### IEEE 스타일
- 페이지 상단 왼쪽: 왼쪽 정렬로 NTUST CSIE Special Project
- 페이지 상단 오른쪽: 오른쪽 정렬로 우리 제목
- 페이지 하단 왼쪽: 왼쪽 정렬로 부제목
- 페이지 하단 오른쪽: 오른쪽 정렬로 현재 페이지/총 페이지 수
- 부록: 깃헙링크 넣기

### 논문 삽화
- 시스템 구성 시각화
- 프로그램 스크린샷
- 마인드맵, 플로우차트 형식으로 시각화

### AI 검토
- 에이아이 냄새 제거 후 그래멀리로 한번 더 검토

## 포스터 작성 가이드

### 내용 구성
- 논문 각 파트를 요약
- 문제 의식
- ORAN 구조 설명
- 우리의 접근법
- 연구 성과
- 마무리

### 작성 요구사항
- 내용에서 텍스트만 추출, 냄새 제거 후 그래멀리로 한번 더 검토
- 논문 시각화

### 최종 제작
- 큐알코드 깃헙링크 갱신
- 워터마크: 학교 원형/바형 로고 + 연구실 로고
- 최종 출력 pdf로 하고 주문 넣기

## 데모 스크립트

### 구조
- 설명 + 실제 구동 영상 + 결론

### 구성 논의
- 이해하기 쉽게, 쉬운 단어로

### 상세 내용
다들 디도스 공격이라고 들어보셨나요? 보안 문제가 뉴스에 나올 때면 단골처럼 등장하는 공격 기술이 바로 디도스인데요, 막연하게만 생각했던 디도스 공격을 보안 학습자가 쉽게 연구해볼 수 있도록 연구 플랫폼을 만들었습니다.

이 프로그램은 5G 통신에 핵심 개념인 기술 오픈소스화에서 출발하는데요, 현재 이 분야에서 대표적인 오픈소스 프로젝트인 OAI를 기반으로 연구 플랫폼을 애드온처럼 추가했습니다.

이 플랫폼은 기본적으로 5가지 시나리오가 있고요, 각각 ?????입니다. 넽웤 구성은 ?가지가 있으며 공격 기술은 총 ?개, 탐지 기술은 ?개, 방어 기술은 ?개 입니다.

기본 설정된 프리셋 환경 외에도 학습자가 직접 원하는 환경으로 수정 및 적용할 수 있습니다. 각 폴더 내에 원하는 기술 코드를 짜서 넣고 새로고침만 하면 바로 실험해볼 수 있습니다.

예시를 보여드리겠습니다. (영상)

### 연습
한 달을 매일 연습해서 최종적으로는 외워지도록, 메모 필요 없도록 준비.

### 데모 영상 요구사항
- 부분 데모: 1 proper example of attack & defence, easy vocabulary easy understand
- 전체 데모: DDoS에 대한 설명 짧게 포함

## 교수님 문서

### 프로젝트 기록 통합본
- 전체 타임라인 계획서 및 이행 기록
  - 프로젝트 역할 분담, 맡은 기능 표와 그림으로 만들기
- 공부한 내용
  - 네트워크 슬라이싱 3가지 콘셉: 대역폭 속도 중점/초저지연 중점/다량 중점
  - 참고문헌 정리

## 프로젝트 규칙

### 샌드박스 룰
- add-on 폴더 내에서만 수정
- 폴더 밖 파일에 수정이 필요하면 그 파일을 폴더 내로 복제해와서 그 파일을 수정해 사용
- copied_file.txt에 기록

### 오픈 마인드 룰
- 좋은 새로운 아이디어가 있으면 얼마든지 적용
- new_idea.txt에 기록

### 항상 문서화 룰
- 새로운 파일이 생성될 때마다 file_info.txt에 기록
  - 해당 파일의 용도
  - 다른 파일간의 상관관계
  - 모든 함수의 용도 설명

### 항상 테스트 룰
- 새로운 기능 추가할 때마다 테스트를 거쳐 정상작동 확인
- 통과한 새로운 기능은 tested_feature.txt에 기록

### 항상 배우기 룰
- 구현하다 막혔을 때는 최신 논문 찾아보고 기법 배우기
- 새로 배운 것은 referred_docs.txt에 기록

## 파일 구조

```
SP5G
└── add-on
    ├── docs
    │   ├── NTUST
    │   │   ├── paper.tex
    │   │   ├── poster.json
    │   │   ├── demo_script.md
    │   │   ├── example.mp4
    │   │   └── demo.mp4
    │   └── maintainance
    │       ├── copied_file.txt
    │       ├── new_idea.txt
    │       ├── file_info.txt
    │       ├── tested_feature.txt
    │       └── referred_docs.txt
    ├── units
    │   ├── actioner
    │   │   ├── attacker
    │   │   ├── defender
    │   │   └── detector
    │   ├── dashboard
    │   ├── networker
    │   │   └── system5g
    │   │       ├── 5g_rfsimulator_custom_v2.1.10
    │   │       └── ue_traffic
    │   └── statistician
    ├── .gitignore
    ├── README.md
    └── sp5g
```

## 수정 사항

### 파일 구조
- 지정된 구조로 수정
- .gitignore 업데이트

### 대시보드 수정
- 시간 위젯: 24시간제로, 국제 통용 포맷으로
- 연결성 테스트: 접기펼치기 가능하게
- 공격 탐지 방어: 조금 더 직관적이게 분류
- 옵션 항목: 드롭다운 항목에서 따로 빼기
- 동적 토폴로지: 불 켜지는 걸로
- 시나리오 개수: 시나리오 갯수가 안 맞아
- 시스템 스테이터스: 시스템 스테이터스 안 맞아

### 웹 디자인 프롬프트
- 호버 액션: 호버 시 사각 모달은 y축 위로 변화, 둥근 모달은 크기 크게 변화
- 모든 인터렉션 가능한 버튼이나 입력란 등 모달은 호버 기능 가지기
- 입력란 등, 포커스 역할이 있는 모달은 포커스 시 포커스 됐다는 걸 알리는 표현이 있어야 함
- 웹사이트 만들 때 팁, 주의사항 등의 가이드라인을 찾아서 커스텀 할 수 있는데 아직 안 한 부분 찾아보자

## 추가 기능

### UI/UX
- 라이트/다크 모드 (기본값은 라이트)
- 사용된 색상 관리
- 토폴로지: 토폴로지에 모두 보기 - UE, 봇넷, IP 보기, 동적으로 변경
- 알림: 알림에 토폴로지 변경사항 알림, 각 액션 유닛도 알림 발송하기

### 기능 향상
- 만들면 좋은 테이블, 그래프 등 도식 추천
- 초기 리소스 시작 값으로 초기값 설정 (환경마다 다를 테니까)
- 명확한 증거로 공격 증명 탐지 증명 방어 증명
- 피해 규모 계산법 연구나 논문 참고
- 액션을 하나씩만 선택하는 게 아니고 체크박스처럼 한번에 여러 옵션 선택 가능하게 (UI에도 유려하게 반영)
- 시나리오마다 유효한 공격, 방어 설계
  - 방어를 다 켜면 공격 하나도 안 통함
  - 방어 다 끄면 어느 공격이든 통함
  - 특정 방어는 특정 공격을 막을 수 있음
  - 모든 경우의 수 표로 만들어 학습자에게 제공
  - 이유도 문서로 볼 수 있게 제공 (웹에서 팝업창처럼?)
  - 각 액션 별 설명도 제공
- 각 유닛마다 독립적 네트워크임을 설명, 그리고 UI에 직관적으로 표시
- 라스트 임팩트 어땠는지 표시 -> 계속 실험해볼 수 있도록 유도
- 비교하기 쉽게 어떻게 하는지 고민
- 학습자가 더 나은 코드/버전 업데이트한 코드/디버그한 코드가 있으면 직접 적용해볼 수 있도록 설계
  - 액션 별 폴더로 관리해서 그 폴더에 코드 넣고 새로 컴파일만 하면 바로 적용되게 (기본적으로 폴더 내 모든 코드를 컴파일)
  - 네트워크 구성 = 유닛도 폴더별 관리로 똑같이 커스텀 가능하게
- 코드 표시할 때는 IDE 에디터 뷰처럼 기본 화면을 왼쪽 반으로 동적 전환하고 코드는 오른쪽 반으로 나오게

## 마무리 작업

### 테스트 및 검증
- 오프라인 테스트: 오프라인일 때 돌아가는지 테스트
- 실패 리질리언스: 실패 리질리언스를 가지도록 수정

### 코드 리뷰
최대한 비판적이게 리뷰:
- 중복된 코드 제거
- 쓰이지 않는/레거시 코드 제거
- 필요없는 파일 제거
- 코드에 일관성 없는 부분 수정
- 업데이트 필요한 문서 업데이트
- 문제가 있는 부분은 뭔지. 예를 들면 루프라던가, 효율이 정말 안 좋은 부분
- 이 코드를 만드려면 어떤 프롬프트를 짜야하는지 역질문

### 문서화 개선
- 어떤 단어들을 합리적인 해석 내에서 조금 더 관심을 가질만한 어휘로 풀어낼지

### 통합 및 확장
- 머신러닝 모델을 쓴다면 다른 인터페이스에 대한 유사한 연구의 모델들과 통합하기 쉽게 할 방법이 있는지

### 발표 준비
- 발표에서 데모는 영상으로 하되 질문 후에 라이브 조작 가능하다 안내하기

### 연구 차별화
우리 연구가 기존 연구들과 뭐가 다른지:

#### 학습자 학습 용이성
- 오픈소스를 포크해온 프로젝트인만큼 오픈소스를 계승
- 편리한 웹사이트 기반 조작
- 액션 탭 하단에 show code로 코드 직접 확인

#### 현실성
- 시나리오 프리셋으로 사태의 심각성을 직관적으로 묘사
- 다양한 공격, 탐지, 방어 기술을 적용하여 현실적인 (다방면) 실험 구현
- 다른 프로젝트와 통합 용이성을 고려한 모델 설계
  - 종합세트 버전(sp5g all 브랜치)
  - 방어 기능만 있는 버전(sp5g defender-only 브랜치)
- 보편화/보급화하기 쉬운 배포법
  - 깃 풀로 설치 가능하게
  - 기타 방법은?

#### 독창성
- 독창적이라고 결론난 기능은 예시 연구나 논문 찾아보기 -> alphaxiv로

### Q&A 리스트
- 논문에 뭐가 모자란지, 모자란 건 논문에 추가하고 더 이상 모자란 게 없을 때 Q&A 생각하기
- 쫜티 작년 재작년 평가항목 사진 보면서 참고 및 평가항목 추측해보고 적용하기 -> 인풋 뽑아서 상담하기

## 향후 개발 방향

- AN 피피티 싹 긁어오기
- 공격 업그레이드
  - Consider Optional Security
  - Consider Static/Dynamic/Dependency analysis
- 방어 난제
  - 방어 기법이 무거워지면 RIC의 개념이랑 중복되는 게 아닌지


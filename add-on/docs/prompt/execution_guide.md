# 실행 가이드

이 문서는 AI 모델이 프로젝트를 단계별로 실행할 수 있도록 작성된 가이드입니다.

## 실행 원칙

1. **의존성 순서 준수**: 각 태스크는 dependencies에 명시된 태스크가 완료된 후에만 시작
2. **검증 필수**: 각 태스크 완료 시 validation 항목을 모두 확인
3. **문서화 필수**: 모든 작업은 프로젝트 규칙에 따라 문서화
4. **테스트 필수**: 모든 기능은 테스트를 거쳐 정상작동 확인

## 실행 순서

### Phase 1: 프롬프트 완성 (우선순위 1)
1. `prompt_review` 태스크 실행
   - 전체 프롬프트 검토
   - 중간 생성물 관리 방법 결정
   - 클린아키텍쳐 요구사항 정리

### Phase 2: 코드 구현

#### 2.1 대시보드 구현 (우선순위 1, 의존성 없음)
1. `code_dashboard` 태스크 실행
   - 토폴로지 시각화 컴포넌트 구현
   - 시스템 제어 버튼 구현
   - 시나리오 선택 드롭다운 구현
   - 수동/자동 모드 구현
   - 검증: 모든 기능이 정상 작동하는지 확인

#### 2.2 UE 트래픽 시뮬레이션 (우선순위 2, 의존성 없음)
1. `code_ue_traffic` 태스크 실행
   - 여러 UE 타입 구현
   - 트래픽 시뮬레이션 로직 구현
   - 검증: 모든 UE 타입이 정상 시뮬레이션되는지 확인

#### 2.3 네트워크 유닛 구현 (우선순위 2, 의존성: code_dashboard)
1. `code_network_units` 태스크 실행
   - 각 유닛을 독립된 네임스페이스로 분리
   - 공격자 구현 (감염자, 봇넷 포함)
   - 탐지자 구현
   - 방어자 구현
   - 검증: 모든 유닛이 독립적으로 작동하는지 확인

#### 2.4 시나리오 구현 (우선순위 2, 의존성: code_ue_traffic)
1. `code_scenario` 태스크 실행
   - 각 시나리오별 UE 구성
   - 공격 애니메이션 구현
   - 배경 및 인디케이터 구현
   - 검증: 모든 시나리오가 정상 작동하는지 확인

#### 2.5 통계 및 측정 구현 (우선순위 3, 의존성: code_network_units)
1. `code_statistician` 태스크 실행
   - 베이즈 테이블 구현
   - 공격 효과 측정 구현
   - 방어 효과 측정 구현
   - 검증: 모든 측정이 정확한지 확인

#### 2.6 독창성 평가 (우선순위 3, 의존성: code_statistician)
1. `code_originality` 태스크 실행
   - feature.txt 읽기
   - 독창성 평가
   - 예시 연구/논문 찾기
   - 검증: 독창성 평가 완료 확인

#### 2.7 코드 마무리 (우선순위 4, 의존성: code_originality)
1. `code_finalization` 태스크 실행
   - 오프라인 테스트
   - 재귀 체크
   - 코드 구조 확인
   - 컴파일 및 최적화
   - GitHub 브랜치 정리
   - 검증: 모든 검증 항목 통과 확인

### Phase 3: 디자인 다듬기

#### 3.1 대시보드 디자인 (의존성: code_dashboard)
1. `design_about_page` 실행
2. `design_responsive` 실행
3. `design_landing_page` 실행
4. `design_web_analysis` 실행

#### 3.2 README 작성 (의존성: code_finalization)
1. `design_readme` 실행
   - 코드 실행 순차 그래프 포함

### Phase 4: 논문 작성

#### 4.1 논문 초안 (의존성: code_finalization)
1. `paper_abstract` 실행
   - 앱스트랙 구조 확인
   - 개인적 경험담 포함
   - F1 인터페이스 선택 이유 설명
   - AI 검토

#### 4.2 논문 삽화 (의존성: paper_abstract)
1. `paper_illustrations` 실행
   - 시스템 구성 시각화
   - 프로그램 스크린샷
   - 마인드맵/플로우차트

#### 4.3 논문 최종 (의존성: paper_illustrations)
1. `paper_final` 실행
   - Overleaf 형식으로 작성
   - IEEE 스타일 적용
   - 모든 섹션 완성

### Phase 5: 포스터 제작

#### 5.1 포스터 내용 (의존성: paper_final)
1. `poster_content` 실행
   - 논문 요약
   - 텍스트 정리

#### 5.2 포스터 최종 (의존성: poster_content)
1. `poster_final` 실행
   - QR 코드 업데이트
   - 워터마크 추가
   - PDF 출력

### Phase 6: 데모 영상

#### 6.1 데모 스크립트 (의존성: code_finalization)
1. `demo_script` 실행
   - 스크립트 작성
   - 구조 논의

#### 6.2 부분 데모 (의존성: demo_script)
1. `demo_partial` 실행
   - 예시 영상 제작

#### 6.3 전체 데모 (의존성: demo_partial)
1. `demo_full` 실행
   - 전체 데모 영상 제작
   - DDoS 설명 포함

### Phase 7: 교수님 문서

1. `prof_timeline` 실행
2. `prof_study_content` 실행

### Phase 8: 수정 사항

모든 수정 태스크는 의존성에 따라 순차 실행:
1. `fix_file_structure`
2. `fix_time_widget`
3. `fix_connectivity_test`
4. `fix_action_classification`
5. `fix_options_dropdown`
6. `fix_topology_dynamic`
7. `fix_scenario_count`
8. `fix_system_status`
9. `fix_web_design`

### Phase 9: 추가 기능

모든 추가 기능은 의존성에 따라 순차 실행:
1. `add_theme_mode`
2. `add_color_management`
3. `add_topology_enhancement`
4. `add_notifications`
5. `add_diagrams`
6. `add_initial_resources`
7. `add_evidence_proof`
8. `add_damage_calculation`
9. `add_multi_select`
10. `add_scenario_validation`
11. `add_network_independence`
12. `add_impact_display`
13. `add_comparison_feature`
14. `add_custom_code`
15. `add_code_viewer`

### Phase 10: 마무리

1. `final_offline_test` 실행
2. `final_resilience` 실행
3. `final_code_review` 실행
4. `final_vocabulary` 실행
5. `final_ml_integration` 실행
6. `final_presentation_note` 실행
7. `final_research_comparison` 실행
8. `final_qa_list` 실행

## 각 태스크 실행 시 체크리스트

각 태스크를 실행할 때 다음을 확인:

1. **의존성 확인**: dependencies에 명시된 모든 태스크가 완료되었는지
2. **요구사항 확인**: requirements의 모든 항목을 이해했는지
3. **출력 생성**: outputs에 명시된 모든 파일/결과물을 생성했는지
4. **검증 수행**: validation의 모든 항목을 확인했는지
5. **문서화**: 프로젝트 규칙에 따라 문서화했는지
   - 새 파일 생성 시: file_info.txt에 기록
   - 테스트 통과 시: tested_feature.txt에 기록
   - 새 아이디어 적용 시: new_idea.txt에 기록
   - 참고 자료 사용 시: referred_docs.txt에 기록
   - 파일 복사 시: copied_file.txt에 기록

## 문제 발생 시

1. **막혔을 때**: referred_docs.txt에 기록하고 최신 논문 찾아보기
2. **에러 발생 시**: file_info.txt에 기록하고 문제 해결 방법 문서화
3. **테스트 실패 시**: tested_feature.txt에 기록하고 원인 분석

## 우선순위 가이드

- **Priority 1**: 최우선, 다른 작업의 기반이 되는 작업
- **Priority 2**: 중요, 프로젝트 핵심 기능
- **Priority 3**: 중요하지만 우선순위는 낮음
- **Priority 4**: 추가 기능, 핵심 기능 완성 후
- **Priority 5**: 마무리 작업, 모든 기능 완성 후

## 검증 기준

각 태스크의 validation 항목은 다음 중 하나 이상을 포함할 수 있습니다:

- **기능 검증**: 해당 기능이 정상 작동하는지
- **파일 검증**: 필요한 파일이 생성되었는지
- **형식 검증**: 출력 형식이 요구사항에 맞는지
- **통합 검증**: 다른 모듈과 정상 통합되는지
- **성능 검증**: 성능 요구사항을 만족하는지

## 참고

- 모든 태스크는 `tasks.yaml` 파일에 상세 정의되어 있습니다
- 프로젝트 메타데이터는 `project_spec.json`에 있습니다
- 배경 설명은 `context.md`에 있습니다


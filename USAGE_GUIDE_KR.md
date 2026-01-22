# HACCP 스마트 조리 모니터링 시스템 사용 가이드

## 1. 개요
이 문서는 Thingsboard를 사용하여 HACCP 조리 모니터링 시스템을 설정하고 사용하는 방법을 설명합니다. 시스템은 **Custom Widget** (대시보드 UI), **Rule Chain** (로직 처리), **Simulation Script** (디바이스 에뮬레이션)로 구성됩니다.

## 2. Thingsboard 설정 방법

### 2.1 디바이스 생성 (Device)
1.  Thingsboard 메뉴에서 **Devices**로 이동합니다.
2.  `+` 버튼을 눌러 **Add new device**를 선택합니다.
3.  이름: `HACCP Smart Cooker` (원하는 이름 입력)
4.  **Add**를 클릭합니다.
5.  생성된 디바이스를 클릭하고 **Manage Credentials**를 엽니다.
6.  **Access Token** 유형을 선택하고, 토큰 값을 `HACCP_DEVICE_TOKEN_001`로 설정합니다. (시뮬레이션 스크립트와 일치해야 함)

### 2.2 Rule Chain Import
1.  **Rule Chains** 메뉴로 이동합니다.
2.  `+` 버튼 -> **Import rule chain**을 선택합니다.
3.  `haccp_rule_chain.json` 파일을 업로드합니다.
4.  Import된 Rule Chain을 열고, **Input** 노드가 있는지 확인합니다. (없다면 기본 Root Rule Chain에서 연결해 주어야 합니다. 보통 Root Rule Chain의 'Save Timeseries' 이후나 병렬로 연결합니다.)
    *   *Tip*: 가장 쉬운 테스트 방법은 이 Rule Chain을 해당 디바이스의 **Root Rule Chain**으로 설정하는 것입니다. (Device Profile 설정 필요)

### 2.3 Widget Import
1.  **Widgets Bundles** 메뉴로 이동합니다.
2.  `+` 버튼 -> **Import widgets bundle**을 선택합니다.
3.  `haccp_widget.json` 파일을 업로드합니다.
4.  `HACCP Widgets` 번들이 생성되었는지 확인합니다.

### 2.4 대시보드 구성 (Dashboard Setup)
위젯을 디바이스와 연결하는 핵심 단계입니다.

1.  **Dashboards** 메뉴 -> `+` -> **Create new dashboard** (이름: `HACCP Dashboard`).
2.  대시보드를 열고 우측 하단 펜 아이콘(Edit mode)을 클릭합니다.
3.  **Entity Aliases** 아이콘(상단)을 클릭합니다.
4.  **Add alias**를 클릭합니다.
    *   **Alias name**: `My Cooker`
    *   **Filter type**: `Single entity`
    *   **Type**: `Device`
    *   **Device**: `HACCP Smart Cooker` (2.1에서 생성한 디바이스 선택)
    *   **Add** 후 **Save** 합니다.
5.  **Add new widget** -> **Current bundle** 클릭 -> `HACCP Widgets` 선택.
6.  `HACCP Smart Monitor` 위젯을 선택합니다.
7.  **Datasources** 설정에서:
    *   **Type**: `Entity`
    *   **Alias**: `My Cooker` (방금 만든 Alias 선택)
8.  **Add**를 눌러 위젯을 대시보드에 추가합니다.
9.  대시보드를 저장합니다 (체크 아이콘).

## 3. 시뮬레이션 및 테스트

1.  터미널에서 시뮬레이션 스크립트 실행:
    ```bash
    pip install tb-mqtt-client
    python haccp_sim.py
    ```
2.  대시보드에서 온도가 올라가는 것을 확인합니다.
3.  **Settings** 탭에서 Target Temp와 Duration을 설정하고 **Save** 합니다.
4.  **Monitor** 탭에서 **Start Cooking** 버튼을 누릅니다. (또는 Auto 모드 테스트)
5.  조리가 완료되면 **History** 탭에서 기록을 확인합니다.

import os
import shutil
import base64
import sys
import pathlib

# Fix for Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def encode_user_data():
    # 실제 세션 정보가 담긴 state.json 경로
    source_state_file = pathlib.Path(r'c:\Users\82106\OneDrive\바탕 화면\python_workplace\antigravity-awesome-skills\skills\notebooklm\data\browser_state\state.json')
    
    if not source_state_file.exists():
        print(f"❌ '{source_state_file}' 파일을 찾을 수 없습니다. 로그인이 필요합니다.")
        return
    
    # 파일 크기 확인 (64KB 제한)
    file_size = source_state_file.stat().st_size
    print(f"1. 세션 파일 확인: {source_state_file} ({file_size / 1024:.1f} KB)")
    
    if file_size > 60000:
        print("⚠️ 주의: 세션 파일이 60KB를 초과하여 GitHub Secrets에 등록되지 않을 수 있습니다.")

    print("2. Base64 인코딩 중...")
    with open(source_state_file, 'rb') as f:
        encoded = base64.b64encode(f.read()).decode('utf-8')
        
    print("3. 비밀 파일 저장 중...")
    with open('auth_secret_DO_NOT_COMMIT.txt', 'w', encoding='utf-8') as f:
        f.write(encoded)
        
    print("\n✅ 성공적으로 변환되었습니다!")
    print("\n[다음 진행 단계]")
    print("1. 같은 폴더에 생성된 'auth_secret_DO_NOT_COMMIT.txt' 파일을 메모장으로 엽니다.")
    print("2. 안의 내용(긴 문자열)을 전체 선택(Ctrl+A) 하여 복사(Ctrl+C)합니다.")
    print("3. 본인의 GitHub Repository -> 상단 [Settings] 탭 항목을 누릅니다.")
    print("4. 좌측 메뉴에서 [Secrets and variables] -> [Actions] 를 클릭합니다.")
    print("5. 초록색 [New repository secret] 버튼을 누릅니다.")
    print("   - Name:  AUTH_DATA")
    print("   - Secret: (방금 복사한 긴 문자열 붙여넣기)")
    print("6. [Add secret]을 눌러 저장합니다.")

if __name__ == "__main__":
    encode_user_data()

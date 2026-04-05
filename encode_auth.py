import os
import shutil
import base64

def encode_user_data():
    if not os.path.exists('user_data'):
        print("❌ 'user_data' 디렉토리가 없습니다. 로그인 세션이 존재하지 않습니다.")
        return
    
    print("1. 로그인 세션 압축 중...")
    shutil.make_archive('user_data_archive', 'zip', 'user_data')
    
    print("2. Base64 인코딩 중...")
    with open('user_data_archive.zip', 'rb') as f:
        encoded = base64.b64encode(f.read()).decode('utf-8')
        
    print("3. 저장 중...")
    with open('auth_secret_DO_NOT_COMMIT.txt', 'w', encoding='utf-8') as f:
        f.write(encoded)
        
    print("\n✅ 성공적으로 변환되었습니다!")
    print("\n[다음 진행 단계]")
    print("1. 같은 폴더에 생성된 'auth_secret_DO_NOT_COMMIT.txt' 파일을 메모장으로 엽니다.")
    print("2. 안의 내용(엄청나게 긴 문자열)을 전체 선택(Ctrl+A) 하여 복사(Ctrl+C)합니다.")
    print("3. 본인의 GitHub Repository -> 상단 [Settings] 탭 항목을 누릅니다.")
    print("4. 좌측 메뉴에서 [Secrets and variables] -> [Actions] 를 클릭합니다.")
    print("5. 초록색 [New repository secret] 버튼을 누릅니다.")
    print("   - Name:  AUTH_DATA")
    print("   - Secret: (방금 복사한 긴 문자열 붙여넣기)")
    print("6. [Add secret]을 눌러 저장합니다.")
    print("\n이제 해당 문자열은 GitHub 비밀금고에 안전하게 보관되어, 매주 리포터를 돌릴 때 접속 수단으로 사용됩니다!")

if __name__ == "__main__":
    encode_user_data()

from traffic_violation import TrafficViolationSubmitter, UserInfo, ViolationInfo
import re
import os

# 簡易台灣身分證檢核（與模型一致）
def is_valid_twid(twid: str) -> bool:
    twid = twid.strip().upper()
    if not re.match(r'^[A-Z][0-9]{9}$', twid):
        return False
    letter_map = {
        'A':10,'B':11,'C':12,'D':13,'E':14,'F':15,'G':16,'H':17,'I':34,'J':18,
        'K':19,'L':20,'M':21,'N':22,'O':35,'P':23,'Q':24,'R':25,'S':26,'T':27,
        'U':28,'V':29,'W':32,'X':30,'Y':31,'Z':33
    }
    x = letter_map[twid[0]]
    x1, x2 = divmod(x, 10)
    weights = [1,9,8,7,6,5,4,3,2,1,1]
    digits = [x1, x2] + [int(d) for d in twid[1:]]
    checksum = sum(d*w for d, w in zip(digits, weights))
    return checksum % 10 == 0

def normalize_gender(raw: str) -> str | None:
    s = raw.strip().lower()
    if s in ['1', 'male', 'm', '男']:
        return 'male'
    if s in ['2', 'female', 'f', '女']:
        return 'female'
    return None

def main():
    print("=== 交通違規檢舉工具 ===")
    
    # 設定選項
    print("\n--- 設定選項 ---")
    enable_ocr = input("是否啟用OCR自動識別驗證碼？(y/n，預設y)：").strip().lower()
    enable_ocr = enable_ocr != 'n'  # 預設啟用
    
    captcha_dir = input("驗證碼暫存資料夾路徑（Enter使用預設captcha_catch）：").strip()
    if not captcha_dir:
        captcha_dir = None
    
    max_retries = input("OCR重試次數（Enter使用預設3次）：").strip()
    if not max_retries:
        max_retries = 3
    else:
        try:
            max_retries = int(max_retries)
        except ValueError:
            max_retries = 3
    
    # 建立提交器
    submitter = TrafficViolationSubmitter(
        captcha_temp_dir=captcha_dir,
        enable_ocr=enable_ocr,
        max_captcha_retries=max_retries
    )
    
    print(f"設定完成：OCR={'啟用' if enable_ocr else '停用'}，重試次數={max_retries}")
    
    name = input("\n姓名：")

    # 手動輸入性別並驗證
    while True:
        g = input("性別 (male/female 或 1/2/男/女)：").strip()
        gender_norm = normalize_gender(g)
        if gender_norm:
            break
        print("性別輸入錯誤，請輸入 male/female 或 1/2/男/女")

    # 即時驗證身分證字號（僅格式）
    while True:
        sub = input("身分證字號：").strip().upper()
        if not re.match(r'^[A-Z][0-9]{9}$', sub):
            print("格式錯誤：需為1個大寫英文字母+9位數字，例如 A123456789")
            continue
        break

    address = input("聯絡地址：")
    phone = input("聯絡電話：")
    email = input("Email：")

    user_info = UserInfo(
        name=name,
        gender=gender_norm,
        sub=sub,
        address=address,
        phone=phone,
        email=email
    )
    
    while True:
        print("\n" + "="*50)
        
        violation_info = ViolationInfo(
            video_file=input("影片檔案路徑："),
            violation_datetime=input("違規時間 (YYYY-MM-DD HH:MM)："),
            license_plate=input("車牌號碼："),
            location=input("違規地點："),
            description=input("違規描述：") or "闖紅燈",
            qclass=input("違規條文 (Enter使用預設)：") or "53-1 駕駛人行經有燈光號誌管制之交岔路口闖紅燈者。"
        )

        # 預覽所有資料
        print("\n--- 最終預覽 ---")
        print(f"姓名：{user_info.name}")
        print(f"性別：{'男' if user_info.gender=='male' else '女'}")
        print(f"身分證字號：{user_info.sub}")
        print(f"聯絡地址：{user_info.address}")
        print(f"聯絡電話：{user_info.phone}")
        print(f"Email：{user_info.email}")
        print(f"影片檔案路徑：{violation_info.video_file}")
        print(f"違規時間：{violation_info.violation_datetime}")
        print(f"車牌號碼：{violation_info.license_plate}")
        print(f"違規地點：{violation_info.location}")
        print(f"違規描述：{violation_info.description}")
        print(f"違規條文：{violation_info.qclass}")
        print("------------------")
        confirm = input("\n是否確認送出？(y/n)：").lower()
        if confirm != 'y':
            print("已取消送出，可重新輸入資料。")
            continue
        
        # 提交檢舉
        result = submitter.submit_violation(user_info, violation_info)
        
        # 處理結果
        if result.success:
            print("檢舉成功！")
        else:
            print(f"檢舉失敗：{result.message}")
            
            # 如果需要手動輸入驗證碼
            if result.captcha_required:
                print(f"請查看驗證碼圖片：{result.captcha_path}")
                manual_captcha = input("請手動輸入驗證碼：")
                
                # 重新提交（只傳驗證碼，不重新提交所有資料）
                result = submitter.submit_violation(user_info, violation_info, manual_captcha)
                
                if result.success:
                    print("檢舉成功！")
                else:
                    print(f"檢舉失敗：{result.message}")
        
        if input("\n是否繼續檢舉？(y/n)：").lower() != 'y':
            break
    
    # 清理所有驗證碼圖片
    submitter.cleanup_all_captcha_images()
    print("已清理所有驗證碼圖片")

if __name__ == "__main__":
    main()

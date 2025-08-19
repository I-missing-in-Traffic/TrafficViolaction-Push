import requests
from bs4 import BeautifulSoup
import time
import os
import logging
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import re
import tempfile
import shutil
from typing import Dict, Tuple, Optional

from .models import UserInfo, ViolationInfo, SubmissionResult
from .exceptions import TrafficViolationError, CaptchaError, SubmissionError

class TrafficViolationSubmitter:
    def __init__(self, log_file: str = "traffic_violation.log", captcha_temp_dir: Optional[str] = None, enable_ocr: bool = True, max_captcha_retries: int = 3):
        """
        Args:
            log_file: 日誌檔案路徑
            captcha_temp_dir: 驗證碼暫存資料夾，None則使用當前路徑下的captcha_catch
            enable_ocr: 是否啟用OCR自動識別驗證碼
            max_captcha_retries: 驗證碼識別最大重試次數
        """
        # 配置日誌
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            encoding="utf-8",
        )
        self.logger = logging.getLogger(__name__)
        
        # Set captcha settings
        self.enable_ocr = enable_ocr
        self.max_captcha_retries = max_captcha_retries
        
        # Set captcha temporary directory
        if captcha_temp_dir:
            self.captcha_temp_dir = captcha_temp_dir
        else:
            self.captcha_temp_dir = os.path.join(os.getcwd(), "captcha_catch")
        
        # Ensure the temporary directory exists
        os.makedirs(self.captcha_temp_dir, exist_ok=True)
        self.logger.info(f"驗證碼暫存資料夾：{self.captcha_temp_dir}")
        
        self.base_url = "https://suggest.police.taichung.gov.tw/traffic/"
        self.form_url = self.base_url + "traffic_write.jsp"
        self.submit_url = self.base_url + "traffic_writesave.jsp"
        self.captcha_url = "https://suggest.police.taichung.gov.tw/GetCaptchaImageServlet"
        
        self.headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": self.form_url,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        
        # 建立session
        self.session = requests.Session()

    def get_captcha_image(self) -> str:
        """
        獲取驗證碼圖片
        
        Returns:
            驗證碼圖片路徑
        """
        try:
            captcha_response = self.session.get(
                self.captcha_url + "?t=" + str(int(time.time())), 
                headers=self.headers,
                timeout=10
            )
            captcha_response.raise_for_status()
            
            # 使用暫存資料夾
            captcha_path = os.path.join(self.captcha_temp_dir, f"captcha_{int(time.time())}.png")
            with open(captcha_path, "wb") as f:
                f.write(captcha_response.content)
            
            self.logger.info("驗證碼圖片獲取成功")
            return captcha_path
            
        except Exception as e:
            self.logger.error(f"驗證碼圖片獲取失敗：{str(e)}")
            raise CaptchaError(f"驗證碼圖片獲取失敗：{str(e)}")

    def solve_captcha(self, image_path: str) -> str:
        """
        Auto-identify captcha
        
        Args:
            image_path: 驗證碼圖片路徑
            
        Returns:
            識別出的驗證碼文字
        """
        try:
            captcha_image = Image.open(image_path).convert("L")
            captcha_image = captcha_image.filter(ImageFilter.SHARPEN)
            captcha_image = ImageEnhance.Contrast(captcha_image).enhance(2.0)
            
            # OCR
            captcha_text = pytesseract.image_to_string(
                captcha_image,
                config="--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
            ).strip()
            
            self.logger.info(f"驗證碼自動識別結果：{captcha_text}")
            
            if len(captcha_text) >= 4 and captcha_text.isalnum():
                return captcha_text
            else:
                raise CaptchaError(f"驗證碼識別結果不符合預期：{captcha_text}")
                
        except Exception as e:
            self.logger.error(f"驗證碼識別失敗：{str(e)}")
            raise CaptchaError(f"驗證碼識別失敗：{str(e)}")

    def cleanup_captcha_image(self, image_path: str):
        """
        Clean up captcha image
        
        Args:
            image_path: 驗證碼圖片路徑
        """
        try:
            if os.path.exists(image_path):
                os.remove(image_path)
                self.logger.info(f"驗證碼圖片已清理：{image_path}")
        except Exception as e:
            self.logger.warning(f"清理驗證碼圖片失敗：{e}")

    def cleanup_all_captcha_images(self):
        """
        Clean up all captcha images
        """
        try:
            for filename in os.listdir(self.captcha_temp_dir):
                if filename.startswith("captcha_") and filename.endswith(".png"):
                    file_path = os.path.join(self.captcha_temp_dir, filename)
                    os.remove(file_path)
            self.logger.info("所有驗證碼圖片已清理")
        except Exception as e:
            self.logger.warning(f"清理所有驗證碼圖片失敗：{e}")

    def parse_location(self, location: str) -> Tuple[str, str, str]:
        """
        Parse violation location
        Args:
            location: 完整地址
        Returns:
            (區域, 街道, 詳細地址)
        """
        try:
            loc = re.sub(r"[\u4e00-\u9fa5]{2,3}市", "", location).strip()
            
            # 取區
            cityarea_match = re.search(r"([\u4e00-\u9fa5]{1,3}區)", loc)
            cityarea = cityarea_match.group(1) if cityarea_match else "西屯區"
            loc = loc.replace(cityarea, "", 1).strip()

            # 取街道
            street_match = re.search(r"([\u4e00-\u9fa5A-Za-z0-9\-]+?(?:路|街|道|大道|巷|段))", loc)
            street = street_match.group(1) if street_match else "其他路段"
            loc = loc.replace(street, "", 1).strip() if street else loc

            inputaddress = loc if loc else "附近"
            return cityarea, street, inputaddress
        except Exception as e:
            self.logger.warning(f"地點解析失敗：{location}，使用預設值")
            return "西屯區", "大隆路", "192號"

    def parse_license_plate(self, license_plate: str) -> Tuple[str, str]:
        """
        Parse license plate
        
        Args:
            license_plate: 車牌號碼 (如: ABC-1234)
            
        Returns:
            (字母部分, 數字部分)
        """
        if "-" in license_plate:
            parts = license_plate.split("-")
            return parts[0], parts[1]
        else:
            return "", license_plate

    def submit_violation(
        self, 
        user_info: UserInfo, 
        violation_info: ViolationInfo, 
        captcha_text: Optional[str] = None
    ) -> SubmissionResult:
        """
        Submit violation
        
        Args:
            user_info: 用戶資料
            violation_info: 違規資料
            captcha_text: 驗證碼文字 (可選，不提供則自動識別)
            
        Returns:
            提交結果
        """
        captcha_path = None
        try:
            # Check video file
            if not os.path.exists(violation_info.video_file):
                return SubmissionResult(
                    success=False,
                    message=f"影片檔案不存在：{violation_info.video_file}"
                )

            # Get form page
            response = self.session.get(self.form_url, headers=self.headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            totfilesize_input = soup.find("input", {"id": "totfilesize"})
            if not totfilesize_input:
                return SubmissionResult(
                    success=False,
                    message="無法找到參數"
                )
            totfilesize = totfilesize_input["value"]

            # Process captcha
            if not captcha_text:
                if self.enable_ocr:
                    # Enable OCR, try to auto-identify
                    captcha_path = self.get_captcha_image()
                    captcha_text = self._try_ocr_with_retry(captcha_path)
                else:
                    # Disable OCR, require manual input
                    captcha_path = self.get_captcha_image()
                    return SubmissionResult(
                        success=False,
                        message="需要手動輸入驗證碼",
                        captcha_path=captcha_path,
                        captcha_required=True
                    )
            else:
                # Use provided captcha, but still need to download image
                captcha_path = self.get_captcha_image()

            # Parse location and license plate
            cityarea, street, inputaddress = self.parse_location(violation_info.location)
            license_alpha, license_num = self.parse_license_plate(violation_info.license_plate)

            # Prepare description content
            detailcontent = f"車輛於{violation_info.violation_datetime}在{violation_info.location}{violation_info.description}，詳見附件影片。"
            if len(detailcontent) > 500:
                detailcontent = detailcontent[:500]

            # Prepare form data
            form_data = {
                "totfilesize": totfilesize,
                "name": user_info.name,
                "gender": (
                    "male" if user_info.gender in ["male", "1", "m", "男"] else
                    "female" if user_info.gender in ["female", "2", "f", "女"] else
                    ""
                ),
                "isforeigner": "taiwan",
                "sub": user_info.sub,
                "address": user_info.address,
                "liaisontel": user_info.phone,
                "email": user_info.email,
                "job": "",
                "qclass": violation_info.qclass,
                "cityarea": cityarea,
                "street": street,
                "inputaddress": inputaddress,
                "violationdatetime": violation_info.violation_datetime,
                "licensenumber1": "",
                "licensenumber2": license_alpha,
                "licensenumber3": license_num,
                "licensenumber4": "",
                "detailcontent": detailcontent,
                "captcha": captcha_text,
            }

            # Prepare file
            files = {
                "filename1": (
                    os.path.basename(violation_info.video_file),
                    open(violation_info.video_file, "rb"),
                    "video/mp4",
                )
            }

            # Submit form
            response = self.session.post(
                self.submit_url, 
                headers=self.headers, 
                data=form_data, 
                files=files, 
                timeout=30
            )
            files["filename1"][1].close()

            # Check result
            if response.status_code == 200:
                # If the returned page contains alert, parse and output clear error reasons
                alerts = re.findall(r'alert\(["\']([\s\S]*?)["\']\)', response.text)
                if alerts:
                    combined = " ".join(alerts)
                    cleaned = combined.replace("\n", " ").replace("\r", " ")
                    # 轉成人類可讀：移除【】並按驚嘆號切分
                    cleaned = cleaned.replace("【", "").replace("】", "")
                    parts = re.split(r'[!！]+', cleaned)
                    reasons = [p.strip() for p in parts if p.strip()]
                    human_message = "；".join(reasons) if reasons else "未知原因"
                    self.logger.warning(f"提交失敗：{human_message}")
                    return SubmissionResult(
                        success=False,
                        message=f"提交失敗：{human_message}",
                        captcha_path=captcha_path
                    )

                if "錯誤" not in response.text:
                    self.logger.info(f"檔案 {violation_info.video_file} 上傳成功")
                    return SubmissionResult(
                        success=True,
                        message="檢舉提交成功",
                        captcha_path=captcha_path
                    )

                # No alert but contains error message
                snippet = response.text[:200]
                self.logger.warning(f"提交失敗：{snippet}")
                return SubmissionResult(
                    success=False,
                    message="提交失敗：伺服器回應包含錯誤訊息",
                    captcha_path=captcha_path
                )
            else:
                self.logger.warning(f"提交失敗：HTTP {response.status_code}")
                return SubmissionResult(
                    success=False,
                    message=f"提交失敗，狀態碼：{response.status_code}",
                    captcha_path=captcha_path
                )

        except Exception as e:
            self.logger.error(f"提交失敗：{str(e)}")
            return SubmissionResult(
                success=False,
                message=f"提交過程發生錯誤：{str(e)}",
                captcha_path=captcha_path
            )
        finally:
            # Clean up captcha image
            if captcha_path:
                self.cleanup_captcha_image(captcha_path)

    def _try_ocr_with_retry(self, captcha_path: str) -> str:
        """
        Try OCR with retry
        
        Args:
            captcha_path: 驗證碼圖片路徑
            
        Returns:
            識別出的驗證碼文字
            
        Raises:
            CaptchaError: 超過重試次數後拋出
        """
        for attempt in range(self.max_captcha_retries):
            try:
                captcha_text = self.solve_captcha(captcha_path)
                return captcha_text
            except CaptchaError as e:
                if attempt < self.max_captcha_retries - 1:
                    self.logger.warning(f"第 {attempt + 1} 次OCR識別失敗，重試中...")
                    # Download captcha image again
                    self.cleanup_captcha_image(captcha_path)
                    captcha_path = self.get_captcha_image()
                    continue
                else:
                    # Last attempt failed, raise exception
                    self.logger.error(f"OCR識別失敗，已達最大重試次數 {self.max_captcha_retries}")
                    raise CaptchaError(f"OCR識別失敗，已達最大重試次數 {self.max_captcha_retries}")

    def __del__(self):
        try:
            self.cleanup_all_captcha_images()
        except:
            pass

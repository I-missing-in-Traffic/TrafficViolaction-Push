from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime

class UserInfo(BaseModel):
    name: str = Field(..., description="檢舉人姓名")
    gender: str = Field(..., description="性別：male/female 或 1/2/男/女")
    sub: str = Field(..., description="身分證字號")
    address: str = Field(..., description="聯絡地址")
    phone: str = Field(..., description="聯絡電話")
    email: str = Field(..., description="Email地址")

    @field_validator('gender')
    @classmethod
    def validate_gender(cls, v):
        s = str(v).strip().lower()
        if s in ['1', 'male', 'm', '男']:
            return 'male'
        if s in ['2', 'female', 'f', '女']:
            return 'female'
        raise ValueError('gender must be male/female 或 1/2/男/女')

    def gender_from_sub(self) -> str:
        """Optional: Infer gender from ID number, does not affect manual input"""
        if len(self.sub) == 10 and self.sub[1] in ['1', '2']:
            return 'male' if self.sub[1] == '1' else 'female'
        return 'male'

    @field_validator('sub')
    @classmethod
    def validate_sub(cls, v):
        import re
        v = v.strip().upper()
        if not re.match(r'^[A-Z][0-9]{9}$', v):
            raise ValueError('身分證字號格式錯誤，必須為1個大寫英文字母+9位數字')
        return v

class ViolationInfo(BaseModel):
    video_file: str = Field(..., description="影片檔案路徑")
    violation_datetime: str = Field(..., description="違規時間 (YYYY-MM-DD HH:MM)")
    license_plate: str = Field(..., description="車牌號碼")
    location: str = Field(..., description="違規地點")
    description: str = Field("闖紅燈", description="違規描述")
    qclass: str = Field(
        "53-1 駕駛人行經有燈光號誌管制之交岔路口闖紅燈者。", # 預設啟用，後續可以自定義，請見fulfill_violation
        description="違規條文"
    )

class SubmissionResult(BaseModel):
    success: bool
    message: str
    captcha_path: Optional[str] = None
    captcha_required: bool = False

class TrafficViolationError(Exception):
    """Base exception class"""
    pass

class CaptchaError(TrafficViolationError):
    """Captcha related error"""
    pass

class SubmissionError(TrafficViolationError):
    """Submission related error"""
    pass

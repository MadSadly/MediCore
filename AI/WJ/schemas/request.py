from pydantic import BaseModel


class DiagnoseRequest(BaseModel):
    """진단 요청 메타데이터 (파일은 multipart로 별도 수신)"""
    patient_uid: str | None = None

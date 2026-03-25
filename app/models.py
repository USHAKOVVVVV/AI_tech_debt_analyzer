from sqlalchemy import Column, Integer, String, JSON, DateTime
from datetime import datetime
from .database import Base

class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    repo_url = Column(String)
    analysis_date = Column(DateTime, default=datetime.utcnow)
    model_name = Column(String)
    # Храним весь отчет от ЛЛМ как JSON, чтобы потом легко выгрузить
    full_report = Column(JSON)
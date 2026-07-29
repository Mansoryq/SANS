import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.settings import AppSetting
from app.core.encryption import encrypt_value
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()

try:
    wa_token = db.query(AppSetting).filter_by(key="wa_token").first()
    wa_phone_id = db.query(AppSetting).filter_by(key="wa_phone_id").first()
    mode = db.query(AppSetting).filter_by(key="mode").first()
    
    if wa_token:
        wa_token.value = encrypt_value("EAAMb1UMmobsBSIWSlQpNGa0SZAQstobkHfsI4KCKOTUGWRHojsKVrlX2OVwN3ZC0pZC1b7Yq0ylN5IhATZCBZAIoQ3KUNRG76cZCZCRs5LZCVOnwWAxbx7haABNcDVIZBdHsIQG7Cjor65pVsSUeXWpvgFOFzsAk4GhEtkTv882ZA5VrTciCTHVN9ekQSZBqYGv4SLkmiHap42wODiuio3l5XXgAY8HkmqEZB8jFNI8N2JS34ZAshvmH1giEK15OE23bNT2PXoZC6828fTQCBqqccfVkuPj0Kt8elSzYNF6gZDZD")
    
    if wa_phone_id:
        wa_phone_id.value = "1309636498890779"
        
    if mode:
        mode.value = "prod"
        
    db.commit()
    print("Settings updated successfully.")
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()

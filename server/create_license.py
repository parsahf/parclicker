from database import SessionLocal, License
from datetime import datetime, timedelta

db = SessionLocal()

license_data = License(
    license_key="PAR-2026-001",
    username="Parsa",
    active=True,
    expires_at=datetime.now() + timedelta(days=30)
)

db.add(license_data)
db.commit()

print("License created successfully!")
print("Key:", license_data.license_key)
print("Expires:", license_data.expires_at)

db.close()
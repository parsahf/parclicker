
from datetime import datetime
from dateutil.relativedelta import relativedelta

from database import SessionLocal, Subscription


db = SessionLocal()


username = "parsa_hfa"
cps = 50
months = 12
price = 1_000_000

license_key = "PAR-50CPS-12M-002"


# بررسی اینکه این اشتراک قبلاً ساخته نشده باشد
existing = db.query(Subscription).filter(
    Subscription.license_key == license_key
).first()


if existing:

    print("این اشتراک قبلاً ساخته شده است.")
    print("License Key:", existing.license_key)

else:

    created_at = datetime.now()

    expires_at = created_at + relativedelta(
        months=months
    )

    subscription = Subscription(
        username=username,
        license_key=license_key,
        cps=cps,
        months=months,
        price=price,
        active=True,
        created_at=created_at,
        expires_at=expires_at
    )

    db.add(subscription)
    db.commit()
    db.refresh(subscription)

    print()
    print("Subscription created successfully!")
    print("-------------------------------")
    print("Username:", subscription.username)
    print("CPS:", subscription.cps)
    print("Months:", subscription.months)
    print("Price:", subscription.price)
    print("License:", subscription.license_key)
    print("Created:", subscription.created_at)
    print("Expires:", subscription.expires_at)


db.close()


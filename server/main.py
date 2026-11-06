from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel
from datetime import datetime, timedelta
import hashlib
import secrets

from server.database import (
    SessionLocal,
    License,
    User,
    Session,
    Subscription,
    SoftwareDevice,
    Order
)


app = FastAPI(title="ParClicker API")


# =========================
# Models
# =========================

class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class SoftwareIDRequest(BaseModel):
    software_id: str


class OrderRequest(BaseModel):
    software_id: str
    cps: int
    months: int


# =========================
# Authentication
# =========================

def get_current_user(request: Request):

    token = request.cookies.get("parclicker_session")

    if not token:
        return None

    db = SessionLocal()

    session_data = db.query(Session).filter(
        Session.token == token
    ).first()

    if session_data is None:
        db.close()
        return None

    if datetime.now() > session_data.expires_at:

        db.delete(session_data)
        db.commit()
        db.close()

        return None

    username = session_data.username

    db.close()

    return username


# =========================
# Main website
# =========================

@app.get("/")
def home(request: Request):

    username = get_current_user(request)

    if username is None:

        return RedirectResponse(
            url="/login-page",
            status_code=303
        )

    return FileResponse(
        "server/static/index.html"
    )


# =========================
# Login page
# =========================

@app.get("/login-page")
def login_page():

    return FileResponse(
        "server/static/login.html"
    )


# =========================
# Signup page
# =========================

@app.get("/signup-page")
def signup_page():

    return FileResponse(
        "server/static/signup.html"
    )


# =========================
# Register
# =========================

@app.post("/register")
def register(data: RegisterRequest):

    db = SessionLocal()

    existing_user = db.query(User).filter(
        User.username == data.username
    ).first()

    if existing_user:

        db.close()

        return {
            "success": False,
            "message": "Username already exists"
        }

    password_hash = hashlib.sha256(
        data.password.encode()
    ).hexdigest()

    new_user = User(
        username=data.username,
        password_hash=password_hash
    )

    db.add(new_user)
    db.commit()

    db.close()

    return {
        "success": True,
        "message": "Account created successfully"
    }


# =========================
# Login
# =========================

@app.post("/login")
def login(data: LoginRequest):

    db = SessionLocal()

    user = db.query(User).filter(
        User.username == data.username
    ).first()

    if user is None:

        db.close()

        return {
            "success": False,
            "message": "Username or password is incorrect"
        }

    password_hash = hashlib.sha256(
        data.password.encode()
    ).hexdigest()

    if password_hash != user.password_hash:

        db.close()

        return {
            "success": False,
            "message": "Username or password is incorrect"
        }

    token = secrets.token_urlsafe(32)

    session_data = Session(
        token=token,
        username=user.username,
        expires_at=datetime.now() + timedelta(days=7)
    )

    db.add(session_data)
    db.commit()

    db.close()

    response = RedirectResponse(
        url="/",
        status_code=303
    )

    response.set_cookie(
        key="parclicker_session",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=7 * 24 * 60 * 60
    )

    return response


# =========================
# Logout
# =========================

@app.get("/logout")
def logout(request: Request):

    token = request.cookies.get("parclicker_session")

    if token:

        db = SessionLocal()

        session_data = db.query(Session).filter(
            Session.token == token
        ).first()

        if session_data:

            db.delete(session_data)
            db.commit()

        db.close()

    response = RedirectResponse(
        url="/login-page",
        status_code=303
    )

    response.delete_cookie(
        "parclicker_session"
    )

    return response


# =========================
# Current user
# =========================

@app.get("/me")
def get_me(request: Request):

    username = get_current_user(request)

    if username is None:

        return {
            "logged_in": False
        }

    return {
        "logged_in": True,
        "username": username
    }


# =========================
# Dashboard page
# =========================

@app.get("/dashboard")
def dashboard(request: Request):

    username = get_current_user(request)

    if username is None:

        return RedirectResponse(
            url="/login-page",
            status_code=303
        )

    return FileResponse(
        "server/static/dashboard.html"
    )


# =========================
# Dashboard API
# =========================

@app.get("/api/dashboard")
def dashboard_data(request: Request):

    username = get_current_user(request)

    if username is None:

        return {
            "logged_in": False
        }

    db = SessionLocal()

    license_data = db.query(License).filter(
        License.username == username
    ).first()

    subscription = db.query(Subscription).filter(
        Subscription.username == username
    ).order_by(
        Subscription.id.desc()
    ).first()

    software_devices = db.query(
        SoftwareDevice
    ).filter(
        SoftwareDevice.username == username
    ).order_by(
        SoftwareDevice.id.desc()
    ).all()

    result = {
        "logged_in": True,
        "username": username,
        "license": None,
        "subscription": None,
        "software_ids": []
    }

    # =========================
    # License
    # =========================

    if license_data:

        expired = False

        if license_data.expires_at:

            expired = (
                datetime.now() >
                license_data.expires_at
            )

        result["license"] = {

            "key": license_data.license_key,

            "active": license_data.active,

            "expired": expired,

            "expires_at": license_data.expires_at
        }

    # =========================
    # Subscription
    # =========================

    if subscription:

        expired = False

        if subscription.expires_at:

            expired = (
                datetime.now() >
                subscription.expires_at
            )

        result["subscription"] = {

            "license_key":
                subscription.license_key,

            "software_id":
                subscription.software_id,

            "cps":
                subscription.cps,

            "months":
                subscription.months,

            "price":
                subscription.price,

            "active":
                subscription.active,

            "expired":
                expired,

            "created_at":
                subscription.created_at,

            "expires_at":
                subscription.expires_at
        }

    # =========================
    # Software IDs
    # =========================

    for device in software_devices:

        result["software_ids"].append({

            "software_id":
                device.software_id,

            "active":
                device.active,

            "created_at":
                device.created_at
        })

    db.close()

    return result


# =========================
# Register Software ID
# =========================

@app.post("/api/software/register")
def register_software(
    data: SoftwareIDRequest,
    request: Request
):

    username = get_current_user(request)

    if username is None:

        return {
            "success": False,
            "message": "You must login first"
        }

    software_id = data.software_id.strip()

    if not software_id:

        return {
            "success": False,
            "message": "Software ID is required"
        }

    if len(software_id) > 100:

        return {
            "success": False,
            "message": "Invalid Software ID"
        }

    db = SessionLocal()

    existing = db.query(
        SoftwareDevice
    ).filter(
        SoftwareDevice.software_id == software_id
    ).first()

    if existing:

        if existing.username == username:

            db.close()

            return {
                "success": True,
                "message": "Software ID is already registered",
                "software_id": existing.software_id
            }

        db.close()

        return {
            "success": False,
            "message": "This Software ID belongs to another account"
        }

    software_device = SoftwareDevice(
        software_id=software_id,
        username=username,
        active=True,
        created_at=datetime.now()
    )

    db.add(software_device)
    db.commit()
    db.refresh(software_device)

    db.close()

    return {
        "success": True,
        "message": "Software ID registered successfully",
        "software_id": software_device.software_id
    }


# =========================
# Check Software ID
# =========================

@app.get("/api/software/check/{software_id}")
def check_software(
    software_id: str,
    request: Request
):

    username = get_current_user(request)

    if username is None:

        return {
            "valid": False,
            "message": "You must login first"
        }

    software_id = software_id.strip()

    if not software_id:

        return {
            "valid": False,
            "message": "Software ID is required"
        }

    db = SessionLocal()

    device = db.query(
        SoftwareDevice
    ).filter(
        SoftwareDevice.software_id == software_id
    ).first()

    db.close()

    if device is None:

        return {
            "valid": False,
            "message": "Software ID not found"
        }

    if device.username != username:

        return {
            "valid": False,
            "message": "This Software ID belongs to another account"
        }

    if not device.active:

        return {
            "valid": False,
            "message": "Software ID is disabled"
        }

    return {
        "valid": True,
        "message": "Software ID is valid",
        "software_id": device.software_id
    }


# =========================
# Software Permission
# =========================

@app.get("/api/software/permission/{software_id}")
def software_permission(software_id: str):

    software_id = software_id.strip()

    db = SessionLocal()

    try:

        device = (
            db.query(SoftwareDevice)
            .filter(
                SoftwareDevice.software_id == software_id
            )
            .first()
        )

        if not device:

            return {
                "allowed": False,
                "message": "این ID در سرور ثبت نشده است."
            }

        if not device.active:

            return {
                "allowed": False,
                "message": "این ID غیرفعال شده است."
            }

        # =========================
        # فقط اشتراک همین Software ID
        # =========================

        subscription = (
            db.query(Subscription)
            .filter(
                Subscription.software_id == software_id
            )
            .order_by(
                Subscription.created_at.desc()
            )
            .first()
        )

        if not subscription:

            return {
                "allowed": False,
                "message": "برای این ID اشتراک وجود ندارد."
            }

        if subscription.username != device.username:

            return {
                "allowed": False,
                "message": "این اشتراک متعلق به صاحب ID نیست."
            }

        if not subscription.active:

            return {
                "allowed": False,
                "message": "اشتراک شما غیرفعال است."
            }

        if subscription.expires_at:

            now = datetime.now()

            if subscription.expires_at <= now:

                return {
                    "allowed": False,
                    "message": "اشتراک شما منقضی شده است."
                }

        return {
            "allowed": True,
            "message": "اجازه استفاده صادر شد.",
            "software_id": software_id,
            "username": device.username,
            "cps": subscription.cps,
            "expires_at": (
                subscription.expires_at.isoformat()
                if subscription.expires_at
                else None
            )
        }

    finally:

        db.close()


# =========================
# CREATE ORDER
# =========================

@app.post("/api/order/create")
def create_order(
    data: OrderRequest,
    request: Request
):

    username = get_current_user(request)

    if username is None:

        return {
            "success": False,
            "message": "You must login first"
        }

    software_id = data.software_id.strip()

    # =========================
    # Validate CPS
    # =========================

    if data.cps < 1 or data.cps > 1000:

        return {
            "success": False,
            "message": "CPS must be between 1 and 1000"
        }

    # =========================
    # Validate months
    # =========================

    if data.months < 1 or data.months > 12:

        return {
            "success": False,
            "message": "Months must be between 1 and 12"
        }

    # =========================
    # Validate Software ID
    # =========================

    db = SessionLocal()

    device = db.query(
        SoftwareDevice
    ).filter(
        SoftwareDevice.software_id == software_id
    ).first()

    if device is None:

        db.close()

        return {
            "success": False,
            "message": "Software ID is not registered"
        }

    if device.username != username:

        db.close()

        return {
            "success": False,
            "message": "This Software ID belongs to another account"
        }

    if not device.active:

        db.close()

        return {
            "success": False,
            "message": "Software ID is disabled"
        }

    # =========================
    # Calculate price
    # =========================

    base_price = data.cps * 2000 * data.months

    discount_rate = (
        (data.months - 1) / 66
    )

    discount_amount = round(
        base_price * discount_rate
    )

    final_price = (
        base_price -
        discount_amount
    )

    # =========================
    # Create order
    # =========================

    order = Order(

        username=username,

        software_id=software_id,

        cps=data.cps,

        months=data.months,

        price=final_price,

        status="pending",

        created_at=datetime.now()
    )

    db.add(order)

    db.commit()

    db.refresh(order)

    order_id = order.id

    db.close()

    return {

        "success": True,

        "message": "Order created successfully",

        "order_id": order_id,

        "software_id": software_id,

        "cps": data.cps,

        "months": data.months,

        "base_price": base_price,

        "discount_amount": discount_amount,

        "price": final_price,

        "status": "pending"
    }


# =========================
# GET USER ORDERS
# =========================

@app.get("/api/orders")
def get_orders(request: Request):

    username = get_current_user(request)

    if username is None:

        return {
            "success": False,
            "message": "You must login first"
        }

    db = SessionLocal()

    orders = db.query(
        Order
    ).filter(
        Order.username == username
    ).order_by(
        Order.id.desc()
    ).all()

    result = []

    for order in orders:

        result.append({

            "id":
                order.id,

            "software_id":
                order.software_id,

            "cps":
                order.cps,

            "months":
                order.months,

            "price":
                order.price,

            "status":
                order.status,

            "created_at":
                order.created_at,

            "paid_at":
                order.paid_at
        })

    db.close()

    return {

        "success": True,

        "orders": result

    }


# =========================
# PAYMENT PAGE
# =========================

@app.get("/payment")
def payment_page(request: Request):

    username = get_current_user(request)

    if username is None:

        return RedirectResponse(
            url="/login-page",
            status_code=303
        )

    return FileResponse(
        "server/static/payment.html"
    )


# =========================
# GET ORDER
# =========================

@app.get("/api/order/{order_id}")
def get_order(
    order_id: int,
    request: Request
):

    username = get_current_user(request)

    if username is None:

        return {
            "success": False,
            "message": "You must login first"
        }

    db = SessionLocal()

    order = db.query(
        Order
    ).filter(
        Order.id == order_id
    ).first()

    if order is None:

        db.close()

        return {
            "success": False,
            "message": "Order not found"
        }

    if order.username != username:

        db.close()

        return {
            "success": False,
            "message": "This order belongs to another account"
        }

    result = {

        "id":
            order.id,

        "software_id":
            order.software_id,

        "cps":
            order.cps,

        "months":
            order.months,

        "price":
            order.price,

        "status":
            order.status,

        "created_at":
            order.created_at,

        "paid_at":
            order.paid_at
    }

    db.close()

    return {

        "success": True,

        "order": result

    }


# =========================
# FAKE PAYMENT
# =========================

@app.post("/api/order/{order_id}/fake-pay")
def fake_payment(
    order_id: int,
    request: Request
):

    username = get_current_user(request)

    if username is None:

        return {
            "success": False,
            "message": "You must login first"
        }

    db = SessionLocal()

    try:

        order = db.query(
            Order
        ).filter(
            Order.id == order_id
        ).first()

        if order is None:

            return {
                "success": False,
                "message": "Order not found"
            }

        if order.username != username:

            return {
                "success": False,
                "message": "This order belongs to another account"
            }

        if order.status == "paid":

            return {
                "success": False,
                "message": "This order has already been paid"
            }

        # =========================
        # پیدا کردن Software ID
        # =========================

        device = db.query(
            SoftwareDevice
        ).filter(
            SoftwareDevice.software_id == order.software_id
        ).first()

        if device is None:

            return {
                "success": False,
                "message": "Software ID not found"
            }

        if device.username != username:

            return {
                "success": False,
                "message": "Software ID belongs to another account"
            }

        if not device.active:

            return {
                "success": False,
                "message": "Software ID is disabled"
            }

        # =========================
        # پرداخت سفارش
        # =========================

        payment_time = datetime.now()

        order.status = "paid"
        order.paid_at = payment_time

        # =========================
        # ساخت License Key
        # =========================

        license_key = (
            "PC-"
            + secrets.token_hex(8).upper()
        )

        # =========================
        # محاسبه تاریخ انقضا
        # =========================

        expires_at = (
            payment_time +
            timedelta(
                days=30 * order.months
            )
        )

        # =========================
        # ساخت اشتراک
        # =========================

        subscription = Subscription(

            username=username,

            license_key=license_key,

            software_id=order.software_id,

            cps=order.cps,

            months=order.months,

            price=order.price,

            active=True,

            created_at=payment_time,

            expires_at=expires_at
        )

        db.add(subscription)

        db.commit()

        db.refresh(subscription)

        return {

            "success": True,

            "message":
                "Payment completed successfully",

            "order_id":
                order.id,

            "status":
                "paid",

            "software_id":
                order.software_id,

            "cps":
                subscription.cps,

            "months":
                subscription.months,

            "license_key":
                subscription.license_key,

            "expires_at":
                subscription.expires_at

        }

    except Exception as e:

        db.rollback()

        return {

            "success": False,

            "message":
                f"Payment error: {str(e)}"

        }

    finally:

        db.close()


# =========================
# License checker
# =========================

@app.get("/license/{license_key}")
def check_license(
    license_key: str,
    request: Request
):

    username = get_current_user(request)

    if username is None:

        return {
            "valid": False,
            "message": "You must login first"
        }

    db = SessionLocal()

    license_data = db.query(
        License
    ).filter(
        License.license_key == license_key
    ).first()

    db.close()

    if license_data is None:

        return {
            "valid": False,
            "message": "License not found"
        }

    if not license_data.active:

        return {
            "valid": False,
            "message": "License is disabled"
        }

    if license_data.expires_at is not None:

        if datetime.now() > license_data.expires_at:

            return {
                "valid": False,
                "message": "License has expired"
            }

    return {

        "valid": True,

        "message": "License is active",

        "username":
            license_data.username,

        "expires_at":
            license_data.expires_at
    }
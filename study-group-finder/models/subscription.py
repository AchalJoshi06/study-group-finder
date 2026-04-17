from datetime import datetime

from extensions import db


class Subscription(db.Model):
    __tablename__ = "subscription"
    __table_args__ = (
        db.CheckConstraint("plan_type IN ('free', 'premium')", name="ck_subscription_plan_type"),
        db.CheckConstraint("status IN ('active', 'expired')", name="ck_subscription_status"),
        db.CheckConstraint("end_date > start_date", name="ck_subscription_date_window"),
        db.Index("ix_subscription_user_end", "user_id", "end_date"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    plan_type = db.Column(db.String(20), nullable=False, default="free")
    start_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="active")
    stripe_subscription_id = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="subscriptions")

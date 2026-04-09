import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import Generator, Optional, Any
from app.core.config import settings


def get_connection():
    return psycopg2.connect(settings.database_url)


@contextmanager
def get_cursor(dict_cursor: bool = True) -> Generator:
    conn = get_connection()
    try:
        cursor_factory = RealDictCursor if dict_cursor else None
        cur = conn.cursor(cursor_factory=cursor_factory)
        yield cur
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


class UserDB:
    @staticmethod
    def get_by_id(user_id: int) -> Optional[dict]:
        with get_cursor() as cur:
            cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            return cur.fetchone()

    @staticmethod
    def get_by_email(email: str) -> Optional[dict]:
        with get_cursor() as cur:
            cur.execute("SELECT * FROM users WHERE email = %s", (email,))
            return cur.fetchone()

    @staticmethod
    def get_all() -> list:
        with get_cursor() as cur:
            cur.execute("SELECT * FROM users ORDER BY created_at DESC")
            return cur.fetchall()

    @staticmethod
    def create(email: str, name: str = "", tier: str = "free") -> dict:
        with get_cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (email, name, tier)
                VALUES (%s, %s, %s)
                ON CONFLICT (email) DO UPDATE SET
                    name = EXCLUDED.name,
                    tier = EXCLUDED.tier,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING *
                """,
                (email, name, tier),
            )
            return cur.fetchone()

    @staticmethod
    def create_with_password(email: str, name: str, password: str) -> dict:
        from app.core.auth import hash_password
        with get_cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (email, name, tier, password_hash, must_set_password)
                VALUES (%s, %s, %s, %s, FALSE)
                ON CONFLICT (email) DO UPDATE SET
                    name = EXCLUDED.name,
                    password_hash = EXCLUDED.password_hash,
                    must_set_password = FALSE,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING *
                """,
                (email, name, "free", hash_password(password)),
            )
            return cur.fetchone()

    @staticmethod
    def update(email: str, **kwargs) -> dict:
        allowed = [
            "name",
            "tier",
            "subscribed_at",
            "subscription_expires",
            "billing_cycle",
            "pro_started_at",
            "runs_used",
            "password_hash",
            "last_login",
            "must_set_password",
        ]
        updates = {k: v for k, v in kwargs.items() if k in allowed}

        if not updates:
            return UserDB.get_by_email(email)

        set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
        values = list(updates.values()) + [email]

        with get_cursor() as cur:
            cur.execute(
                f"UPDATE users SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE email = %s RETURNING *",
                values,
            )
            return cur.fetchone()

    @staticmethod
    def count_by_tier() -> dict:
        with get_cursor() as cur:
            cur.execute("""
                SELECT tier, COUNT(*) as count 
                FROM users 
                GROUP BY tier
            """)
            results = cur.fetchall()
            return {r["tier"]: r["count"] for r in results}


class TrackedRunDB:
    @staticmethod
    def create(agent_id: str, user_id: str = "anonymous") -> dict:
        with get_cursor() as cur:
            cur.execute(
                """
                INSERT INTO tracked_runs (agent_id, user_id)
                VALUES (%s, %s)
                RETURNING *
                """,
                (agent_id, user_id),
            )
            return cur.fetchone()

    @staticmethod
    def get_all() -> list:
        with get_cursor() as cur:
            cur.execute("SELECT * FROM tracked_runs ORDER BY timestamp DESC")
            return cur.fetchall()

    @staticmethod
    def count_by_agent() -> dict:
        with get_cursor() as cur:
            cur.execute("""
                SELECT agent_id, COUNT(*) as count 
                FROM tracked_runs 
                GROUP BY agent_id
                ORDER BY count DESC
            """)
            results = cur.fetchall()
            return {r["agent_id"]: r["count"] for r in results}

    @staticmethod
    def count_by_user() -> dict:
        with get_cursor() as cur:
            cur.execute("""
                SELECT user_id, COUNT(*) as count 
                FROM tracked_runs 
                GROUP BY user_id
            """)
            results = cur.fetchall()
            return {r["user_id"]: r["count"] for r in results}

    @staticmethod
    def get_daily_trend(days: int = 30) -> list:
        with get_cursor() as cur:
            cur.execute(
                """
                SELECT DATE(timestamp) as date, COUNT(*) as runs
                FROM tracked_runs
                WHERE timestamp >= CURRENT_DATE - INTERVAL '%s days'
                GROUP BY DATE(timestamp)
                ORDER BY date
            """,
                (days,),
            )
            return [dict(r) for r in cur.fetchall()]

    @staticmethod
    def get_hourly_trend() -> list:
        with get_cursor() as cur:
            cur.execute("""
                SELECT EXTRACT(HOUR FROM timestamp) as hour, COUNT(*) as runs
                FROM tracked_runs
                GROUP BY EXTRACT(HOUR FROM timestamp)
                ORDER BY hour
            """)
            return [dict(r) for r in cur.fetchall()]


class PaymentDB:
    @staticmethod
    def create(
        user_email: str,
        user_name: str = "",
        amount: float = 0,
        billing_cycle: str = "monthly",
        status: str = "pending",
    ) -> dict:
        with get_cursor() as cur:
            cur.execute(
                """
                INSERT INTO payments (user_email, user_name, amount, billing_cycle, status)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING *
                """,
                (user_email, user_name, amount, billing_cycle, status),
            )
            return cur.fetchone()

    @staticmethod
    def get_all() -> list:
        with get_cursor() as cur:
            cur.execute("SELECT * FROM payments ORDER BY date DESC")
            return cur.fetchall()

    @staticmethod
    def get_completed() -> list:
        with get_cursor() as cur:
            cur.execute(
                "SELECT * FROM payments WHERE status = 'completed' ORDER BY date DESC"
            )
            return cur.fetchall()


class PendingPaymentDB:
    @staticmethod
    def create(
        payment_id: str,
        user_email: str,
        user_name: str = "",
        billing_cycle: str = "monthly",
        amount: float = 0,
        screenshot_path: str = "",
    ) -> dict:
        with get_cursor() as cur:
            cur.execute(
                """
                INSERT INTO pending_payments (id, user_email, user_name, billing_cycle, amount, screenshot_path)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    payment_id,
                    user_email,
                    user_name,
                    billing_cycle,
                    amount,
                    screenshot_path,
                ),
            )
            return cur.fetchone()

    @staticmethod
    def get_by_id(payment_id: str) -> Optional[dict]:
        with get_cursor() as cur:
            cur.execute("SELECT * FROM pending_payments WHERE id = %s", (payment_id,))
            return cur.fetchone()

    @staticmethod
    def get_pending() -> list:
        with get_cursor() as cur:
            cur.execute(
                "SELECT * FROM pending_payments WHERE status = 'pending' ORDER BY submitted_at DESC"
            )
            return cur.fetchall()

    @staticmethod
    def update_status(payment_id: str, status: str) -> dict:
        column = "approved_at" if status == "approved" else "rejected_at"
        with get_cursor() as cur:
            cur.execute(
                f"UPDATE pending_payments SET status = %s, {column} = CURRENT_TIMESTAMP WHERE id = %s RETURNING *",
                (status, payment_id),
            )
            return cur.fetchone()


class AdminConfigDB:
    @staticmethod
    def get(key: str) -> Optional[dict]:
        with get_cursor() as cur:
            cur.execute("SELECT * FROM admin_config WHERE key = %s", (key,))
            return cur.fetchone()

    @staticmethod
    def get_all() -> list:
        with get_cursor() as cur:
            cur.execute("SELECT * FROM admin_config ORDER BY key")
            return cur.fetchall()

    @staticmethod
    def set(key: str, value: Any, description: str = "") -> dict:
        with get_cursor() as cur:
            cur.execute(
                """
                INSERT INTO admin_config (key, value, description)
                VALUES (%s, %s, %s)
                ON CONFLICT (key) DO UPDATE SET
                    value = EXCLUDED.value,
                    description = COALESCE(EXCLUDED.description, admin_config.description),
                    updated_at = CURRENT_TIMESTAMP
                RETURNING *
                """,
                (key, str(value), description),
            )
            return cur.fetchone()

    @staticmethod
    def initialize_defaults():
        defaults = [
            ("openrouter_api_key", "", "OpenRouter API Key for LLM calls"),
            ("upi_id", "marketing@upi", "UPI ID for payments"),
            ("monthly_price", "1000", "Monthly subscription price (INR)"),
            ("yearly_price", "9000", "Yearly subscription price (INR)"),
            ("anonymous_runs_limit", "5", "Runs for anonymous users"),
            ("free_user_runs_limit", "25", "Runs for free users"),
            ("pro_runs_limit", "100", "Runs for Pro users per month"),
            ("refund_tier1_days", "7", "100% refund tier - days"),
            ("refund_tier1_runs", "10", "100% refund tier - runs"),
            ("refund_tier1_percent", "100", "100% refund tier - percentage"),
            ("refund_tier2_days", "15", "50% refund tier - days"),
            ("refund_tier2_runs", "50", "50% refund tier - runs"),
            ("refund_tier2_percent", "50", "50% refund tier - percentage"),
        ]
        for key, value, desc in defaults:
            AdminConfigDB.set(key, value, desc)

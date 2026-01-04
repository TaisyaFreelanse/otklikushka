"""Database module for storing projects, bids, and settings."""
import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
import config


class Database:
    """Database handler for Freelancehunt bot."""
    
    def __init__(self, db_path: Path = None):
        """Initialize database connection."""
        self.db_path = db_path or config.DATABASE_PATH
        self.conn = None
        self.init_database()
    
    def get_connection(self):
        """Get or create database connection."""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def init_database(self):
        """Initialize database schema."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Projects table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                category TEXT,
                budget REAL,
                deadline INTEGER,
                url TEXT NOT NULL UNIQUE,
                created_at TEXT,
                first_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Bids table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bids (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                bid_amount REAL NOT NULL,
                bid_deadline INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                sent_at TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        """)
        
        # Settings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        
        # Other projects table (projects outside categories)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS other_projects (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                category TEXT,
                budget REAL,
                deadline INTEGER,
                url TEXT NOT NULL UNIQUE,
                created_at TEXT,
                first_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                notified INTEGER DEFAULT 0
            )
        """)
        
        # Initialize default settings
        cursor.execute("""
            INSERT OR IGNORE INTO settings (key, value) 
            VALUES ('enabled', 'false')
        """)
        cursor.execute("""
            INSERT OR IGNORE INTO settings (key, value) 
            VALUES ('check_interval', ?)
        """, (str(config.CHECK_INTERVAL),))
        cursor.execute("""
            INSERT OR IGNORE INTO settings (key, value) 
            VALUES ('categories', '[]')
        """)
        
        conn.commit()
    
    # Projects methods
    def add_project(self, project_id: str, title: str, category: str, 
                   budget: Optional[float], deadline: Optional[int], 
                   url: str, created_at: str = None) -> bool:
        """Add a new project or return False if it already exists."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            created_at = created_at or datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO projects (id, title, category, budget, deadline, url, created_at, first_seen_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (project_id, title, category, budget, deadline, url, created_at, datetime.now().isoformat()))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def project_exists(self, project_id: str) -> bool:
        """Check if project exists in database."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM projects WHERE id = ?", (project_id,))
        return cursor.fetchone() is not None
    
    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project by ID."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    # Bids methods
    def add_bid(self, project_id: str, bid_amount: float, 
                bid_deadline: int, status: str = "pending") -> int:
        """Add a new bid and return its ID."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO bids (project_id, bid_amount, bid_deadline, status, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (project_id, bid_amount, bid_deadline, status, datetime.now().isoformat()))
        conn.commit()
        return cursor.lastrowid
    
    def update_bid_status(self, bid_id: int, status: str):
        """Update bid status."""
        conn = self.get_connection()
        cursor = conn.cursor()
        sent_at = datetime.now().isoformat() if status in ("sent", "failed") else None
        cursor.execute("""
            UPDATE bids 
            SET status = ?, sent_at = ?
            WHERE id = ?
        """, (status, sent_at, bid_id))
        conn.commit()
    
    def get_last_bids(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get last N bids with project information."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                b.id,
                b.project_id,
                b.bid_amount,
                b.bid_deadline,
                b.status,
                b.created_at,
                b.sent_at,
                p.title,
                p.url,
                p.category
            FROM bids b
            JOIN projects p ON b.project_id = p.id
            ORDER BY b.created_at DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def get_pending_bids(self) -> List[Dict[str, Any]]:
        """Get all pending bids."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                b.id,
                b.project_id,
                b.bid_amount,
                b.bid_deadline,
                p.title,
                p.url
            FROM bids b
            JOIN projects p ON b.project_id = p.id
            WHERE b.status = 'pending'
            ORDER BY b.created_at ASC
        """)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    # Settings methods
    def get_setting(self, key: str, default: str = None) -> str:
        """Get setting value."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row["value"] if row else default
    
    def set_setting(self, key: str, value: str):
        """Set setting value."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO settings (key, value)
            VALUES (?, ?)
        """, (key, value))
        conn.commit()
    
    def get_enabled(self) -> bool:
        """Check if auto-bidding is enabled."""
        return self.get_setting("enabled", "false").lower() == "true"
    
    def set_enabled(self, enabled: bool):
        """Enable or disable auto-bidding."""
        self.set_setting("enabled", "true" if enabled else "false")
    
    def get_categories(self) -> List[str]:
        """Get list of categories to monitor."""
        categories_json = self.get_setting("categories", "[]")
        try:
            return json.loads(categories_json)
        except json.JSONDecodeError:
            return []
    
    def set_categories(self, categories: List[str]):
        """Set list of categories to monitor."""
        self.set_setting("categories", json.dumps(categories))
    
    def get_last_check_time(self) -> Optional[datetime]:
        """Get last check time."""
        last_check = self.get_setting("last_check_time")
        if last_check:
            try:
                return datetime.fromisoformat(last_check)
            except ValueError:
                return None
        return None
    
    def set_last_check_time(self, check_time: datetime = None):
        """Set last check time."""
        if check_time is None:
            check_time = datetime.now()
        self.set_setting("last_check_time", check_time.isoformat())
    
    # Other projects methods (projects outside categories)
    def add_other_project(self, project_id: str, title: str, category: str,
                         budget: Optional[float], deadline: Optional[int],
                         url: str, created_at: str = None) -> bool:
        """Add a project outside categories or return False if it already exists."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            created_at = created_at or datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO other_projects (id, title, category, budget, deadline, url, created_at, first_seen_at, notified)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
            """, (project_id, title, category, budget, deadline, url, created_at, datetime.now().isoformat()))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def get_new_other_projects(self) -> List[Dict[str, Any]]:
        """Get other projects that haven't been notified yet."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM other_projects
            WHERE notified = 0
            ORDER BY first_seen_at DESC
        """)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def mark_other_project_notified(self, project_id: str):
        """Mark other project as notified."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE other_projects
            SET notified = 1
            WHERE id = ?
        """, (project_id,))
        conn.commit()
    
    def get_all_other_projects(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all other projects."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM other_projects
            ORDER BY first_seen_at DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None


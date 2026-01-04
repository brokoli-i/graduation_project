# ============================================================
# database.py # Veritabanı depolama modülü (BDIM)
# ============================================================
import sqlite3
import json
from typing import Optional, List
from datetime import datetime
from models import SlabDesignResult, DesignOut, LoadAnalysis, ThicknessCheck


class SlabDatabase:
    """SQLite-based database for slab design results"""
    
    def __init__(self, db_path: str = "slab_designs.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database and create tables if not exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS slab_designs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    slab_id TEXT UNIQUE NOT NULL,
                    lx_m REAL,
                    ly_m REAL,
                    h_mm REAL,
                    concrete TEXT,
                    steel TEXT,
                    g_total_kN_m2 REAL,
                    q_live_kN_m2 REAL,
                    pd_factored_kN_m2 REAL,
                    slab_type TEXT,
                    slab_case INTEGER,
                    m_ratio REAL,
                    Lsn_x_m REAL,
                    Lsn_y_m REAL,
                    x_bottom_main TEXT,
                    x_bottom_pilye TEXT,
                    x_top TEXT,
                    y_bottom_main TEXT,
                    y_bottom_pilye TEXT,
                    y_top TEXT,
                    distribution_bars TEXT,
                    h_min_required_mm REAL,
                    thickness_ok INTEGER,
                    created_at TEXT,
                    notes TEXT
                )
            """)
            conn.commit()
    
    def save_design(self, result: SlabDesignResult) -> int:
        """Save design to database, return row ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO slab_designs (
                    slab_id, lx_m, ly_m, h_mm, concrete, steel,
                    g_total_kN_m2, q_live_kN_m2, pd_factored_kN_m2,
                    slab_type, slab_case, m_ratio, Lsn_x_m, Lsn_y_m,
                    x_bottom_main, x_bottom_pilye, x_top,
                    y_bottom_main, y_bottom_pilye, y_top,
                    distribution_bars, h_min_required_mm, thickness_ok,
                    created_at, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.slab_id, result.lx_m, result.ly_m, result.h_mm,
                result.concrete, result.steel,
                result.g_total_kN_m2, result.q_live_kN_m2, result.pd_factored_kN_m2,
                result.slab_type, result.slab_case, result.m_ratio,
                result.Lsn_x_m, result.Lsn_y_m,
                result.x_bottom_main, result.x_bottom_pilye, result.x_top,
                result.y_bottom_main, result.y_bottom_pilye, result.y_top,
                result.distribution_bars, result.h_min_required_mm,
                1 if result.thickness_ok else 0,
                result.created_at, result.notes
            ))
            conn.commit()
            return cursor.lastrowid or 0
    
    def get_design(self, slab_id: str) -> Optional[SlabDesignResult]:
        """Retrieve design by slab_id"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM slab_designs WHERE slab_id = ?", (slab_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_result(row)
        return None
    
    def list_designs(self) -> List[SlabDesignResult]:
        """List all saved designs"""
        results = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM slab_designs ORDER BY created_at DESC")
            for row in cursor.fetchall():
                results.append(self._row_to_result(row))
        return results
    
    def delete_design(self, slab_id: str) -> bool:
        """Delete a design by slab_id"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM slab_designs WHERE slab_id = ?", (slab_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def _row_to_result(self, row) -> SlabDesignResult:
        """Convert database row to SlabDesignResult"""
        return SlabDesignResult(
            slab_id=row[1],
            lx_m=row[2],
            ly_m=row[3],
            h_mm=row[4],
            concrete=row[5],
            steel=row[6],
            g_total_kN_m2=row[7],
            q_live_kN_m2=row[8],
            pd_factored_kN_m2=row[9],
            slab_type=row[10],
            slab_case=row[11],
            m_ratio=row[12],
            Lsn_x_m=row[13],
            Lsn_y_m=row[14],
            x_bottom_main=row[15],
            x_bottom_pilye=row[16],
            x_top=row[17],
            y_bottom_main=row[18],
            y_bottom_pilye=row[19],
            y_top=row[20],
            distribution_bars=row[21] or "",
            h_min_required_mm=row[22],
            thickness_ok=bool(row[23]),
            created_at=row[24],
            notes=row[25] or ""
        )


def create_design_result(
    slab_id: str,
    data,  # InputData
    out_x: DesignOut,
    out_y: DesignOut,
    load: LoadAnalysis,
    thk: ThicknessCheck,
    notes: str = ""
) -> SlabDesignResult:
    """Create a SlabDesignResult from design outputs"""
    from models import BarChoice
    
    def format_bar(c: Optional[BarChoice]) -> str:
        if c is None or c.phi <= 0:
            return "-"
        return f"Ø{c.phi}/{c.s_cm:.0f}"
    
    # X direction
    if out_x.main_bottom_layout and out_x.main_bottom_layout.straight.phi > 0:
        x_bottom = format_bar(out_x.main_bottom_layout.straight)
        x_pilye = format_bar(out_x.main_bottom_layout.pilye)
    else:
        x_bottom = "-"
        x_pilye = "-"
    x_top = format_bar(out_x.top_layout)
    
    # Y direction
    if out_y.main_bottom_layout and out_y.main_bottom_layout.straight.phi > 0:
        y_bottom = format_bar(out_y.main_bottom_layout.straight)
        y_pilye = format_bar(out_y.main_bottom_layout.pilye)
    else:
        y_bottom = "-"
        y_pilye = "-"
    y_top = format_bar(out_y.top_layout)
    
    # Distribution bars
    dist = "-"
    if out_x.dist_bars and out_x.dist_bars.phi > 0:
        dist = format_bar(out_x.dist_bars)
    elif out_y.dist_bars and out_y.dist_bars.phi > 0:
        dist = format_bar(out_y.dist_bars)
    
    return SlabDesignResult(
        slab_id=slab_id,
        lx_m=data.lx,
        ly_m=data.ly,
        h_mm=data.h_mm,
        concrete=data.concrete,
        steel=data.steel,
        g_total_kN_m2=load.g_total,
        q_live_kN_m2=load.q_live,
        pd_factored_kN_m2=load.pd_factored,
        slab_type=out_x.slab_type,
        slab_case=out_x.slab_case,
        m_ratio=out_x.m,
        Lsn_x_m=out_x.Lsn_x,
        Lsn_y_m=out_x.Lsn_y,
        x_bottom_main=x_bottom,
        x_bottom_pilye=x_pilye,
        x_top=x_top,
        y_bottom_main=y_bottom,
        y_bottom_pilye=y_pilye,
        y_top=y_top,
        distribution_bars=dist,
        h_min_required_mm=thk.h_min_mm,
        thickness_ok=thk.ok,
        notes=notes
    )

"""
Репозиторий для работы с транзакциями (реализация MySQL)
"""

from typing import List, Dict, Optional
from decimal import Decimal
from datetime import datetime
from domain.repositories.transaction_repository import TransactionRepositoryInterface
from infrastructure.database.connection_pool import database_service


class TransactionRepository(TransactionRepositoryInterface):
    """Реализация TransactionRepository для MySQL"""
    
    def __init__(self, db=None):
        self.db = db or database_service
    
    async def create(self, trans_type: str, user_id: int, 
                     material_id: int, quantity: Decimal, 
                     comment: str = "") -> int:
        """Создать транзакцию"""
        async with self.db.transaction() as conn:
            query_trans = """
                INSERT INTO transactions (type, user_id, comment)
                VALUES (%s, %s, %s)
            """
            async with conn.cursor() as cur:
                await cur.execute(query_trans, (trans_type, user_id, comment))
                trans_id = cur.lastrowid
                
                query_item = """
                    INSERT INTO transaction_items (transaction_id, material_id, quantity)
                    VALUES (%s, %s, %s)
                """
                await cur.execute(query_item, (trans_id, material_id, quantity))
                
                return trans_id
    
    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        user_id: Optional[int] = None,
        material_id: Optional[int] = None,
        trans_type: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> List[Dict]:
        """Получить все транзакции с фильтрацией"""
        
        params = []
        where_clauses = []

        base_query = """
            SELECT 
                t.id,
                t.user_id,
                t.type,
                t.created_at,
                u.login as user_name,
                GROUP_CONCAT(m.name SEPARATOR ', ') as material_name,
                t.comment,
                COUNT(ti.id) as items_count,
                SUM(ti.quantity) as total_quantity
            FROM transactions t
            JOIN users u ON u.id = t.user_id
            JOIN transaction_items ti ON ti.transaction_id = t.id
            JOIN materials m ON ti.material_id = m.id
        """

        if user_id is not None:
            where_clauses.append("t.user_id = %s")
            params.append(user_id)
        
        if material_id is not None:
            # This subquery ensures we filter transactions by material_id
            where_clauses.append("t.id IN (SELECT DISTINCT transaction_id FROM transaction_items WHERE material_id = %s)")
            params.append(material_id)

        if trans_type is not None:
            where_clauses.append("t.type = %s")
            params.append(trans_type)
            
        if date_from is not None:
            where_clauses.append("t.created_at >= %s")
            params.append(date_from)
            
        if date_to is not None:
            where_clauses.append("t.created_at <= %s")
            params.append(date_to)

        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)
            
        query = f"{base_query} {where_sql} GROUP BY t.id ORDER BY t.created_at DESC LIMIT %s OFFSET %s"
        
        params.extend([limit, offset])
        return await self.db.fetch_all(query, tuple(params))
    
    async def get_today_stats(self) -> Dict:
        """Получить статистику за сегодня"""
        query = """
            SELECT 
                COUNT(DISTINCT CASE WHEN type = 'IN' THEN t.id END) as in_count,
                COUNT(DISTINCT CASE WHEN type = 'OUT' THEN t.id END) as out_count,
                COALESCE(SUM(CASE WHEN type = 'IN' THEN ti.quantity ELSE 0 END), 0) as in_quantity,
                COALESCE(SUM(CASE WHEN type = 'OUT' THEN ti.quantity ELSE 0 END), 0) as out_quantity
            FROM transactions t
            JOIN transaction_items ti ON ti.transaction_id = t.id
            WHERE DATE(t.created_at) = CURDATE()
        """
        result = await self.db.fetch_one(query)
        return result or {}
    
    async def get_total_count(
        self,
        user_id: Optional[int] = None,
        material_id: Optional[int] = None,
        trans_type: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> int:
        """Получить общее количество транзакций с фильтрацией"""
        
        params = []
        where_clauses = []
        
        # Base query for counting from transactions
        base_query = "FROM transactions t"
        
        # If filtering by material_id, we need to join transaction_items
        if material_id is not None:
            base_query += " JOIN transaction_items ti ON t.id = ti.transaction_id"
            where_clauses.append("ti.material_id = %s")
            params.append(material_id)

        if user_id is not None:
            where_clauses.append("t.user_id = %s")
            params.append(user_id)

        if trans_type is not None:
            where_clauses.append("t.type = %s")
            params.append(trans_type)
            
        if date_from is not None:
            where_clauses.append("t.created_at >= %s")
            params.append(date_from)
            
        if date_to is not None:
            where_clauses.append("t.created_at <= %s")
            params.append(date_to)

        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)
            
        # We use DISTINCT t.id to count unique transactions
        query = f"SELECT COUNT(DISTINCT t.id) as total_count {base_query} {where_sql}"
        
        result = await self.db.fetch_one(query, tuple(params))
        return result["total_count"] if result else 0
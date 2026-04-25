-- =============================================================================
-- Warehouse Inventory — полная схема БД
-- Запустить на чистой (пустой) схеме: mysql -u root -p inventory < schema.sql
-- =============================================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- -----------------------------------------------------------------------------
-- 1. units — единицы измерения
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS units (
    id          INT          AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL COMMENT 'Полное название (штука, килограмм…)',
    short_name  VARCHAR(20)  NOT NULL COMMENT 'Короткое название (шт, кг, л…)',
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 2. equipment_groups — группы оборудования
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS equipment_groups (
    id          BIGINT       AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 3. material_groups — группы материалов (без иерархии parent_id)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS material_groups (
    id          INT          AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 4. equipment_group_material_groups — M2M: группы оборудования ↔ группы материалов
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS equipment_group_material_groups (
    equipment_group_id  BIGINT    NOT NULL,
    material_group_id   INT       NOT NULL,
    created_at          TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (equipment_group_id, material_group_id),
    KEY idx_egmg_material_group (material_group_id),
    CONSTRAINT fk_egmg_equipment_group
        FOREIGN KEY (equipment_group_id) REFERENCES equipment_groups (id)
        ON DELETE CASCADE,
    CONSTRAINT fk_egmg_material_group
        FOREIGN KEY (material_group_id)  REFERENCES material_groups  (id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 5. materials — материалы
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS materials (
    id                  INT             AUTO_INCREMENT PRIMARY KEY,
    name                VARCHAR(255)    NOT NULL,
    article             VARCHAR(100)    NOT NULL UNIQUE COMMENT 'Артикул',
    unit_id             INT             NOT NULL,
    group_id            INT             NOT NULL,
    equipment_group_id  BIGINT          NULL     COMMENT 'Устаревшее поле (используйте equipment_group_material_groups)',
    min_stock           DECIMAL(10, 3)  NOT NULL DEFAULT 0.000 COMMENT 'Минимальный остаток',
    created_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_materials_unit
        FOREIGN KEY (unit_id)  REFERENCES units          (id),
    CONSTRAINT fk_materials_group
        FOREIGN KEY (group_id) REFERENCES material_groups (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 6. stock — текущие остатки
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS stock (
    material_id  INT            NOT NULL PRIMARY KEY,
    quantity     DECIMAL(10, 3) NOT NULL DEFAULT 0.000,
    updated_at   DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_stock_material
        FOREIGN KEY (material_id) REFERENCES materials (id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 7. users — пользователи
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id             INT          AUTO_INCREMENT PRIMARY KEY,
    login          VARCHAR(100) NOT NULL UNIQUE,
    full_name      VARCHAR(255) NULL,
    password_hash  VARCHAR(255) NOT NULL COMMENT 'SHA-256 hex',
    role           ENUM('admin','user') NOT NULL DEFAULT 'user',
    is_active      TINYINT(1)   NOT NULL DEFAULT 1,
    created_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login     DATETIME     NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 8. transactions — операции прихода / расхода
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS transactions (
    id          INT          AUTO_INCREMENT PRIMARY KEY,
    type        ENUM('IN','OUT') NOT NULL COMMENT 'IN — приход, OUT — расход',
    user_id     INT          NOT NULL,
    comment     VARCHAR(500) NULL DEFAULT '',
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_transactions_user
        FOREIGN KEY (user_id) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 9. transaction_items — позиции транзакций
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS transaction_items (
    id              INT            AUTO_INCREMENT PRIMARY KEY,
    transaction_id  INT            NOT NULL,
    material_id     INT            NOT NULL,
    quantity        DECIMAL(10, 3) NOT NULL,
    CONSTRAINT fk_ti_transaction
        FOREIGN KEY (transaction_id) REFERENCES transactions (id)
        ON DELETE CASCADE,
    CONSTRAINT fk_ti_material
        FOREIGN KEY (material_id)    REFERENCES materials    (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;

-- =============================================================================
-- Начальные данные
-- =============================================================================

-- Единицы измерения
INSERT INTO units (name, short_name) VALUES
    ('Штука',       'шт'),
    ('Килограмм',   'кг'),
    ('Литр',        'л'),
    ('Метр',        'м'),
    ('Упаковка',    'уп'),
    ('Комплект',    'компл');

-- Администратор: login=admin, password=admin123  (SHA-256)
INSERT INTO users (login, full_name, password_hash, role, is_active) VALUES
    ('admin', 'Administrator', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', 'admin', 1);

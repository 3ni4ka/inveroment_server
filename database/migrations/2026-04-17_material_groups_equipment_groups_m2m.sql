-- Normalize material groups model:
-- 1) Remove nested material_groups hierarchy (parent_id).
-- 2) Add many-to-many relation between equipment_groups and material_groups.

START TRANSACTION;

CREATE TABLE IF NOT EXISTS equipment_group_material_groups (
    equipment_group_id BIGINT NOT NULL,
    material_group_id BIGINT NOT NULL,
    created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (equipment_group_id, material_group_id),
    KEY idx_egmg_material_group (material_group_id),
    CONSTRAINT fk_egmg_equipment_group
        FOREIGN KEY (equipment_group_id) REFERENCES equipment_groups (id)
        ON DELETE CASCADE,
    CONSTRAINT fk_egmg_material_group
        FOREIGN KEY (material_group_id) REFERENCES material_groups (id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Backfill link table from existing materials.equipment_group_id + materials.group_id combinations.
INSERT IGNORE INTO equipment_group_material_groups (equipment_group_id, material_group_id)
SELECT DISTINCT m.equipment_group_id, m.group_id
FROM materials m
WHERE m.equipment_group_id IS NOT NULL
  AND m.group_id IS NOT NULL;

-- Drop self-hierarchy in material_groups.
ALTER TABLE material_groups DROP FOREIGN KEY fk_material_groups_parent;
ALTER TABLE material_groups DROP INDEX fk_material_groups_parent;
ALTER TABLE material_groups DROP COLUMN parent_id;

COMMIT;

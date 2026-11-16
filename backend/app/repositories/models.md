# 数据库设计

## games

| 列 | 类型 | 说明 |
| --- | --- | --- |
| `id` | `uuid` | 主键，`gen_random_uuid()` |
| `name` | `text` | 游戏名称 |
| `created_at` | `timestamptz` | 创建时间 |
| `updated_at` | `timestamptz` | 更新时间 |

## sandbox_sessions

| 列 | 类型 | 说明 |
| --- | --- | --- |
| `id` | `uuid` | 主键 |
| `game_id` | `uuid` | 外键 `games.id`，`ON DELETE CASCADE`，唯一 |
| `sandbox_id` | `text` | 当前沙盒 ID；归档后为 `NULL` |
| `lifecycle_state` | `text` | `active` / `archiving` / `archived` / `restoring` |
| `snapshot_key` | `text` | OSS 对象 key |
| `snapshot_at` | `timestamptz` | 快照时间 |
| `snapshot_bytes` | `bigint` | tar.gz 字节数 |
| `snapshot_sha256` | `text` | tar.gz SHA-256 |
| `last_used_at` | `timestamptz` | 应用层最近使用时间 |
| `archive_retry_at` | `timestamptz` | 归档失败后的重试时间 |
| `archive_attempts` | `integer` | 连续归档失败次数 |
| `last_error` | `text` | 最近一次错误摘要 |
| `created_at` | `timestamptz` | 创建时间 |
| `updated_at` | `timestamptz` | 更新时间 |

索引：

- `sandbox_sessions_game_idx`：`game_id` 唯一
- `sandbox_sessions_last_used_idx`：`last_used_at`
- `sandbox_sessions_retry_idx`：`archive_retry_at`

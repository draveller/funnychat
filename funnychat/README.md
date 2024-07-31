## 插件说明

抽签/解签/签到


## 插件配置

将 `plugins/funnychat` 目录下的 `config.json.template` 配置模板复制为最终生效的 `config.json`。 (如果未配置则会默认使用`config.json.template`模板中配置)。

以下是插件配置项说明：

```bash
{
    "mysql": {
      "host": "dzl-database.mysql.rds.aliyuncs.com",
      "port": 3306,
      "user": "root",
      "password": "MuL!zsV8dHov346i4oY7KBXsX3",
      "database": "funny_chat"
    },
    "redis": {
      "host": "47.102.41.226",
      "port": 6379,
      "password": "ding@7788",
      "db": 0
    }
  }
```

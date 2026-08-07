# 第 16 章：发布 TypeScript 定义文件

## 16.1：在 npm 库中包含定义文件

将类型声明添加到你的 `package.json`：

```json
{
  ...
  "typings": "path/file.d.ts"
  ...
}
```

现在，每当该库被导入时，TypeScript 将加载该类型声明文件。

---

===

GoalKicker.com – TypeScript Notes for Professionals   53

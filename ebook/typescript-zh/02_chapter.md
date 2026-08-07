## 第 2 章：为什么要以及何时使用 TypeScript

如果你总体上认同类型系统的论点，那么你会对 TypeScript 感到满意。它为 JavaScript 生态系统带来了类型系统的许多优点（安全性、可读性、改进的工具支持）。同时，它也有一些类型系统的缺点（增加复杂度和不完整性）。

### 2.1 安全性

TypeScript 通过静态分析及早捕获类型错误：

```typescript
function double(x: number): number {
  return 2 * x;
}
double('2');
//   ~~~ Argument of type '"2"' is not assignable to parameter of type 'number'.
```

### 2.2 可读性

TypeScript 使编辑器能够提供上下文文档：

你再也不会忘记 `String.prototype.slice` 接收的是 `(start, stop)` 还是 `(start, length)` 了！

### 2.3 工具支持

TypeScript 允许编辑器执行了解语言规则的自动化重构。

例如，Visual Studio Code 能够重命名内部 `foo` 的引用，而不会改变外部 `foo`。使用简单的查找/替换很难做到这一点。

---

GoalKicker.com – TypeScript Notes for Professionals 9

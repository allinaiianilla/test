第 11 章：严格空值检查

第 11.1 节：严格空值检查实践

默认情况下，TypeScript 中所有类型都允许 `null`：

```typescript
function getId(x: Element) {
  return x.id;
}
getId(null);   // TypeScript 不会报错，但这是一个运行时错误。
```

TypeScript 2.0 增加了对严格空值检查的支持。如果你在运行 `tsc` 时设置 `--strictNullChecks`（或在 `tsconfig.json` 中设置此标志），那么类型将不再允许 `null`：

```typescript
function getId(x: Element) {
  return x.id;
}
getId(null);   // 错误：类型"null"的参数不能赋给类型"Element"的参数。
```

你必须显式地允许 `null` 值：

```typescript
function getId(x: Element| null ) {
  return   x.id;   // 错误 TS2531：对象可能为 "null"。
}
getId(null);
```

使用适当的守卫后，代码类型检查通过且能正确运行：

```typescript
function getId(x: Element| null ) {
  if (x) {
    return x.id;   // 在此分支中，x 的类型为 Element
  } else {
    return null;   // 在此分支中，x 的类型为 null。
  }
}
getId(null);
```

第 11.2 节：非空断言

非空断言操作符 `!` 允许你在 TypeScript 编译器无法自动推断时，断言一个表达式既不是 `null` 也不是 `undefined`：

```typescript
type ListNode = { data: number; next?: ListNode; };

function addNext(node: ListNode) {
  if (node.next === undefined) {
    node.next = {data: 0};
  }
}

function setNextValue(node: ListNode, value: number) {
  addNext(node);
  // 尽管我们知道 `node.next` 已定义，因为我们刚调用了 `addNext`，
  // TypeScript 无法在下面这行代码中推断出这一点：
  // node.next.data = value;

  // 因此，我们可以使用非空断言操作符 !，
  // 来断言 node.next 不是 undefined 并消除编译器警告
  node.next!.data = value;
}
```

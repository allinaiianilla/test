## 第 4 章：数组

### 4.1 在数组中查找对象

使用 `find()`

```typescript
const inventory = [
  {name: 'apples', quantity: 2},
  {name: 'bananas', quantity: 0},
  {name: 'cherries', quantity: 5}
];

function findCherries(fruit) {
  return fruit.name === 'cherries';
}

inventory.find(findCherries); // { name: 'cherries', quantity: 5 }
/* OR */
inventory.find(e => e.name === 'apples'); // { name: 'apples', quantity: 2 }
```

---

GoalKicker.com – TypeScript Notes for Professionals 18

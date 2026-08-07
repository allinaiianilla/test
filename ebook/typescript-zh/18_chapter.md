第 18 章：混入

| 参数 | 描述 |
|------|------|
| derivedCtor | 要用作组合类的类 |
| baseCtors | 要添加到组合类的类的数组 |

第 18.1 节：混入示例

要创建混入，只需声明可以用作"行为"的轻量级类：

```typescript
class Flies {
    fly() {
        alert('Is it a bird? Is it a plane?');
    }
}

class Climbs {
    climb() {
        alert('My spider-sense is tingling.');
    }
}

class Bulletproof {
    deflect() {
        alert('My wings are a shield of steel.');
    }
}
```

然后你可以将这些行为应用到组合类中：

```typescript
class BeetleGuy implements Climbs, Bulletproof {
    climb: () => void;
    deflect: () => void;
}
applyMixins (BeetleGuy, [Climbs, Bulletproof]);
```

`applyMixins` 函数用于完成组合工作。

```typescript
function applyMixins(derivedCtor: any, baseCtors: any[]) {
    baseCtors.forEach(baseCtor => {
        Object.getOwnPropertyNames(baseCtor.prototype).forEach(name => {
            if (name !== 'constructor') {
                derivedCtor.prototype[name] = baseCtor.prototype[name];
            }
        });
    });
}
```

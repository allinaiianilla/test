## 第 8 章：类装饰器

| 参数 | 描述 |
|------|------|
| `target` | 被装饰的类 |

### 8.1 使用类装饰器生成元数据

这次我们将声明一个类装饰器，当应用到类上时将为其添加一些元数据：

```typescript
function addMetadata(target: any) {
  // Add some metadata
  target.__customMetadata = {
    someKey: "someValue"
  };

  // Return target
  return target;
}
```

然后我们可以应用该类装饰器：

```typescript
@addMetadata
class Person {
  private _name: string;
  public constructor(name: string) {
    this._name = name;
  }
  public greet() {
    return this._name;
  }
}

function getMetadataFromClass(target: any) {
  return target.__customMetadata;
}

console.log(getMetadataFromClass(Person));
```

装饰器在类声明时应用，而不是在我们创建类实例时应用。这意味着元数据在类的所有实例之间是共享的：

```typescript
function getMetadataFromInstance(target: any) {
  return target.constructor.__customMetadata;
}

let person1 = new Person("John");
let person2 = new Person("Lisa");

console.log(getMetadataFromInstance(person1));
console.log(getMetadataFromInstance(person2));
```

### 8.2 向类装饰器传递参数

我们可以用另一个函数包装类装饰器以允许自定义：

```typescript
function addMetadata(metadata: any) {
  return function log(target: any) {
    // Add metadata
    target.__customMetadata = metadata;

    // Return target
    return target;
  }
}
```

`addMetadata` 接受一些用作配置的参数，然后返回一个匿名函数，该函数才是实际的装饰器。在装饰器中，我们可以访问这些参数，因为存在闭包。然后我们可以通过传递一些配置值来调用装饰器：

```typescript
@addMetadata({ guid: "417c6ec7-ec05-4954-a3c6-73a0d7f9f5bf" })
class Person {
  private _name: string;
  public constructor(name: string) {
    this._name = name;
  }
  public greet() {
    return this._name;
  }
}
```

我们可以使用以下函数访问生成的元数据：

```typescript
function getMetadataFromClass(target: any) {
  return target.__customMetadata;
}

console.log(getMetadataFromInstance(Person));
```

如果一切正常，控制台应该显示：

```
{ guid: "417c6ec7-ec05-4954-a3c6-73a0d7f9f5bf" }
```

### 8.3 基本类装饰器

类装饰器只是一个函数，它接受类作为其唯一参数，并在对其进行某些操作后返回该类：

```typescript
function log<T>(target: T) {
  // Do something with target
  console.log(target);

  // Return target
  return target;
}
```

然后我们可以将类装饰器应用到一个类上：

```typescript
@log
class Person {
  private _name: string;
  public constructor(name: string) {
    this._name = name;
  }
  public greet() {
    return this._name;
  }
}
```

---

GoalKicker.com – TypeScript Notes for Professionals 32

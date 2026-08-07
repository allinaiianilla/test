## 第 5 章：枚举

### 5.1 具有显式值的枚举

默认情况下，所有枚举值都解析为数字。假设你有这样的代码：

```typescript
enum MimeType {
  JPEG,
  PNG,
  PDF
}
```

例如，`MimeType.PDF` 的实际值将是 `2`。但有时需要让枚举解析为不同的类型。例如，你从后端/前端/另一个系统接收到一个明确是字符串的值。这可能很麻烦，但幸运的是有这种方法：

```typescript
enum MimeType {
  JPEG = <any>'image/jpeg',
  PNG  = <any>'image/png',
  PDF  = <any>'application/pdf'
}
```

这将 `MimeType.PDF` 解析为 `application/pdf`。

自从 TypeScript 2.4 起，可以声明字符串枚举：

```typescript
enum MimeType {
  JPEG = 'image/jpeg',
  PNG  = 'image/png',
  PDF  = 'application/pdf',
}
```

你也可以使用相同的方法显式提供数字值：

```typescript
enum MyType {
  Value = 3,
  ValueEx = 30,
  ValueEx2 = 300
}
```

更复杂的类型也可以工作，因为非常量枚举在运行时是真实的对象，例如：

```typescript
enum FancyType {
  OneArr = <any>[1],
  TwoArr = <any>[2, 2],
  ThreeArr = <any>[3, 3, 3]
}
```

编译结果：

```typescript
var FancyType;
(function (FancyType) {
  FancyType[FancyType["OneArr"] = [1]] = "OneArr";
  FancyType[FancyType["TwoArr"] = [2, 2]] = "TwoArr";
  FancyType[FancyType["ThreeArr"] = [3, 3, 3]] = "ThreeArr";
})(FancyType || (FancyType = {}));
```

### 5.2 如何获取所有枚举值

```typescript
enum SomeEnum { A, B }

let enumValues:Array<string>= [];

for(let value in SomeEnum) {
  if(typeof SomeEnum[value] === 'number') {
    enumValues.push(value);
  }
}

enumValues.forEach(v=> console.log(v))
//A
//B
```

### 5.3 无需自定义枚举实现即可扩展枚举

```typescript
enum SourceEnum {
  value1 = <any>'value1',
  value2 = <any>'value2'
}

enum AdditionToSourceEnum {
  value3 = <any>'value3',
  value4 = <any>'value4'
}

// we need this type for TypeScript to resolve the types correctly
type TestEnumType = SourceEnum | AdditionToSourceEnum;
// and we need this value "instance" to use values
let TestEnum = Object.assign({}, SourceEnum, AdditionToSourceEnum);
// also works fine the TypeScript 2 feature
// let TestEnum = { ...SourceEnum, ...AdditionToSourceEnum };

function check(test: TestEnumType) {
  return test === TestEnum.value2;
}

console.log(TestEnum.value1);
console.log(TestEnum.value2 === <any>'value2');
console.log(check(TestEnum.value2));
console.log(check(TestEnum.value3));
```

### 5.4 自定义枚举实现：枚举的扩展

有时需要自己实现枚举。例如，没有明确的方法来扩展其他枚举。自定义实现允许这样做：

```typescript
class Enum {
  constructor(protected value: string) {}

  public toString() {
    return String(this.value);
  }

  public is(value: Enum | string) {
    return this.value = value.toString();
  }
}

class SourceEnum extends Enum {
  public static value1 = new SourceEnum('value1');
  public static value2 = new SourceEnum('value2');
}

class TestEnum extends SourceEnum {
  public static value3 = new TestEnum('value3');
  public static value4 = new TestEnum('value4');
}

function check(test: TestEnum) {
  return test === TestEnum.value2;
}

let value1 = TestEnum.value1;

console.log(value1 + 'hello');
console.log(value1.toString() === 'value1');
console.log(value1.is('value1'));
console.log(!TestEnum.value3.is(TestEnum.value3));
console.log(check(TestEnum.value2));
// this works but perhaps your TSLint would complain
// attention! does not work with ===
// use .is() instead
console.log(TestEnum.value1 == <any>'value1');
```

---

GoalKicker.com – TypeScript Notes for Professionals 21

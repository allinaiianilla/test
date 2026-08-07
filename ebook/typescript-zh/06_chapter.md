## 第 6 章：函数

### 6.1 可选参数和默认参数

**可选参数**

在 TypeScript 中，每个参数默认为函数所必需。你可以在参数名末尾加上 `?` 将其设置为可选。例如，此函数的 `lastName` 参数是可选的：

```typescript
function buildName(firstName: string, lastName?: string) {
  // ...
}
```

可选参数必须放在所有必需参数之后：

```typescript
function buildName(firstName?: string, lastName: string) // Invalid
```

**默认参数**

如果用户传入 `undefined` 或不指定参数值，则会分配默认值。这被称为默认初始化参数。例如，"Smith" 是 `lastName` 参数的默认值。

```typescript
function buildName(firstName: string, lastName = "Smith") {
  // ...
}

buildName('foo', 'bar');      // firstName == 'foo', lastName == 'bar'
buildName('foo');             // firstName == 'foo', lastName == 'Smith'
buildName('foo', undefined);  // firstName == 'foo', lastName == 'Smith'
```

### 6.2 函数作为参数

假设我们想接收一个函数作为参数，可以这样做：

```typescript
function foo(otherFunc: Function): void { ... }
```

如果我们想接收一个构造函数作为参数：

```typescript
function foo(constructorFunc: { new () }) {
  new constructorFunc();
}

function foo(constructorWithParamsFunc: { new (num: number) }) {
  new constructorWithParamsFunc(1);
}
```

或者为了使阅读更容易，我们可以定义一个接口来描述构造函数：

```typescript
interface IConstructor {
  new ();
}

function foo(contructorFunc: IConstructor) {
  new constructorFunc();
}
```

或者带参数：

```typescript
interface INumberConstructor {
  new (num: number);
}

function foo(contructorFunc: INumberConstructor) {
  new contructorFunc(1);
}
```

甚至使用泛型：

```typescript
interface ITConstructor<T, U> {
  new (item: T): U;
}

function foo<T, U>(contructorFunc: ITConstructor<T, U>, item: T): U {
  return new contructorFunc(item);
}
```

如果我们想接收一个普通函数而不是构造函数，几乎是一样的：

```typescript
function foo(func: { (): void }) { func(); }

function foo(constructorWithParamsFunc: { (num: number): void }) {
  new constructorWithParamsFunc(1);
}
```

或者为了使阅读更容易，我们可以定义一个接口来描述函数：

```typescript
interface IFunction { (): void; }
function foo(func: IFunction) { func(); }
```

或者带参数：

```typescript
interface INumberFunction { (num: number): string; }
function foo(func: INumberFunction) { func(1); }
```

甚至使用泛型：

```typescript
interface ITFunc<T, U> { (item: T): U; }
function foo<T, U>(contructorFunc: ITFunc<T, U>, item: T): U {
  return func(item);
}
```

### 6.3 使用联合类型的函数

TypeScript 函数可以使用联合类型接收多个预定义类型的参数。

```typescript
function whatTime(hour:number|string, minute:number|string):string{
  return hour+':'+minute;
}

whatTime(1,30)      //'1:30'
whatTime('1',30)    //'1:30'
whatTime(1,'30')    //'1:30'
whatTime('1','30')  //'1:30'
```

TypeScript 将这些参数视为其他类型的联合单一类型，因此你的函数必须能够处理联合中的任何类型的参数。

```typescript
function addTen(start:number|string):number{
  if(typeof number === 'string'){
    return parseInt(number)+10;
  } else {
    else return number+10;
  }
}
```

### 6.4 函数的类型

**命名函数**

```typescript
function multiply(a, b) {
  return a * b;
}
```

**匿名函数**

```typescript
let multiply = function(a, b) { return a * b; };
```

**Lambda / 箭头函数**

```typescript
let multiply = (a, b) => { return a * b; };
```

---

GoalKicker.com – TypeScript Notes for Professionals 24

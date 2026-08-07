## 第 7 章：类

TypeScript 与 ECMAScript 6 一样，支持使用类进行面向对象编程。这与较旧的 JavaScript 版本不同，后者仅支持基于原型的继承链。TypeScript 中的类支持类似于 Java 和 C# 等语言，即类可以从其他类继承，而对象则作为类实例进行实例化。与这些语言类似，TypeScript 类也可以实现接口或使用泛型。

### 7.1 抽象类

```typescript
abstract class Machine {
  constructor(public manufacturer: string) { }

  // An abstract class can define methods of its own, or...
  summary(): string {
    return `${this.manufacturer} makes this machine.`;
  }

  // Require inheriting classes to implement methods
  abstract moreInfo(): string;
}

class Car extends Machine {
  constructor(manufacturer: string, public position: number, protected speed: number) {
    super(manufacturer);
  }

  move() {
    this.position += this.speed;
  }

  moreInfo() {
    return `This is a car located at ${this.position} and going ${this.speed}mph!`;
  }
}

let myCar = new Car("Konda", 10, 70);
myCar.move(); // position is now 80
console.log(myCar.summary()); // prints "Konda makes this machine."
console.log(myCar.moreInfo()); // prints "This is a car located at 80 and going 70mph!"
```

抽象类是其他类可以扩展的基类。它们不能自身实例化（即你不能 `new Machine("Konda")`）。TypeScript 中抽象类的两个关键特征是：

1. 它们可以实现自己的方法。
2. 它们可以定义继承类必须实现的方法。

因此，抽象类在概念上可以被视为接口和类的组合。

### 7.2 简单类

```typescript
class Car {
  public position: number = 0;
  private speed: number = 42;

  move() {
    this.position += this.speed;
  }
}
```

在此示例中，我们声明了一个简单的 `Car` 类。该类有三个成员：一个私有属性 `speed`、一个公共属性 `position` 和一个公共方法 `move`。注意，每个成员默认是公共的。这就是为什么即使我们没有使用 `public` 关键字，`move()` 也是公共的。

```typescript
var car = new Car();     // create an instance of Car
car.move();              // call a method
console.log(car.position); // access a public property
```

### 7.3 基本继承

```typescript
class Car {
  public position: number = 0;
  protected speed: number = 42;

  move() {
    this.position += this.speed;
  }
}

class SelfDrivingCar extends Car {
  move() {
    // start moving around :-)
    super.move();
    super.move();
  }
}
```

此示例展示了如何使用 `extends` 关键字创建 `Car` 类的非常简单的子类。`SelfDrivingCar` 类重写了 `move()` 方法，并使用 `super` 调用基类实现。

### 7.4 构造函数

在此示例中，我们使用 `constructor` 在基类中声明一个公共属性 `position` 和一个受保护属性 `speed`。这些属性被称为参数属性。它们让我们可以在一个地方同时声明构造函数参数和成员。TypeScript 最棒的特性之一，就是自动将构造函数参数赋值给相关属性。

```typescript
class Car {
  public position: number;
  protected speed: number;

  constructor(position: number, speed: number) {
    this.position = position;
    this.speed = speed;
  }

  move() {
    this.position += this.speed;
  }
}
```

所有这些代码可以简化为一个单一的构造函数：

```typescript
class Car {
  constructor(public position: number, protected speed: number) {}

  move() {
    this.position += this.speed;
  }
}
```

这两种写法从 TypeScript（设计时和编译时）编译到 JavaScript 的结果相同，但编写的代码明显更少：

```javascript
var Car = (function () {
  function Car(position, speed) {
    this.position = position;
    this.speed = speed;
  }
  Car.prototype.move = function () {
    this.position += this.speed;
  };
  return Car;
}());
```

派生类的构造函数必须使用 `super()` 调用基类构造函数。

```typescript
class SelfDrivingCar extends Car {
  constructor(startAutoPilot: boolean) {
    super(0, 42);
    if (startAutoPilot) {
      this.move();
    }
  }
}

let car = new SelfDrivingCar(true);
console.log(car.position); // access the public property position
```

### 7.5 访问器

在此示例中，我们修改了"简单类"示例，以允许访问 `speed` 属性。TypeScript 访问器允许我们在 getter 或 setter 中添加额外的代码。

```typescript
class Car {
  public position: number = 0;
  private _speed: number = 42;
  private _MAX_SPEED = 100

  move() {
    this.position += this._speed;
  }

  get speed(): number {
    return this._speed;
  }

  set speed(value: number) {
    this._speed = Math.min(value, this._MAX_SPEED);
  }
}

let car = new Car();
car.speed = 120;
console.log(car.speed); // 100
```

### 7.6 编译转换

给定一个 `SomeClass` 类，让我们看看 TypeScript 如何编译转换为 JavaScript。

**TypeScript 源码**

```typescript
class SomeClass {
  public static SomeStaticValue: string = "hello";
  public someMemberValue: number = 15;
  private somePrivateValue: boolean = false;

  constructor () {
    SomeClass.SomeStaticValue = SomeClass.getGoodbye();
    this.someMemberValue = this.getFortyTwo();
    this.somePrivateValue = this.getTrue();
  }

  public static getGoodbye(): string {
    return "goodbye!";
  }

  public getFortyTwo(): number {
    return 42;
  }

  private getTrue(): boolean {
    return true;
  }
}
```

**JavaScript 源码**

使用 TypeScript v2.2.2 编译转换后，输出如下：

```javascript
var SomeClass = (function () {
  function SomeClass() {
    this.someMemberValue = 15;
    this.somePrivateValue = false;
    SomeClass.SomeStaticValue = SomeClass.getGoodbye();
    this.someMemberValue = this.getFortyTwo();
    this.somePrivateValue = this.getTrue();
  }
  SomeClass.getGoodbye = function () {
    return "goodbye!";
  };
  SomeClass.prototype.getFortyTwo = function () {
    return 42;
  };
  SomeClass.prototype.getTrue = function () {
    return true;
  };
  return SomeClass;
}());
SomeClass.SomeStaticValue = "hello";
```

**观察结果**

- 类的 prototype 修改被包裹在 IIFE 中。
- 成员变量在主类函数内部定义。
- 静态属性直接添加到类对象上，而实例属性则添加到 prototype 上。

### 7.7 将函数猴子补丁到现有类中

有时能够用新函数扩展类是很有用的。例如，假设一个字符串应该被转换为驼峰命名格式。我们需要告诉 TypeScript，`String` 包含一个名为 `toCamelCase` 的函数，该函数返回 `string`。

```typescript
interface String {
  toCamelCase(): string;
}
```

现在我们可以将此函数补丁到 `String` 实现中。

```typescript
String.prototype.toCamelCase = function() : string {
  return this.replace(/[^a-z ]/ig, '')
    .replace(/(?:^\w|[A-Z]|\b\w|\s+)/g, (match: any, index: number) => {
      return +match === 0 ? "" : match[index === 0 ? 'toLowerCase' : 'toUpperCase']();
    });
}
```

如果加载了此 `String` 扩展，可以这样使用：

```typescript
"This is an example".toCamelCase(); // => "thisIsAnExample"
```

---

GoalKicker.com – TypeScript Notes for Professionals 29

## 第 9 章：接口

接口指定了实现该接口的任何类都应该具备的字段和函数列表。反过来，类除非拥有接口上指定的每个字段和函数，否则无法实现该接口。使用接口的主要好处是，它允许以多态方式使用不同类型的对象。这是因为任何实现该接口的类至少都拥有这些字段和函数。

### 9.1 扩展接口

假设我们有一个接口：

```typescript
interface IPerson {
  name: string;
  age: number;
  breath(): void;
}
```

我们想创建一个更具体的接口，该接口具有 person 的相同属性，我们可以使用 `extends` 关键字：

```typescript
interface IManager extends IPerson {
  managerId: number;
  managePeople(people: IPerson[]): void;
}
```

此外，还可以扩展多个接口。

### 9.2 类接口

在接口中声明公共变量和方法类型，以定义其他 TypeScript 代码如何与它交互。

```typescript
interface ISampleClassInterface {
  sampleVariable: string;
  sampleMethod(): void;
  optionalVariable?: string;
}
```

这里我们创建一个实现了该接口的类。

```typescript
class SampleClass implements ISampleClassInterface {
  public sampleVariable: string;
  private answerToLifeTheUniverseAndEverything: number;

  constructor() {
    this.sampleVariable = 'string value';
    this.answerToLifeTheUniverseAndEverything = 42;
  }

  public sampleMethod(): void {
    // do nothing
  }

  private answer(q: any): number {
    return this.answerToLifeTheUniverseAndEverything;
  }
}
```

该示例展示了如何创建接口 `ISampleClassInterface` 和实现该接口的类 `SampleClass`。

### 9.3 使用接口实现多态

使用接口的主要原因是实现多态，并提供给开发者通过实现接口的方法在未来以自己的方式实现。假设我们有一个接口和三个类：

```typescript
interface Connector {
  doConnect(): boolean;
}
```

这是 connector 接口。现在我们将为 Wifi 通信实现它。

```typescript
export class WifiConnector implements Connector {
  public doConnect(): boolean {
    console.log("Connecting via wifi");
    console.log("Get password");
    console.log("Lease an IP for 24 hours");
    console.log("Connected");
    return true
  }
}
```

这里我们开发了名为 `WifiConnector` 的具体类，它有自己的实现。它现在是类型 `Connector`。现在我们正在创建包含 `Connector` 组件的 `System` 类。这称为依赖注入。

```typescript
export class System {
  constructor(private connector: Connector) { //inject Connector type
    connector.doConnect()
  }
}
```

`constructor(private connector: Connector)` 这一行非常重要。`Connector` 是一个接口，必须具有 `doConnect()`。由于 `Connector` 是一个接口，这个 `System` 类具有更大的灵活性。我们可以传递任何实现了 `Connector` 接口的类型。未来的开发者会获得更大的灵活性。例如，现在开发者想要添加蓝牙连接模块：

```typescript
export class BluetoothConnector implements Connector {
  public doConnect(): boolean {
    console.log("Connecting via Bluetooth");
    console.log("Pair with PIN");
    console.log("Connected");
    return true
  }
}
```

可以看到 Wifi 和 Bluetooth 有各自的实现方式。它们有自己不同的连接方式。然而，由于两者都实现了 `Connector` 类型，它们现在都是 `Connector` 类型。因此我们可以将其中任何一个作为构造函数参数传递给 `System` 类。这称为多态。`System` 类现在不知道它是 Bluetooth 还是 Wifi，我们甚至可以通过简单地实现 `Connector` 接口来添加另一个通信模块，如 Infrared、Bluetooth5 等。这称为鸭子类型。`Connector` 类型现在是动态的，因为 `doConnect()` 只是一个占位符，开发者可以按自己的方式去实现它。

如果在 `constructor(private connector: WifiConnector)` 中，`WifiConnector` 是一个具体类，会发生什么？那么 `System` 类将只与 `WifiConnector` 紧密耦合，而无法使用其他任何东西。这里接口通过多态解决了我们的问题。

### 9.4 泛型接口

和类一样，接口也可以接收多态参数（即泛型）。

**在接口上声明泛型参数**

```typescript
interface IStatus<U> {
  code: U;
}

interface IEvents<T> {
  list: T[];
  emit(event: T): void;
  getAll(): T[];
}
```

这里你可以看到我们的两个接口接受了一些泛型参数 `T` 和 `U`。

**实现泛型接口**

我们将创建一个简单的类来实现接口 `IEvents`。

```typescript
class State<T> implements IEvents<T> {
  list: T[];

  constructor() {
    this.list = [];
  }

  emit(event: T): void {
    this.list.push(event);
  }

  getAll(): T[] {
    return this.list;
  }
}
```

让我们创建 `State` 类的一些实例。在我们的示例中，`State` 类将通过使用 `IStatus<T>` 来处理泛型状态。通过这种方式，接口 `IEvent<T>` 也将处理 `IStatus<T>`。

```typescript
const s = new State<IStatus<number>>();

// The 'code' property is expected to be a number, so:
s.emit({ code: 200 }); // works
s.emit({ code: '500' }); // type error

s.getAll().forEach(event => console.log(event.code));
```

这里我们的 `State` 类被类型化为 `IStatus<number>`。

```typescript
const s2 = new State<IStatus<Code>>();

//We are able to emit code as the type Code
s2.emit({ code: { message: 'OK', status: 200 } });

s2.getAll().map(event => event.code).forEach(event => {
  console.log(event.message);
  console.log(event.status);
});
```

我们的 `State` 类被类型化为 `IStatus<Code>`。通过这种方式，我们可以向 emit 方法传递更复杂的类型。正如你所见，泛型接口对于静态类型代码来说是非常有用的工具。

### 9.5 向现有接口添加函数或属性

假设我们有一个 `JQuery` 类型定义的引用，我们想扩展它以包含来自我们包含的插件的额外函数，而该插件没有官方的类型定义。我们可以通过在一个独立的接口声明中使用相同的 `JQuery` 名称来声明插件添加的函数，轻松地扩展它：

```typescript
interface JQuery {
  pluginFunctionThatDoesNothing(): void;

  // create chainable function
  manipulateDOM(HTMLElement): JQuery;
}
```

编译器会将所有具有相同名称的声明合并为一个——有关更多详细信息，请参阅声明合并。

### 9.6 隐式实现与对象形状

TypeScript 支持接口，但编译器输出的是 JavaScript，而 JavaScript 不支持接口。因此，接口在编译步骤中实际上会丢失。这就是为什么接口的类型检查依赖于对象的形状——即对象是否支持接口上的字段和函数——而不是依赖于接口是否被实际实现。

```typescript
interface IKickable {
  kick(distance: number): void;
}

class Ball {
  kick(distance: number): void {
    console.log("Kicked", distance, "meters!");
  }
}

let kickable: IKickable = new Ball();
kickable.kick(40);
```

因此，即使 `Ball` 没有显式实现 `IKickable`，一个 `Ball` 实例也可以被赋值给（并作为）`IKickable` 来操作，即使指定了类型。

### 9.7 使用接口强制类型

TypeScript 的核心优势之一是它强制代码中传递的值的数据类型，以帮助防止错误。

假设你正在制作一个宠物约会应用程序。你有这个简单的函数来检查两只宠物是否彼此兼容……

```typescript
checkCompatible(petOne, petTwo) {
  if (petOne.species === petTwo.species &&
      Math.abs(petOne.age - petTwo.age) <= 5) {
    return true;
  }
}
```

这是完全功能性的代码，但对于其他人来说太容易——尤其是在这个应用程序上工作的其他人，没有编写这个函数的人——不知道他们应该传递具有 'species' 和 'age' 属性的对象。他们可能错误地尝试 `checkCompatible(petOne.species, petTwo.species)`，然后当函数尝试访问 petOne.species.species 或 petOne.species.age 时，只能自己去理解抛出的错误！

我们可以通过指定宠物参数上想要的属性来防止这种情况发生：

```typescript
checkCompatible(petOne: {species: string, age: number},
                petTwo: {species: string, age: number}) {
  //...
}
```

在这种情况下，TypeScript 将确保传递给函数的所有内容都具有 'species' 和 'age' 属性（如果它们有额外的属性也完全没问题），但即使只指定了两个属性，这仍然是一个笨拙的解决方案。有了接口，就有了更好的方法！

首先我们定义我们的接口：

```typescript
interface Pet {
  species: string;
  age: number;
  //We can add more properties if we choose.
}
```

现在我们只需将参数的类型指定为我们的新接口，像这样……

```typescript
checkCompatible(petOne: Pet, petTwo: Pet) {
  //...
}
```

……然后 TypeScript 将确保传递给函数的参数包含 Pet 接口中指定的属性！

---

GoalKicker.com – TypeScript Notes for Professionals 37

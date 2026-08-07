第 13 章：TypeScript 基础示例

第 13.1 节：使用 extends 和 super 关键字的基础类继承示例

一个通用的 Car 类包含一些汽车属性和一个描述方法：

```typescript
class Car{
    name:string;
    engineCapacity:string;
    constructor(name:string,engineCapacity:string){
        this.name = name;
        this.engineCapacity = engineCapacity;
    }
    describeCar(){
     console.log(`${this.name} car comes with ${this.engineCapacity} displacement`);
    }
}
new Car("maruti ciaz","1500cc").describeCar();
```

HondaCar 继承自已有的通用 Car 类并新增属性。

```typescript
class HondaCar extends Car{
    seatingCapacity:number;
    constructor(name:string,engineCapacity:string,seatingCapacity:number){
        super(name,engineCapacity);
        this.seatingCapacity=seatingCapacity;
    }
    describeHondaCar(){
        super.describeCar();
        console.log(`this cars comes with seating capacity of ${this.seatingCapacity}`);
    }
}
new HondaCar("honda jazz","1200cc",4).describeHondaCar();
```

第 13.2 节：静态类变量示例——统计方法被调用的次数

此处 `countInstance` 是一个静态类变量：

```typescript
class StaticTest{
    static countInstance : number= 0;
    constructor(){
        StaticTest.countInstance++;
    }
}
new StaticTest();
new StaticTest();
console.log(StaticTest.countInstance);
```

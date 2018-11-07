function isDateBoolean(obj: any): boolean {
    return typeof obj === 'object' && 'toISOString' in obj;
}

function test2(i:number) {
    console.log(isDateBoolean(k));
}
let k = 5;
test2(k);
function isDateBoolean(obj) {
    return typeof obj === 'object' && 'toISOString' in obj;
}
function test2(i) {
    console.log(isDateBoolean(i));
}
var k = 5;
test2(k);

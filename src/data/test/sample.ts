var x = foo();
if(x > 5){
    try{
        var y = x;
    }
    catch{
        let tt = 5;
        console.log('ysy')
    }
}
let k = 5;
test2(k);
function foo(){
    return k;
}
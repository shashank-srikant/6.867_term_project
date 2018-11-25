function foo(q) {
    let j = 4;
    return q + j * j;
}

var x = foo(4);
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

function test2(k){
	let mmm = 212;
	k = mmm + k;
	k = mmm;
	return k;
}


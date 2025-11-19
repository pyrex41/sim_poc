(function(scope){
'use strict';

function F(arity, fun, wrapper) {
  wrapper.a = arity;
  wrapper.f = fun;
  return wrapper;
}

function F2(fun) {
  return F(2, fun, function(a) { return function(b) { return fun(a,b); }; })
}
function F3(fun) {
  return F(3, fun, function(a) {
    return function(b) { return function(c) { return fun(a, b, c); }; };
  });
}
function F4(fun) {
  return F(4, fun, function(a) { return function(b) { return function(c) {
    return function(d) { return fun(a, b, c, d); }; }; };
  });
}
function F5(fun) {
  return F(5, fun, function(a) { return function(b) { return function(c) {
    return function(d) { return function(e) { return fun(a, b, c, d, e); }; }; }; };
  });
}
function F6(fun) {
  return F(6, fun, function(a) { return function(b) { return function(c) {
    return function(d) { return function(e) { return function(f) {
    return fun(a, b, c, d, e, f); }; }; }; }; };
  });
}
function F7(fun) {
  return F(7, fun, function(a) { return function(b) { return function(c) {
    return function(d) { return function(e) { return function(f) {
    return function(g) { return fun(a, b, c, d, e, f, g); }; }; }; }; }; };
  });
}
function F8(fun) {
  return F(8, fun, function(a) { return function(b) { return function(c) {
    return function(d) { return function(e) { return function(f) {
    return function(g) { return function(h) {
    return fun(a, b, c, d, e, f, g, h); }; }; }; }; }; }; };
  });
}
function F9(fun) {
  return F(9, fun, function(a) { return function(b) { return function(c) {
    return function(d) { return function(e) { return function(f) {
    return function(g) { return function(h) { return function(i) {
    return fun(a, b, c, d, e, f, g, h, i); }; }; }; }; }; }; }; };
  });
}

function A2(fun, a, b) {
  return fun.a === 2 ? fun.f(a, b) : fun(a)(b);
}
function A3(fun, a, b, c) {
  return fun.a === 3 ? fun.f(a, b, c) : fun(a)(b)(c);
}
function A4(fun, a, b, c, d) {
  return fun.a === 4 ? fun.f(a, b, c, d) : fun(a)(b)(c)(d);
}
function A5(fun, a, b, c, d, e) {
  return fun.a === 5 ? fun.f(a, b, c, d, e) : fun(a)(b)(c)(d)(e);
}
function A6(fun, a, b, c, d, e, f) {
  return fun.a === 6 ? fun.f(a, b, c, d, e, f) : fun(a)(b)(c)(d)(e)(f);
}
function A7(fun, a, b, c, d, e, f, g) {
  return fun.a === 7 ? fun.f(a, b, c, d, e, f, g) : fun(a)(b)(c)(d)(e)(f)(g);
}
function A8(fun, a, b, c, d, e, f, g, h) {
  return fun.a === 8 ? fun.f(a, b, c, d, e, f, g, h) : fun(a)(b)(c)(d)(e)(f)(g)(h);
}
function A9(fun, a, b, c, d, e, f, g, h, i) {
  return fun.a === 9 ? fun.f(a, b, c, d, e, f, g, h, i) : fun(a)(b)(c)(d)(e)(f)(g)(h)(i);
}

console.warn('Compiled in DEV mode. Follow the advice at https://elm-lang.org/0.19.1/optimize for better performance and smaller assets.');


// EQUALITY

function _Utils_eq(x, y)
{
	for (
		var pair, stack = [], isEqual = _Utils_eqHelp(x, y, 0, stack);
		isEqual && (pair = stack.pop());
		isEqual = _Utils_eqHelp(pair.a, pair.b, 0, stack)
		)
	{}

	return isEqual;
}

function _Utils_eqHelp(x, y, depth, stack)
{
	if (x === y)
	{
		return true;
	}

	if (typeof x !== 'object' || x === null || y === null)
	{
		typeof x === 'function' && _Debug_crash(5);
		return false;
	}

	if (depth > 100)
	{
		stack.push(_Utils_Tuple2(x,y));
		return true;
	}

	/**/
	if (x.$ === 'Set_elm_builtin')
	{
		x = $elm$core$Set$toList(x);
		y = $elm$core$Set$toList(y);
	}
	if (x.$ === 'RBNode_elm_builtin' || x.$ === 'RBEmpty_elm_builtin')
	{
		x = $elm$core$Dict$toList(x);
		y = $elm$core$Dict$toList(y);
	}
	//*/

	/**_UNUSED/
	if (x.$ < 0)
	{
		x = $elm$core$Dict$toList(x);
		y = $elm$core$Dict$toList(y);
	}
	//*/

	for (var key in x)
	{
		if (!_Utils_eqHelp(x[key], y[key], depth + 1, stack))
		{
			return false;
		}
	}
	return true;
}

var _Utils_equal = F2(_Utils_eq);
var _Utils_notEqual = F2(function(a, b) { return !_Utils_eq(a,b); });



// COMPARISONS

// Code in Generate/JavaScript.hs, Basics.js, and List.js depends on
// the particular integer values assigned to LT, EQ, and GT.

function _Utils_cmp(x, y, ord)
{
	if (typeof x !== 'object')
	{
		return x === y ? /*EQ*/ 0 : x < y ? /*LT*/ -1 : /*GT*/ 1;
	}

	/**/
	if (x instanceof String)
	{
		var a = x.valueOf();
		var b = y.valueOf();
		return a === b ? 0 : a < b ? -1 : 1;
	}
	//*/

	/**_UNUSED/
	if (typeof x.$ === 'undefined')
	//*/
	/**/
	if (x.$[0] === '#')
	//*/
	{
		return (ord = _Utils_cmp(x.a, y.a))
			? ord
			: (ord = _Utils_cmp(x.b, y.b))
				? ord
				: _Utils_cmp(x.c, y.c);
	}

	// traverse conses until end of a list or a mismatch
	for (; x.b && y.b && !(ord = _Utils_cmp(x.a, y.a)); x = x.b, y = y.b) {} // WHILE_CONSES
	return ord || (x.b ? /*GT*/ 1 : y.b ? /*LT*/ -1 : /*EQ*/ 0);
}

var _Utils_lt = F2(function(a, b) { return _Utils_cmp(a, b) < 0; });
var _Utils_le = F2(function(a, b) { return _Utils_cmp(a, b) < 1; });
var _Utils_gt = F2(function(a, b) { return _Utils_cmp(a, b) > 0; });
var _Utils_ge = F2(function(a, b) { return _Utils_cmp(a, b) >= 0; });

var _Utils_compare = F2(function(x, y)
{
	var n = _Utils_cmp(x, y);
	return n < 0 ? $elm$core$Basics$LT : n ? $elm$core$Basics$GT : $elm$core$Basics$EQ;
});


// COMMON VALUES

var _Utils_Tuple0_UNUSED = 0;
var _Utils_Tuple0 = { $: '#0' };

function _Utils_Tuple2_UNUSED(a, b) { return { a: a, b: b }; }
function _Utils_Tuple2(a, b) { return { $: '#2', a: a, b: b }; }

function _Utils_Tuple3_UNUSED(a, b, c) { return { a: a, b: b, c: c }; }
function _Utils_Tuple3(a, b, c) { return { $: '#3', a: a, b: b, c: c }; }

function _Utils_chr_UNUSED(c) { return c; }
function _Utils_chr(c) { return new String(c); }


// RECORDS

function _Utils_update(oldRecord, updatedFields)
{
	var newRecord = {};

	for (var key in oldRecord)
	{
		newRecord[key] = oldRecord[key];
	}

	for (var key in updatedFields)
	{
		newRecord[key] = updatedFields[key];
	}

	return newRecord;
}


// APPEND

var _Utils_append = F2(_Utils_ap);

function _Utils_ap(xs, ys)
{
	// append Strings
	if (typeof xs === 'string')
	{
		return xs + ys;
	}

	// append Lists
	if (!xs.b)
	{
		return ys;
	}
	var root = _List_Cons(xs.a, ys);
	xs = xs.b
	for (var curr = root; xs.b; xs = xs.b) // WHILE_CONS
	{
		curr = curr.b = _List_Cons(xs.a, ys);
	}
	return root;
}



var _List_Nil_UNUSED = { $: 0 };
var _List_Nil = { $: '[]' };

function _List_Cons_UNUSED(hd, tl) { return { $: 1, a: hd, b: tl }; }
function _List_Cons(hd, tl) { return { $: '::', a: hd, b: tl }; }


var _List_cons = F2(_List_Cons);

function _List_fromArray(arr)
{
	var out = _List_Nil;
	for (var i = arr.length; i--; )
	{
		out = _List_Cons(arr[i], out);
	}
	return out;
}

function _List_toArray(xs)
{
	for (var out = []; xs.b; xs = xs.b) // WHILE_CONS
	{
		out.push(xs.a);
	}
	return out;
}

var _List_map2 = F3(function(f, xs, ys)
{
	for (var arr = []; xs.b && ys.b; xs = xs.b, ys = ys.b) // WHILE_CONSES
	{
		arr.push(A2(f, xs.a, ys.a));
	}
	return _List_fromArray(arr);
});

var _List_map3 = F4(function(f, xs, ys, zs)
{
	for (var arr = []; xs.b && ys.b && zs.b; xs = xs.b, ys = ys.b, zs = zs.b) // WHILE_CONSES
	{
		arr.push(A3(f, xs.a, ys.a, zs.a));
	}
	return _List_fromArray(arr);
});

var _List_map4 = F5(function(f, ws, xs, ys, zs)
{
	for (var arr = []; ws.b && xs.b && ys.b && zs.b; ws = ws.b, xs = xs.b, ys = ys.b, zs = zs.b) // WHILE_CONSES
	{
		arr.push(A4(f, ws.a, xs.a, ys.a, zs.a));
	}
	return _List_fromArray(arr);
});

var _List_map5 = F6(function(f, vs, ws, xs, ys, zs)
{
	for (var arr = []; vs.b && ws.b && xs.b && ys.b && zs.b; vs = vs.b, ws = ws.b, xs = xs.b, ys = ys.b, zs = zs.b) // WHILE_CONSES
	{
		arr.push(A5(f, vs.a, ws.a, xs.a, ys.a, zs.a));
	}
	return _List_fromArray(arr);
});

var _List_sortBy = F2(function(f, xs)
{
	return _List_fromArray(_List_toArray(xs).sort(function(a, b) {
		return _Utils_cmp(f(a), f(b));
	}));
});

var _List_sortWith = F2(function(f, xs)
{
	return _List_fromArray(_List_toArray(xs).sort(function(a, b) {
		var ord = A2(f, a, b);
		return ord === $elm$core$Basics$EQ ? 0 : ord === $elm$core$Basics$LT ? -1 : 1;
	}));
});



var _JsArray_empty = [];

function _JsArray_singleton(value)
{
    return [value];
}

function _JsArray_length(array)
{
    return array.length;
}

var _JsArray_initialize = F3(function(size, offset, func)
{
    var result = new Array(size);

    for (var i = 0; i < size; i++)
    {
        result[i] = func(offset + i);
    }

    return result;
});

var _JsArray_initializeFromList = F2(function (max, ls)
{
    var result = new Array(max);

    for (var i = 0; i < max && ls.b; i++)
    {
        result[i] = ls.a;
        ls = ls.b;
    }

    result.length = i;
    return _Utils_Tuple2(result, ls);
});

var _JsArray_unsafeGet = F2(function(index, array)
{
    return array[index];
});

var _JsArray_unsafeSet = F3(function(index, value, array)
{
    var length = array.length;
    var result = new Array(length);

    for (var i = 0; i < length; i++)
    {
        result[i] = array[i];
    }

    result[index] = value;
    return result;
});

var _JsArray_push = F2(function(value, array)
{
    var length = array.length;
    var result = new Array(length + 1);

    for (var i = 0; i < length; i++)
    {
        result[i] = array[i];
    }

    result[length] = value;
    return result;
});

var _JsArray_foldl = F3(function(func, acc, array)
{
    var length = array.length;

    for (var i = 0; i < length; i++)
    {
        acc = A2(func, array[i], acc);
    }

    return acc;
});

var _JsArray_foldr = F3(function(func, acc, array)
{
    for (var i = array.length - 1; i >= 0; i--)
    {
        acc = A2(func, array[i], acc);
    }

    return acc;
});

var _JsArray_map = F2(function(func, array)
{
    var length = array.length;
    var result = new Array(length);

    for (var i = 0; i < length; i++)
    {
        result[i] = func(array[i]);
    }

    return result;
});

var _JsArray_indexedMap = F3(function(func, offset, array)
{
    var length = array.length;
    var result = new Array(length);

    for (var i = 0; i < length; i++)
    {
        result[i] = A2(func, offset + i, array[i]);
    }

    return result;
});

var _JsArray_slice = F3(function(from, to, array)
{
    return array.slice(from, to);
});

var _JsArray_appendN = F3(function(n, dest, source)
{
    var destLen = dest.length;
    var itemsToCopy = n - destLen;

    if (itemsToCopy > source.length)
    {
        itemsToCopy = source.length;
    }

    var size = destLen + itemsToCopy;
    var result = new Array(size);

    for (var i = 0; i < destLen; i++)
    {
        result[i] = dest[i];
    }

    for (var i = 0; i < itemsToCopy; i++)
    {
        result[i + destLen] = source[i];
    }

    return result;
});



// LOG

var _Debug_log_UNUSED = F2(function(tag, value)
{
	return value;
});

var _Debug_log = F2(function(tag, value)
{
	console.log(tag + ': ' + _Debug_toString(value));
	return value;
});


// TODOS

function _Debug_todo(moduleName, region)
{
	return function(message) {
		_Debug_crash(8, moduleName, region, message);
	};
}

function _Debug_todoCase(moduleName, region, value)
{
	return function(message) {
		_Debug_crash(9, moduleName, region, value, message);
	};
}


// TO STRING

function _Debug_toString_UNUSED(value)
{
	return '<internals>';
}

function _Debug_toString(value)
{
	return _Debug_toAnsiString(false, value);
}

function _Debug_toAnsiString(ansi, value)
{
	if (typeof value === 'function')
	{
		return _Debug_internalColor(ansi, '<function>');
	}

	if (typeof value === 'boolean')
	{
		return _Debug_ctorColor(ansi, value ? 'True' : 'False');
	}

	if (typeof value === 'number')
	{
		return _Debug_numberColor(ansi, value + '');
	}

	if (value instanceof String)
	{
		return _Debug_charColor(ansi, "'" + _Debug_addSlashes(value, true) + "'");
	}

	if (typeof value === 'string')
	{
		return _Debug_stringColor(ansi, '"' + _Debug_addSlashes(value, false) + '"');
	}

	if (typeof value === 'object' && '$' in value)
	{
		var tag = value.$;

		if (typeof tag === 'number')
		{
			return _Debug_internalColor(ansi, '<internals>');
		}

		if (tag[0] === '#')
		{
			var output = [];
			for (var k in value)
			{
				if (k === '$') continue;
				output.push(_Debug_toAnsiString(ansi, value[k]));
			}
			return '(' + output.join(',') + ')';
		}

		if (tag === 'Set_elm_builtin')
		{
			return _Debug_ctorColor(ansi, 'Set')
				+ _Debug_fadeColor(ansi, '.fromList') + ' '
				+ _Debug_toAnsiString(ansi, $elm$core$Set$toList(value));
		}

		if (tag === 'RBNode_elm_builtin' || tag === 'RBEmpty_elm_builtin')
		{
			return _Debug_ctorColor(ansi, 'Dict')
				+ _Debug_fadeColor(ansi, '.fromList') + ' '
				+ _Debug_toAnsiString(ansi, $elm$core$Dict$toList(value));
		}

		if (tag === 'Array_elm_builtin')
		{
			return _Debug_ctorColor(ansi, 'Array')
				+ _Debug_fadeColor(ansi, '.fromList') + ' '
				+ _Debug_toAnsiString(ansi, $elm$core$Array$toList(value));
		}

		if (tag === '::' || tag === '[]')
		{
			var output = '[';

			value.b && (output += _Debug_toAnsiString(ansi, value.a), value = value.b)

			for (; value.b; value = value.b) // WHILE_CONS
			{
				output += ',' + _Debug_toAnsiString(ansi, value.a);
			}
			return output + ']';
		}

		var output = '';
		for (var i in value)
		{
			if (i === '$') continue;
			var str = _Debug_toAnsiString(ansi, value[i]);
			var c0 = str[0];
			var parenless = c0 === '{' || c0 === '(' || c0 === '[' || c0 === '<' || c0 === '"' || str.indexOf(' ') < 0;
			output += ' ' + (parenless ? str : '(' + str + ')');
		}
		return _Debug_ctorColor(ansi, tag) + output;
	}

	if (typeof DataView === 'function' && value instanceof DataView)
	{
		return _Debug_stringColor(ansi, '<' + value.byteLength + ' bytes>');
	}

	if (typeof File !== 'undefined' && value instanceof File)
	{
		return _Debug_internalColor(ansi, '<' + value.name + '>');
	}

	if (typeof value === 'object')
	{
		var output = [];
		for (var key in value)
		{
			var field = key[0] === '_' ? key.slice(1) : key;
			output.push(_Debug_fadeColor(ansi, field) + ' = ' + _Debug_toAnsiString(ansi, value[key]));
		}
		if (output.length === 0)
		{
			return '{}';
		}
		return '{ ' + output.join(', ') + ' }';
	}

	return _Debug_internalColor(ansi, '<internals>');
}

function _Debug_addSlashes(str, isChar)
{
	var s = str
		.replace(/\\/g, '\\\\')
		.replace(/\n/g, '\\n')
		.replace(/\t/g, '\\t')
		.replace(/\r/g, '\\r')
		.replace(/\v/g, '\\v')
		.replace(/\0/g, '\\0');

	if (isChar)
	{
		return s.replace(/\'/g, '\\\'');
	}
	else
	{
		return s.replace(/\"/g, '\\"');
	}
}

function _Debug_ctorColor(ansi, string)
{
	return ansi ? '\x1b[96m' + string + '\x1b[0m' : string;
}

function _Debug_numberColor(ansi, string)
{
	return ansi ? '\x1b[95m' + string + '\x1b[0m' : string;
}

function _Debug_stringColor(ansi, string)
{
	return ansi ? '\x1b[93m' + string + '\x1b[0m' : string;
}

function _Debug_charColor(ansi, string)
{
	return ansi ? '\x1b[92m' + string + '\x1b[0m' : string;
}

function _Debug_fadeColor(ansi, string)
{
	return ansi ? '\x1b[37m' + string + '\x1b[0m' : string;
}

function _Debug_internalColor(ansi, string)
{
	return ansi ? '\x1b[36m' + string + '\x1b[0m' : string;
}

function _Debug_toHexDigit(n)
{
	return String.fromCharCode(n < 10 ? 48 + n : 55 + n);
}


// CRASH


function _Debug_crash_UNUSED(identifier)
{
	throw new Error('https://github.com/elm/core/blob/1.0.0/hints/' + identifier + '.md');
}


function _Debug_crash(identifier, fact1, fact2, fact3, fact4)
{
	switch(identifier)
	{
		case 0:
			throw new Error('What node should I take over? In JavaScript I need something like:\n\n    Elm.Main.init({\n        node: document.getElementById("elm-node")\n    })\n\nYou need to do this with any Browser.sandbox or Browser.element program.');

		case 1:
			throw new Error('Browser.application programs cannot handle URLs like this:\n\n    ' + document.location.href + '\n\nWhat is the root? The root of your file system? Try looking at this program with `elm reactor` or some other server.');

		case 2:
			var jsonErrorString = fact1;
			throw new Error('Problem with the flags given to your Elm program on initialization.\n\n' + jsonErrorString);

		case 3:
			var portName = fact1;
			throw new Error('There can only be one port named `' + portName + '`, but your program has multiple.');

		case 4:
			var portName = fact1;
			var problem = fact2;
			throw new Error('Trying to send an unexpected type of value through port `' + portName + '`:\n' + problem);

		case 5:
			throw new Error('Trying to use `(==)` on functions.\nThere is no way to know if functions are "the same" in the Elm sense.\nRead more about this at https://package.elm-lang.org/packages/elm/core/latest/Basics#== which describes why it is this way and what the better version will look like.');

		case 6:
			var moduleName = fact1;
			throw new Error('Your page is loading multiple Elm scripts with a module named ' + moduleName + '. Maybe a duplicate script is getting loaded accidentally? If not, rename one of them so I know which is which!');

		case 8:
			var moduleName = fact1;
			var region = fact2;
			var message = fact3;
			throw new Error('TODO in module `' + moduleName + '` ' + _Debug_regionToString(region) + '\n\n' + message);

		case 9:
			var moduleName = fact1;
			var region = fact2;
			var value = fact3;
			var message = fact4;
			throw new Error(
				'TODO in module `' + moduleName + '` from the `case` expression '
				+ _Debug_regionToString(region) + '\n\nIt received the following value:\n\n    '
				+ _Debug_toString(value).replace('\n', '\n    ')
				+ '\n\nBut the branch that handles it says:\n\n    ' + message.replace('\n', '\n    ')
			);

		case 10:
			throw new Error('Bug in https://github.com/elm/virtual-dom/issues');

		case 11:
			throw new Error('Cannot perform mod 0. Division by zero error.');
	}
}

function _Debug_regionToString(region)
{
	if (region.start.line === region.end.line)
	{
		return 'on line ' + region.start.line;
	}
	return 'on lines ' + region.start.line + ' through ' + region.end.line;
}



// MATH

var _Basics_add = F2(function(a, b) { return a + b; });
var _Basics_sub = F2(function(a, b) { return a - b; });
var _Basics_mul = F2(function(a, b) { return a * b; });
var _Basics_fdiv = F2(function(a, b) { return a / b; });
var _Basics_idiv = F2(function(a, b) { return (a / b) | 0; });
var _Basics_pow = F2(Math.pow);

var _Basics_remainderBy = F2(function(b, a) { return a % b; });

// https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/divmodnote-letter.pdf
var _Basics_modBy = F2(function(modulus, x)
{
	var answer = x % modulus;
	return modulus === 0
		? _Debug_crash(11)
		:
	((answer > 0 && modulus < 0) || (answer < 0 && modulus > 0))
		? answer + modulus
		: answer;
});


// TRIGONOMETRY

var _Basics_pi = Math.PI;
var _Basics_e = Math.E;
var _Basics_cos = Math.cos;
var _Basics_sin = Math.sin;
var _Basics_tan = Math.tan;
var _Basics_acos = Math.acos;
var _Basics_asin = Math.asin;
var _Basics_atan = Math.atan;
var _Basics_atan2 = F2(Math.atan2);


// MORE MATH

function _Basics_toFloat(x) { return x; }
function _Basics_truncate(n) { return n | 0; }
function _Basics_isInfinite(n) { return n === Infinity || n === -Infinity; }

var _Basics_ceiling = Math.ceil;
var _Basics_floor = Math.floor;
var _Basics_round = Math.round;
var _Basics_sqrt = Math.sqrt;
var _Basics_log = Math.log;
var _Basics_isNaN = isNaN;


// BOOLEANS

function _Basics_not(bool) { return !bool; }
var _Basics_and = F2(function(a, b) { return a && b; });
var _Basics_or  = F2(function(a, b) { return a || b; });
var _Basics_xor = F2(function(a, b) { return a !== b; });



var _String_cons = F2(function(chr, str)
{
	return chr + str;
});

function _String_uncons(string)
{
	var word = string.charCodeAt(0);
	return !isNaN(word)
		? $elm$core$Maybe$Just(
			0xD800 <= word && word <= 0xDBFF
				? _Utils_Tuple2(_Utils_chr(string[0] + string[1]), string.slice(2))
				: _Utils_Tuple2(_Utils_chr(string[0]), string.slice(1))
		)
		: $elm$core$Maybe$Nothing;
}

var _String_append = F2(function(a, b)
{
	return a + b;
});

function _String_length(str)
{
	return str.length;
}

var _String_map = F2(function(func, string)
{
	var len = string.length;
	var array = new Array(len);
	var i = 0;
	while (i < len)
	{
		var word = string.charCodeAt(i);
		if (0xD800 <= word && word <= 0xDBFF)
		{
			array[i] = func(_Utils_chr(string[i] + string[i+1]));
			i += 2;
			continue;
		}
		array[i] = func(_Utils_chr(string[i]));
		i++;
	}
	return array.join('');
});

var _String_filter = F2(function(isGood, str)
{
	var arr = [];
	var len = str.length;
	var i = 0;
	while (i < len)
	{
		var char = str[i];
		var word = str.charCodeAt(i);
		i++;
		if (0xD800 <= word && word <= 0xDBFF)
		{
			char += str[i];
			i++;
		}

		if (isGood(_Utils_chr(char)))
		{
			arr.push(char);
		}
	}
	return arr.join('');
});

function _String_reverse(str)
{
	var len = str.length;
	var arr = new Array(len);
	var i = 0;
	while (i < len)
	{
		var word = str.charCodeAt(i);
		if (0xD800 <= word && word <= 0xDBFF)
		{
			arr[len - i] = str[i + 1];
			i++;
			arr[len - i] = str[i - 1];
			i++;
		}
		else
		{
			arr[len - i] = str[i];
			i++;
		}
	}
	return arr.join('');
}

var _String_foldl = F3(function(func, state, string)
{
	var len = string.length;
	var i = 0;
	while (i < len)
	{
		var char = string[i];
		var word = string.charCodeAt(i);
		i++;
		if (0xD800 <= word && word <= 0xDBFF)
		{
			char += string[i];
			i++;
		}
		state = A2(func, _Utils_chr(char), state);
	}
	return state;
});

var _String_foldr = F3(function(func, state, string)
{
	var i = string.length;
	while (i--)
	{
		var char = string[i];
		var word = string.charCodeAt(i);
		if (0xDC00 <= word && word <= 0xDFFF)
		{
			i--;
			char = string[i] + char;
		}
		state = A2(func, _Utils_chr(char), state);
	}
	return state;
});

var _String_split = F2(function(sep, str)
{
	return str.split(sep);
});

var _String_join = F2(function(sep, strs)
{
	return strs.join(sep);
});

var _String_slice = F3(function(start, end, str) {
	return str.slice(start, end);
});

function _String_trim(str)
{
	return str.trim();
}

function _String_trimLeft(str)
{
	return str.replace(/^\s+/, '');
}

function _String_trimRight(str)
{
	return str.replace(/\s+$/, '');
}

function _String_words(str)
{
	return _List_fromArray(str.trim().split(/\s+/g));
}

function _String_lines(str)
{
	return _List_fromArray(str.split(/\r\n|\r|\n/g));
}

function _String_toUpper(str)
{
	return str.toUpperCase();
}

function _String_toLower(str)
{
	return str.toLowerCase();
}

var _String_any = F2(function(isGood, string)
{
	var i = string.length;
	while (i--)
	{
		var char = string[i];
		var word = string.charCodeAt(i);
		if (0xDC00 <= word && word <= 0xDFFF)
		{
			i--;
			char = string[i] + char;
		}
		if (isGood(_Utils_chr(char)))
		{
			return true;
		}
	}
	return false;
});

var _String_all = F2(function(isGood, string)
{
	var i = string.length;
	while (i--)
	{
		var char = string[i];
		var word = string.charCodeAt(i);
		if (0xDC00 <= word && word <= 0xDFFF)
		{
			i--;
			char = string[i] + char;
		}
		if (!isGood(_Utils_chr(char)))
		{
			return false;
		}
	}
	return true;
});

var _String_contains = F2(function(sub, str)
{
	return str.indexOf(sub) > -1;
});

var _String_startsWith = F2(function(sub, str)
{
	return str.indexOf(sub) === 0;
});

var _String_endsWith = F2(function(sub, str)
{
	return str.length >= sub.length &&
		str.lastIndexOf(sub) === str.length - sub.length;
});

var _String_indexes = F2(function(sub, str)
{
	var subLen = sub.length;

	if (subLen < 1)
	{
		return _List_Nil;
	}

	var i = 0;
	var is = [];

	while ((i = str.indexOf(sub, i)) > -1)
	{
		is.push(i);
		i = i + subLen;
	}

	return _List_fromArray(is);
});


// TO STRING

function _String_fromNumber(number)
{
	return number + '';
}


// INT CONVERSIONS

function _String_toInt(str)
{
	var total = 0;
	var code0 = str.charCodeAt(0);
	var start = code0 == 0x2B /* + */ || code0 == 0x2D /* - */ ? 1 : 0;

	for (var i = start; i < str.length; ++i)
	{
		var code = str.charCodeAt(i);
		if (code < 0x30 || 0x39 < code)
		{
			return $elm$core$Maybe$Nothing;
		}
		total = 10 * total + code - 0x30;
	}

	return i == start
		? $elm$core$Maybe$Nothing
		: $elm$core$Maybe$Just(code0 == 0x2D ? -total : total);
}


// FLOAT CONVERSIONS

function _String_toFloat(s)
{
	// check if it is a hex, octal, or binary number
	if (s.length === 0 || /[\sxbo]/.test(s))
	{
		return $elm$core$Maybe$Nothing;
	}
	var n = +s;
	// faster isNaN check
	return n === n ? $elm$core$Maybe$Just(n) : $elm$core$Maybe$Nothing;
}

function _String_fromList(chars)
{
	return _List_toArray(chars).join('');
}




function _Char_toCode(char)
{
	var code = char.charCodeAt(0);
	if (0xD800 <= code && code <= 0xDBFF)
	{
		return (code - 0xD800) * 0x400 + char.charCodeAt(1) - 0xDC00 + 0x10000
	}
	return code;
}

function _Char_fromCode(code)
{
	return _Utils_chr(
		(code < 0 || 0x10FFFF < code)
			? '\uFFFD'
			:
		(code <= 0xFFFF)
			? String.fromCharCode(code)
			:
		(code -= 0x10000,
			String.fromCharCode(Math.floor(code / 0x400) + 0xD800, code % 0x400 + 0xDC00)
		)
	);
}

function _Char_toUpper(char)
{
	return _Utils_chr(char.toUpperCase());
}

function _Char_toLower(char)
{
	return _Utils_chr(char.toLowerCase());
}

function _Char_toLocaleUpper(char)
{
	return _Utils_chr(char.toLocaleUpperCase());
}

function _Char_toLocaleLower(char)
{
	return _Utils_chr(char.toLocaleLowerCase());
}



/**/
function _Json_errorToString(error)
{
	return $elm$json$Json$Decode$errorToString(error);
}
//*/


// CORE DECODERS

function _Json_succeed(msg)
{
	return {
		$: 0,
		a: msg
	};
}

function _Json_fail(msg)
{
	return {
		$: 1,
		a: msg
	};
}

function _Json_decodePrim(decoder)
{
	return { $: 2, b: decoder };
}

var _Json_decodeInt = _Json_decodePrim(function(value) {
	return (typeof value !== 'number')
		? _Json_expecting('an INT', value)
		:
	(-2147483647 < value && value < 2147483647 && (value | 0) === value)
		? $elm$core$Result$Ok(value)
		:
	(isFinite(value) && !(value % 1))
		? $elm$core$Result$Ok(value)
		: _Json_expecting('an INT', value);
});

var _Json_decodeBool = _Json_decodePrim(function(value) {
	return (typeof value === 'boolean')
		? $elm$core$Result$Ok(value)
		: _Json_expecting('a BOOL', value);
});

var _Json_decodeFloat = _Json_decodePrim(function(value) {
	return (typeof value === 'number')
		? $elm$core$Result$Ok(value)
		: _Json_expecting('a FLOAT', value);
});

var _Json_decodeValue = _Json_decodePrim(function(value) {
	return $elm$core$Result$Ok(_Json_wrap(value));
});

var _Json_decodeString = _Json_decodePrim(function(value) {
	return (typeof value === 'string')
		? $elm$core$Result$Ok(value)
		: (value instanceof String)
			? $elm$core$Result$Ok(value + '')
			: _Json_expecting('a STRING', value);
});

function _Json_decodeList(decoder) { return { $: 3, b: decoder }; }
function _Json_decodeArray(decoder) { return { $: 4, b: decoder }; }

function _Json_decodeNull(value) { return { $: 5, c: value }; }

var _Json_decodeField = F2(function(field, decoder)
{
	return {
		$: 6,
		d: field,
		b: decoder
	};
});

var _Json_decodeIndex = F2(function(index, decoder)
{
	return {
		$: 7,
		e: index,
		b: decoder
	};
});

function _Json_decodeKeyValuePairs(decoder)
{
	return {
		$: 8,
		b: decoder
	};
}

function _Json_mapMany(f, decoders)
{
	return {
		$: 9,
		f: f,
		g: decoders
	};
}

var _Json_andThen = F2(function(callback, decoder)
{
	return {
		$: 10,
		b: decoder,
		h: callback
	};
});

function _Json_oneOf(decoders)
{
	return {
		$: 11,
		g: decoders
	};
}


// DECODING OBJECTS

var _Json_map1 = F2(function(f, d1)
{
	return _Json_mapMany(f, [d1]);
});

var _Json_map2 = F3(function(f, d1, d2)
{
	return _Json_mapMany(f, [d1, d2]);
});

var _Json_map3 = F4(function(f, d1, d2, d3)
{
	return _Json_mapMany(f, [d1, d2, d3]);
});

var _Json_map4 = F5(function(f, d1, d2, d3, d4)
{
	return _Json_mapMany(f, [d1, d2, d3, d4]);
});

var _Json_map5 = F6(function(f, d1, d2, d3, d4, d5)
{
	return _Json_mapMany(f, [d1, d2, d3, d4, d5]);
});

var _Json_map6 = F7(function(f, d1, d2, d3, d4, d5, d6)
{
	return _Json_mapMany(f, [d1, d2, d3, d4, d5, d6]);
});

var _Json_map7 = F8(function(f, d1, d2, d3, d4, d5, d6, d7)
{
	return _Json_mapMany(f, [d1, d2, d3, d4, d5, d6, d7]);
});

var _Json_map8 = F9(function(f, d1, d2, d3, d4, d5, d6, d7, d8)
{
	return _Json_mapMany(f, [d1, d2, d3, d4, d5, d6, d7, d8]);
});


// DECODE

var _Json_runOnString = F2(function(decoder, string)
{
	try
	{
		var value = JSON.parse(string);
		return _Json_runHelp(decoder, value);
	}
	catch (e)
	{
		return $elm$core$Result$Err(A2($elm$json$Json$Decode$Failure, 'This is not valid JSON! ' + e.message, _Json_wrap(string)));
	}
});

var _Json_run = F2(function(decoder, value)
{
	return _Json_runHelp(decoder, _Json_unwrap(value));
});

function _Json_runHelp(decoder, value)
{
	switch (decoder.$)
	{
		case 2:
			return decoder.b(value);

		case 5:
			return (value === null)
				? $elm$core$Result$Ok(decoder.c)
				: _Json_expecting('null', value);

		case 3:
			if (!_Json_isArray(value))
			{
				return _Json_expecting('a LIST', value);
			}
			return _Json_runArrayDecoder(decoder.b, value, _List_fromArray);

		case 4:
			if (!_Json_isArray(value))
			{
				return _Json_expecting('an ARRAY', value);
			}
			return _Json_runArrayDecoder(decoder.b, value, _Json_toElmArray);

		case 6:
			var field = decoder.d;
			if (typeof value !== 'object' || value === null || !(field in value))
			{
				return _Json_expecting('an OBJECT with a field named `' + field + '`', value);
			}
			var result = _Json_runHelp(decoder.b, value[field]);
			return ($elm$core$Result$isOk(result)) ? result : $elm$core$Result$Err(A2($elm$json$Json$Decode$Field, field, result.a));

		case 7:
			var index = decoder.e;
			if (!_Json_isArray(value))
			{
				return _Json_expecting('an ARRAY', value);
			}
			if (index >= value.length)
			{
				return _Json_expecting('a LONGER array. Need index ' + index + ' but only see ' + value.length + ' entries', value);
			}
			var result = _Json_runHelp(decoder.b, value[index]);
			return ($elm$core$Result$isOk(result)) ? result : $elm$core$Result$Err(A2($elm$json$Json$Decode$Index, index, result.a));

		case 8:
			if (typeof value !== 'object' || value === null || _Json_isArray(value))
			{
				return _Json_expecting('an OBJECT', value);
			}

			var keyValuePairs = _List_Nil;
			// TODO test perf of Object.keys and switch when support is good enough
			for (var key in value)
			{
				if (value.hasOwnProperty(key))
				{
					var result = _Json_runHelp(decoder.b, value[key]);
					if (!$elm$core$Result$isOk(result))
					{
						return $elm$core$Result$Err(A2($elm$json$Json$Decode$Field, key, result.a));
					}
					keyValuePairs = _List_Cons(_Utils_Tuple2(key, result.a), keyValuePairs);
				}
			}
			return $elm$core$Result$Ok($elm$core$List$reverse(keyValuePairs));

		case 9:
			var answer = decoder.f;
			var decoders = decoder.g;
			for (var i = 0; i < decoders.length; i++)
			{
				var result = _Json_runHelp(decoders[i], value);
				if (!$elm$core$Result$isOk(result))
				{
					return result;
				}
				answer = answer(result.a);
			}
			return $elm$core$Result$Ok(answer);

		case 10:
			var result = _Json_runHelp(decoder.b, value);
			return (!$elm$core$Result$isOk(result))
				? result
				: _Json_runHelp(decoder.h(result.a), value);

		case 11:
			var errors = _List_Nil;
			for (var temp = decoder.g; temp.b; temp = temp.b) // WHILE_CONS
			{
				var result = _Json_runHelp(temp.a, value);
				if ($elm$core$Result$isOk(result))
				{
					return result;
				}
				errors = _List_Cons(result.a, errors);
			}
			return $elm$core$Result$Err($elm$json$Json$Decode$OneOf($elm$core$List$reverse(errors)));

		case 1:
			return $elm$core$Result$Err(A2($elm$json$Json$Decode$Failure, decoder.a, _Json_wrap(value)));

		case 0:
			return $elm$core$Result$Ok(decoder.a);
	}
}

function _Json_runArrayDecoder(decoder, value, toElmValue)
{
	var len = value.length;
	var array = new Array(len);
	for (var i = 0; i < len; i++)
	{
		var result = _Json_runHelp(decoder, value[i]);
		if (!$elm$core$Result$isOk(result))
		{
			return $elm$core$Result$Err(A2($elm$json$Json$Decode$Index, i, result.a));
		}
		array[i] = result.a;
	}
	return $elm$core$Result$Ok(toElmValue(array));
}

function _Json_isArray(value)
{
	return Array.isArray(value) || (typeof FileList !== 'undefined' && value instanceof FileList);
}

function _Json_toElmArray(array)
{
	return A2($elm$core$Array$initialize, array.length, function(i) { return array[i]; });
}

function _Json_expecting(type, value)
{
	return $elm$core$Result$Err(A2($elm$json$Json$Decode$Failure, 'Expecting ' + type, _Json_wrap(value)));
}


// EQUALITY

function _Json_equality(x, y)
{
	if (x === y)
	{
		return true;
	}

	if (x.$ !== y.$)
	{
		return false;
	}

	switch (x.$)
	{
		case 0:
		case 1:
			return x.a === y.a;

		case 2:
			return x.b === y.b;

		case 5:
			return x.c === y.c;

		case 3:
		case 4:
		case 8:
			return _Json_equality(x.b, y.b);

		case 6:
			return x.d === y.d && _Json_equality(x.b, y.b);

		case 7:
			return x.e === y.e && _Json_equality(x.b, y.b);

		case 9:
			return x.f === y.f && _Json_listEquality(x.g, y.g);

		case 10:
			return x.h === y.h && _Json_equality(x.b, y.b);

		case 11:
			return _Json_listEquality(x.g, y.g);
	}
}

function _Json_listEquality(aDecoders, bDecoders)
{
	var len = aDecoders.length;
	if (len !== bDecoders.length)
	{
		return false;
	}
	for (var i = 0; i < len; i++)
	{
		if (!_Json_equality(aDecoders[i], bDecoders[i]))
		{
			return false;
		}
	}
	return true;
}


// ENCODE

var _Json_encode = F2(function(indentLevel, value)
{
	return JSON.stringify(_Json_unwrap(value), null, indentLevel) + '';
});

function _Json_wrap(value) { return { $: 0, a: value }; }
function _Json_unwrap(value) { return value.a; }

function _Json_wrap_UNUSED(value) { return value; }
function _Json_unwrap_UNUSED(value) { return value; }

function _Json_emptyArray() { return []; }
function _Json_emptyObject() { return {}; }

var _Json_addField = F3(function(key, value, object)
{
	object[key] = _Json_unwrap(value);
	return object;
});

function _Json_addEntry(func)
{
	return F2(function(entry, array)
	{
		array.push(_Json_unwrap(func(entry)));
		return array;
	});
}

var _Json_encodeNull = _Json_wrap(null);



// TASKS

function _Scheduler_succeed(value)
{
	return {
		$: 0,
		a: value
	};
}

function _Scheduler_fail(error)
{
	return {
		$: 1,
		a: error
	};
}

function _Scheduler_binding(callback)
{
	return {
		$: 2,
		b: callback,
		c: null
	};
}

var _Scheduler_andThen = F2(function(callback, task)
{
	return {
		$: 3,
		b: callback,
		d: task
	};
});

var _Scheduler_onError = F2(function(callback, task)
{
	return {
		$: 4,
		b: callback,
		d: task
	};
});

function _Scheduler_receive(callback)
{
	return {
		$: 5,
		b: callback
	};
}


// PROCESSES

var _Scheduler_guid = 0;

function _Scheduler_rawSpawn(task)
{
	var proc = {
		$: 0,
		e: _Scheduler_guid++,
		f: task,
		g: null,
		h: []
	};

	_Scheduler_enqueue(proc);

	return proc;
}

function _Scheduler_spawn(task)
{
	return _Scheduler_binding(function(callback) {
		callback(_Scheduler_succeed(_Scheduler_rawSpawn(task)));
	});
}

function _Scheduler_rawSend(proc, msg)
{
	proc.h.push(msg);
	_Scheduler_enqueue(proc);
}

var _Scheduler_send = F2(function(proc, msg)
{
	return _Scheduler_binding(function(callback) {
		_Scheduler_rawSend(proc, msg);
		callback(_Scheduler_succeed(_Utils_Tuple0));
	});
});

function _Scheduler_kill(proc)
{
	return _Scheduler_binding(function(callback) {
		var task = proc.f;
		if (task.$ === 2 && task.c)
		{
			task.c();
		}

		proc.f = null;

		callback(_Scheduler_succeed(_Utils_Tuple0));
	});
}


/* STEP PROCESSES

type alias Process =
  { $ : tag
  , id : unique_id
  , root : Task
  , stack : null | { $: SUCCEED | FAIL, a: callback, b: stack }
  , mailbox : [msg]
  }

*/


var _Scheduler_working = false;
var _Scheduler_queue = [];


function _Scheduler_enqueue(proc)
{
	_Scheduler_queue.push(proc);
	if (_Scheduler_working)
	{
		return;
	}
	_Scheduler_working = true;
	while (proc = _Scheduler_queue.shift())
	{
		_Scheduler_step(proc);
	}
	_Scheduler_working = false;
}


function _Scheduler_step(proc)
{
	while (proc.f)
	{
		var rootTag = proc.f.$;
		if (rootTag === 0 || rootTag === 1)
		{
			while (proc.g && proc.g.$ !== rootTag)
			{
				proc.g = proc.g.i;
			}
			if (!proc.g)
			{
				return;
			}
			proc.f = proc.g.b(proc.f.a);
			proc.g = proc.g.i;
		}
		else if (rootTag === 2)
		{
			proc.f.c = proc.f.b(function(newRoot) {
				proc.f = newRoot;
				_Scheduler_enqueue(proc);
			});
			return;
		}
		else if (rootTag === 5)
		{
			if (proc.h.length === 0)
			{
				return;
			}
			proc.f = proc.f.b(proc.h.shift());
		}
		else // if (rootTag === 3 || rootTag === 4)
		{
			proc.g = {
				$: rootTag === 3 ? 0 : 1,
				b: proc.f.b,
				i: proc.g
			};
			proc.f = proc.f.d;
		}
	}
}



function _Process_sleep(time)
{
	return _Scheduler_binding(function(callback) {
		var id = setTimeout(function() {
			callback(_Scheduler_succeed(_Utils_Tuple0));
		}, time);

		return function() { clearTimeout(id); };
	});
}




// PROGRAMS


var _Platform_worker = F4(function(impl, flagDecoder, debugMetadata, args)
{
	return _Platform_initialize(
		flagDecoder,
		args,
		impl.init,
		impl.update,
		impl.subscriptions,
		function() { return function() {} }
	);
});



// INITIALIZE A PROGRAM


function _Platform_initialize(flagDecoder, args, init, update, subscriptions, stepperBuilder)
{
	var result = A2(_Json_run, flagDecoder, _Json_wrap(args ? args['flags'] : undefined));
	$elm$core$Result$isOk(result) || _Debug_crash(2 /**/, _Json_errorToString(result.a) /**/);
	var managers = {};
	var initPair = init(result.a);
	var model = initPair.a;
	var stepper = stepperBuilder(sendToApp, model);
	var ports = _Platform_setupEffects(managers, sendToApp);

	function sendToApp(msg, viewMetadata)
	{
		var pair = A2(update, msg, model);
		stepper(model = pair.a, viewMetadata);
		_Platform_enqueueEffects(managers, pair.b, subscriptions(model));
	}

	_Platform_enqueueEffects(managers, initPair.b, subscriptions(model));

	return ports ? { ports: ports } : {};
}



// TRACK PRELOADS
//
// This is used by code in elm/browser and elm/http
// to register any HTTP requests that are triggered by init.
//


var _Platform_preload;


function _Platform_registerPreload(url)
{
	_Platform_preload.add(url);
}



// EFFECT MANAGERS


var _Platform_effectManagers = {};


function _Platform_setupEffects(managers, sendToApp)
{
	var ports;

	// setup all necessary effect managers
	for (var key in _Platform_effectManagers)
	{
		var manager = _Platform_effectManagers[key];

		if (manager.a)
		{
			ports = ports || {};
			ports[key] = manager.a(key, sendToApp);
		}

		managers[key] = _Platform_instantiateManager(manager, sendToApp);
	}

	return ports;
}


function _Platform_createManager(init, onEffects, onSelfMsg, cmdMap, subMap)
{
	return {
		b: init,
		c: onEffects,
		d: onSelfMsg,
		e: cmdMap,
		f: subMap
	};
}


function _Platform_instantiateManager(info, sendToApp)
{
	var router = {
		g: sendToApp,
		h: undefined
	};

	var onEffects = info.c;
	var onSelfMsg = info.d;
	var cmdMap = info.e;
	var subMap = info.f;

	function loop(state)
	{
		return A2(_Scheduler_andThen, loop, _Scheduler_receive(function(msg)
		{
			var value = msg.a;

			if (msg.$ === 0)
			{
				return A3(onSelfMsg, router, value, state);
			}

			return cmdMap && subMap
				? A4(onEffects, router, value.i, value.j, state)
				: A3(onEffects, router, cmdMap ? value.i : value.j, state);
		}));
	}

	return router.h = _Scheduler_rawSpawn(A2(_Scheduler_andThen, loop, info.b));
}



// ROUTING


var _Platform_sendToApp = F2(function(router, msg)
{
	return _Scheduler_binding(function(callback)
	{
		router.g(msg);
		callback(_Scheduler_succeed(_Utils_Tuple0));
	});
});


var _Platform_sendToSelf = F2(function(router, msg)
{
	return A2(_Scheduler_send, router.h, {
		$: 0,
		a: msg
	});
});



// BAGS


function _Platform_leaf(home)
{
	return function(value)
	{
		return {
			$: 1,
			k: home,
			l: value
		};
	};
}


function _Platform_batch(list)
{
	return {
		$: 2,
		m: list
	};
}


var _Platform_map = F2(function(tagger, bag)
{
	return {
		$: 3,
		n: tagger,
		o: bag
	}
});



// PIPE BAGS INTO EFFECT MANAGERS
//
// Effects must be queued!
//
// Say your init contains a synchronous command, like Time.now or Time.here
//
//   - This will produce a batch of effects (FX_1)
//   - The synchronous task triggers the subsequent `update` call
//   - This will produce a batch of effects (FX_2)
//
// If we just start dispatching FX_2, subscriptions from FX_2 can be processed
// before subscriptions from FX_1. No good! Earlier versions of this code had
// this problem, leading to these reports:
//
//   https://github.com/elm/core/issues/980
//   https://github.com/elm/core/pull/981
//   https://github.com/elm/compiler/issues/1776
//
// The queue is necessary to avoid ordering issues for synchronous commands.


// Why use true/false here? Why not just check the length of the queue?
// The goal is to detect "are we currently dispatching effects?" If we
// are, we need to bail and let the ongoing while loop handle things.
//
// Now say the queue has 1 element. When we dequeue the final element,
// the queue will be empty, but we are still actively dispatching effects.
// So you could get queue jumping in a really tricky category of cases.
//
var _Platform_effectsQueue = [];
var _Platform_effectsActive = false;


function _Platform_enqueueEffects(managers, cmdBag, subBag)
{
	_Platform_effectsQueue.push({ p: managers, q: cmdBag, r: subBag });

	if (_Platform_effectsActive) return;

	_Platform_effectsActive = true;
	for (var fx; fx = _Platform_effectsQueue.shift(); )
	{
		_Platform_dispatchEffects(fx.p, fx.q, fx.r);
	}
	_Platform_effectsActive = false;
}


function _Platform_dispatchEffects(managers, cmdBag, subBag)
{
	var effectsDict = {};
	_Platform_gatherEffects(true, cmdBag, effectsDict, null);
	_Platform_gatherEffects(false, subBag, effectsDict, null);

	for (var home in managers)
	{
		_Scheduler_rawSend(managers[home], {
			$: 'fx',
			a: effectsDict[home] || { i: _List_Nil, j: _List_Nil }
		});
	}
}


function _Platform_gatherEffects(isCmd, bag, effectsDict, taggers)
{
	switch (bag.$)
	{
		case 1:
			var home = bag.k;
			var effect = _Platform_toEffect(isCmd, home, taggers, bag.l);
			effectsDict[home] = _Platform_insert(isCmd, effect, effectsDict[home]);
			return;

		case 2:
			for (var list = bag.m; list.b; list = list.b) // WHILE_CONS
			{
				_Platform_gatherEffects(isCmd, list.a, effectsDict, taggers);
			}
			return;

		case 3:
			_Platform_gatherEffects(isCmd, bag.o, effectsDict, {
				s: bag.n,
				t: taggers
			});
			return;
	}
}


function _Platform_toEffect(isCmd, home, taggers, value)
{
	function applyTaggers(x)
	{
		for (var temp = taggers; temp; temp = temp.t)
		{
			x = temp.s(x);
		}
		return x;
	}

	var map = isCmd
		? _Platform_effectManagers[home].e
		: _Platform_effectManagers[home].f;

	return A2(map, applyTaggers, value)
}


function _Platform_insert(isCmd, newEffect, effects)
{
	effects = effects || { i: _List_Nil, j: _List_Nil };

	isCmd
		? (effects.i = _List_Cons(newEffect, effects.i))
		: (effects.j = _List_Cons(newEffect, effects.j));

	return effects;
}



// PORTS


function _Platform_checkPortName(name)
{
	if (_Platform_effectManagers[name])
	{
		_Debug_crash(3, name)
	}
}



// OUTGOING PORTS


function _Platform_outgoingPort(name, converter)
{
	_Platform_checkPortName(name);
	_Platform_effectManagers[name] = {
		e: _Platform_outgoingPortMap,
		u: converter,
		a: _Platform_setupOutgoingPort
	};
	return _Platform_leaf(name);
}


var _Platform_outgoingPortMap = F2(function(tagger, value) { return value; });


function _Platform_setupOutgoingPort(name)
{
	var subs = [];
	var converter = _Platform_effectManagers[name].u;

	// CREATE MANAGER

	var init = _Process_sleep(0);

	_Platform_effectManagers[name].b = init;
	_Platform_effectManagers[name].c = F3(function(router, cmdList, state)
	{
		for ( ; cmdList.b; cmdList = cmdList.b) // WHILE_CONS
		{
			// grab a separate reference to subs in case unsubscribe is called
			var currentSubs = subs;
			var value = _Json_unwrap(converter(cmdList.a));
			for (var i = 0; i < currentSubs.length; i++)
			{
				currentSubs[i](value);
			}
		}
		return init;
	});

	// PUBLIC API

	function subscribe(callback)
	{
		subs.push(callback);
	}

	function unsubscribe(callback)
	{
		// copy subs into a new array in case unsubscribe is called within a
		// subscribed callback
		subs = subs.slice();
		var index = subs.indexOf(callback);
		if (index >= 0)
		{
			subs.splice(index, 1);
		}
	}

	return {
		subscribe: subscribe,
		unsubscribe: unsubscribe
	};
}



// INCOMING PORTS


function _Platform_incomingPort(name, converter)
{
	_Platform_checkPortName(name);
	_Platform_effectManagers[name] = {
		f: _Platform_incomingPortMap,
		u: converter,
		a: _Platform_setupIncomingPort
	};
	return _Platform_leaf(name);
}


var _Platform_incomingPortMap = F2(function(tagger, finalTagger)
{
	return function(value)
	{
		return tagger(finalTagger(value));
	};
});


function _Platform_setupIncomingPort(name, sendToApp)
{
	var subs = _List_Nil;
	var converter = _Platform_effectManagers[name].u;

	// CREATE MANAGER

	var init = _Scheduler_succeed(null);

	_Platform_effectManagers[name].b = init;
	_Platform_effectManagers[name].c = F3(function(router, subList, state)
	{
		subs = subList;
		return init;
	});

	// PUBLIC API

	function send(incomingValue)
	{
		var result = A2(_Json_run, converter, _Json_wrap(incomingValue));

		$elm$core$Result$isOk(result) || _Debug_crash(4, name, result.a);

		var value = result.a;
		for (var temp = subs; temp.b; temp = temp.b) // WHILE_CONS
		{
			sendToApp(temp.a(value));
		}
	}

	return { send: send };
}



// EXPORT ELM MODULES
//
// Have DEBUG and PROD versions so that we can (1) give nicer errors in
// debug mode and (2) not pay for the bits needed for that in prod mode.
//


function _Platform_export_UNUSED(exports)
{
	scope['Elm']
		? _Platform_mergeExportsProd(scope['Elm'], exports)
		: scope['Elm'] = exports;
}


function _Platform_mergeExportsProd(obj, exports)
{
	for (var name in exports)
	{
		(name in obj)
			? (name == 'init')
				? _Debug_crash(6)
				: _Platform_mergeExportsProd(obj[name], exports[name])
			: (obj[name] = exports[name]);
	}
}


function _Platform_export(exports)
{
	scope['Elm']
		? _Platform_mergeExportsDebug('Elm', scope['Elm'], exports)
		: scope['Elm'] = exports;
}


function _Platform_mergeExportsDebug(moduleName, obj, exports)
{
	for (var name in exports)
	{
		(name in obj)
			? (name == 'init')
				? _Debug_crash(6, moduleName)
				: _Platform_mergeExportsDebug(moduleName + '.' + name, obj[name], exports[name])
			: (obj[name] = exports[name]);
	}
}




// HELPERS


var _VirtualDom_divertHrefToApp;

var _VirtualDom_doc = typeof document !== 'undefined' ? document : {};


function _VirtualDom_appendChild(parent, child)
{
	parent.appendChild(child);
}

var _VirtualDom_init = F4(function(virtualNode, flagDecoder, debugMetadata, args)
{
	// NOTE: this function needs _Platform_export available to work

	/**_UNUSED/
	var node = args['node'];
	//*/
	/**/
	var node = args && args['node'] ? args['node'] : _Debug_crash(0);
	//*/

	node.parentNode.replaceChild(
		_VirtualDom_render(virtualNode, function() {}),
		node
	);

	return {};
});



// TEXT


function _VirtualDom_text(string)
{
	return {
		$: 0,
		a: string
	};
}



// NODE


var _VirtualDom_nodeNS = F2(function(namespace, tag)
{
	return F2(function(factList, kidList)
	{
		for (var kids = [], descendantsCount = 0; kidList.b; kidList = kidList.b) // WHILE_CONS
		{
			var kid = kidList.a;
			descendantsCount += (kid.b || 0);
			kids.push(kid);
		}
		descendantsCount += kids.length;

		return {
			$: 1,
			c: tag,
			d: _VirtualDom_organizeFacts(factList),
			e: kids,
			f: namespace,
			b: descendantsCount
		};
	});
});


var _VirtualDom_node = _VirtualDom_nodeNS(undefined);



// KEYED NODE


var _VirtualDom_keyedNodeNS = F2(function(namespace, tag)
{
	return F2(function(factList, kidList)
	{
		for (var kids = [], descendantsCount = 0; kidList.b; kidList = kidList.b) // WHILE_CONS
		{
			var kid = kidList.a;
			descendantsCount += (kid.b.b || 0);
			kids.push(kid);
		}
		descendantsCount += kids.length;

		return {
			$: 2,
			c: tag,
			d: _VirtualDom_organizeFacts(factList),
			e: kids,
			f: namespace,
			b: descendantsCount
		};
	});
});


var _VirtualDom_keyedNode = _VirtualDom_keyedNodeNS(undefined);



// CUSTOM


function _VirtualDom_custom(factList, model, render, diff)
{
	return {
		$: 3,
		d: _VirtualDom_organizeFacts(factList),
		g: model,
		h: render,
		i: diff
	};
}



// MAP


var _VirtualDom_map = F2(function(tagger, node)
{
	return {
		$: 4,
		j: tagger,
		k: node,
		b: 1 + (node.b || 0)
	};
});



// LAZY


function _VirtualDom_thunk(refs, thunk)
{
	return {
		$: 5,
		l: refs,
		m: thunk,
		k: undefined
	};
}

var _VirtualDom_lazy = F2(function(func, a)
{
	return _VirtualDom_thunk([func, a], function() {
		return func(a);
	});
});

var _VirtualDom_lazy2 = F3(function(func, a, b)
{
	return _VirtualDom_thunk([func, a, b], function() {
		return A2(func, a, b);
	});
});

var _VirtualDom_lazy3 = F4(function(func, a, b, c)
{
	return _VirtualDom_thunk([func, a, b, c], function() {
		return A3(func, a, b, c);
	});
});

var _VirtualDom_lazy4 = F5(function(func, a, b, c, d)
{
	return _VirtualDom_thunk([func, a, b, c, d], function() {
		return A4(func, a, b, c, d);
	});
});

var _VirtualDom_lazy5 = F6(function(func, a, b, c, d, e)
{
	return _VirtualDom_thunk([func, a, b, c, d, e], function() {
		return A5(func, a, b, c, d, e);
	});
});

var _VirtualDom_lazy6 = F7(function(func, a, b, c, d, e, f)
{
	return _VirtualDom_thunk([func, a, b, c, d, e, f], function() {
		return A6(func, a, b, c, d, e, f);
	});
});

var _VirtualDom_lazy7 = F8(function(func, a, b, c, d, e, f, g)
{
	return _VirtualDom_thunk([func, a, b, c, d, e, f, g], function() {
		return A7(func, a, b, c, d, e, f, g);
	});
});

var _VirtualDom_lazy8 = F9(function(func, a, b, c, d, e, f, g, h)
{
	return _VirtualDom_thunk([func, a, b, c, d, e, f, g, h], function() {
		return A8(func, a, b, c, d, e, f, g, h);
	});
});



// FACTS


var _VirtualDom_on = F2(function(key, handler)
{
	return {
		$: 'a0',
		n: key,
		o: handler
	};
});
var _VirtualDom_style = F2(function(key, value)
{
	return {
		$: 'a1',
		n: key,
		o: value
	};
});
var _VirtualDom_property = F2(function(key, value)
{
	return {
		$: 'a2',
		n: key,
		o: value
	};
});
var _VirtualDom_attribute = F2(function(key, value)
{
	return {
		$: 'a3',
		n: key,
		o: value
	};
});
var _VirtualDom_attributeNS = F3(function(namespace, key, value)
{
	return {
		$: 'a4',
		n: key,
		o: { f: namespace, o: value }
	};
});



// XSS ATTACK VECTOR CHECKS


function _VirtualDom_noScript(tag)
{
	return tag == 'script' ? 'p' : tag;
}

function _VirtualDom_noOnOrFormAction(key)
{
	return /^(on|formAction$)/i.test(key) ? 'data-' + key : key;
}

function _VirtualDom_noInnerHtmlOrFormAction(key)
{
	return key == 'innerHTML' || key == 'formAction' ? 'data-' + key : key;
}

function _VirtualDom_noJavaScriptUri_UNUSED(value)
{
	return /^javascript:/i.test(value.replace(/\s/g,'')) ? '' : value;
}

function _VirtualDom_noJavaScriptUri(value)
{
	return /^javascript:/i.test(value.replace(/\s/g,''))
		? 'javascript:alert("This is an XSS vector. Please use ports or web components instead.")'
		: value;
}

function _VirtualDom_noJavaScriptOrHtmlUri_UNUSED(value)
{
	return /^\s*(javascript:|data:text\/html)/i.test(value) ? '' : value;
}

function _VirtualDom_noJavaScriptOrHtmlUri(value)
{
	return /^\s*(javascript:|data:text\/html)/i.test(value)
		? 'javascript:alert("This is an XSS vector. Please use ports or web components instead.")'
		: value;
}



// MAP FACTS


var _VirtualDom_mapAttribute = F2(function(func, attr)
{
	return (attr.$ === 'a0')
		? A2(_VirtualDom_on, attr.n, _VirtualDom_mapHandler(func, attr.o))
		: attr;
});

function _VirtualDom_mapHandler(func, handler)
{
	var tag = $elm$virtual_dom$VirtualDom$toHandlerInt(handler);

	// 0 = Normal
	// 1 = MayStopPropagation
	// 2 = MayPreventDefault
	// 3 = Custom

	return {
		$: handler.$,
		a:
			!tag
				? A2($elm$json$Json$Decode$map, func, handler.a)
				:
			A3($elm$json$Json$Decode$map2,
				tag < 3
					? _VirtualDom_mapEventTuple
					: _VirtualDom_mapEventRecord,
				$elm$json$Json$Decode$succeed(func),
				handler.a
			)
	};
}

var _VirtualDom_mapEventTuple = F2(function(func, tuple)
{
	return _Utils_Tuple2(func(tuple.a), tuple.b);
});

var _VirtualDom_mapEventRecord = F2(function(func, record)
{
	return {
		message: func(record.message),
		stopPropagation: record.stopPropagation,
		preventDefault: record.preventDefault
	}
});



// ORGANIZE FACTS


function _VirtualDom_organizeFacts(factList)
{
	for (var facts = {}; factList.b; factList = factList.b) // WHILE_CONS
	{
		var entry = factList.a;

		var tag = entry.$;
		var key = entry.n;
		var value = entry.o;

		if (tag === 'a2')
		{
			(key === 'className')
				? _VirtualDom_addClass(facts, key, _Json_unwrap(value))
				: facts[key] = _Json_unwrap(value);

			continue;
		}

		var subFacts = facts[tag] || (facts[tag] = {});
		(tag === 'a3' && key === 'class')
			? _VirtualDom_addClass(subFacts, key, value)
			: subFacts[key] = value;
	}

	return facts;
}

function _VirtualDom_addClass(object, key, newClass)
{
	var classes = object[key];
	object[key] = classes ? classes + ' ' + newClass : newClass;
}



// RENDER


function _VirtualDom_render(vNode, eventNode)
{
	var tag = vNode.$;

	if (tag === 5)
	{
		return _VirtualDom_render(vNode.k || (vNode.k = vNode.m()), eventNode);
	}

	if (tag === 0)
	{
		return _VirtualDom_doc.createTextNode(vNode.a);
	}

	if (tag === 4)
	{
		var subNode = vNode.k;
		var tagger = vNode.j;

		while (subNode.$ === 4)
		{
			typeof tagger !== 'object'
				? tagger = [tagger, subNode.j]
				: tagger.push(subNode.j);

			subNode = subNode.k;
		}

		var subEventRoot = { j: tagger, p: eventNode };
		var domNode = _VirtualDom_render(subNode, subEventRoot);
		domNode.elm_event_node_ref = subEventRoot;
		return domNode;
	}

	if (tag === 3)
	{
		var domNode = vNode.h(vNode.g);
		_VirtualDom_applyFacts(domNode, eventNode, vNode.d);
		return domNode;
	}

	// at this point `tag` must be 1 or 2

	var domNode = vNode.f
		? _VirtualDom_doc.createElementNS(vNode.f, vNode.c)
		: _VirtualDom_doc.createElement(vNode.c);

	if (_VirtualDom_divertHrefToApp && vNode.c == 'a')
	{
		domNode.addEventListener('click', _VirtualDom_divertHrefToApp(domNode));
	}

	_VirtualDom_applyFacts(domNode, eventNode, vNode.d);

	for (var kids = vNode.e, i = 0; i < kids.length; i++)
	{
		_VirtualDom_appendChild(domNode, _VirtualDom_render(tag === 1 ? kids[i] : kids[i].b, eventNode));
	}

	return domNode;
}



// APPLY FACTS


function _VirtualDom_applyFacts(domNode, eventNode, facts)
{
	for (var key in facts)
	{
		var value = facts[key];

		key === 'a1'
			? _VirtualDom_applyStyles(domNode, value)
			:
		key === 'a0'
			? _VirtualDom_applyEvents(domNode, eventNode, value)
			:
		key === 'a3'
			? _VirtualDom_applyAttrs(domNode, value)
			:
		key === 'a4'
			? _VirtualDom_applyAttrsNS(domNode, value)
			:
		((key !== 'value' && key !== 'checked') || domNode[key] !== value) && (domNode[key] = value);
	}
}



// APPLY STYLES


function _VirtualDom_applyStyles(domNode, styles)
{
	var domNodeStyle = domNode.style;

	for (var key in styles)
	{
		domNodeStyle[key] = styles[key];
	}
}



// APPLY ATTRS


function _VirtualDom_applyAttrs(domNode, attrs)
{
	for (var key in attrs)
	{
		var value = attrs[key];
		typeof value !== 'undefined'
			? domNode.setAttribute(key, value)
			: domNode.removeAttribute(key);
	}
}



// APPLY NAMESPACED ATTRS


function _VirtualDom_applyAttrsNS(domNode, nsAttrs)
{
	for (var key in nsAttrs)
	{
		var pair = nsAttrs[key];
		var namespace = pair.f;
		var value = pair.o;

		typeof value !== 'undefined'
			? domNode.setAttributeNS(namespace, key, value)
			: domNode.removeAttributeNS(namespace, key);
	}
}



// APPLY EVENTS


function _VirtualDom_applyEvents(domNode, eventNode, events)
{
	var allCallbacks = domNode.elmFs || (domNode.elmFs = {});

	for (var key in events)
	{
		var newHandler = events[key];
		var oldCallback = allCallbacks[key];

		if (!newHandler)
		{
			domNode.removeEventListener(key, oldCallback);
			allCallbacks[key] = undefined;
			continue;
		}

		if (oldCallback)
		{
			var oldHandler = oldCallback.q;
			if (oldHandler.$ === newHandler.$)
			{
				oldCallback.q = newHandler;
				continue;
			}
			domNode.removeEventListener(key, oldCallback);
		}

		oldCallback = _VirtualDom_makeCallback(eventNode, newHandler);
		domNode.addEventListener(key, oldCallback,
			_VirtualDom_passiveSupported
			&& { passive: $elm$virtual_dom$VirtualDom$toHandlerInt(newHandler) < 2 }
		);
		allCallbacks[key] = oldCallback;
	}
}



// PASSIVE EVENTS


var _VirtualDom_passiveSupported;

try
{
	window.addEventListener('t', null, Object.defineProperty({}, 'passive', {
		get: function() { _VirtualDom_passiveSupported = true; }
	}));
}
catch(e) {}



// EVENT HANDLERS


function _VirtualDom_makeCallback(eventNode, initialHandler)
{
	function callback(event)
	{
		var handler = callback.q;
		var result = _Json_runHelp(handler.a, event);

		if (!$elm$core$Result$isOk(result))
		{
			return;
		}

		var tag = $elm$virtual_dom$VirtualDom$toHandlerInt(handler);

		// 0 = Normal
		// 1 = MayStopPropagation
		// 2 = MayPreventDefault
		// 3 = Custom

		var value = result.a;
		var message = !tag ? value : tag < 3 ? value.a : value.message;
		var stopPropagation = tag == 1 ? value.b : tag == 3 && value.stopPropagation;
		var currentEventNode = (
			stopPropagation && event.stopPropagation(),
			(tag == 2 ? value.b : tag == 3 && value.preventDefault) && event.preventDefault(),
			eventNode
		);
		var tagger;
		var i;
		while (tagger = currentEventNode.j)
		{
			if (typeof tagger == 'function')
			{
				message = tagger(message);
			}
			else
			{
				for (var i = tagger.length; i--; )
				{
					message = tagger[i](message);
				}
			}
			currentEventNode = currentEventNode.p;
		}
		currentEventNode(message, stopPropagation); // stopPropagation implies isSync
	}

	callback.q = initialHandler;

	return callback;
}

function _VirtualDom_equalEvents(x, y)
{
	return x.$ == y.$ && _Json_equality(x.a, y.a);
}



// DIFF


// TODO: Should we do patches like in iOS?
//
// type Patch
//   = At Int Patch
//   | Batch (List Patch)
//   | Change ...
//
// How could it not be better?
//
function _VirtualDom_diff(x, y)
{
	var patches = [];
	_VirtualDom_diffHelp(x, y, patches, 0);
	return patches;
}


function _VirtualDom_pushPatch(patches, type, index, data)
{
	var patch = {
		$: type,
		r: index,
		s: data,
		t: undefined,
		u: undefined
	};
	patches.push(patch);
	return patch;
}


function _VirtualDom_diffHelp(x, y, patches, index)
{
	if (x === y)
	{
		return;
	}

	var xType = x.$;
	var yType = y.$;

	// Bail if you run into different types of nodes. Implies that the
	// structure has changed significantly and it's not worth a diff.
	if (xType !== yType)
	{
		if (xType === 1 && yType === 2)
		{
			y = _VirtualDom_dekey(y);
			yType = 1;
		}
		else
		{
			_VirtualDom_pushPatch(patches, 0, index, y);
			return;
		}
	}

	// Now we know that both nodes are the same $.
	switch (yType)
	{
		case 5:
			var xRefs = x.l;
			var yRefs = y.l;
			var i = xRefs.length;
			var same = i === yRefs.length;
			while (same && i--)
			{
				same = xRefs[i] === yRefs[i];
			}
			if (same)
			{
				y.k = x.k;
				return;
			}
			y.k = y.m();
			var subPatches = [];
			_VirtualDom_diffHelp(x.k, y.k, subPatches, 0);
			subPatches.length > 0 && _VirtualDom_pushPatch(patches, 1, index, subPatches);
			return;

		case 4:
			// gather nested taggers
			var xTaggers = x.j;
			var yTaggers = y.j;
			var nesting = false;

			var xSubNode = x.k;
			while (xSubNode.$ === 4)
			{
				nesting = true;

				typeof xTaggers !== 'object'
					? xTaggers = [xTaggers, xSubNode.j]
					: xTaggers.push(xSubNode.j);

				xSubNode = xSubNode.k;
			}

			var ySubNode = y.k;
			while (ySubNode.$ === 4)
			{
				nesting = true;

				typeof yTaggers !== 'object'
					? yTaggers = [yTaggers, ySubNode.j]
					: yTaggers.push(ySubNode.j);

				ySubNode = ySubNode.k;
			}

			// Just bail if different numbers of taggers. This implies the
			// structure of the virtual DOM has changed.
			if (nesting && xTaggers.length !== yTaggers.length)
			{
				_VirtualDom_pushPatch(patches, 0, index, y);
				return;
			}

			// check if taggers are "the same"
			if (nesting ? !_VirtualDom_pairwiseRefEqual(xTaggers, yTaggers) : xTaggers !== yTaggers)
			{
				_VirtualDom_pushPatch(patches, 2, index, yTaggers);
			}

			// diff everything below the taggers
			_VirtualDom_diffHelp(xSubNode, ySubNode, patches, index + 1);
			return;

		case 0:
			if (x.a !== y.a)
			{
				_VirtualDom_pushPatch(patches, 3, index, y.a);
			}
			return;

		case 1:
			_VirtualDom_diffNodes(x, y, patches, index, _VirtualDom_diffKids);
			return;

		case 2:
			_VirtualDom_diffNodes(x, y, patches, index, _VirtualDom_diffKeyedKids);
			return;

		case 3:
			if (x.h !== y.h)
			{
				_VirtualDom_pushPatch(patches, 0, index, y);
				return;
			}

			var factsDiff = _VirtualDom_diffFacts(x.d, y.d);
			factsDiff && _VirtualDom_pushPatch(patches, 4, index, factsDiff);

			var patch = y.i(x.g, y.g);
			patch && _VirtualDom_pushPatch(patches, 5, index, patch);

			return;
	}
}

// assumes the incoming arrays are the same length
function _VirtualDom_pairwiseRefEqual(as, bs)
{
	for (var i = 0; i < as.length; i++)
	{
		if (as[i] !== bs[i])
		{
			return false;
		}
	}

	return true;
}

function _VirtualDom_diffNodes(x, y, patches, index, diffKids)
{
	// Bail if obvious indicators have changed. Implies more serious
	// structural changes such that it's not worth it to diff.
	if (x.c !== y.c || x.f !== y.f)
	{
		_VirtualDom_pushPatch(patches, 0, index, y);
		return;
	}

	var factsDiff = _VirtualDom_diffFacts(x.d, y.d);
	factsDiff && _VirtualDom_pushPatch(patches, 4, index, factsDiff);

	diffKids(x, y, patches, index);
}



// DIFF FACTS


// TODO Instead of creating a new diff object, it's possible to just test if
// there *is* a diff. During the actual patch, do the diff again and make the
// modifications directly. This way, there's no new allocations. Worth it?
function _VirtualDom_diffFacts(x, y, category)
{
	var diff;

	// look for changes and removals
	for (var xKey in x)
	{
		if (xKey === 'a1' || xKey === 'a0' || xKey === 'a3' || xKey === 'a4')
		{
			var subDiff = _VirtualDom_diffFacts(x[xKey], y[xKey] || {}, xKey);
			if (subDiff)
			{
				diff = diff || {};
				diff[xKey] = subDiff;
			}
			continue;
		}

		// remove if not in the new facts
		if (!(xKey in y))
		{
			diff = diff || {};
			diff[xKey] =
				!category
					? (typeof x[xKey] === 'string' ? '' : null)
					:
				(category === 'a1')
					? ''
					:
				(category === 'a0' || category === 'a3')
					? undefined
					:
				{ f: x[xKey].f, o: undefined };

			continue;
		}

		var xValue = x[xKey];
		var yValue = y[xKey];

		// reference equal, so don't worry about it
		if (xValue === yValue && xKey !== 'value' && xKey !== 'checked'
			|| category === 'a0' && _VirtualDom_equalEvents(xValue, yValue))
		{
			continue;
		}

		diff = diff || {};
		diff[xKey] = yValue;
	}

	// add new stuff
	for (var yKey in y)
	{
		if (!(yKey in x))
		{
			diff = diff || {};
			diff[yKey] = y[yKey];
		}
	}

	return diff;
}



// DIFF KIDS


function _VirtualDom_diffKids(xParent, yParent, patches, index)
{
	var xKids = xParent.e;
	var yKids = yParent.e;

	var xLen = xKids.length;
	var yLen = yKids.length;

	// FIGURE OUT IF THERE ARE INSERTS OR REMOVALS

	if (xLen > yLen)
	{
		_VirtualDom_pushPatch(patches, 6, index, {
			v: yLen,
			i: xLen - yLen
		});
	}
	else if (xLen < yLen)
	{
		_VirtualDom_pushPatch(patches, 7, index, {
			v: xLen,
			e: yKids
		});
	}

	// PAIRWISE DIFF EVERYTHING ELSE

	for (var minLen = xLen < yLen ? xLen : yLen, i = 0; i < minLen; i++)
	{
		var xKid = xKids[i];
		_VirtualDom_diffHelp(xKid, yKids[i], patches, ++index);
		index += xKid.b || 0;
	}
}



// KEYED DIFF


function _VirtualDom_diffKeyedKids(xParent, yParent, patches, rootIndex)
{
	var localPatches = [];

	var changes = {}; // Dict String Entry
	var inserts = []; // Array { index : Int, entry : Entry }
	// type Entry = { tag : String, vnode : VNode, index : Int, data : _ }

	var xKids = xParent.e;
	var yKids = yParent.e;
	var xLen = xKids.length;
	var yLen = yKids.length;
	var xIndex = 0;
	var yIndex = 0;

	var index = rootIndex;

	while (xIndex < xLen && yIndex < yLen)
	{
		var x = xKids[xIndex];
		var y = yKids[yIndex];

		var xKey = x.a;
		var yKey = y.a;
		var xNode = x.b;
		var yNode = y.b;

		var newMatch = undefined;
		var oldMatch = undefined;

		// check if keys match

		if (xKey === yKey)
		{
			index++;
			_VirtualDom_diffHelp(xNode, yNode, localPatches, index);
			index += xNode.b || 0;

			xIndex++;
			yIndex++;
			continue;
		}

		// look ahead 1 to detect insertions and removals.

		var xNext = xKids[xIndex + 1];
		var yNext = yKids[yIndex + 1];

		if (xNext)
		{
			var xNextKey = xNext.a;
			var xNextNode = xNext.b;
			oldMatch = yKey === xNextKey;
		}

		if (yNext)
		{
			var yNextKey = yNext.a;
			var yNextNode = yNext.b;
			newMatch = xKey === yNextKey;
		}


		// swap x and y
		if (newMatch && oldMatch)
		{
			index++;
			_VirtualDom_diffHelp(xNode, yNextNode, localPatches, index);
			_VirtualDom_insertNode(changes, localPatches, xKey, yNode, yIndex, inserts);
			index += xNode.b || 0;

			index++;
			_VirtualDom_removeNode(changes, localPatches, xKey, xNextNode, index);
			index += xNextNode.b || 0;

			xIndex += 2;
			yIndex += 2;
			continue;
		}

		// insert y
		if (newMatch)
		{
			index++;
			_VirtualDom_insertNode(changes, localPatches, yKey, yNode, yIndex, inserts);
			_VirtualDom_diffHelp(xNode, yNextNode, localPatches, index);
			index += xNode.b || 0;

			xIndex += 1;
			yIndex += 2;
			continue;
		}

		// remove x
		if (oldMatch)
		{
			index++;
			_VirtualDom_removeNode(changes, localPatches, xKey, xNode, index);
			index += xNode.b || 0;

			index++;
			_VirtualDom_diffHelp(xNextNode, yNode, localPatches, index);
			index += xNextNode.b || 0;

			xIndex += 2;
			yIndex += 1;
			continue;
		}

		// remove x, insert y
		if (xNext && xNextKey === yNextKey)
		{
			index++;
			_VirtualDom_removeNode(changes, localPatches, xKey, xNode, index);
			_VirtualDom_insertNode(changes, localPatches, yKey, yNode, yIndex, inserts);
			index += xNode.b || 0;

			index++;
			_VirtualDom_diffHelp(xNextNode, yNextNode, localPatches, index);
			index += xNextNode.b || 0;

			xIndex += 2;
			yIndex += 2;
			continue;
		}

		break;
	}

	// eat up any remaining nodes with removeNode and insertNode

	while (xIndex < xLen)
	{
		index++;
		var x = xKids[xIndex];
		var xNode = x.b;
		_VirtualDom_removeNode(changes, localPatches, x.a, xNode, index);
		index += xNode.b || 0;
		xIndex++;
	}

	while (yIndex < yLen)
	{
		var endInserts = endInserts || [];
		var y = yKids[yIndex];
		_VirtualDom_insertNode(changes, localPatches, y.a, y.b, undefined, endInserts);
		yIndex++;
	}

	if (localPatches.length > 0 || inserts.length > 0 || endInserts)
	{
		_VirtualDom_pushPatch(patches, 8, rootIndex, {
			w: localPatches,
			x: inserts,
			y: endInserts
		});
	}
}



// CHANGES FROM KEYED DIFF


var _VirtualDom_POSTFIX = '_elmW6BL';


function _VirtualDom_insertNode(changes, localPatches, key, vnode, yIndex, inserts)
{
	var entry = changes[key];

	// never seen this key before
	if (!entry)
	{
		entry = {
			c: 0,
			z: vnode,
			r: yIndex,
			s: undefined
		};

		inserts.push({ r: yIndex, A: entry });
		changes[key] = entry;

		return;
	}

	// this key was removed earlier, a match!
	if (entry.c === 1)
	{
		inserts.push({ r: yIndex, A: entry });

		entry.c = 2;
		var subPatches = [];
		_VirtualDom_diffHelp(entry.z, vnode, subPatches, entry.r);
		entry.r = yIndex;
		entry.s.s = {
			w: subPatches,
			A: entry
		};

		return;
	}

	// this key has already been inserted or moved, a duplicate!
	_VirtualDom_insertNode(changes, localPatches, key + _VirtualDom_POSTFIX, vnode, yIndex, inserts);
}


function _VirtualDom_removeNode(changes, localPatches, key, vnode, index)
{
	var entry = changes[key];

	// never seen this key before
	if (!entry)
	{
		var patch = _VirtualDom_pushPatch(localPatches, 9, index, undefined);

		changes[key] = {
			c: 1,
			z: vnode,
			r: index,
			s: patch
		};

		return;
	}

	// this key was inserted earlier, a match!
	if (entry.c === 0)
	{
		entry.c = 2;
		var subPatches = [];
		_VirtualDom_diffHelp(vnode, entry.z, subPatches, index);

		_VirtualDom_pushPatch(localPatches, 9, index, {
			w: subPatches,
			A: entry
		});

		return;
	}

	// this key has already been removed or moved, a duplicate!
	_VirtualDom_removeNode(changes, localPatches, key + _VirtualDom_POSTFIX, vnode, index);
}



// ADD DOM NODES
//
// Each DOM node has an "index" assigned in order of traversal. It is important
// to minimize our crawl over the actual DOM, so these indexes (along with the
// descendantsCount of virtual nodes) let us skip touching entire subtrees of
// the DOM if we know there are no patches there.


function _VirtualDom_addDomNodes(domNode, vNode, patches, eventNode)
{
	_VirtualDom_addDomNodesHelp(domNode, vNode, patches, 0, 0, vNode.b, eventNode);
}


// assumes `patches` is non-empty and indexes increase monotonically.
function _VirtualDom_addDomNodesHelp(domNode, vNode, patches, i, low, high, eventNode)
{
	var patch = patches[i];
	var index = patch.r;

	while (index === low)
	{
		var patchType = patch.$;

		if (patchType === 1)
		{
			_VirtualDom_addDomNodes(domNode, vNode.k, patch.s, eventNode);
		}
		else if (patchType === 8)
		{
			patch.t = domNode;
			patch.u = eventNode;

			var subPatches = patch.s.w;
			if (subPatches.length > 0)
			{
				_VirtualDom_addDomNodesHelp(domNode, vNode, subPatches, 0, low, high, eventNode);
			}
		}
		else if (patchType === 9)
		{
			patch.t = domNode;
			patch.u = eventNode;

			var data = patch.s;
			if (data)
			{
				data.A.s = domNode;
				var subPatches = data.w;
				if (subPatches.length > 0)
				{
					_VirtualDom_addDomNodesHelp(domNode, vNode, subPatches, 0, low, high, eventNode);
				}
			}
		}
		else
		{
			patch.t = domNode;
			patch.u = eventNode;
		}

		i++;

		if (!(patch = patches[i]) || (index = patch.r) > high)
		{
			return i;
		}
	}

	var tag = vNode.$;

	if (tag === 4)
	{
		var subNode = vNode.k;

		while (subNode.$ === 4)
		{
			subNode = subNode.k;
		}

		return _VirtualDom_addDomNodesHelp(domNode, subNode, patches, i, low + 1, high, domNode.elm_event_node_ref);
	}

	// tag must be 1 or 2 at this point

	var vKids = vNode.e;
	var childNodes = domNode.childNodes;
	for (var j = 0; j < vKids.length; j++)
	{
		low++;
		var vKid = tag === 1 ? vKids[j] : vKids[j].b;
		var nextLow = low + (vKid.b || 0);
		if (low <= index && index <= nextLow)
		{
			i = _VirtualDom_addDomNodesHelp(childNodes[j], vKid, patches, i, low, nextLow, eventNode);
			if (!(patch = patches[i]) || (index = patch.r) > high)
			{
				return i;
			}
		}
		low = nextLow;
	}
	return i;
}



// APPLY PATCHES


function _VirtualDom_applyPatches(rootDomNode, oldVirtualNode, patches, eventNode)
{
	if (patches.length === 0)
	{
		return rootDomNode;
	}

	_VirtualDom_addDomNodes(rootDomNode, oldVirtualNode, patches, eventNode);
	return _VirtualDom_applyPatchesHelp(rootDomNode, patches);
}

function _VirtualDom_applyPatchesHelp(rootDomNode, patches)
{
	for (var i = 0; i < patches.length; i++)
	{
		var patch = patches[i];
		var localDomNode = patch.t
		var newNode = _VirtualDom_applyPatch(localDomNode, patch);
		if (localDomNode === rootDomNode)
		{
			rootDomNode = newNode;
		}
	}
	return rootDomNode;
}

function _VirtualDom_applyPatch(domNode, patch)
{
	switch (patch.$)
	{
		case 0:
			return _VirtualDom_applyPatchRedraw(domNode, patch.s, patch.u);

		case 4:
			_VirtualDom_applyFacts(domNode, patch.u, patch.s);
			return domNode;

		case 3:
			domNode.replaceData(0, domNode.length, patch.s);
			return domNode;

		case 1:
			return _VirtualDom_applyPatchesHelp(domNode, patch.s);

		case 2:
			if (domNode.elm_event_node_ref)
			{
				domNode.elm_event_node_ref.j = patch.s;
			}
			else
			{
				domNode.elm_event_node_ref = { j: patch.s, p: patch.u };
			}
			return domNode;

		case 6:
			var data = patch.s;
			for (var i = 0; i < data.i; i++)
			{
				domNode.removeChild(domNode.childNodes[data.v]);
			}
			return domNode;

		case 7:
			var data = patch.s;
			var kids = data.e;
			var i = data.v;
			var theEnd = domNode.childNodes[i];
			for (; i < kids.length; i++)
			{
				domNode.insertBefore(_VirtualDom_render(kids[i], patch.u), theEnd);
			}
			return domNode;

		case 9:
			var data = patch.s;
			if (!data)
			{
				domNode.parentNode.removeChild(domNode);
				return domNode;
			}
			var entry = data.A;
			if (typeof entry.r !== 'undefined')
			{
				domNode.parentNode.removeChild(domNode);
			}
			entry.s = _VirtualDom_applyPatchesHelp(domNode, data.w);
			return domNode;

		case 8:
			return _VirtualDom_applyPatchReorder(domNode, patch);

		case 5:
			return patch.s(domNode);

		default:
			_Debug_crash(10); // 'Ran into an unknown patch!'
	}
}


function _VirtualDom_applyPatchRedraw(domNode, vNode, eventNode)
{
	var parentNode = domNode.parentNode;
	var newNode = _VirtualDom_render(vNode, eventNode);

	if (!newNode.elm_event_node_ref)
	{
		newNode.elm_event_node_ref = domNode.elm_event_node_ref;
	}

	if (parentNode && newNode !== domNode)
	{
		parentNode.replaceChild(newNode, domNode);
	}
	return newNode;
}


function _VirtualDom_applyPatchReorder(domNode, patch)
{
	var data = patch.s;

	// remove end inserts
	var frag = _VirtualDom_applyPatchReorderEndInsertsHelp(data.y, patch);

	// removals
	domNode = _VirtualDom_applyPatchesHelp(domNode, data.w);

	// inserts
	var inserts = data.x;
	for (var i = 0; i < inserts.length; i++)
	{
		var insert = inserts[i];
		var entry = insert.A;
		var node = entry.c === 2
			? entry.s
			: _VirtualDom_render(entry.z, patch.u);
		domNode.insertBefore(node, domNode.childNodes[insert.r]);
	}

	// add end inserts
	if (frag)
	{
		_VirtualDom_appendChild(domNode, frag);
	}

	return domNode;
}


function _VirtualDom_applyPatchReorderEndInsertsHelp(endInserts, patch)
{
	if (!endInserts)
	{
		return;
	}

	var frag = _VirtualDom_doc.createDocumentFragment();
	for (var i = 0; i < endInserts.length; i++)
	{
		var insert = endInserts[i];
		var entry = insert.A;
		_VirtualDom_appendChild(frag, entry.c === 2
			? entry.s
			: _VirtualDom_render(entry.z, patch.u)
		);
	}
	return frag;
}


function _VirtualDom_virtualize(node)
{
	// TEXT NODES

	if (node.nodeType === 3)
	{
		return _VirtualDom_text(node.textContent);
	}


	// WEIRD NODES

	if (node.nodeType !== 1)
	{
		return _VirtualDom_text('');
	}


	// ELEMENT NODES

	var attrList = _List_Nil;
	var attrs = node.attributes;
	for (var i = attrs.length; i--; )
	{
		var attr = attrs[i];
		var name = attr.name;
		var value = attr.value;
		attrList = _List_Cons( A2(_VirtualDom_attribute, name, value), attrList );
	}

	var tag = node.tagName.toLowerCase();
	var kidList = _List_Nil;
	var kids = node.childNodes;

	for (var i = kids.length; i--; )
	{
		kidList = _List_Cons(_VirtualDom_virtualize(kids[i]), kidList);
	}
	return A3(_VirtualDom_node, tag, attrList, kidList);
}

function _VirtualDom_dekey(keyedNode)
{
	var keyedKids = keyedNode.e;
	var len = keyedKids.length;
	var kids = new Array(len);
	for (var i = 0; i < len; i++)
	{
		kids[i] = keyedKids[i].b;
	}

	return {
		$: 1,
		c: keyedNode.c,
		d: keyedNode.d,
		e: kids,
		f: keyedNode.f,
		b: keyedNode.b
	};
}




// ELEMENT


var _Debugger_element;

var _Browser_element = _Debugger_element || F4(function(impl, flagDecoder, debugMetadata, args)
{
	return _Platform_initialize(
		flagDecoder,
		args,
		impl.init,
		impl.update,
		impl.subscriptions,
		function(sendToApp, initialModel) {
			var view = impl.view;
			/**_UNUSED/
			var domNode = args['node'];
			//*/
			/**/
			var domNode = args && args['node'] ? args['node'] : _Debug_crash(0);
			//*/
			var currNode = _VirtualDom_virtualize(domNode);

			return _Browser_makeAnimator(initialModel, function(model)
			{
				var nextNode = view(model);
				var patches = _VirtualDom_diff(currNode, nextNode);
				domNode = _VirtualDom_applyPatches(domNode, currNode, patches, sendToApp);
				currNode = nextNode;
			});
		}
	);
});



// DOCUMENT


var _Debugger_document;

var _Browser_document = _Debugger_document || F4(function(impl, flagDecoder, debugMetadata, args)
{
	return _Platform_initialize(
		flagDecoder,
		args,
		impl.init,
		impl.update,
		impl.subscriptions,
		function(sendToApp, initialModel) {
			var divertHrefToApp = impl.setup && impl.setup(sendToApp)
			var view = impl.view;
			var title = _VirtualDom_doc.title;
			var bodyNode = _VirtualDom_doc.body;
			var currNode = _VirtualDom_virtualize(bodyNode);
			return _Browser_makeAnimator(initialModel, function(model)
			{
				_VirtualDom_divertHrefToApp = divertHrefToApp;
				var doc = view(model);
				var nextNode = _VirtualDom_node('body')(_List_Nil)(doc.body);
				var patches = _VirtualDom_diff(currNode, nextNode);
				bodyNode = _VirtualDom_applyPatches(bodyNode, currNode, patches, sendToApp);
				currNode = nextNode;
				_VirtualDom_divertHrefToApp = 0;
				(title !== doc.title) && (_VirtualDom_doc.title = title = doc.title);
			});
		}
	);
});



// ANIMATION


var _Browser_cancelAnimationFrame =
	typeof cancelAnimationFrame !== 'undefined'
		? cancelAnimationFrame
		: function(id) { clearTimeout(id); };

var _Browser_requestAnimationFrame =
	typeof requestAnimationFrame !== 'undefined'
		? requestAnimationFrame
		: function(callback) { return setTimeout(callback, 1000 / 60); };


function _Browser_makeAnimator(model, draw)
{
	draw(model);

	var state = 0;

	function updateIfNeeded()
	{
		state = state === 1
			? 0
			: ( _Browser_requestAnimationFrame(updateIfNeeded), draw(model), 1 );
	}

	return function(nextModel, isSync)
	{
		model = nextModel;

		isSync
			? ( draw(model),
				state === 2 && (state = 1)
				)
			: ( state === 0 && _Browser_requestAnimationFrame(updateIfNeeded),
				state = 2
				);
	};
}



// APPLICATION


function _Browser_application(impl)
{
	var onUrlChange = impl.onUrlChange;
	var onUrlRequest = impl.onUrlRequest;
	var key = function() { key.a(onUrlChange(_Browser_getUrl())); };

	return _Browser_document({
		setup: function(sendToApp)
		{
			key.a = sendToApp;
			_Browser_window.addEventListener('popstate', key);
			_Browser_window.navigator.userAgent.indexOf('Trident') < 0 || _Browser_window.addEventListener('hashchange', key);

			return F2(function(domNode, event)
			{
				if (!event.ctrlKey && !event.metaKey && !event.shiftKey && event.button < 1 && !domNode.target && !domNode.hasAttribute('download'))
				{
					event.preventDefault();
					var href = domNode.href;
					var curr = _Browser_getUrl();
					var next = $elm$url$Url$fromString(href).a;
					sendToApp(onUrlRequest(
						(next
							&& curr.protocol === next.protocol
							&& curr.host === next.host
							&& curr.port_.a === next.port_.a
						)
							? $elm$browser$Browser$Internal(next)
							: $elm$browser$Browser$External(href)
					));
				}
			});
		},
		init: function(flags)
		{
			return A3(impl.init, flags, _Browser_getUrl(), key);
		},
		view: impl.view,
		update: impl.update,
		subscriptions: impl.subscriptions
	});
}

function _Browser_getUrl()
{
	return $elm$url$Url$fromString(_VirtualDom_doc.location.href).a || _Debug_crash(1);
}

var _Browser_go = F2(function(key, n)
{
	return A2($elm$core$Task$perform, $elm$core$Basics$never, _Scheduler_binding(function() {
		n && history.go(n);
		key();
	}));
});

var _Browser_pushUrl = F2(function(key, url)
{
	return A2($elm$core$Task$perform, $elm$core$Basics$never, _Scheduler_binding(function() {
		history.pushState({}, '', url);
		key();
	}));
});

var _Browser_replaceUrl = F2(function(key, url)
{
	return A2($elm$core$Task$perform, $elm$core$Basics$never, _Scheduler_binding(function() {
		history.replaceState({}, '', url);
		key();
	}));
});



// GLOBAL EVENTS


var _Browser_fakeNode = { addEventListener: function() {}, removeEventListener: function() {} };
var _Browser_doc = typeof document !== 'undefined' ? document : _Browser_fakeNode;
var _Browser_window = typeof window !== 'undefined' ? window : _Browser_fakeNode;

var _Browser_on = F3(function(node, eventName, sendToSelf)
{
	return _Scheduler_spawn(_Scheduler_binding(function(callback)
	{
		function handler(event)	{ _Scheduler_rawSpawn(sendToSelf(event)); }
		node.addEventListener(eventName, handler, _VirtualDom_passiveSupported && { passive: true });
		return function() { node.removeEventListener(eventName, handler); };
	}));
});

var _Browser_decodeEvent = F2(function(decoder, event)
{
	var result = _Json_runHelp(decoder, event);
	return $elm$core$Result$isOk(result) ? $elm$core$Maybe$Just(result.a) : $elm$core$Maybe$Nothing;
});



// PAGE VISIBILITY


function _Browser_visibilityInfo()
{
	return (typeof _VirtualDom_doc.hidden !== 'undefined')
		? { hidden: 'hidden', change: 'visibilitychange' }
		:
	(typeof _VirtualDom_doc.mozHidden !== 'undefined')
		? { hidden: 'mozHidden', change: 'mozvisibilitychange' }
		:
	(typeof _VirtualDom_doc.msHidden !== 'undefined')
		? { hidden: 'msHidden', change: 'msvisibilitychange' }
		:
	(typeof _VirtualDom_doc.webkitHidden !== 'undefined')
		? { hidden: 'webkitHidden', change: 'webkitvisibilitychange' }
		: { hidden: 'hidden', change: 'visibilitychange' };
}



// ANIMATION FRAMES


function _Browser_rAF()
{
	return _Scheduler_binding(function(callback)
	{
		var id = _Browser_requestAnimationFrame(function() {
			callback(_Scheduler_succeed(Date.now()));
		});

		return function() {
			_Browser_cancelAnimationFrame(id);
		};
	});
}


function _Browser_now()
{
	return _Scheduler_binding(function(callback)
	{
		callback(_Scheduler_succeed(Date.now()));
	});
}



// DOM STUFF


function _Browser_withNode(id, doStuff)
{
	return _Scheduler_binding(function(callback)
	{
		_Browser_requestAnimationFrame(function() {
			var node = document.getElementById(id);
			callback(node
				? _Scheduler_succeed(doStuff(node))
				: _Scheduler_fail($elm$browser$Browser$Dom$NotFound(id))
			);
		});
	});
}


function _Browser_withWindow(doStuff)
{
	return _Scheduler_binding(function(callback)
	{
		_Browser_requestAnimationFrame(function() {
			callback(_Scheduler_succeed(doStuff()));
		});
	});
}


// FOCUS and BLUR


var _Browser_call = F2(function(functionName, id)
{
	return _Browser_withNode(id, function(node) {
		node[functionName]();
		return _Utils_Tuple0;
	});
});



// WINDOW VIEWPORT


function _Browser_getViewport()
{
	return {
		scene: _Browser_getScene(),
		viewport: {
			x: _Browser_window.pageXOffset,
			y: _Browser_window.pageYOffset,
			width: _Browser_doc.documentElement.clientWidth,
			height: _Browser_doc.documentElement.clientHeight
		}
	};
}

function _Browser_getScene()
{
	var body = _Browser_doc.body;
	var elem = _Browser_doc.documentElement;
	return {
		width: Math.max(body.scrollWidth, body.offsetWidth, elem.scrollWidth, elem.offsetWidth, elem.clientWidth),
		height: Math.max(body.scrollHeight, body.offsetHeight, elem.scrollHeight, elem.offsetHeight, elem.clientHeight)
	};
}

var _Browser_setViewport = F2(function(x, y)
{
	return _Browser_withWindow(function()
	{
		_Browser_window.scroll(x, y);
		return _Utils_Tuple0;
	});
});



// ELEMENT VIEWPORT


function _Browser_getViewportOf(id)
{
	return _Browser_withNode(id, function(node)
	{
		return {
			scene: {
				width: node.scrollWidth,
				height: node.scrollHeight
			},
			viewport: {
				x: node.scrollLeft,
				y: node.scrollTop,
				width: node.clientWidth,
				height: node.clientHeight
			}
		};
	});
}


var _Browser_setViewportOf = F3(function(id, x, y)
{
	return _Browser_withNode(id, function(node)
	{
		node.scrollLeft = x;
		node.scrollTop = y;
		return _Utils_Tuple0;
	});
});



// ELEMENT


function _Browser_getElement(id)
{
	return _Browser_withNode(id, function(node)
	{
		var rect = node.getBoundingClientRect();
		var x = _Browser_window.pageXOffset;
		var y = _Browser_window.pageYOffset;
		return {
			scene: _Browser_getScene(),
			viewport: {
				x: x,
				y: y,
				width: _Browser_doc.documentElement.clientWidth,
				height: _Browser_doc.documentElement.clientHeight
			},
			element: {
				x: x + rect.left,
				y: y + rect.top,
				width: rect.width,
				height: rect.height
			}
		};
	});
}



// LOAD and RELOAD


function _Browser_reload(skipCache)
{
	return A2($elm$core$Task$perform, $elm$core$Basics$never, _Scheduler_binding(function(callback)
	{
		_VirtualDom_doc.location.reload(skipCache);
	}));
}

function _Browser_load(url)
{
	return A2($elm$core$Task$perform, $elm$core$Basics$never, _Scheduler_binding(function(callback)
	{
		try
		{
			_Browser_window.location = url;
		}
		catch(err)
		{
			// Only Firefox can throw a NS_ERROR_MALFORMED_URI exception here.
			// Other browsers reload the page, so let's be consistent about that.
			_VirtualDom_doc.location.reload(false);
		}
	}));
}



// SEND REQUEST

var _Http_toTask = F3(function(router, toTask, request)
{
	return _Scheduler_binding(function(callback)
	{
		function done(response) {
			callback(toTask(request.expect.a(response)));
		}

		var xhr = new XMLHttpRequest();
		xhr.addEventListener('error', function() { done($elm$http$Http$NetworkError_); });
		xhr.addEventListener('timeout', function() { done($elm$http$Http$Timeout_); });
		xhr.addEventListener('load', function() { done(_Http_toResponse(request.expect.b, xhr)); });
		$elm$core$Maybe$isJust(request.tracker) && _Http_track(router, xhr, request.tracker.a);

		try {
			xhr.open(request.method, request.url, true);
		} catch (e) {
			return done($elm$http$Http$BadUrl_(request.url));
		}

		_Http_configureRequest(xhr, request);

		request.body.a && xhr.setRequestHeader('Content-Type', request.body.a);
		xhr.send(request.body.b);

		return function() { xhr.c = true; xhr.abort(); };
	});
});


// CONFIGURE

function _Http_configureRequest(xhr, request)
{
	for (var headers = request.headers; headers.b; headers = headers.b) // WHILE_CONS
	{
		xhr.setRequestHeader(headers.a.a, headers.a.b);
	}
	xhr.timeout = request.timeout.a || 0;
	xhr.responseType = request.expect.d;
	xhr.withCredentials = request.allowCookiesFromOtherDomains;
}


// RESPONSES

function _Http_toResponse(toBody, xhr)
{
	return A2(
		200 <= xhr.status && xhr.status < 300 ? $elm$http$Http$GoodStatus_ : $elm$http$Http$BadStatus_,
		_Http_toMetadata(xhr),
		toBody(xhr.response)
	);
}


// METADATA

function _Http_toMetadata(xhr)
{
	return {
		url: xhr.responseURL,
		statusCode: xhr.status,
		statusText: xhr.statusText,
		headers: _Http_parseHeaders(xhr.getAllResponseHeaders())
	};
}


// HEADERS

function _Http_parseHeaders(rawHeaders)
{
	if (!rawHeaders)
	{
		return $elm$core$Dict$empty;
	}

	var headers = $elm$core$Dict$empty;
	var headerPairs = rawHeaders.split('\r\n');
	for (var i = headerPairs.length; i--; )
	{
		var headerPair = headerPairs[i];
		var index = headerPair.indexOf(': ');
		if (index > 0)
		{
			var key = headerPair.substring(0, index);
			var value = headerPair.substring(index + 2);

			headers = A3($elm$core$Dict$update, key, function(oldValue) {
				return $elm$core$Maybe$Just($elm$core$Maybe$isJust(oldValue)
					? value + ', ' + oldValue.a
					: value
				);
			}, headers);
		}
	}
	return headers;
}


// EXPECT

var _Http_expect = F3(function(type, toBody, toValue)
{
	return {
		$: 0,
		d: type,
		b: toBody,
		a: toValue
	};
});

var _Http_mapExpect = F2(function(func, expect)
{
	return {
		$: 0,
		d: expect.d,
		b: expect.b,
		a: function(x) { return func(expect.a(x)); }
	};
});

function _Http_toDataView(arrayBuffer)
{
	return new DataView(arrayBuffer);
}


// BODY and PARTS

var _Http_emptyBody = { $: 0 };
var _Http_pair = F2(function(a, b) { return { $: 0, a: a, b: b }; });

function _Http_toFormData(parts)
{
	for (var formData = new FormData(); parts.b; parts = parts.b) // WHILE_CONS
	{
		var part = parts.a;
		formData.append(part.a, part.b);
	}
	return formData;
}

var _Http_bytesToBlob = F2(function(mime, bytes)
{
	return new Blob([bytes], { type: mime });
});


// PROGRESS

function _Http_track(router, xhr, tracker)
{
	// TODO check out lengthComputable on loadstart event

	xhr.upload.addEventListener('progress', function(event) {
		if (xhr.c) { return; }
		_Scheduler_rawSpawn(A2($elm$core$Platform$sendToSelf, router, _Utils_Tuple2(tracker, $elm$http$Http$Sending({
			sent: event.loaded,
			size: event.total
		}))));
	});
	xhr.addEventListener('progress', function(event) {
		if (xhr.c) { return; }
		_Scheduler_rawSpawn(A2($elm$core$Platform$sendToSelf, router, _Utils_Tuple2(tracker, $elm$http$Http$Receiving({
			received: event.loaded,
			size: event.lengthComputable ? $elm$core$Maybe$Just(event.total) : $elm$core$Maybe$Nothing
		}))));
	});
}

function _Url_percentEncode(string)
{
	return encodeURIComponent(string);
}

function _Url_percentDecode(string)
{
	try
	{
		return $elm$core$Maybe$Just(decodeURIComponent(string));
	}
	catch (e)
	{
		return $elm$core$Maybe$Nothing;
	}
}


function _Time_now(millisToPosix)
{
	return _Scheduler_binding(function(callback)
	{
		callback(_Scheduler_succeed(millisToPosix(Date.now())));
	});
}

var _Time_setInterval = F2(function(interval, task)
{
	return _Scheduler_binding(function(callback)
	{
		var id = setInterval(function() { _Scheduler_rawSpawn(task); }, interval);
		return function() { clearInterval(id); };
	});
});

function _Time_here()
{
	return _Scheduler_binding(function(callback)
	{
		callback(_Scheduler_succeed(
			A2($elm$time$Time$customZone, -(new Date().getTimezoneOffset()), _List_Nil)
		));
	});
}


function _Time_getZoneName()
{
	return _Scheduler_binding(function(callback)
	{
		try
		{
			var name = $elm$time$Time$Name(Intl.DateTimeFormat().resolvedOptions().timeZone);
		}
		catch (e)
		{
			var name = $elm$time$Time$Offset(new Date().getTimezoneOffset());
		}
		callback(_Scheduler_succeed(name));
	});
}



// DECODER

var _File_decoder = _Json_decodePrim(function(value) {
	// NOTE: checks if `File` exists in case this is run on node
	return (typeof File !== 'undefined' && value instanceof File)
		? $elm$core$Result$Ok(value)
		: _Json_expecting('a FILE', value);
});


// METADATA

function _File_name(file) { return file.name; }
function _File_mime(file) { return file.type; }
function _File_size(file) { return file.size; }

function _File_lastModified(file)
{
	return $elm$time$Time$millisToPosix(file.lastModified);
}


// DOWNLOAD

var _File_downloadNode;

function _File_getDownloadNode()
{
	return _File_downloadNode || (_File_downloadNode = document.createElement('a'));
}

var _File_download = F3(function(name, mime, content)
{
	return _Scheduler_binding(function(callback)
	{
		var blob = new Blob([content], {type: mime});

		// for IE10+
		if (navigator.msSaveOrOpenBlob)
		{
			navigator.msSaveOrOpenBlob(blob, name);
			return;
		}

		// for HTML5
		var node = _File_getDownloadNode();
		var objectUrl = URL.createObjectURL(blob);
		node.href = objectUrl;
		node.download = name;
		_File_click(node);
		URL.revokeObjectURL(objectUrl);
	});
});

function _File_downloadUrl(href)
{
	return _Scheduler_binding(function(callback)
	{
		var node = _File_getDownloadNode();
		node.href = href;
		node.download = '';
		node.origin === location.origin || (node.target = '_blank');
		_File_click(node);
	});
}


// IE COMPATIBILITY

function _File_makeBytesSafeForInternetExplorer(bytes)
{
	// only needed by IE10 and IE11 to fix https://github.com/elm/file/issues/10
	// all other browsers can just run `new Blob([bytes])` directly with no problem
	//
	return new Uint8Array(bytes.buffer, bytes.byteOffset, bytes.byteLength);
}

function _File_click(node)
{
	// only needed by IE10 and IE11 to fix https://github.com/elm/file/issues/11
	// all other browsers have MouseEvent and do not need this conditional stuff
	//
	if (typeof MouseEvent === 'function')
	{
		node.dispatchEvent(new MouseEvent('click'));
	}
	else
	{
		var event = document.createEvent('MouseEvents');
		event.initMouseEvent('click', true, true, window, 0, 0, 0, 0, 0, false, false, false, false, 0, null);
		document.body.appendChild(node);
		node.dispatchEvent(event);
		document.body.removeChild(node);
	}
}


// UPLOAD

var _File_node;

function _File_uploadOne(mimes)
{
	return _Scheduler_binding(function(callback)
	{
		_File_node = document.createElement('input');
		_File_node.type = 'file';
		_File_node.accept = A2($elm$core$String$join, ',', mimes);
		_File_node.addEventListener('change', function(event)
		{
			callback(_Scheduler_succeed(event.target.files[0]));
		});
		_File_click(_File_node);
	});
}

function _File_uploadOneOrMore(mimes)
{
	return _Scheduler_binding(function(callback)
	{
		_File_node = document.createElement('input');
		_File_node.type = 'file';
		_File_node.multiple = true;
		_File_node.accept = A2($elm$core$String$join, ',', mimes);
		_File_node.addEventListener('change', function(event)
		{
			var elmFiles = _List_fromArray(event.target.files);
			callback(_Scheduler_succeed(_Utils_Tuple2(elmFiles.a, elmFiles.b)));
		});
		_File_click(_File_node);
	});
}


// CONTENT

function _File_toString(blob)
{
	return _Scheduler_binding(function(callback)
	{
		var reader = new FileReader();
		reader.addEventListener('loadend', function() {
			callback(_Scheduler_succeed(reader.result));
		});
		reader.readAsText(blob);
		return function() { reader.abort(); };
	});
}

function _File_toBytes(blob)
{
	return _Scheduler_binding(function(callback)
	{
		var reader = new FileReader();
		reader.addEventListener('loadend', function() {
			callback(_Scheduler_succeed(new DataView(reader.result)));
		});
		reader.readAsArrayBuffer(blob);
		return function() { reader.abort(); };
	});
}

function _File_toUrl(blob)
{
	return _Scheduler_binding(function(callback)
	{
		var reader = new FileReader();
		reader.addEventListener('loadend', function() {
			callback(_Scheduler_succeed(reader.result));
		});
		reader.readAsDataURL(blob);
		return function() { reader.abort(); };
	});
}

var $author$project$Main$LinkClicked = function (a) {
	return {$: 'LinkClicked', a: a};
};
var $author$project$Main$UrlChanged = function (a) {
	return {$: 'UrlChanged', a: a};
};
var $elm$core$Basics$EQ = {$: 'EQ'};
var $elm$core$Basics$GT = {$: 'GT'};
var $elm$core$Basics$LT = {$: 'LT'};
var $elm$core$List$cons = _List_cons;
var $elm$core$Dict$foldr = F3(
	function (func, acc, t) {
		foldr:
		while (true) {
			if (t.$ === 'RBEmpty_elm_builtin') {
				return acc;
			} else {
				var key = t.b;
				var value = t.c;
				var left = t.d;
				var right = t.e;
				var $temp$func = func,
					$temp$acc = A3(
					func,
					key,
					value,
					A3($elm$core$Dict$foldr, func, acc, right)),
					$temp$t = left;
				func = $temp$func;
				acc = $temp$acc;
				t = $temp$t;
				continue foldr;
			}
		}
	});
var $elm$core$Dict$toList = function (dict) {
	return A3(
		$elm$core$Dict$foldr,
		F3(
			function (key, value, list) {
				return A2(
					$elm$core$List$cons,
					_Utils_Tuple2(key, value),
					list);
			}),
		_List_Nil,
		dict);
};
var $elm$core$Dict$keys = function (dict) {
	return A3(
		$elm$core$Dict$foldr,
		F3(
			function (key, value, keyList) {
				return A2($elm$core$List$cons, key, keyList);
			}),
		_List_Nil,
		dict);
};
var $elm$core$Set$toList = function (_v0) {
	var dict = _v0.a;
	return $elm$core$Dict$keys(dict);
};
var $elm$core$Elm$JsArray$foldr = _JsArray_foldr;
var $elm$core$Array$foldr = F3(
	function (func, baseCase, _v0) {
		var tree = _v0.c;
		var tail = _v0.d;
		var helper = F2(
			function (node, acc) {
				if (node.$ === 'SubTree') {
					var subTree = node.a;
					return A3($elm$core$Elm$JsArray$foldr, helper, acc, subTree);
				} else {
					var values = node.a;
					return A3($elm$core$Elm$JsArray$foldr, func, acc, values);
				}
			});
		return A3(
			$elm$core$Elm$JsArray$foldr,
			helper,
			A3($elm$core$Elm$JsArray$foldr, func, baseCase, tail),
			tree);
	});
var $elm$core$Array$toList = function (array) {
	return A3($elm$core$Array$foldr, $elm$core$List$cons, _List_Nil, array);
};
var $elm$core$Result$Err = function (a) {
	return {$: 'Err', a: a};
};
var $elm$json$Json$Decode$Failure = F2(
	function (a, b) {
		return {$: 'Failure', a: a, b: b};
	});
var $elm$json$Json$Decode$Field = F2(
	function (a, b) {
		return {$: 'Field', a: a, b: b};
	});
var $elm$json$Json$Decode$Index = F2(
	function (a, b) {
		return {$: 'Index', a: a, b: b};
	});
var $elm$core$Result$Ok = function (a) {
	return {$: 'Ok', a: a};
};
var $elm$json$Json$Decode$OneOf = function (a) {
	return {$: 'OneOf', a: a};
};
var $elm$core$Basics$False = {$: 'False'};
var $elm$core$Basics$add = _Basics_add;
var $elm$core$Maybe$Just = function (a) {
	return {$: 'Just', a: a};
};
var $elm$core$Maybe$Nothing = {$: 'Nothing'};
var $elm$core$String$all = _String_all;
var $elm$core$Basics$and = _Basics_and;
var $elm$core$Basics$append = _Utils_append;
var $elm$json$Json$Encode$encode = _Json_encode;
var $elm$core$String$fromInt = _String_fromNumber;
var $elm$core$String$join = F2(
	function (sep, chunks) {
		return A2(
			_String_join,
			sep,
			_List_toArray(chunks));
	});
var $elm$core$String$split = F2(
	function (sep, string) {
		return _List_fromArray(
			A2(_String_split, sep, string));
	});
var $elm$json$Json$Decode$indent = function (str) {
	return A2(
		$elm$core$String$join,
		'\n    ',
		A2($elm$core$String$split, '\n', str));
};
var $elm$core$List$foldl = F3(
	function (func, acc, list) {
		foldl:
		while (true) {
			if (!list.b) {
				return acc;
			} else {
				var x = list.a;
				var xs = list.b;
				var $temp$func = func,
					$temp$acc = A2(func, x, acc),
					$temp$list = xs;
				func = $temp$func;
				acc = $temp$acc;
				list = $temp$list;
				continue foldl;
			}
		}
	});
var $elm$core$List$length = function (xs) {
	return A3(
		$elm$core$List$foldl,
		F2(
			function (_v0, i) {
				return i + 1;
			}),
		0,
		xs);
};
var $elm$core$List$map2 = _List_map2;
var $elm$core$Basics$le = _Utils_le;
var $elm$core$Basics$sub = _Basics_sub;
var $elm$core$List$rangeHelp = F3(
	function (lo, hi, list) {
		rangeHelp:
		while (true) {
			if (_Utils_cmp(lo, hi) < 1) {
				var $temp$lo = lo,
					$temp$hi = hi - 1,
					$temp$list = A2($elm$core$List$cons, hi, list);
				lo = $temp$lo;
				hi = $temp$hi;
				list = $temp$list;
				continue rangeHelp;
			} else {
				return list;
			}
		}
	});
var $elm$core$List$range = F2(
	function (lo, hi) {
		return A3($elm$core$List$rangeHelp, lo, hi, _List_Nil);
	});
var $elm$core$List$indexedMap = F2(
	function (f, xs) {
		return A3(
			$elm$core$List$map2,
			f,
			A2(
				$elm$core$List$range,
				0,
				$elm$core$List$length(xs) - 1),
			xs);
	});
var $elm$core$Char$toCode = _Char_toCode;
var $elm$core$Char$isLower = function (_char) {
	var code = $elm$core$Char$toCode(_char);
	return (97 <= code) && (code <= 122);
};
var $elm$core$Char$isUpper = function (_char) {
	var code = $elm$core$Char$toCode(_char);
	return (code <= 90) && (65 <= code);
};
var $elm$core$Basics$or = _Basics_or;
var $elm$core$Char$isAlpha = function (_char) {
	return $elm$core$Char$isLower(_char) || $elm$core$Char$isUpper(_char);
};
var $elm$core$Char$isDigit = function (_char) {
	var code = $elm$core$Char$toCode(_char);
	return (code <= 57) && (48 <= code);
};
var $elm$core$Char$isAlphaNum = function (_char) {
	return $elm$core$Char$isLower(_char) || ($elm$core$Char$isUpper(_char) || $elm$core$Char$isDigit(_char));
};
var $elm$core$List$reverse = function (list) {
	return A3($elm$core$List$foldl, $elm$core$List$cons, _List_Nil, list);
};
var $elm$core$String$uncons = _String_uncons;
var $elm$json$Json$Decode$errorOneOf = F2(
	function (i, error) {
		return '\n\n(' + ($elm$core$String$fromInt(i + 1) + (') ' + $elm$json$Json$Decode$indent(
			$elm$json$Json$Decode$errorToString(error))));
	});
var $elm$json$Json$Decode$errorToString = function (error) {
	return A2($elm$json$Json$Decode$errorToStringHelp, error, _List_Nil);
};
var $elm$json$Json$Decode$errorToStringHelp = F2(
	function (error, context) {
		errorToStringHelp:
		while (true) {
			switch (error.$) {
				case 'Field':
					var f = error.a;
					var err = error.b;
					var isSimple = function () {
						var _v1 = $elm$core$String$uncons(f);
						if (_v1.$ === 'Nothing') {
							return false;
						} else {
							var _v2 = _v1.a;
							var _char = _v2.a;
							var rest = _v2.b;
							return $elm$core$Char$isAlpha(_char) && A2($elm$core$String$all, $elm$core$Char$isAlphaNum, rest);
						}
					}();
					var fieldName = isSimple ? ('.' + f) : ('[\'' + (f + '\']'));
					var $temp$error = err,
						$temp$context = A2($elm$core$List$cons, fieldName, context);
					error = $temp$error;
					context = $temp$context;
					continue errorToStringHelp;
				case 'Index':
					var i = error.a;
					var err = error.b;
					var indexName = '[' + ($elm$core$String$fromInt(i) + ']');
					var $temp$error = err,
						$temp$context = A2($elm$core$List$cons, indexName, context);
					error = $temp$error;
					context = $temp$context;
					continue errorToStringHelp;
				case 'OneOf':
					var errors = error.a;
					if (!errors.b) {
						return 'Ran into a Json.Decode.oneOf with no possibilities' + function () {
							if (!context.b) {
								return '!';
							} else {
								return ' at json' + A2(
									$elm$core$String$join,
									'',
									$elm$core$List$reverse(context));
							}
						}();
					} else {
						if (!errors.b.b) {
							var err = errors.a;
							var $temp$error = err,
								$temp$context = context;
							error = $temp$error;
							context = $temp$context;
							continue errorToStringHelp;
						} else {
							var starter = function () {
								if (!context.b) {
									return 'Json.Decode.oneOf';
								} else {
									return 'The Json.Decode.oneOf at json' + A2(
										$elm$core$String$join,
										'',
										$elm$core$List$reverse(context));
								}
							}();
							var introduction = starter + (' failed in the following ' + ($elm$core$String$fromInt(
								$elm$core$List$length(errors)) + ' ways:'));
							return A2(
								$elm$core$String$join,
								'\n\n',
								A2(
									$elm$core$List$cons,
									introduction,
									A2($elm$core$List$indexedMap, $elm$json$Json$Decode$errorOneOf, errors)));
						}
					}
				default:
					var msg = error.a;
					var json = error.b;
					var introduction = function () {
						if (!context.b) {
							return 'Problem with the given value:\n\n';
						} else {
							return 'Problem with the value at json' + (A2(
								$elm$core$String$join,
								'',
								$elm$core$List$reverse(context)) + ':\n\n    ');
						}
					}();
					return introduction + ($elm$json$Json$Decode$indent(
						A2($elm$json$Json$Encode$encode, 4, json)) + ('\n\n' + msg));
			}
		}
	});
var $elm$core$Array$branchFactor = 32;
var $elm$core$Array$Array_elm_builtin = F4(
	function (a, b, c, d) {
		return {$: 'Array_elm_builtin', a: a, b: b, c: c, d: d};
	});
var $elm$core$Elm$JsArray$empty = _JsArray_empty;
var $elm$core$Basics$ceiling = _Basics_ceiling;
var $elm$core$Basics$fdiv = _Basics_fdiv;
var $elm$core$Basics$logBase = F2(
	function (base, number) {
		return _Basics_log(number) / _Basics_log(base);
	});
var $elm$core$Basics$toFloat = _Basics_toFloat;
var $elm$core$Array$shiftStep = $elm$core$Basics$ceiling(
	A2($elm$core$Basics$logBase, 2, $elm$core$Array$branchFactor));
var $elm$core$Array$empty = A4($elm$core$Array$Array_elm_builtin, 0, $elm$core$Array$shiftStep, $elm$core$Elm$JsArray$empty, $elm$core$Elm$JsArray$empty);
var $elm$core$Elm$JsArray$initialize = _JsArray_initialize;
var $elm$core$Array$Leaf = function (a) {
	return {$: 'Leaf', a: a};
};
var $elm$core$Basics$apL = F2(
	function (f, x) {
		return f(x);
	});
var $elm$core$Basics$apR = F2(
	function (x, f) {
		return f(x);
	});
var $elm$core$Basics$eq = _Utils_equal;
var $elm$core$Basics$floor = _Basics_floor;
var $elm$core$Elm$JsArray$length = _JsArray_length;
var $elm$core$Basics$gt = _Utils_gt;
var $elm$core$Basics$max = F2(
	function (x, y) {
		return (_Utils_cmp(x, y) > 0) ? x : y;
	});
var $elm$core$Basics$mul = _Basics_mul;
var $elm$core$Array$SubTree = function (a) {
	return {$: 'SubTree', a: a};
};
var $elm$core$Elm$JsArray$initializeFromList = _JsArray_initializeFromList;
var $elm$core$Array$compressNodes = F2(
	function (nodes, acc) {
		compressNodes:
		while (true) {
			var _v0 = A2($elm$core$Elm$JsArray$initializeFromList, $elm$core$Array$branchFactor, nodes);
			var node = _v0.a;
			var remainingNodes = _v0.b;
			var newAcc = A2(
				$elm$core$List$cons,
				$elm$core$Array$SubTree(node),
				acc);
			if (!remainingNodes.b) {
				return $elm$core$List$reverse(newAcc);
			} else {
				var $temp$nodes = remainingNodes,
					$temp$acc = newAcc;
				nodes = $temp$nodes;
				acc = $temp$acc;
				continue compressNodes;
			}
		}
	});
var $elm$core$Tuple$first = function (_v0) {
	var x = _v0.a;
	return x;
};
var $elm$core$Array$treeFromBuilder = F2(
	function (nodeList, nodeListSize) {
		treeFromBuilder:
		while (true) {
			var newNodeSize = $elm$core$Basics$ceiling(nodeListSize / $elm$core$Array$branchFactor);
			if (newNodeSize === 1) {
				return A2($elm$core$Elm$JsArray$initializeFromList, $elm$core$Array$branchFactor, nodeList).a;
			} else {
				var $temp$nodeList = A2($elm$core$Array$compressNodes, nodeList, _List_Nil),
					$temp$nodeListSize = newNodeSize;
				nodeList = $temp$nodeList;
				nodeListSize = $temp$nodeListSize;
				continue treeFromBuilder;
			}
		}
	});
var $elm$core$Array$builderToArray = F2(
	function (reverseNodeList, builder) {
		if (!builder.nodeListSize) {
			return A4(
				$elm$core$Array$Array_elm_builtin,
				$elm$core$Elm$JsArray$length(builder.tail),
				$elm$core$Array$shiftStep,
				$elm$core$Elm$JsArray$empty,
				builder.tail);
		} else {
			var treeLen = builder.nodeListSize * $elm$core$Array$branchFactor;
			var depth = $elm$core$Basics$floor(
				A2($elm$core$Basics$logBase, $elm$core$Array$branchFactor, treeLen - 1));
			var correctNodeList = reverseNodeList ? $elm$core$List$reverse(builder.nodeList) : builder.nodeList;
			var tree = A2($elm$core$Array$treeFromBuilder, correctNodeList, builder.nodeListSize);
			return A4(
				$elm$core$Array$Array_elm_builtin,
				$elm$core$Elm$JsArray$length(builder.tail) + treeLen,
				A2($elm$core$Basics$max, 5, depth * $elm$core$Array$shiftStep),
				tree,
				builder.tail);
		}
	});
var $elm$core$Basics$idiv = _Basics_idiv;
var $elm$core$Basics$lt = _Utils_lt;
var $elm$core$Array$initializeHelp = F5(
	function (fn, fromIndex, len, nodeList, tail) {
		initializeHelp:
		while (true) {
			if (fromIndex < 0) {
				return A2(
					$elm$core$Array$builderToArray,
					false,
					{nodeList: nodeList, nodeListSize: (len / $elm$core$Array$branchFactor) | 0, tail: tail});
			} else {
				var leaf = $elm$core$Array$Leaf(
					A3($elm$core$Elm$JsArray$initialize, $elm$core$Array$branchFactor, fromIndex, fn));
				var $temp$fn = fn,
					$temp$fromIndex = fromIndex - $elm$core$Array$branchFactor,
					$temp$len = len,
					$temp$nodeList = A2($elm$core$List$cons, leaf, nodeList),
					$temp$tail = tail;
				fn = $temp$fn;
				fromIndex = $temp$fromIndex;
				len = $temp$len;
				nodeList = $temp$nodeList;
				tail = $temp$tail;
				continue initializeHelp;
			}
		}
	});
var $elm$core$Basics$remainderBy = _Basics_remainderBy;
var $elm$core$Array$initialize = F2(
	function (len, fn) {
		if (len <= 0) {
			return $elm$core$Array$empty;
		} else {
			var tailLen = len % $elm$core$Array$branchFactor;
			var tail = A3($elm$core$Elm$JsArray$initialize, tailLen, len - tailLen, fn);
			var initialFromIndex = (len - tailLen) - $elm$core$Array$branchFactor;
			return A5($elm$core$Array$initializeHelp, fn, initialFromIndex, len, _List_Nil, tail);
		}
	});
var $elm$core$Basics$True = {$: 'True'};
var $elm$core$Result$isOk = function (result) {
	if (result.$ === 'Ok') {
		return true;
	} else {
		return false;
	}
};
var $elm$json$Json$Decode$map = _Json_map1;
var $elm$json$Json$Decode$map2 = _Json_map2;
var $elm$json$Json$Decode$succeed = _Json_succeed;
var $elm$virtual_dom$VirtualDom$toHandlerInt = function (handler) {
	switch (handler.$) {
		case 'Normal':
			return 0;
		case 'MayStopPropagation':
			return 1;
		case 'MayPreventDefault':
			return 2;
		default:
			return 3;
	}
};
var $elm$browser$Browser$External = function (a) {
	return {$: 'External', a: a};
};
var $elm$browser$Browser$Internal = function (a) {
	return {$: 'Internal', a: a};
};
var $elm$core$Basics$identity = function (x) {
	return x;
};
var $elm$browser$Browser$Dom$NotFound = function (a) {
	return {$: 'NotFound', a: a};
};
var $elm$url$Url$Http = {$: 'Http'};
var $elm$url$Url$Https = {$: 'Https'};
var $elm$url$Url$Url = F6(
	function (protocol, host, port_, path, query, fragment) {
		return {fragment: fragment, host: host, path: path, port_: port_, protocol: protocol, query: query};
	});
var $elm$core$String$contains = _String_contains;
var $elm$core$String$length = _String_length;
var $elm$core$String$slice = _String_slice;
var $elm$core$String$dropLeft = F2(
	function (n, string) {
		return (n < 1) ? string : A3(
			$elm$core$String$slice,
			n,
			$elm$core$String$length(string),
			string);
	});
var $elm$core$String$indexes = _String_indexes;
var $elm$core$String$isEmpty = function (string) {
	return string === '';
};
var $elm$core$String$left = F2(
	function (n, string) {
		return (n < 1) ? '' : A3($elm$core$String$slice, 0, n, string);
	});
var $elm$core$String$toInt = _String_toInt;
var $elm$url$Url$chompBeforePath = F5(
	function (protocol, path, params, frag, str) {
		if ($elm$core$String$isEmpty(str) || A2($elm$core$String$contains, '@', str)) {
			return $elm$core$Maybe$Nothing;
		} else {
			var _v0 = A2($elm$core$String$indexes, ':', str);
			if (!_v0.b) {
				return $elm$core$Maybe$Just(
					A6($elm$url$Url$Url, protocol, str, $elm$core$Maybe$Nothing, path, params, frag));
			} else {
				if (!_v0.b.b) {
					var i = _v0.a;
					var _v1 = $elm$core$String$toInt(
						A2($elm$core$String$dropLeft, i + 1, str));
					if (_v1.$ === 'Nothing') {
						return $elm$core$Maybe$Nothing;
					} else {
						var port_ = _v1;
						return $elm$core$Maybe$Just(
							A6(
								$elm$url$Url$Url,
								protocol,
								A2($elm$core$String$left, i, str),
								port_,
								path,
								params,
								frag));
					}
				} else {
					return $elm$core$Maybe$Nothing;
				}
			}
		}
	});
var $elm$url$Url$chompBeforeQuery = F4(
	function (protocol, params, frag, str) {
		if ($elm$core$String$isEmpty(str)) {
			return $elm$core$Maybe$Nothing;
		} else {
			var _v0 = A2($elm$core$String$indexes, '/', str);
			if (!_v0.b) {
				return A5($elm$url$Url$chompBeforePath, protocol, '/', params, frag, str);
			} else {
				var i = _v0.a;
				return A5(
					$elm$url$Url$chompBeforePath,
					protocol,
					A2($elm$core$String$dropLeft, i, str),
					params,
					frag,
					A2($elm$core$String$left, i, str));
			}
		}
	});
var $elm$url$Url$chompBeforeFragment = F3(
	function (protocol, frag, str) {
		if ($elm$core$String$isEmpty(str)) {
			return $elm$core$Maybe$Nothing;
		} else {
			var _v0 = A2($elm$core$String$indexes, '?', str);
			if (!_v0.b) {
				return A4($elm$url$Url$chompBeforeQuery, protocol, $elm$core$Maybe$Nothing, frag, str);
			} else {
				var i = _v0.a;
				return A4(
					$elm$url$Url$chompBeforeQuery,
					protocol,
					$elm$core$Maybe$Just(
						A2($elm$core$String$dropLeft, i + 1, str)),
					frag,
					A2($elm$core$String$left, i, str));
			}
		}
	});
var $elm$url$Url$chompAfterProtocol = F2(
	function (protocol, str) {
		if ($elm$core$String$isEmpty(str)) {
			return $elm$core$Maybe$Nothing;
		} else {
			var _v0 = A2($elm$core$String$indexes, '#', str);
			if (!_v0.b) {
				return A3($elm$url$Url$chompBeforeFragment, protocol, $elm$core$Maybe$Nothing, str);
			} else {
				var i = _v0.a;
				return A3(
					$elm$url$Url$chompBeforeFragment,
					protocol,
					$elm$core$Maybe$Just(
						A2($elm$core$String$dropLeft, i + 1, str)),
					A2($elm$core$String$left, i, str));
			}
		}
	});
var $elm$core$String$startsWith = _String_startsWith;
var $elm$url$Url$fromString = function (str) {
	return A2($elm$core$String$startsWith, 'http://', str) ? A2(
		$elm$url$Url$chompAfterProtocol,
		$elm$url$Url$Http,
		A2($elm$core$String$dropLeft, 7, str)) : (A2($elm$core$String$startsWith, 'https://', str) ? A2(
		$elm$url$Url$chompAfterProtocol,
		$elm$url$Url$Https,
		A2($elm$core$String$dropLeft, 8, str)) : $elm$core$Maybe$Nothing);
};
var $elm$core$Basics$never = function (_v0) {
	never:
	while (true) {
		var nvr = _v0.a;
		var $temp$_v0 = nvr;
		_v0 = $temp$_v0;
		continue never;
	}
};
var $elm$core$Task$Perform = function (a) {
	return {$: 'Perform', a: a};
};
var $elm$core$Task$succeed = _Scheduler_succeed;
var $elm$core$Task$init = $elm$core$Task$succeed(_Utils_Tuple0);
var $elm$core$List$foldrHelper = F4(
	function (fn, acc, ctr, ls) {
		if (!ls.b) {
			return acc;
		} else {
			var a = ls.a;
			var r1 = ls.b;
			if (!r1.b) {
				return A2(fn, a, acc);
			} else {
				var b = r1.a;
				var r2 = r1.b;
				if (!r2.b) {
					return A2(
						fn,
						a,
						A2(fn, b, acc));
				} else {
					var c = r2.a;
					var r3 = r2.b;
					if (!r3.b) {
						return A2(
							fn,
							a,
							A2(
								fn,
								b,
								A2(fn, c, acc)));
					} else {
						var d = r3.a;
						var r4 = r3.b;
						var res = (ctr > 500) ? A3(
							$elm$core$List$foldl,
							fn,
							acc,
							$elm$core$List$reverse(r4)) : A4($elm$core$List$foldrHelper, fn, acc, ctr + 1, r4);
						return A2(
							fn,
							a,
							A2(
								fn,
								b,
								A2(
									fn,
									c,
									A2(fn, d, res))));
					}
				}
			}
		}
	});
var $elm$core$List$foldr = F3(
	function (fn, acc, ls) {
		return A4($elm$core$List$foldrHelper, fn, acc, 0, ls);
	});
var $elm$core$List$map = F2(
	function (f, xs) {
		return A3(
			$elm$core$List$foldr,
			F2(
				function (x, acc) {
					return A2(
						$elm$core$List$cons,
						f(x),
						acc);
				}),
			_List_Nil,
			xs);
	});
var $elm$core$Task$andThen = _Scheduler_andThen;
var $elm$core$Task$map = F2(
	function (func, taskA) {
		return A2(
			$elm$core$Task$andThen,
			function (a) {
				return $elm$core$Task$succeed(
					func(a));
			},
			taskA);
	});
var $elm$core$Task$map2 = F3(
	function (func, taskA, taskB) {
		return A2(
			$elm$core$Task$andThen,
			function (a) {
				return A2(
					$elm$core$Task$andThen,
					function (b) {
						return $elm$core$Task$succeed(
							A2(func, a, b));
					},
					taskB);
			},
			taskA);
	});
var $elm$core$Task$sequence = function (tasks) {
	return A3(
		$elm$core$List$foldr,
		$elm$core$Task$map2($elm$core$List$cons),
		$elm$core$Task$succeed(_List_Nil),
		tasks);
};
var $elm$core$Platform$sendToApp = _Platform_sendToApp;
var $elm$core$Task$spawnCmd = F2(
	function (router, _v0) {
		var task = _v0.a;
		return _Scheduler_spawn(
			A2(
				$elm$core$Task$andThen,
				$elm$core$Platform$sendToApp(router),
				task));
	});
var $elm$core$Task$onEffects = F3(
	function (router, commands, state) {
		return A2(
			$elm$core$Task$map,
			function (_v0) {
				return _Utils_Tuple0;
			},
			$elm$core$Task$sequence(
				A2(
					$elm$core$List$map,
					$elm$core$Task$spawnCmd(router),
					commands)));
	});
var $elm$core$Task$onSelfMsg = F3(
	function (_v0, _v1, _v2) {
		return $elm$core$Task$succeed(_Utils_Tuple0);
	});
var $elm$core$Task$cmdMap = F2(
	function (tagger, _v0) {
		var task = _v0.a;
		return $elm$core$Task$Perform(
			A2($elm$core$Task$map, tagger, task));
	});
_Platform_effectManagers['Task'] = _Platform_createManager($elm$core$Task$init, $elm$core$Task$onEffects, $elm$core$Task$onSelfMsg, $elm$core$Task$cmdMap);
var $elm$core$Task$command = _Platform_leaf('Task');
var $elm$core$Task$perform = F2(
	function (toMessage, task) {
		return $elm$core$Task$command(
			$elm$core$Task$Perform(
				A2($elm$core$Task$map, toMessage, task)));
	});
var $elm$browser$Browser$application = _Browser_application;
var $author$project$Main$AudioGalleryMsg = function (a) {
	return {$: 'AudioGalleryMsg', a: a};
};
var $author$project$Main$AudioMsg = function (a) {
	return {$: 'AudioMsg', a: a};
};
var $author$project$Main$AuthMsg = function (a) {
	return {$: 'AuthMsg', a: a};
};
var $author$project$Main$BriefGalleryMsg = function (a) {
	return {$: 'BriefGalleryMsg', a: a};
};
var $author$project$Main$CreativeBriefEditorMsg = function (a) {
	return {$: 'CreativeBriefEditorMsg', a: a};
};
var $author$project$Main$GalleryMsg = function (a) {
	return {$: 'GalleryMsg', a: a};
};
var $author$project$Main$ImageGalleryMsg = function (a) {
	return {$: 'ImageGalleryMsg', a: a};
};
var $author$project$Main$ImageMsg = function (a) {
	return {$: 'ImageMsg', a: a};
};
var $author$project$Main$SimulationGalleryMsg = function (a) {
	return {$: 'SimulationGalleryMsg', a: a};
};
var $author$project$Main$Translate = {$: 'Translate'};
var $author$project$Main$VideoMsg = function (a) {
	return {$: 'VideoMsg', a: a};
};
var $author$project$Main$VideoToTextGalleryMsg = function (a) {
	return {$: 'VideoToTextGalleryMsg', a: a};
};
var $author$project$Main$VideoToTextMsg = function (a) {
	return {$: 'VideoToTextMsg', a: a};
};
var $elm$core$Platform$Cmd$batch = _Platform_batch;
var $author$project$Auth$CheckAuthResult = function (a) {
	return {$: 'CheckAuthResult', a: a};
};
var $elm$http$Http$BadStatus_ = F2(
	function (a, b) {
		return {$: 'BadStatus_', a: a, b: b};
	});
var $elm$http$Http$BadUrl_ = function (a) {
	return {$: 'BadUrl_', a: a};
};
var $elm$http$Http$GoodStatus_ = F2(
	function (a, b) {
		return {$: 'GoodStatus_', a: a, b: b};
	});
var $elm$http$Http$NetworkError_ = {$: 'NetworkError_'};
var $elm$http$Http$Receiving = function (a) {
	return {$: 'Receiving', a: a};
};
var $elm$http$Http$Sending = function (a) {
	return {$: 'Sending', a: a};
};
var $elm$http$Http$Timeout_ = {$: 'Timeout_'};
var $elm$core$Dict$RBEmpty_elm_builtin = {$: 'RBEmpty_elm_builtin'};
var $elm$core$Dict$empty = $elm$core$Dict$RBEmpty_elm_builtin;
var $elm$core$Maybe$isJust = function (maybe) {
	if (maybe.$ === 'Just') {
		return true;
	} else {
		return false;
	}
};
var $elm$core$Platform$sendToSelf = _Platform_sendToSelf;
var $elm$core$Basics$compare = _Utils_compare;
var $elm$core$Dict$get = F2(
	function (targetKey, dict) {
		get:
		while (true) {
			if (dict.$ === 'RBEmpty_elm_builtin') {
				return $elm$core$Maybe$Nothing;
			} else {
				var key = dict.b;
				var value = dict.c;
				var left = dict.d;
				var right = dict.e;
				var _v1 = A2($elm$core$Basics$compare, targetKey, key);
				switch (_v1.$) {
					case 'LT':
						var $temp$targetKey = targetKey,
							$temp$dict = left;
						targetKey = $temp$targetKey;
						dict = $temp$dict;
						continue get;
					case 'EQ':
						return $elm$core$Maybe$Just(value);
					default:
						var $temp$targetKey = targetKey,
							$temp$dict = right;
						targetKey = $temp$targetKey;
						dict = $temp$dict;
						continue get;
				}
			}
		}
	});
var $elm$core$Dict$Black = {$: 'Black'};
var $elm$core$Dict$RBNode_elm_builtin = F5(
	function (a, b, c, d, e) {
		return {$: 'RBNode_elm_builtin', a: a, b: b, c: c, d: d, e: e};
	});
var $elm$core$Dict$Red = {$: 'Red'};
var $elm$core$Dict$balance = F5(
	function (color, key, value, left, right) {
		if ((right.$ === 'RBNode_elm_builtin') && (right.a.$ === 'Red')) {
			var _v1 = right.a;
			var rK = right.b;
			var rV = right.c;
			var rLeft = right.d;
			var rRight = right.e;
			if ((left.$ === 'RBNode_elm_builtin') && (left.a.$ === 'Red')) {
				var _v3 = left.a;
				var lK = left.b;
				var lV = left.c;
				var lLeft = left.d;
				var lRight = left.e;
				return A5(
					$elm$core$Dict$RBNode_elm_builtin,
					$elm$core$Dict$Red,
					key,
					value,
					A5($elm$core$Dict$RBNode_elm_builtin, $elm$core$Dict$Black, lK, lV, lLeft, lRight),
					A5($elm$core$Dict$RBNode_elm_builtin, $elm$core$Dict$Black, rK, rV, rLeft, rRight));
			} else {
				return A5(
					$elm$core$Dict$RBNode_elm_builtin,
					color,
					rK,
					rV,
					A5($elm$core$Dict$RBNode_elm_builtin, $elm$core$Dict$Red, key, value, left, rLeft),
					rRight);
			}
		} else {
			if ((((left.$ === 'RBNode_elm_builtin') && (left.a.$ === 'Red')) && (left.d.$ === 'RBNode_elm_builtin')) && (left.d.a.$ === 'Red')) {
				var _v5 = left.a;
				var lK = left.b;
				var lV = left.c;
				var _v6 = left.d;
				var _v7 = _v6.a;
				var llK = _v6.b;
				var llV = _v6.c;
				var llLeft = _v6.d;
				var llRight = _v6.e;
				var lRight = left.e;
				return A5(
					$elm$core$Dict$RBNode_elm_builtin,
					$elm$core$Dict$Red,
					lK,
					lV,
					A5($elm$core$Dict$RBNode_elm_builtin, $elm$core$Dict$Black, llK, llV, llLeft, llRight),
					A5($elm$core$Dict$RBNode_elm_builtin, $elm$core$Dict$Black, key, value, lRight, right));
			} else {
				return A5($elm$core$Dict$RBNode_elm_builtin, color, key, value, left, right);
			}
		}
	});
var $elm$core$Dict$insertHelp = F3(
	function (key, value, dict) {
		if (dict.$ === 'RBEmpty_elm_builtin') {
			return A5($elm$core$Dict$RBNode_elm_builtin, $elm$core$Dict$Red, key, value, $elm$core$Dict$RBEmpty_elm_builtin, $elm$core$Dict$RBEmpty_elm_builtin);
		} else {
			var nColor = dict.a;
			var nKey = dict.b;
			var nValue = dict.c;
			var nLeft = dict.d;
			var nRight = dict.e;
			var _v1 = A2($elm$core$Basics$compare, key, nKey);
			switch (_v1.$) {
				case 'LT':
					return A5(
						$elm$core$Dict$balance,
						nColor,
						nKey,
						nValue,
						A3($elm$core$Dict$insertHelp, key, value, nLeft),
						nRight);
				case 'EQ':
					return A5($elm$core$Dict$RBNode_elm_builtin, nColor, nKey, value, nLeft, nRight);
				default:
					return A5(
						$elm$core$Dict$balance,
						nColor,
						nKey,
						nValue,
						nLeft,
						A3($elm$core$Dict$insertHelp, key, value, nRight));
			}
		}
	});
var $elm$core$Dict$insert = F3(
	function (key, value, dict) {
		var _v0 = A3($elm$core$Dict$insertHelp, key, value, dict);
		if ((_v0.$ === 'RBNode_elm_builtin') && (_v0.a.$ === 'Red')) {
			var _v1 = _v0.a;
			var k = _v0.b;
			var v = _v0.c;
			var l = _v0.d;
			var r = _v0.e;
			return A5($elm$core$Dict$RBNode_elm_builtin, $elm$core$Dict$Black, k, v, l, r);
		} else {
			var x = _v0;
			return x;
		}
	});
var $elm$core$Dict$getMin = function (dict) {
	getMin:
	while (true) {
		if ((dict.$ === 'RBNode_elm_builtin') && (dict.d.$ === 'RBNode_elm_builtin')) {
			var left = dict.d;
			var $temp$dict = left;
			dict = $temp$dict;
			continue getMin;
		} else {
			return dict;
		}
	}
};
var $elm$core$Dict$moveRedLeft = function (dict) {
	if (((dict.$ === 'RBNode_elm_builtin') && (dict.d.$ === 'RBNode_elm_builtin')) && (dict.e.$ === 'RBNode_elm_builtin')) {
		if ((dict.e.d.$ === 'RBNode_elm_builtin') && (dict.e.d.a.$ === 'Red')) {
			var clr = dict.a;
			var k = dict.b;
			var v = dict.c;
			var _v1 = dict.d;
			var lClr = _v1.a;
			var lK = _v1.b;
			var lV = _v1.c;
			var lLeft = _v1.d;
			var lRight = _v1.e;
			var _v2 = dict.e;
			var rClr = _v2.a;
			var rK = _v2.b;
			var rV = _v2.c;
			var rLeft = _v2.d;
			var _v3 = rLeft.a;
			var rlK = rLeft.b;
			var rlV = rLeft.c;
			var rlL = rLeft.d;
			var rlR = rLeft.e;
			var rRight = _v2.e;
			return A5(
				$elm$core$Dict$RBNode_elm_builtin,
				$elm$core$Dict$Red,
				rlK,
				rlV,
				A5(
					$elm$core$Dict$RBNode_elm_builtin,
					$elm$core$Dict$Black,
					k,
					v,
					A5($elm$core$Dict$RBNode_elm_builtin, $elm$core$Dict$Red, lK, lV, lLeft, lRight),
					rlL),
				A5($elm$core$Dict$RBNode_elm_builtin, $elm$core$Dict$Black, rK, rV, rlR, rRight));
		} else {
			var clr = dict.a;
			var k = dict.b;
			var v = dict.c;
			var _v4 = dict.d;
			var lClr = _v4.a;
			var lK = _v4.b;
			var lV = _v4.c;
			var lLeft = _v4.d;
			var lRight = _v4.e;
			var _v5 = dict.e;
			var rClr = _v5.a;
			var rK = _v5.b;
			var rV = _v5.c;
			var rLeft = _v5.d;
			var rRight = _v5.e;
			if (clr.$ === 'Black') {
				return A5(
					$elm$core$Dict$RBNode_elm_builtin,
					$elm$core$Dict$Black,
					k,
					v,
					A5($elm$core$Dict$RBNode_elm_builtin, $elm$core$Dict$Red, lK, lV, lLeft, lRight),
					A5($elm$core$Dict$RBNode_elm_builtin, $elm$core$Dict$Red, rK, rV, rLeft, rRight));
			} else {
				return A5(
					$elm$core$Dict$RBNode_elm_builtin,
					$elm$core$Dict$Black,
					k,
					v,
					A5($elm$core$Dict$RBNode_elm_builtin, $elm$core$Dict$Red, lK, lV, lLeft, lRight),
					A5($elm$core$Dict$RBNode_elm_builtin, $elm$core$Dict$Red, rK, rV, rLeft, rRight));
			}
		}
	} else {
		return dict;
	}
};
var $elm$core$Dict$moveRedRight = function (dict) {
	if (((dict.$ === 'RBNode_elm_builtin') && (dict.d.$ === 'RBNode_elm_builtin')) && (dict.e.$ === 'RBNode_elm_builtin')) {
		if ((dict.d.d.$ === 'RBNode_elm_builtin') && (dict.d.d.a.$ === 'Red')) {
			var clr = dict.a;
			var k = dict.b;
			var v = dict.c;
			var _v1 = dict.d;
			var lClr = _v1.a;
			var lK = _v1.b;
			var lV = _v1.c;
			var _v2 = _v1.d;
			var _v3 = _v2.a;
			var llK = _v2.b;
			var llV = _v2.c;
			var llLeft = _v2.d;
			var llRight = _v2.e;
			var lRight = _v1.e;
			var _v4 = dict.e;
			var rClr = _v4.a;
			var rK = _v4.b;
			var rV = _v4.c;
			var rLeft = _v4.d;
			var rRight = _v4.e;
			return A5(
				$elm$core$Dict$RBNode_elm_builtin,
				$elm$core$Dict$Red,
				lK,
				lV,
				A5($elm$core$Dict$RBNode_elm_builtin, $elm$core$Dict$Black, llK, llV, llLeft, llRight),
				A5(
					$elm$core$Dict$RBNode_elm_builtin,
					$elm$core$Dict$Black,
					k,
					v,
					lRight,
					A5($elm$core$Dict$RBNode_elm_builtin, $elm$core$Dict$Red, rK, rV, rLeft, rRight)));
		} else {
			var clr = dict.a;
			var k = dict.b;
			var v = dict.c;
			var _v5 = dict.d;
			var lClr = _v5.a;
			var lK = _v5.b;
			var lV = _v5.c;
			var lLeft = _v5.d;
			var lRight = _v5.e;
			var _v6 = dict.e;
			var rClr = _v6.a;
			var rK = _v6.b;
			var rV = _v6.c;
			var rLeft = _v6.d;
			var rRight = _v6.e;
			if (clr.$ === 'Black') {
				return A5(
					$elm$core$Dict$RBNode_elm_builtin,
					$elm$core$Dict$Black,
					k,
					v,
					A5($elm$core$Dict$RBNode_elm_builtin, $elm$core$Dict$Red, lK, lV, lLeft, lRight),
					A5($elm$core$Dict$RBNode_elm_builtin, $elm$core$Dict$Red, rK, rV, rLeft, rRight));
			} else {
				return A5(
					$elm$core$Dict$RBNode_elm_builtin,
					$elm$core$Dict$Black,
					k,
					v,
					A5($elm$core$Dict$RBNode_elm_builtin, $elm$core$Dict$Red, lK, lV, lLeft, lRight),
					A5($elm$core$Dict$RBNode_elm_builtin, $elm$core$Dict$Red, rK, rV, rLeft, rRight));
			}
		}
	} else {
		return dict;
	}
};
var $elm$core$Dict$removeHelpPrepEQGT = F7(
	function (targetKey, dict, color, key, value, left, right) {
		if ((left.$ === 'RBNode_elm_builtin') && (left.a.$ === 'Red')) {
			var _v1 = left.a;
			var lK = left.b;
			var lV = left.c;
			var lLeft = left.d;
			var lRight = left.e;
			return A5(
				$elm$core$Dict$RBNode_elm_builtin,
				color,
				lK,
				lV,
				lLeft,
				A5($elm$core$Dict$RBNode_elm_builtin, $elm$core$Dict$Red, key, value, lRight, right));
		} else {
			_v2$2:
			while (true) {
				if ((right.$ === 'RBNode_elm_builtin') && (right.a.$ === 'Black')) {
					if (right.d.$ === 'RBNode_elm_builtin') {
						if (right.d.a.$ === 'Black') {
							var _v3 = right.a;
							var _v4 = right.d;
							var _v5 = _v4.a;
							return $elm$core$Dict$moveRedRight(dict);
						} else {
							break _v2$2;
						}
					} else {
						var _v6 = right.a;
						var _v7 = right.d;
						return $elm$core$Dict$moveRedRight(dict);
					}
				} else {
					break _v2$2;
				}
			}
			return dict;
		}
	});
var $elm$core$Dict$removeMin = function (dict) {
	if ((dict.$ === 'RBNode_elm_builtin') && (dict.d.$ === 'RBNode_elm_builtin')) {
		var color = dict.a;
		var key = dict.b;
		var value = dict.c;
		var left = dict.d;
		var lColor = left.a;
		var lLeft = left.d;
		var right = dict.e;
		if (lColor.$ === 'Black') {
			if ((lLeft.$ === 'RBNode_elm_builtin') && (lLeft.a.$ === 'Red')) {
				var _v3 = lLeft.a;
				return A5(
					$elm$core$Dict$RBNode_elm_builtin,
					color,
					key,
					value,
					$elm$core$Dict$removeMin(left),
					right);
			} else {
				var _v4 = $elm$core$Dict$moveRedLeft(dict);
				if (_v4.$ === 'RBNode_elm_builtin') {
					var nColor = _v4.a;
					var nKey = _v4.b;
					var nValue = _v4.c;
					var nLeft = _v4.d;
					var nRight = _v4.e;
					return A5(
						$elm$core$Dict$balance,
						nColor,
						nKey,
						nValue,
						$elm$core$Dict$removeMin(nLeft),
						nRight);
				} else {
					return $elm$core$Dict$RBEmpty_elm_builtin;
				}
			}
		} else {
			return A5(
				$elm$core$Dict$RBNode_elm_builtin,
				color,
				key,
				value,
				$elm$core$Dict$removeMin(left),
				right);
		}
	} else {
		return $elm$core$Dict$RBEmpty_elm_builtin;
	}
};
var $elm$core$Dict$removeHelp = F2(
	function (targetKey, dict) {
		if (dict.$ === 'RBEmpty_elm_builtin') {
			return $elm$core$Dict$RBEmpty_elm_builtin;
		} else {
			var color = dict.a;
			var key = dict.b;
			var value = dict.c;
			var left = dict.d;
			var right = dict.e;
			if (_Utils_cmp(targetKey, key) < 0) {
				if ((left.$ === 'RBNode_elm_builtin') && (left.a.$ === 'Black')) {
					var _v4 = left.a;
					var lLeft = left.d;
					if ((lLeft.$ === 'RBNode_elm_builtin') && (lLeft.a.$ === 'Red')) {
						var _v6 = lLeft.a;
						return A5(
							$elm$core$Dict$RBNode_elm_builtin,
							color,
							key,
							value,
							A2($elm$core$Dict$removeHelp, targetKey, left),
							right);
					} else {
						var _v7 = $elm$core$Dict$moveRedLeft(dict);
						if (_v7.$ === 'RBNode_elm_builtin') {
							var nColor = _v7.a;
							var nKey = _v7.b;
							var nValue = _v7.c;
							var nLeft = _v7.d;
							var nRight = _v7.e;
							return A5(
								$elm$core$Dict$balance,
								nColor,
								nKey,
								nValue,
								A2($elm$core$Dict$removeHelp, targetKey, nLeft),
								nRight);
						} else {
							return $elm$core$Dict$RBEmpty_elm_builtin;
						}
					}
				} else {
					return A5(
						$elm$core$Dict$RBNode_elm_builtin,
						color,
						key,
						value,
						A2($elm$core$Dict$removeHelp, targetKey, left),
						right);
				}
			} else {
				return A2(
					$elm$core$Dict$removeHelpEQGT,
					targetKey,
					A7($elm$core$Dict$removeHelpPrepEQGT, targetKey, dict, color, key, value, left, right));
			}
		}
	});
var $elm$core$Dict$removeHelpEQGT = F2(
	function (targetKey, dict) {
		if (dict.$ === 'RBNode_elm_builtin') {
			var color = dict.a;
			var key = dict.b;
			var value = dict.c;
			var left = dict.d;
			var right = dict.e;
			if (_Utils_eq(targetKey, key)) {
				var _v1 = $elm$core$Dict$getMin(right);
				if (_v1.$ === 'RBNode_elm_builtin') {
					var minKey = _v1.b;
					var minValue = _v1.c;
					return A5(
						$elm$core$Dict$balance,
						color,
						minKey,
						minValue,
						left,
						$elm$core$Dict$removeMin(right));
				} else {
					return $elm$core$Dict$RBEmpty_elm_builtin;
				}
			} else {
				return A5(
					$elm$core$Dict$balance,
					color,
					key,
					value,
					left,
					A2($elm$core$Dict$removeHelp, targetKey, right));
			}
		} else {
			return $elm$core$Dict$RBEmpty_elm_builtin;
		}
	});
var $elm$core$Dict$remove = F2(
	function (key, dict) {
		var _v0 = A2($elm$core$Dict$removeHelp, key, dict);
		if ((_v0.$ === 'RBNode_elm_builtin') && (_v0.a.$ === 'Red')) {
			var _v1 = _v0.a;
			var k = _v0.b;
			var v = _v0.c;
			var l = _v0.d;
			var r = _v0.e;
			return A5($elm$core$Dict$RBNode_elm_builtin, $elm$core$Dict$Black, k, v, l, r);
		} else {
			var x = _v0;
			return x;
		}
	});
var $elm$core$Dict$update = F3(
	function (targetKey, alter, dictionary) {
		var _v0 = alter(
			A2($elm$core$Dict$get, targetKey, dictionary));
		if (_v0.$ === 'Just') {
			var value = _v0.a;
			return A3($elm$core$Dict$insert, targetKey, value, dictionary);
		} else {
			return A2($elm$core$Dict$remove, targetKey, dictionary);
		}
	});
var $elm$core$Basics$composeR = F3(
	function (f, g, x) {
		return g(
			f(x));
	});
var $elm$http$Http$expectBytesResponse = F2(
	function (toMsg, toResult) {
		return A3(
			_Http_expect,
			'arraybuffer',
			_Http_toDataView,
			A2($elm$core$Basics$composeR, toResult, toMsg));
	});
var $elm$http$Http$BadBody = function (a) {
	return {$: 'BadBody', a: a};
};
var $elm$http$Http$BadStatus = function (a) {
	return {$: 'BadStatus', a: a};
};
var $elm$http$Http$BadUrl = function (a) {
	return {$: 'BadUrl', a: a};
};
var $elm$http$Http$NetworkError = {$: 'NetworkError'};
var $elm$http$Http$Timeout = {$: 'Timeout'};
var $elm$core$Result$mapError = F2(
	function (f, result) {
		if (result.$ === 'Ok') {
			var v = result.a;
			return $elm$core$Result$Ok(v);
		} else {
			var e = result.a;
			return $elm$core$Result$Err(
				f(e));
		}
	});
var $elm$http$Http$resolve = F2(
	function (toResult, response) {
		switch (response.$) {
			case 'BadUrl_':
				var url = response.a;
				return $elm$core$Result$Err(
					$elm$http$Http$BadUrl(url));
			case 'Timeout_':
				return $elm$core$Result$Err($elm$http$Http$Timeout);
			case 'NetworkError_':
				return $elm$core$Result$Err($elm$http$Http$NetworkError);
			case 'BadStatus_':
				var metadata = response.a;
				return $elm$core$Result$Err(
					$elm$http$Http$BadStatus(metadata.statusCode));
			default:
				var body = response.b;
				return A2(
					$elm$core$Result$mapError,
					$elm$http$Http$BadBody,
					toResult(body));
		}
	});
var $elm$http$Http$expectWhatever = function (toMsg) {
	return A2(
		$elm$http$Http$expectBytesResponse,
		toMsg,
		$elm$http$Http$resolve(
			function (_v0) {
				return $elm$core$Result$Ok(_Utils_Tuple0);
			}));
};
var $elm$http$Http$emptyBody = _Http_emptyBody;
var $elm$http$Http$Request = function (a) {
	return {$: 'Request', a: a};
};
var $elm$http$Http$State = F2(
	function (reqs, subs) {
		return {reqs: reqs, subs: subs};
	});
var $elm$http$Http$init = $elm$core$Task$succeed(
	A2($elm$http$Http$State, $elm$core$Dict$empty, _List_Nil));
var $elm$core$Process$kill = _Scheduler_kill;
var $elm$core$Process$spawn = _Scheduler_spawn;
var $elm$http$Http$updateReqs = F3(
	function (router, cmds, reqs) {
		updateReqs:
		while (true) {
			if (!cmds.b) {
				return $elm$core$Task$succeed(reqs);
			} else {
				var cmd = cmds.a;
				var otherCmds = cmds.b;
				if (cmd.$ === 'Cancel') {
					var tracker = cmd.a;
					var _v2 = A2($elm$core$Dict$get, tracker, reqs);
					if (_v2.$ === 'Nothing') {
						var $temp$router = router,
							$temp$cmds = otherCmds,
							$temp$reqs = reqs;
						router = $temp$router;
						cmds = $temp$cmds;
						reqs = $temp$reqs;
						continue updateReqs;
					} else {
						var pid = _v2.a;
						return A2(
							$elm$core$Task$andThen,
							function (_v3) {
								return A3(
									$elm$http$Http$updateReqs,
									router,
									otherCmds,
									A2($elm$core$Dict$remove, tracker, reqs));
							},
							$elm$core$Process$kill(pid));
					}
				} else {
					var req = cmd.a;
					return A2(
						$elm$core$Task$andThen,
						function (pid) {
							var _v4 = req.tracker;
							if (_v4.$ === 'Nothing') {
								return A3($elm$http$Http$updateReqs, router, otherCmds, reqs);
							} else {
								var tracker = _v4.a;
								return A3(
									$elm$http$Http$updateReqs,
									router,
									otherCmds,
									A3($elm$core$Dict$insert, tracker, pid, reqs));
							}
						},
						$elm$core$Process$spawn(
							A3(
								_Http_toTask,
								router,
								$elm$core$Platform$sendToApp(router),
								req)));
				}
			}
		}
	});
var $elm$http$Http$onEffects = F4(
	function (router, cmds, subs, state) {
		return A2(
			$elm$core$Task$andThen,
			function (reqs) {
				return $elm$core$Task$succeed(
					A2($elm$http$Http$State, reqs, subs));
			},
			A3($elm$http$Http$updateReqs, router, cmds, state.reqs));
	});
var $elm$core$List$maybeCons = F3(
	function (f, mx, xs) {
		var _v0 = f(mx);
		if (_v0.$ === 'Just') {
			var x = _v0.a;
			return A2($elm$core$List$cons, x, xs);
		} else {
			return xs;
		}
	});
var $elm$core$List$filterMap = F2(
	function (f, xs) {
		return A3(
			$elm$core$List$foldr,
			$elm$core$List$maybeCons(f),
			_List_Nil,
			xs);
	});
var $elm$http$Http$maybeSend = F4(
	function (router, desiredTracker, progress, _v0) {
		var actualTracker = _v0.a;
		var toMsg = _v0.b;
		return _Utils_eq(desiredTracker, actualTracker) ? $elm$core$Maybe$Just(
			A2(
				$elm$core$Platform$sendToApp,
				router,
				toMsg(progress))) : $elm$core$Maybe$Nothing;
	});
var $elm$http$Http$onSelfMsg = F3(
	function (router, _v0, state) {
		var tracker = _v0.a;
		var progress = _v0.b;
		return A2(
			$elm$core$Task$andThen,
			function (_v1) {
				return $elm$core$Task$succeed(state);
			},
			$elm$core$Task$sequence(
				A2(
					$elm$core$List$filterMap,
					A3($elm$http$Http$maybeSend, router, tracker, progress),
					state.subs)));
	});
var $elm$http$Http$Cancel = function (a) {
	return {$: 'Cancel', a: a};
};
var $elm$http$Http$cmdMap = F2(
	function (func, cmd) {
		if (cmd.$ === 'Cancel') {
			var tracker = cmd.a;
			return $elm$http$Http$Cancel(tracker);
		} else {
			var r = cmd.a;
			return $elm$http$Http$Request(
				{
					allowCookiesFromOtherDomains: r.allowCookiesFromOtherDomains,
					body: r.body,
					expect: A2(_Http_mapExpect, func, r.expect),
					headers: r.headers,
					method: r.method,
					timeout: r.timeout,
					tracker: r.tracker,
					url: r.url
				});
		}
	});
var $elm$http$Http$MySub = F2(
	function (a, b) {
		return {$: 'MySub', a: a, b: b};
	});
var $elm$http$Http$subMap = F2(
	function (func, _v0) {
		var tracker = _v0.a;
		var toMsg = _v0.b;
		return A2(
			$elm$http$Http$MySub,
			tracker,
			A2($elm$core$Basics$composeR, toMsg, func));
	});
_Platform_effectManagers['Http'] = _Platform_createManager($elm$http$Http$init, $elm$http$Http$onEffects, $elm$http$Http$onSelfMsg, $elm$http$Http$cmdMap, $elm$http$Http$subMap);
var $elm$http$Http$command = _Platform_leaf('Http');
var $elm$http$Http$subscription = _Platform_leaf('Http');
var $elm$http$Http$request = function (r) {
	return $elm$http$Http$command(
		$elm$http$Http$Request(
			{allowCookiesFromOtherDomains: false, body: r.body, expect: r.expect, headers: r.headers, method: r.method, timeout: r.timeout, tracker: r.tracker, url: r.url}));
};
var $elm$http$Http$get = function (r) {
	return $elm$http$Http$request(
		{body: $elm$http$Http$emptyBody, expect: r.expect, headers: _List_Nil, method: 'GET', timeout: $elm$core$Maybe$Nothing, tracker: $elm$core$Maybe$Nothing, url: r.url});
};
var $author$project$Auth$checkAuth = $elm$http$Http$get(
	{
		expect: $elm$http$Http$expectWhatever($author$project$Auth$CheckAuthResult),
		url: '/api/videos?limit=1'
	});
var $author$project$Route$Videos = {$: 'Videos'};
var $elm$url$Url$Parser$State = F5(
	function (visited, unvisited, params, frag, value) {
		return {frag: frag, params: params, unvisited: unvisited, value: value, visited: visited};
	});
var $elm$url$Url$Parser$getFirstMatch = function (states) {
	getFirstMatch:
	while (true) {
		if (!states.b) {
			return $elm$core$Maybe$Nothing;
		} else {
			var state = states.a;
			var rest = states.b;
			var _v1 = state.unvisited;
			if (!_v1.b) {
				return $elm$core$Maybe$Just(state.value);
			} else {
				if ((_v1.a === '') && (!_v1.b.b)) {
					return $elm$core$Maybe$Just(state.value);
				} else {
					var $temp$states = rest;
					states = $temp$states;
					continue getFirstMatch;
				}
			}
		}
	}
};
var $elm$url$Url$Parser$removeFinalEmpty = function (segments) {
	if (!segments.b) {
		return _List_Nil;
	} else {
		if ((segments.a === '') && (!segments.b.b)) {
			return _List_Nil;
		} else {
			var segment = segments.a;
			var rest = segments.b;
			return A2(
				$elm$core$List$cons,
				segment,
				$elm$url$Url$Parser$removeFinalEmpty(rest));
		}
	}
};
var $elm$url$Url$Parser$preparePath = function (path) {
	var _v0 = A2($elm$core$String$split, '/', path);
	if (_v0.b && (_v0.a === '')) {
		var segments = _v0.b;
		return $elm$url$Url$Parser$removeFinalEmpty(segments);
	} else {
		var segments = _v0;
		return $elm$url$Url$Parser$removeFinalEmpty(segments);
	}
};
var $elm$url$Url$Parser$addToParametersHelp = F2(
	function (value, maybeList) {
		if (maybeList.$ === 'Nothing') {
			return $elm$core$Maybe$Just(
				_List_fromArray(
					[value]));
		} else {
			var list = maybeList.a;
			return $elm$core$Maybe$Just(
				A2($elm$core$List$cons, value, list));
		}
	});
var $elm$url$Url$percentDecode = _Url_percentDecode;
var $elm$url$Url$Parser$addParam = F2(
	function (segment, dict) {
		var _v0 = A2($elm$core$String$split, '=', segment);
		if ((_v0.b && _v0.b.b) && (!_v0.b.b.b)) {
			var rawKey = _v0.a;
			var _v1 = _v0.b;
			var rawValue = _v1.a;
			var _v2 = $elm$url$Url$percentDecode(rawKey);
			if (_v2.$ === 'Nothing') {
				return dict;
			} else {
				var key = _v2.a;
				var _v3 = $elm$url$Url$percentDecode(rawValue);
				if (_v3.$ === 'Nothing') {
					return dict;
				} else {
					var value = _v3.a;
					return A3(
						$elm$core$Dict$update,
						key,
						$elm$url$Url$Parser$addToParametersHelp(value),
						dict);
				}
			}
		} else {
			return dict;
		}
	});
var $elm$url$Url$Parser$prepareQuery = function (maybeQuery) {
	if (maybeQuery.$ === 'Nothing') {
		return $elm$core$Dict$empty;
	} else {
		var qry = maybeQuery.a;
		return A3(
			$elm$core$List$foldr,
			$elm$url$Url$Parser$addParam,
			$elm$core$Dict$empty,
			A2($elm$core$String$split, '&', qry));
	}
};
var $elm$url$Url$Parser$parse = F2(
	function (_v0, url) {
		var parser = _v0.a;
		return $elm$url$Url$Parser$getFirstMatch(
			parser(
				A5(
					$elm$url$Url$Parser$State,
					_List_Nil,
					$elm$url$Url$Parser$preparePath(url.path),
					$elm$url$Url$Parser$prepareQuery(url.query),
					url.fragment,
					$elm$core$Basics$identity)));
	});
var $author$project$Route$Audio = {$: 'Audio'};
var $author$project$Route$AudioDetail = function (a) {
	return {$: 'AudioDetail', a: a};
};
var $author$project$Route$AudioGallery = {$: 'AudioGallery'};
var $author$project$Route$Auth = {$: 'Auth'};
var $author$project$Route$BriefGallery = {$: 'BriefGallery'};
var $author$project$Route$CreativeBriefEditor = {$: 'CreativeBriefEditor'};
var $author$project$Route$Gallery = {$: 'Gallery'};
var $author$project$Route$ImageDetail = function (a) {
	return {$: 'ImageDetail', a: a};
};
var $author$project$Route$ImageGallery = {$: 'ImageGallery'};
var $author$project$Route$Images = {$: 'Images'};
var $author$project$Route$Physics = {$: 'Physics'};
var $author$project$Route$SimulationGallery = {$: 'SimulationGallery'};
var $author$project$Route$VideoDetail = function (a) {
	return {$: 'VideoDetail', a: a};
};
var $author$project$Route$VideoToText = {$: 'VideoToText'};
var $author$project$Route$VideoToTextGallery = {$: 'VideoToTextGallery'};
var $elm$url$Url$Parser$Parser = function (a) {
	return {$: 'Parser', a: a};
};
var $elm$url$Url$Parser$custom = F2(
	function (tipe, stringToSomething) {
		return $elm$url$Url$Parser$Parser(
			function (_v0) {
				var visited = _v0.visited;
				var unvisited = _v0.unvisited;
				var params = _v0.params;
				var frag = _v0.frag;
				var value = _v0.value;
				if (!unvisited.b) {
					return _List_Nil;
				} else {
					var next = unvisited.a;
					var rest = unvisited.b;
					var _v2 = stringToSomething(next);
					if (_v2.$ === 'Just') {
						var nextValue = _v2.a;
						return _List_fromArray(
							[
								A5(
								$elm$url$Url$Parser$State,
								A2($elm$core$List$cons, next, visited),
								rest,
								params,
								frag,
								value(nextValue))
							]);
					} else {
						return _List_Nil;
					}
				}
			});
	});
var $elm$url$Url$Parser$int = A2($elm$url$Url$Parser$custom, 'NUMBER', $elm$core$String$toInt);
var $elm$url$Url$Parser$mapState = F2(
	function (func, _v0) {
		var visited = _v0.visited;
		var unvisited = _v0.unvisited;
		var params = _v0.params;
		var frag = _v0.frag;
		var value = _v0.value;
		return A5(
			$elm$url$Url$Parser$State,
			visited,
			unvisited,
			params,
			frag,
			func(value));
	});
var $elm$url$Url$Parser$map = F2(
	function (subValue, _v0) {
		var parseArg = _v0.a;
		return $elm$url$Url$Parser$Parser(
			function (_v1) {
				var visited = _v1.visited;
				var unvisited = _v1.unvisited;
				var params = _v1.params;
				var frag = _v1.frag;
				var value = _v1.value;
				return A2(
					$elm$core$List$map,
					$elm$url$Url$Parser$mapState(value),
					parseArg(
						A5($elm$url$Url$Parser$State, visited, unvisited, params, frag, subValue)));
			});
	});
var $elm$core$List$append = F2(
	function (xs, ys) {
		if (!ys.b) {
			return xs;
		} else {
			return A3($elm$core$List$foldr, $elm$core$List$cons, ys, xs);
		}
	});
var $elm$core$List$concat = function (lists) {
	return A3($elm$core$List$foldr, $elm$core$List$append, _List_Nil, lists);
};
var $elm$core$List$concatMap = F2(
	function (f, list) {
		return $elm$core$List$concat(
			A2($elm$core$List$map, f, list));
	});
var $elm$url$Url$Parser$oneOf = function (parsers) {
	return $elm$url$Url$Parser$Parser(
		function (state) {
			return A2(
				$elm$core$List$concatMap,
				function (_v0) {
					var parser = _v0.a;
					return parser(state);
				},
				parsers);
		});
};
var $elm$url$Url$Parser$s = function (str) {
	return $elm$url$Url$Parser$Parser(
		function (_v0) {
			var visited = _v0.visited;
			var unvisited = _v0.unvisited;
			var params = _v0.params;
			var frag = _v0.frag;
			var value = _v0.value;
			if (!unvisited.b) {
				return _List_Nil;
			} else {
				var next = unvisited.a;
				var rest = unvisited.b;
				return _Utils_eq(next, str) ? _List_fromArray(
					[
						A5(
						$elm$url$Url$Parser$State,
						A2($elm$core$List$cons, next, visited),
						rest,
						params,
						frag,
						value)
					]) : _List_Nil;
			}
		});
};
var $elm$url$Url$Parser$slash = F2(
	function (_v0, _v1) {
		var parseBefore = _v0.a;
		var parseAfter = _v1.a;
		return $elm$url$Url$Parser$Parser(
			function (state) {
				return A2(
					$elm$core$List$concatMap,
					parseAfter,
					parseBefore(state));
			});
	});
var $elm$url$Url$Parser$top = $elm$url$Url$Parser$Parser(
	function (state) {
		return _List_fromArray(
			[state]);
	});
var $author$project$Route$parser = $elm$url$Url$Parser$oneOf(
	_List_fromArray(
		[
			A2($elm$url$Url$Parser$map, $author$project$Route$Videos, $elm$url$Url$Parser$top),
			A2(
			$elm$url$Url$Parser$map,
			$author$project$Route$Physics,
			$elm$url$Url$Parser$s('physics')),
			A2(
			$elm$url$Url$Parser$map,
			$author$project$Route$Videos,
			$elm$url$Url$Parser$s('videos')),
			A2(
			$elm$url$Url$Parser$map,
			$author$project$Route$VideoDetail,
			A2(
				$elm$url$Url$Parser$slash,
				$elm$url$Url$Parser$s('video'),
				$elm$url$Url$Parser$int)),
			A2(
			$elm$url$Url$Parser$map,
			$author$project$Route$Gallery,
			$elm$url$Url$Parser$s('gallery')),
			A2(
			$elm$url$Url$Parser$map,
			$author$project$Route$SimulationGallery,
			$elm$url$Url$Parser$s('simulations')),
			A2(
			$elm$url$Url$Parser$map,
			$author$project$Route$Images,
			$elm$url$Url$Parser$s('images')),
			A2(
			$elm$url$Url$Parser$map,
			$author$project$Route$ImageDetail,
			A2(
				$elm$url$Url$Parser$slash,
				$elm$url$Url$Parser$s('image'),
				$elm$url$Url$Parser$int)),
			A2(
			$elm$url$Url$Parser$map,
			$author$project$Route$ImageGallery,
			$elm$url$Url$Parser$s('image-gallery')),
			A2(
			$elm$url$Url$Parser$map,
			$author$project$Route$Audio,
			$elm$url$Url$Parser$s('audio')),
			A2(
			$elm$url$Url$Parser$map,
			$author$project$Route$AudioDetail,
			A2(
				$elm$url$Url$Parser$slash,
				$elm$url$Url$Parser$s('audio'),
				$elm$url$Url$Parser$int)),
			A2(
			$elm$url$Url$Parser$map,
			$author$project$Route$AudioGallery,
			$elm$url$Url$Parser$s('audio-gallery')),
			A2(
			$elm$url$Url$Parser$map,
			$author$project$Route$VideoToText,
			$elm$url$Url$Parser$s('video-to-text')),
			A2(
			$elm$url$Url$Parser$map,
			$author$project$Route$VideoToTextGallery,
			$elm$url$Url$Parser$s('video-to-text-gallery')),
			A2(
			$elm$url$Url$Parser$map,
			$author$project$Route$Auth,
			$elm$url$Url$Parser$s('auth')),
			A2(
			$elm$url$Url$Parser$map,
			$author$project$Route$BriefGallery,
			$elm$url$Url$Parser$s('briefs')),
			A2(
			$elm$url$Url$Parser$map,
			$author$project$Route$CreativeBriefEditor,
			$elm$url$Url$Parser$s('creative'))
		]));
var $author$project$Route$fromUrl = function (url) {
	var _v0 = A2($elm$url$Url$Parser$parse, $author$project$Route$parser, url);
	if (_v0.$ === 'Just') {
		var route = _v0.a;
		return $elm$core$Maybe$Just(route);
	} else {
		return $elm$core$Maybe$Just($author$project$Route$Videos);
	}
};
var $author$project$Audio$ModelsFetched = function (a) {
	return {$: 'ModelsFetched', a: a};
};
var $author$project$Audio$AudioModel = F4(
	function (id, name, description, inputSchema) {
		return {description: description, id: id, inputSchema: inputSchema, name: name};
	});
var $elm$json$Json$Decode$field = _Json_decodeField;
var $elm$json$Json$Decode$map4 = _Json_map4;
var $elm$json$Json$Decode$oneOf = _Json_oneOf;
var $elm$json$Json$Decode$maybe = function (decoder) {
	return $elm$json$Json$Decode$oneOf(
		_List_fromArray(
			[
				A2($elm$json$Json$Decode$map, $elm$core$Maybe$Just, decoder),
				$elm$json$Json$Decode$succeed($elm$core$Maybe$Nothing)
			]));
};
var $elm$json$Json$Decode$string = _Json_decodeString;
var $elm$json$Json$Decode$value = _Json_decodeValue;
var $author$project$Audio$audioModelDecoder = A5(
	$elm$json$Json$Decode$map4,
	$author$project$Audio$AudioModel,
	A2($elm$json$Json$Decode$field, 'id', $elm$json$Json$Decode$string),
	A2($elm$json$Json$Decode$field, 'name', $elm$json$Json$Decode$string),
	$elm$json$Json$Decode$oneOf(
		_List_fromArray(
			[
				A2($elm$json$Json$Decode$field, 'description', $elm$json$Json$Decode$string),
				$elm$json$Json$Decode$succeed('No description available')
			])),
	$elm$json$Json$Decode$maybe(
		A2($elm$json$Json$Decode$field, 'input_schema', $elm$json$Json$Decode$value)));
var $elm$json$Json$Decode$decodeString = _Json_runOnString;
var $elm$http$Http$expectStringResponse = F2(
	function (toMsg, toResult) {
		return A3(
			_Http_expect,
			'',
			$elm$core$Basics$identity,
			A2($elm$core$Basics$composeR, toResult, toMsg));
	});
var $elm$http$Http$expectJson = F2(
	function (toMsg, decoder) {
		return A2(
			$elm$http$Http$expectStringResponse,
			toMsg,
			$elm$http$Http$resolve(
				function (string) {
					return A2(
						$elm$core$Result$mapError,
						$elm$json$Json$Decode$errorToString,
						A2($elm$json$Json$Decode$decodeString, decoder, string));
				}));
	});
var $elm$json$Json$Decode$list = _Json_decodeList;
var $author$project$Audio$fetchModels = function (collection) {
	return $elm$http$Http$get(
		{
			expect: A2(
				$elm$http$Http$expectJson,
				$author$project$Audio$ModelsFetched,
				A2(
					$elm$json$Json$Decode$field,
					'models',
					$elm$json$Json$Decode$list($author$project$Audio$audioModelDecoder))),
			url: '/api/audio-models?collection=' + collection
		});
};
var $author$project$Audio$init = _Utils_Tuple2(
	{audioStatus: '', error: $elm$core$Maybe$Nothing, isGenerating: false, models: _List_Nil, outputAudio: $elm$core$Maybe$Nothing, parameters: _List_Nil, pollingAudioId: $elm$core$Maybe$Nothing, requiredFields: _List_Nil, searchQuery: '', selectedCollection: 'ai-music-generation', selectedModel: $elm$core$Maybe$Nothing, selectedVersion: $elm$core$Maybe$Nothing},
	$author$project$Audio$fetchModels('ai-music-generation'));
var $author$project$AudioGallery$AudioFetched = function (a) {
	return {$: 'AudioFetched', a: a};
};
var $elm$json$Json$Decode$andThen = _Json_andThen;
var $elm$json$Json$Decode$float = _Json_decodeFloat;
var $elm$json$Json$Decode$int = _Json_decodeInt;
var $elm$json$Json$Decode$map8 = _Json_map8;
var $author$project$AudioGallery$audioDecoder = A2(
	$elm$json$Json$Decode$andThen,
	function (record) {
		return A3(
			$elm$json$Json$Decode$map2,
			F2(
				function (status, duration) {
					return _Utils_update(
						record,
						{duration: duration, status: status});
				}),
			$elm$json$Json$Decode$oneOf(
				_List_fromArray(
					[
						A2($elm$json$Json$Decode$field, 'status', $elm$json$Json$Decode$string),
						$elm$json$Json$Decode$succeed('completed')
					])),
			$elm$json$Json$Decode$maybe(
				A2($elm$json$Json$Decode$field, 'duration', $elm$json$Json$Decode$float)));
	},
	A9(
		$elm$json$Json$Decode$map8,
		F8(
			function (id, prompt, audioUrl, modelId, createdAt, collection, parameters, metadata) {
				return {audioUrl: audioUrl, collection: collection, createdAt: createdAt, duration: $elm$core$Maybe$Nothing, id: id, metadata: metadata, modelId: modelId, parameters: parameters, prompt: prompt, status: 'completed'};
			}),
		A2($elm$json$Json$Decode$field, 'id', $elm$json$Json$Decode$int),
		A2($elm$json$Json$Decode$field, 'prompt', $elm$json$Json$Decode$string),
		A2($elm$json$Json$Decode$field, 'audio_url', $elm$json$Json$Decode$string),
		A2($elm$json$Json$Decode$field, 'model_id', $elm$json$Json$Decode$string),
		A2($elm$json$Json$Decode$field, 'created_at', $elm$json$Json$Decode$string),
		$elm$json$Json$Decode$maybe(
			A2($elm$json$Json$Decode$field, 'collection', $elm$json$Json$Decode$string)),
		$elm$json$Json$Decode$maybe(
			A2($elm$json$Json$Decode$field, 'parameters', $elm$json$Json$Decode$value)),
		$elm$json$Json$Decode$maybe(
			A2($elm$json$Json$Decode$field, 'metadata', $elm$json$Json$Decode$value))));
var $author$project$AudioGallery$fetchAudio = $elm$http$Http$get(
	{
		expect: A2(
			$elm$http$Http$expectJson,
			$author$project$AudioGallery$AudioFetched,
			A2(
				$elm$json$Json$Decode$field,
				'audio',
				$elm$json$Json$Decode$list($author$project$AudioGallery$audioDecoder))),
		url: '/api/audio?limit=50'
	});
var $author$project$AudioGallery$init = _Utils_Tuple2(
	{audio: _List_Nil, error: $elm$core$Maybe$Nothing, loading: true, selectedAudio: $elm$core$Maybe$Nothing, showRawData: false},
	$author$project$AudioGallery$fetchAudio);
var $author$project$Auth$Checking = {$: 'Checking'};
var $author$project$Auth$init = {error: $elm$core$Maybe$Nothing, loginState: $author$project$Auth$Checking, password: '', username: ''};
var $author$project$BriefGallery$BriefsLoaded = function (a) {
	return {$: 'BriefsLoaded', a: a};
};
var $author$project$BriefGallery$BriefsResponse = F2(
	function (briefs, totalPages) {
		return {briefs: briefs, totalPages: totalPages};
	});
var $author$project$BriefGallery$CreativeBrief = function (id) {
	return function (userId) {
		return function (promptText) {
			return function (imageUrl) {
				return function (videoUrl) {
					return function (creativeDirection) {
						return function (scenes) {
							return function (confidenceScore) {
								return function (createdAt) {
									return function (updatedAt) {
										return {confidenceScore: confidenceScore, createdAt: createdAt, creativeDirection: creativeDirection, id: id, imageUrl: imageUrl, promptText: promptText, scenes: scenes, updatedAt: updatedAt, userId: userId, videoUrl: videoUrl};
									};
								};
							};
						};
					};
				};
			};
		};
	};
};
var $author$project$BriefGallery$Scene = F5(
	function (id, sceneNumber, purpose, duration, visual) {
		return {duration: duration, id: id, purpose: purpose, sceneNumber: sceneNumber, visual: visual};
	});
var $author$project$BriefGallery$VisualDetails = F3(
	function (shotType, subject, generationPrompt) {
		return {generationPrompt: generationPrompt, shotType: shotType, subject: subject};
	});
var $elm$json$Json$Decode$map3 = _Json_map3;
var $author$project$BriefGallery$decodeVisualDetails = A4(
	$elm$json$Json$Decode$map3,
	$author$project$BriefGallery$VisualDetails,
	$elm$json$Json$Decode$maybe(
		A2($elm$json$Json$Decode$field, 'shot_type', $elm$json$Json$Decode$string)),
	$elm$json$Json$Decode$maybe(
		A2($elm$json$Json$Decode$field, 'subject', $elm$json$Json$Decode$string)),
	$elm$json$Json$Decode$maybe(
		A2($elm$json$Json$Decode$field, 'generation_prompt', $elm$json$Json$Decode$string)));
var $elm$json$Json$Decode$map5 = _Json_map5;
var $author$project$BriefGallery$decodeScene = A6(
	$elm$json$Json$Decode$map5,
	$author$project$BriefGallery$Scene,
	A2($elm$json$Json$Decode$field, 'id', $elm$json$Json$Decode$string),
	A2($elm$json$Json$Decode$field, 'scene_number', $elm$json$Json$Decode$int),
	A2($elm$json$Json$Decode$field, 'purpose', $elm$json$Json$Decode$string),
	A2($elm$json$Json$Decode$field, 'duration', $elm$json$Json$Decode$float),
	$elm$json$Json$Decode$maybe(
		A2($elm$json$Json$Decode$field, 'visual', $author$project$BriefGallery$decodeVisualDetails)));
var $elm$json$Json$Decode$null = _Json_decodeNull;
var $elm$json$Json$Decode$nullable = function (decoder) {
	return $elm$json$Json$Decode$oneOf(
		_List_fromArray(
			[
				$elm$json$Json$Decode$null($elm$core$Maybe$Nothing),
				A2($elm$json$Json$Decode$map, $elm$core$Maybe$Just, decoder)
			]));
};
var $NoRedInk$elm_json_decode_pipeline$Json$Decode$Pipeline$custom = $elm$json$Json$Decode$map2($elm$core$Basics$apR);
var $elm$json$Json$Decode$at = F2(
	function (fields, decoder) {
		return A3($elm$core$List$foldr, $elm$json$Json$Decode$field, decoder, fields);
	});
var $elm$json$Json$Decode$decodeValue = _Json_run;
var $NoRedInk$elm_json_decode_pipeline$Json$Decode$Pipeline$optionalDecoder = F3(
	function (path, valDecoder, fallback) {
		var nullOr = function (decoder) {
			return $elm$json$Json$Decode$oneOf(
				_List_fromArray(
					[
						decoder,
						$elm$json$Json$Decode$null(fallback)
					]));
		};
		var handleResult = function (input) {
			var _v0 = A2(
				$elm$json$Json$Decode$decodeValue,
				A2($elm$json$Json$Decode$at, path, $elm$json$Json$Decode$value),
				input);
			if (_v0.$ === 'Ok') {
				var rawValue = _v0.a;
				var _v1 = A2(
					$elm$json$Json$Decode$decodeValue,
					nullOr(valDecoder),
					rawValue);
				if (_v1.$ === 'Ok') {
					var finalResult = _v1.a;
					return $elm$json$Json$Decode$succeed(finalResult);
				} else {
					return A2(
						$elm$json$Json$Decode$at,
						path,
						nullOr(valDecoder));
				}
			} else {
				return $elm$json$Json$Decode$succeed(fallback);
			}
		};
		return A2($elm$json$Json$Decode$andThen, handleResult, $elm$json$Json$Decode$value);
	});
var $NoRedInk$elm_json_decode_pipeline$Json$Decode$Pipeline$optional = F4(
	function (key, valDecoder, fallback, decoder) {
		return A2(
			$NoRedInk$elm_json_decode_pipeline$Json$Decode$Pipeline$custom,
			A3(
				$NoRedInk$elm_json_decode_pipeline$Json$Decode$Pipeline$optionalDecoder,
				_List_fromArray(
					[key]),
				valDecoder,
				fallback),
			decoder);
	});
var $NoRedInk$elm_json_decode_pipeline$Json$Decode$Pipeline$required = F3(
	function (key, valDecoder, decoder) {
		return A2(
			$NoRedInk$elm_json_decode_pipeline$Json$Decode$Pipeline$custom,
			A2($elm$json$Json$Decode$field, key, valDecoder),
			decoder);
	});
var $author$project$BriefGallery$decodeCreativeBrief = A3(
	$NoRedInk$elm_json_decode_pipeline$Json$Decode$Pipeline$required,
	'updated_at',
	$elm$json$Json$Decode$string,
	A3(
		$NoRedInk$elm_json_decode_pipeline$Json$Decode$Pipeline$required,
		'created_at',
		$elm$json$Json$Decode$string,
		A4(
			$NoRedInk$elm_json_decode_pipeline$Json$Decode$Pipeline$optional,
			'confidence_score',
			$elm$json$Json$Decode$nullable($elm$json$Json$Decode$float),
			$elm$core$Maybe$Nothing,
			A3(
				$NoRedInk$elm_json_decode_pipeline$Json$Decode$Pipeline$required,
				'scenes',
				$elm$json$Json$Decode$list($author$project$BriefGallery$decodeScene),
				A3(
					$NoRedInk$elm_json_decode_pipeline$Json$Decode$Pipeline$required,
					'creative_direction',
					$elm$json$Json$Decode$value,
					A4(
						$NoRedInk$elm_json_decode_pipeline$Json$Decode$Pipeline$optional,
						'video_url',
						$elm$json$Json$Decode$nullable($elm$json$Json$Decode$string),
						$elm$core$Maybe$Nothing,
						A4(
							$NoRedInk$elm_json_decode_pipeline$Json$Decode$Pipeline$optional,
							'image_url',
							$elm$json$Json$Decode$nullable($elm$json$Json$Decode$string),
							$elm$core$Maybe$Nothing,
							A4(
								$NoRedInk$elm_json_decode_pipeline$Json$Decode$Pipeline$optional,
								'prompt_text',
								$elm$json$Json$Decode$nullable($elm$json$Json$Decode$string),
								$elm$core$Maybe$Nothing,
								A3(
									$NoRedInk$elm_json_decode_pipeline$Json$Decode$Pipeline$required,
									'user_id',
									$elm$json$Json$Decode$int,
									A3(
										$NoRedInk$elm_json_decode_pipeline$Json$Decode$Pipeline$required,
										'id',
										$elm$json$Json$Decode$string,
										$elm$json$Json$Decode$succeed($author$project$BriefGallery$CreativeBrief)))))))))));
var $author$project$BriefGallery$decodeBriefsResponse = A3(
	$elm$json$Json$Decode$map2,
	$author$project$BriefGallery$BriefsResponse,
	A2(
		$elm$json$Json$Decode$field,
		'briefs',
		$elm$json$Json$Decode$list($author$project$BriefGallery$decodeCreativeBrief)),
	A2($elm$json$Json$Decode$field, 'totalPages', $elm$json$Json$Decode$int));
var $author$project$BriefGallery$loadBriefs = function (page) {
	return $elm$http$Http$get(
		{
			expect: A2($elm$http$Http$expectJson, $author$project$BriefGallery$BriefsLoaded, $author$project$BriefGallery$decodeBriefsResponse),
			url: '/api/creative/briefs?page=' + ($elm$core$String$fromInt(page) + '&limit=12')
		});
};
var $author$project$BriefGallery$init = function (key) {
	return _Utils_Tuple2(
		{briefs: _List_Nil, currentPage: 1, error: $elm$core$Maybe$Nothing, isLoading: true, navigationKey: key, selectedBrief: $elm$core$Maybe$Nothing, totalPages: 1},
		$author$project$BriefGallery$loadBriefs(1));
};
var $author$project$CreativeBriefEditor$ImageModelsFetched = function (a) {
	return {$: 'ImageModelsFetched', a: a};
};
var $author$project$CreativeBriefEditor$ImageModel = F3(
	function (name, owner, description) {
		return {description: description, name: name, owner: owner};
	});
var $elm$core$Maybe$withDefault = F2(
	function (_default, maybe) {
		if (maybe.$ === 'Just') {
			var value = maybe.a;
			return value;
		} else {
			return _default;
		}
	});
var $author$project$CreativeBriefEditor$decodeImageModel = A4(
	$elm$json$Json$Decode$map3,
	$author$project$CreativeBriefEditor$ImageModel,
	A2($elm$json$Json$Decode$field, 'name', $elm$json$Json$Decode$string),
	A2($elm$json$Json$Decode$field, 'owner', $elm$json$Json$Decode$string),
	A2(
		$elm$json$Json$Decode$map,
		$elm$core$Maybe$withDefault(''),
		A2(
			$elm$json$Json$Decode$field,
			'description',
			$elm$json$Json$Decode$nullable($elm$json$Json$Decode$string))));
var $author$project$CreativeBriefEditor$decodeImageModelsList = A2(
	$elm$json$Json$Decode$field,
	'models',
	$elm$json$Json$Decode$list($author$project$CreativeBriefEditor$decodeImageModel));
var $author$project$CreativeBriefEditor$fetchImageModels = $elm$http$Http$get(
	{
		expect: A2($elm$http$Http$expectJson, $author$project$CreativeBriefEditor$ImageModelsFetched, $author$project$CreativeBriefEditor$decodeImageModelsList),
		url: '/api/image-models?collection=text-to-image'
	});
var $author$project$CreativeBriefEditor$init = function (key) {
	return _Utils_Tuple2(
		{autoScenePrompt: '', briefId: $elm$core$Maybe$Nothing, category: 'luxury', error: $elm$core$Maybe$Nothing, generatingImages: false, imageModels: _List_Nil, imageUrl: '', isLoading: false, llmProvider: 'openrouter', loadingImageModels: true, navigationKey: key, platform: 'tiktok', response: $elm$core$Maybe$Nothing, selectedFile: $elm$core$Maybe$Nothing, selectedImageModel: $elm$core$Maybe$Nothing, text: '', videoUrl: ''},
		$author$project$CreativeBriefEditor$fetchImageModels);
};
var $author$project$Image$ModelsFetched = function (a) {
	return {$: 'ModelsFetched', a: a};
};
var $author$project$Image$ImageModel = F4(
	function (id, name, description, inputSchema) {
		return {description: description, id: id, inputSchema: inputSchema, name: name};
	});
var $author$project$Image$videoModelDecoder = A5(
	$elm$json$Json$Decode$map4,
	$author$project$Image$ImageModel,
	A2($elm$json$Json$Decode$field, 'id', $elm$json$Json$Decode$string),
	A2($elm$json$Json$Decode$field, 'name', $elm$json$Json$Decode$string),
	$elm$json$Json$Decode$oneOf(
		_List_fromArray(
			[
				A2($elm$json$Json$Decode$field, 'description', $elm$json$Json$Decode$string),
				$elm$json$Json$Decode$succeed('No description available')
			])),
	$elm$json$Json$Decode$maybe(
		A2($elm$json$Json$Decode$field, 'input_schema', $elm$json$Json$Decode$value)));
var $author$project$Image$fetchModels = function (collection) {
	return $elm$http$Http$get(
		{
			expect: A2(
				$elm$http$Http$expectJson,
				$author$project$Image$ModelsFetched,
				A2(
					$elm$json$Json$Decode$field,
					'models',
					$elm$json$Json$Decode$list($author$project$Image$videoModelDecoder))),
			url: '/api/image-models?collection=' + collection
		});
};
var $author$project$Image$init = _Utils_Tuple2(
	{error: $elm$core$Maybe$Nothing, imageStatus: '', isGenerating: false, models: _List_Nil, outputImage: $elm$core$Maybe$Nothing, parameters: _List_Nil, pollingImageId: $elm$core$Maybe$Nothing, requiredFields: _List_Nil, searchQuery: '', selectedCollection: 'text-to-image', selectedModel: $elm$core$Maybe$Nothing, selectedVersion: $elm$core$Maybe$Nothing, uploadingFile: $elm$core$Maybe$Nothing},
	$author$project$Image$fetchModels('text-to-image'));
var $author$project$ImageGallery$ImagesFetched = function (a) {
	return {$: 'ImagesFetched', a: a};
};
var $author$project$ImageGallery$imageDecoder = A2(
	$elm$json$Json$Decode$andThen,
	function (record) {
		return A3(
			$elm$json$Json$Decode$map2,
			F2(
				function (status, metadata) {
					return _Utils_update(
						record,
						{metadata: metadata, status: status});
				}),
			$elm$json$Json$Decode$oneOf(
				_List_fromArray(
					[
						A2($elm$json$Json$Decode$field, 'status', $elm$json$Json$Decode$string),
						$elm$json$Json$Decode$succeed('completed')
					])),
			$elm$json$Json$Decode$maybe(
				A2($elm$json$Json$Decode$field, 'metadata', $elm$json$Json$Decode$value)));
	},
	A9(
		$elm$json$Json$Decode$map8,
		F8(
			function (id, prompt, imageUrl, thumbnailUrl, modelId, createdAt, collection, parameters) {
				return {collection: collection, createdAt: createdAt, id: id, imageUrl: imageUrl, metadata: $elm$core$Maybe$Nothing, modelId: modelId, parameters: parameters, prompt: prompt, status: 'completed', thumbnailUrl: thumbnailUrl};
			}),
		A2($elm$json$Json$Decode$field, 'id', $elm$json$Json$Decode$int),
		A2($elm$json$Json$Decode$field, 'prompt', $elm$json$Json$Decode$string),
		A2($elm$json$Json$Decode$field, 'image_url', $elm$json$Json$Decode$string),
		A2($elm$json$Json$Decode$field, 'thumbnail_url', $elm$json$Json$Decode$string),
		A2($elm$json$Json$Decode$field, 'model_id', $elm$json$Json$Decode$string),
		A2($elm$json$Json$Decode$field, 'created_at', $elm$json$Json$Decode$string),
		$elm$json$Json$Decode$maybe(
			A2($elm$json$Json$Decode$field, 'collection', $elm$json$Json$Decode$string)),
		$elm$json$Json$Decode$maybe(
			A2($elm$json$Json$Decode$field, 'parameters', $elm$json$Json$Decode$value))));
var $author$project$ImageGallery$fetchImages = $elm$http$Http$get(
	{
		expect: A2(
			$elm$http$Http$expectJson,
			$author$project$ImageGallery$ImagesFetched,
			A2(
				$elm$json$Json$Decode$field,
				'images',
				$elm$json$Json$Decode$list($author$project$ImageGallery$imageDecoder))),
		url: '/api/images?limit=50'
	});
var $author$project$ImageGallery$VideoModelsFetched = function (a) {
	return {$: 'VideoModelsFetched', a: a};
};
var $author$project$ImageGallery$VideoModel = F3(
	function (id, name, description) {
		return {description: description, id: id, name: name};
	});
var $author$project$ImageGallery$videoModelDecoder = A4(
	$elm$json$Json$Decode$map3,
	$author$project$ImageGallery$VideoModel,
	A2($elm$json$Json$Decode$field, 'id', $elm$json$Json$Decode$string),
	A2($elm$json$Json$Decode$field, 'name', $elm$json$Json$Decode$string),
	A2($elm$json$Json$Decode$field, 'description', $elm$json$Json$Decode$string));
var $author$project$ImageGallery$fetchVideoModels = $elm$http$Http$get(
	{
		expect: A2(
			$elm$http$Http$expectJson,
			$author$project$ImageGallery$VideoModelsFetched,
			A2(
				$elm$json$Json$Decode$field,
				'models',
				$elm$json$Json$Decode$list($author$project$ImageGallery$videoModelDecoder))),
		url: '/api/video-models?collection=image-to-video'
	});
var $author$project$ImageGallery$init = _Utils_Tuple2(
	{error: $elm$core$Maybe$Nothing, images: _List_Nil, loading: true, loadingModels: true, selectedImage: $elm$core$Maybe$Nothing, selectedVideoModel: $elm$core$Maybe$Nothing, showRawData: false, videoModels: _List_Nil},
	$elm$core$Platform$Cmd$batch(
		_List_fromArray(
			[$author$project$ImageGallery$fetchImages, $author$project$ImageGallery$fetchVideoModels])));
var $author$project$SimulationGallery$VideosFetched = function (a) {
	return {$: 'VideosFetched', a: a};
};
var $author$project$SimulationGallery$videoDecoder = A2(
	$elm$json$Json$Decode$andThen,
	function (record) {
		return A2(
			$elm$json$Json$Decode$map,
			function (metadata) {
				return _Utils_update(
					record,
					{metadata: metadata});
			},
			$elm$json$Json$Decode$maybe(
				A2($elm$json$Json$Decode$field, 'metadata', $elm$json$Json$Decode$value)));
	},
	A2(
		$elm$json$Json$Decode$andThen,
		function (record) {
			return A3(
				$elm$json$Json$Decode$map2,
				F2(
					function (createdAt, status) {
						return _Utils_update(
							record,
							{createdAt: createdAt, status: status});
					}),
				A2($elm$json$Json$Decode$field, 'created_at', $elm$json$Json$Decode$string),
				A2($elm$json$Json$Decode$field, 'status', $elm$json$Json$Decode$string));
		},
		A9(
			$elm$json$Json$Decode$map8,
			F8(
				function (id, videoPath, quality, duration, fps, resolution, sceneContext, objectDescriptions) {
					return {createdAt: '', duration: duration, fps: fps, id: id, metadata: $elm$core$Maybe$Nothing, objectDescriptions: objectDescriptions, quality: quality, resolution: resolution, sceneContext: sceneContext, status: 'completed', videoPath: videoPath};
				}),
			A2($elm$json$Json$Decode$field, 'id', $elm$json$Json$Decode$int),
			A2($elm$json$Json$Decode$field, 'video_path', $elm$json$Json$Decode$string),
			A2($elm$json$Json$Decode$field, 'quality', $elm$json$Json$Decode$string),
			A2($elm$json$Json$Decode$field, 'duration', $elm$json$Json$Decode$float),
			A2($elm$json$Json$Decode$field, 'fps', $elm$json$Json$Decode$int),
			A2($elm$json$Json$Decode$field, 'resolution', $elm$json$Json$Decode$string),
			$elm$json$Json$Decode$maybe(
				A2($elm$json$Json$Decode$field, 'scene_context', $elm$json$Json$Decode$string)),
			$elm$json$Json$Decode$maybe(
				A2($elm$json$Json$Decode$field, 'object_descriptions', $elm$json$Json$Decode$value)))));
var $author$project$SimulationGallery$fetchVideos = $elm$http$Http$get(
	{
		expect: A2(
			$elm$http$Http$expectJson,
			$author$project$SimulationGallery$VideosFetched,
			A2(
				$elm$json$Json$Decode$field,
				'videos',
				$elm$json$Json$Decode$list($author$project$SimulationGallery$videoDecoder))),
		url: '/api/genesis/videos?limit=50'
	});
var $author$project$SimulationGallery$init = _Utils_Tuple2(
	{error: $elm$core$Maybe$Nothing, loading: true, selectedVideo: $elm$core$Maybe$Nothing, showRawData: false, videos: _List_Nil},
	$author$project$SimulationGallery$fetchVideos);
var $author$project$Video$ModelsFetched = function (a) {
	return {$: 'ModelsFetched', a: a};
};
var $author$project$Video$VideoModel = F4(
	function (id, name, description, inputSchema) {
		return {description: description, id: id, inputSchema: inputSchema, name: name};
	});
var $author$project$Video$videoModelDecoder = A5(
	$elm$json$Json$Decode$map4,
	$author$project$Video$VideoModel,
	A2($elm$json$Json$Decode$field, 'id', $elm$json$Json$Decode$string),
	A2($elm$json$Json$Decode$field, 'name', $elm$json$Json$Decode$string),
	$elm$json$Json$Decode$oneOf(
		_List_fromArray(
			[
				A2($elm$json$Json$Decode$field, 'description', $elm$json$Json$Decode$string),
				$elm$json$Json$Decode$succeed('No description available')
			])),
	$elm$json$Json$Decode$maybe(
		A2($elm$json$Json$Decode$field, 'input_schema', $elm$json$Json$Decode$value)));
var $author$project$Video$fetchModels = function (collection) {
	return $elm$http$Http$get(
		{
			expect: A2(
				$elm$http$Http$expectJson,
				$author$project$Video$ModelsFetched,
				A2(
					$elm$json$Json$Decode$field,
					'models',
					$elm$json$Json$Decode$list($author$project$Video$videoModelDecoder))),
			url: '/api/video-models?collection=' + collection
		});
};
var $author$project$Video$init = _Utils_Tuple2(
	{error: $elm$core$Maybe$Nothing, isGenerating: false, models: _List_Nil, outputVideo: $elm$core$Maybe$Nothing, parameters: _List_Nil, pendingModelSelection: $elm$core$Maybe$Nothing, pendingParameters: _List_Nil, pollingVideoId: $elm$core$Maybe$Nothing, requiredFields: _List_Nil, searchQuery: '', selectedCollection: 'text-to-video', selectedModel: $elm$core$Maybe$Nothing, selectedVersion: $elm$core$Maybe$Nothing, uploadingFile: $elm$core$Maybe$Nothing, videoStatus: ''},
	$author$project$Video$fetchModels('text-to-video'));
var $author$project$VideoGallery$VideosFetched = function (a) {
	return {$: 'VideosFetched', a: a};
};
var $elm$core$Tuple$pair = F2(
	function (a, b) {
		return _Utils_Tuple2(a, b);
	});
var $author$project$VideoGallery$videoDecoder = A2(
	$elm$json$Json$Decode$andThen,
	function (record) {
		return A3(
			$elm$json$Json$Decode$map2,
			F2(
				function (metadata, status) {
					return _Utils_update(
						record,
						{metadata: metadata, status: status});
				}),
			$elm$json$Json$Decode$maybe(
				A2($elm$json$Json$Decode$field, 'metadata', $elm$json$Json$Decode$value)),
			$elm$json$Json$Decode$oneOf(
				_List_fromArray(
					[
						A2($elm$json$Json$Decode$field, 'status', $elm$json$Json$Decode$string),
						$elm$json$Json$Decode$succeed('completed')
					])));
	},
	A9(
		$elm$json$Json$Decode$map8,
		F8(
			function (id, prompt, videoUrl, thumbnailUrl, modelId, createdAt, collection, parameters) {
				return {collection: collection, createdAt: createdAt, id: id, metadata: $elm$core$Maybe$Nothing, modelId: modelId, parameters: parameters, prompt: prompt, status: 'completed', thumbnailUrl: thumbnailUrl, videoUrl: videoUrl};
			}),
		A2($elm$json$Json$Decode$field, 'id', $elm$json$Json$Decode$int),
		A2($elm$json$Json$Decode$field, 'prompt', $elm$json$Json$Decode$string),
		A2($elm$json$Json$Decode$field, 'video_url', $elm$json$Json$Decode$string),
		A2($elm$json$Json$Decode$field, 'thumbnail_url', $elm$json$Json$Decode$string),
		A2($elm$json$Json$Decode$field, 'model_id', $elm$json$Json$Decode$string),
		A2($elm$json$Json$Decode$field, 'created_at', $elm$json$Json$Decode$string),
		$elm$json$Json$Decode$maybe(
			A2($elm$json$Json$Decode$field, 'collection', $elm$json$Json$Decode$string)),
		$elm$json$Json$Decode$maybe(
			A2($elm$json$Json$Decode$field, 'parameters', $elm$json$Json$Decode$value))));
var $author$project$VideoGallery$videosResponseDecoder = A3(
	$elm$json$Json$Decode$map2,
	$elm$core$Tuple$pair,
	A2(
		$elm$json$Json$Decode$field,
		'videos',
		$elm$json$Json$Decode$list($author$project$VideoGallery$videoDecoder)),
	A2($elm$json$Json$Decode$field, 'total', $elm$json$Json$Decode$int));
var $author$project$VideoGallery$fetchVideos = F2(
	function (limit, offset) {
		return $elm$http$Http$get(
			{
				expect: A2($elm$http$Http$expectJson, $author$project$VideoGallery$VideosFetched, $author$project$VideoGallery$videosResponseDecoder),
				url: '/api/videos?limit=' + ($elm$core$String$fromInt(limit) + ('&offset=' + $elm$core$String$fromInt(offset)))
			});
	});
var $author$project$VideoGallery$init = _Utils_Tuple2(
	{currentPage: 1, error: $elm$core$Maybe$Nothing, loading: true, pageSize: 20, selectedVideo: $elm$core$Maybe$Nothing, showRawData: false, totalVideos: 0, videos: _List_Nil},
	A2($author$project$VideoGallery$fetchVideos, 20, 0));
var $author$project$VideoToText$ModelsFetched = function (a) {
	return {$: 'ModelsFetched', a: a};
};
var $author$project$VideoToText$VideoToTextModel = F4(
	function (id, name, description, inputSchema) {
		return {description: description, id: id, inputSchema: inputSchema, name: name};
	});
var $author$project$VideoToText$videoToTextModelDecoder = A5(
	$elm$json$Json$Decode$map4,
	$author$project$VideoToText$VideoToTextModel,
	A2($elm$json$Json$Decode$field, 'id', $elm$json$Json$Decode$string),
	A2($elm$json$Json$Decode$field, 'name', $elm$json$Json$Decode$string),
	$elm$json$Json$Decode$oneOf(
		_List_fromArray(
			[
				A2($elm$json$Json$Decode$field, 'description', $elm$json$Json$Decode$string),
				$elm$json$Json$Decode$succeed('No description available')
			])),
	$elm$json$Json$Decode$maybe(
		A2($elm$json$Json$Decode$field, 'input_schema', $elm$json$Json$Decode$value)));
var $author$project$VideoToText$fetchModels = function (collection) {
	return $elm$http$Http$get(
		{
			expect: A2(
				$elm$http$Http$expectJson,
				$author$project$VideoToText$ModelsFetched,
				A2(
					$elm$json$Json$Decode$field,
					'models',
					$elm$json$Json$Decode$list($author$project$VideoToText$videoToTextModelDecoder))),
			url: '/api/video-models?collection=' + collection
		});
};
var $author$project$VideoToText$init = _Utils_Tuple2(
	{error: $elm$core$Maybe$Nothing, generationStatus: '', isGenerating: false, models: _List_Nil, outputText: $elm$core$Maybe$Nothing, parameters: _List_Nil, pendingModelSelection: $elm$core$Maybe$Nothing, pendingParameters: _List_Nil, pollingVideoId: $elm$core$Maybe$Nothing, requiredFields: _List_Nil, searchQuery: '', selectedCollection: 'video-to-text', selectedModel: $elm$core$Maybe$Nothing, selectedVersion: $elm$core$Maybe$Nothing, uploadingFile: $elm$core$Maybe$Nothing},
	$author$project$VideoToText$fetchModels('video-to-text'));
var $author$project$VideoToTextGallery$VideosFetched = function (a) {
	return {$: 'VideosFetched', a: a};
};
var $author$project$VideoToTextGallery$videoDecoder = A2(
	$elm$json$Json$Decode$andThen,
	function (record) {
		return A2(
			$elm$json$Json$Decode$map,
			function (status) {
				return _Utils_update(
					record,
					{status: status});
			},
			$elm$json$Json$Decode$oneOf(
				_List_fromArray(
					[
						A2($elm$json$Json$Decode$field, 'status', $elm$json$Json$Decode$string),
						$elm$json$Json$Decode$succeed('completed')
					])));
	},
	A9(
		$elm$json$Json$Decode$map8,
		F8(
			function (id, prompt, outputText, modelId, createdAt, collection, parameters, metadata) {
				return {collection: collection, createdAt: createdAt, id: id, metadata: metadata, modelId: modelId, outputText: outputText, parameters: parameters, prompt: prompt, status: 'completed'};
			}),
		A2($elm$json$Json$Decode$field, 'id', $elm$json$Json$Decode$int),
		A2($elm$json$Json$Decode$field, 'prompt', $elm$json$Json$Decode$string),
		$elm$json$Json$Decode$oneOf(
			_List_fromArray(
				[
					A2($elm$json$Json$Decode$field, 'output_text', $elm$json$Json$Decode$string),
					A2($elm$json$Json$Decode$field, 'video_url', $elm$json$Json$Decode$string),
					$elm$json$Json$Decode$succeed('')
				])),
		A2($elm$json$Json$Decode$field, 'model_id', $elm$json$Json$Decode$string),
		A2($elm$json$Json$Decode$field, 'created_at', $elm$json$Json$Decode$string),
		$elm$json$Json$Decode$maybe(
			A2($elm$json$Json$Decode$field, 'collection', $elm$json$Json$Decode$string)),
		$elm$json$Json$Decode$maybe(
			A2($elm$json$Json$Decode$field, 'parameters', $elm$json$Json$Decode$value)),
		$elm$json$Json$Decode$maybe(
			A2($elm$json$Json$Decode$field, 'metadata', $elm$json$Json$Decode$value))));
var $author$project$VideoToTextGallery$videosResponseDecoder = A3(
	$elm$json$Json$Decode$map2,
	$elm$core$Tuple$pair,
	A2(
		$elm$json$Json$Decode$field,
		'videos',
		$elm$json$Json$Decode$list($author$project$VideoToTextGallery$videoDecoder)),
	A2($elm$json$Json$Decode$field, 'total', $elm$json$Json$Decode$int));
var $author$project$VideoToTextGallery$fetchVideos = F2(
	function (limit, offset) {
		return $elm$http$Http$get(
			{
				expect: A2($elm$http$Http$expectJson, $author$project$VideoToTextGallery$VideosFetched, $author$project$VideoToTextGallery$videosResponseDecoder),
				url: '/api/videos?collection=video-to-text&limit=' + ($elm$core$String$fromInt(limit) + ('&offset=' + $elm$core$String$fromInt(offset)))
			});
	});
var $author$project$VideoToTextGallery$init = _Utils_Tuple2(
	{currentPage: 1, error: $elm$core$Maybe$Nothing, loading: true, pageSize: 20, selectedVideo: $elm$core$Maybe$Nothing, showRawData: false, totalVideos: 0, videos: _List_Nil},
	A2($author$project$VideoToTextGallery$fetchVideos, 20, 0));
var $elm$core$Platform$Cmd$map = _Platform_map;
var $author$project$Main$init = F3(
	function (_v0, url, key) {
		var route = $author$project$Route$fromUrl(url);
		var _v1 = $author$project$VideoToTextGallery$init;
		var videoToTextGalleryModel = _v1.a;
		var videoToTextGalleryCmd = _v1.b;
		var _v2 = $author$project$VideoToText$init;
		var videoToTextModel = _v2.a;
		var videoToTextCmd = _v2.b;
		var _v3 = $author$project$Video$init;
		var videoModel = _v3.a;
		var videoCmd = _v3.b;
		var _v4 = $author$project$SimulationGallery$init;
		var simulationGalleryModel = _v4.a;
		var simulationGalleryCmd = _v4.b;
		var _v5 = $author$project$ImageGallery$init;
		var imageGalleryModel = _v5.a;
		var imageGalleryCmd = _v5.b;
		var _v6 = $author$project$Image$init;
		var imageModel = _v6.a;
		var imageCmd = _v6.b;
		var _v7 = $author$project$VideoGallery$init;
		var galleryModel = _v7.a;
		var galleryCmd = _v7.b;
		var _v8 = $author$project$CreativeBriefEditor$init(key);
		var creativeBriefEditorModel = _v8.a;
		var creativeBriefEditorCmd = _v8.b;
		var _v9 = $author$project$BriefGallery$init(key);
		var briefGalleryModel = _v9.a;
		var briefGalleryCmd = _v9.b;
		var _v10 = $author$project$AudioGallery$init;
		var audioGalleryModel = _v10.a;
		var audioGalleryCmd = _v10.b;
		var _v11 = $author$project$Audio$init;
		var audioModel = _v11.a;
		var audioCmd = _v11.b;
		return _Utils_Tuple2(
			{
				audioDetailModel: $elm$core$Maybe$Nothing,
				audioGalleryModel: audioGalleryModel,
				audioModel: audioModel,
				authModel: $author$project$Auth$init,
				briefGalleryModel: briefGalleryModel,
				creativeBriefEditorModel: creativeBriefEditorModel,
				ctrlPressed: false,
				future: _List_Nil,
				galleryModel: galleryModel,
				history: _List_Nil,
				imageDetailModel: $elm$core$Maybe$Nothing,
				imageGalleryModel: imageGalleryModel,
				imageModel: imageModel,
				initialScene: $elm$core$Maybe$Nothing,
				key: key,
				pendingVideoFromImage: $elm$core$Maybe$Nothing,
				route: route,
				scene: {objects: $elm$core$Dict$empty, selectedObject: $elm$core$Maybe$Nothing},
				simulationGalleryModel: simulationGalleryModel,
				simulationState: {isRunning: false, transformMode: $author$project$Main$Translate},
				uiState: {errorMessage: $elm$core$Maybe$Nothing, isGenerating: false, isRefining: false, refineInput: '', textInput: ''},
				url: url,
				videoDetailModel: $elm$core$Maybe$Nothing,
				videoModel: videoModel,
				videoToTextGalleryModel: videoToTextGalleryModel,
				videoToTextModel: videoToTextModel
			},
			$elm$core$Platform$Cmd$batch(
				_List_fromArray(
					[
						A2($elm$core$Platform$Cmd$map, $author$project$Main$VideoMsg, videoCmd),
						A2($elm$core$Platform$Cmd$map, $author$project$Main$GalleryMsg, galleryCmd),
						A2($elm$core$Platform$Cmd$map, $author$project$Main$SimulationGalleryMsg, simulationGalleryCmd),
						A2($elm$core$Platform$Cmd$map, $author$project$Main$ImageMsg, imageCmd),
						A2($elm$core$Platform$Cmd$map, $author$project$Main$ImageGalleryMsg, imageGalleryCmd),
						A2($elm$core$Platform$Cmd$map, $author$project$Main$AudioMsg, audioCmd),
						A2($elm$core$Platform$Cmd$map, $author$project$Main$AudioGalleryMsg, audioGalleryCmd),
						A2($elm$core$Platform$Cmd$map, $author$project$Main$VideoToTextMsg, videoToTextCmd),
						A2($elm$core$Platform$Cmd$map, $author$project$Main$VideoToTextGalleryMsg, videoToTextGalleryCmd),
						A2($elm$core$Platform$Cmd$map, $author$project$Main$CreativeBriefEditorMsg, creativeBriefEditorCmd),
						A2($elm$core$Platform$Cmd$map, $author$project$Main$BriefGalleryMsg, briefGalleryCmd),
						A2($elm$core$Platform$Cmd$map, $author$project$Main$AuthMsg, $author$project$Auth$checkAuth)
					])));
	});
var $author$project$Main$AudioDetailMsg = function (a) {
	return {$: 'AudioDetailMsg', a: a};
};
var $author$project$Main$ImageDetailMsg = function (a) {
	return {$: 'ImageDetailMsg', a: a};
};
var $author$project$Main$KeyDown = function (a) {
	return {$: 'KeyDown', a: a};
};
var $author$project$Main$KeyUp = function (a) {
	return {$: 'KeyUp', a: a};
};
var $author$project$Main$SceneLoadedFromStorage = function (a) {
	return {$: 'SceneLoadedFromStorage', a: a};
};
var $author$project$Main$SelectionChanged = function (a) {
	return {$: 'SelectionChanged', a: a};
};
var $author$project$Main$TransformUpdated = function (a) {
	return {$: 'TransformUpdated', a: a};
};
var $author$project$Main$VideoDetailMsg = function (a) {
	return {$: 'VideoDetailMsg', a: a};
};
var $elm$core$Platform$Sub$batch = _Platform_batch;
var $author$project$Main$keyDecoder = A2($elm$json$Json$Decode$field, 'key', $elm$json$Json$Decode$string);
var $elm$core$Platform$Sub$map = _Platform_map;
var $elm$core$Platform$Sub$none = $elm$core$Platform$Sub$batch(_List_Nil);
var $elm$browser$Browser$Events$Document = {$: 'Document'};
var $elm$browser$Browser$Events$MySub = F3(
	function (a, b, c) {
		return {$: 'MySub', a: a, b: b, c: c};
	});
var $elm$browser$Browser$Events$State = F2(
	function (subs, pids) {
		return {pids: pids, subs: subs};
	});
var $elm$browser$Browser$Events$init = $elm$core$Task$succeed(
	A2($elm$browser$Browser$Events$State, _List_Nil, $elm$core$Dict$empty));
var $elm$browser$Browser$Events$nodeToKey = function (node) {
	if (node.$ === 'Document') {
		return 'd_';
	} else {
		return 'w_';
	}
};
var $elm$browser$Browser$Events$addKey = function (sub) {
	var node = sub.a;
	var name = sub.b;
	return _Utils_Tuple2(
		_Utils_ap(
			$elm$browser$Browser$Events$nodeToKey(node),
			name),
		sub);
};
var $elm$core$Dict$fromList = function (assocs) {
	return A3(
		$elm$core$List$foldl,
		F2(
			function (_v0, dict) {
				var key = _v0.a;
				var value = _v0.b;
				return A3($elm$core$Dict$insert, key, value, dict);
			}),
		$elm$core$Dict$empty,
		assocs);
};
var $elm$core$Dict$foldl = F3(
	function (func, acc, dict) {
		foldl:
		while (true) {
			if (dict.$ === 'RBEmpty_elm_builtin') {
				return acc;
			} else {
				var key = dict.b;
				var value = dict.c;
				var left = dict.d;
				var right = dict.e;
				var $temp$func = func,
					$temp$acc = A3(
					func,
					key,
					value,
					A3($elm$core$Dict$foldl, func, acc, left)),
					$temp$dict = right;
				func = $temp$func;
				acc = $temp$acc;
				dict = $temp$dict;
				continue foldl;
			}
		}
	});
var $elm$core$Dict$merge = F6(
	function (leftStep, bothStep, rightStep, leftDict, rightDict, initialResult) {
		var stepState = F3(
			function (rKey, rValue, _v0) {
				stepState:
				while (true) {
					var list = _v0.a;
					var result = _v0.b;
					if (!list.b) {
						return _Utils_Tuple2(
							list,
							A3(rightStep, rKey, rValue, result));
					} else {
						var _v2 = list.a;
						var lKey = _v2.a;
						var lValue = _v2.b;
						var rest = list.b;
						if (_Utils_cmp(lKey, rKey) < 0) {
							var $temp$rKey = rKey,
								$temp$rValue = rValue,
								$temp$_v0 = _Utils_Tuple2(
								rest,
								A3(leftStep, lKey, lValue, result));
							rKey = $temp$rKey;
							rValue = $temp$rValue;
							_v0 = $temp$_v0;
							continue stepState;
						} else {
							if (_Utils_cmp(lKey, rKey) > 0) {
								return _Utils_Tuple2(
									list,
									A3(rightStep, rKey, rValue, result));
							} else {
								return _Utils_Tuple2(
									rest,
									A4(bothStep, lKey, lValue, rValue, result));
							}
						}
					}
				}
			});
		var _v3 = A3(
			$elm$core$Dict$foldl,
			stepState,
			_Utils_Tuple2(
				$elm$core$Dict$toList(leftDict),
				initialResult),
			rightDict);
		var leftovers = _v3.a;
		var intermediateResult = _v3.b;
		return A3(
			$elm$core$List$foldl,
			F2(
				function (_v4, result) {
					var k = _v4.a;
					var v = _v4.b;
					return A3(leftStep, k, v, result);
				}),
			intermediateResult,
			leftovers);
	});
var $elm$browser$Browser$Events$Event = F2(
	function (key, event) {
		return {event: event, key: key};
	});
var $elm$browser$Browser$Events$spawn = F3(
	function (router, key, _v0) {
		var node = _v0.a;
		var name = _v0.b;
		var actualNode = function () {
			if (node.$ === 'Document') {
				return _Browser_doc;
			} else {
				return _Browser_window;
			}
		}();
		return A2(
			$elm$core$Task$map,
			function (value) {
				return _Utils_Tuple2(key, value);
			},
			A3(
				_Browser_on,
				actualNode,
				name,
				function (event) {
					return A2(
						$elm$core$Platform$sendToSelf,
						router,
						A2($elm$browser$Browser$Events$Event, key, event));
				}));
	});
var $elm$core$Dict$union = F2(
	function (t1, t2) {
		return A3($elm$core$Dict$foldl, $elm$core$Dict$insert, t2, t1);
	});
var $elm$browser$Browser$Events$onEffects = F3(
	function (router, subs, state) {
		var stepRight = F3(
			function (key, sub, _v6) {
				var deads = _v6.a;
				var lives = _v6.b;
				var news = _v6.c;
				return _Utils_Tuple3(
					deads,
					lives,
					A2(
						$elm$core$List$cons,
						A3($elm$browser$Browser$Events$spawn, router, key, sub),
						news));
			});
		var stepLeft = F3(
			function (_v4, pid, _v5) {
				var deads = _v5.a;
				var lives = _v5.b;
				var news = _v5.c;
				return _Utils_Tuple3(
					A2($elm$core$List$cons, pid, deads),
					lives,
					news);
			});
		var stepBoth = F4(
			function (key, pid, _v2, _v3) {
				var deads = _v3.a;
				var lives = _v3.b;
				var news = _v3.c;
				return _Utils_Tuple3(
					deads,
					A3($elm$core$Dict$insert, key, pid, lives),
					news);
			});
		var newSubs = A2($elm$core$List$map, $elm$browser$Browser$Events$addKey, subs);
		var _v0 = A6(
			$elm$core$Dict$merge,
			stepLeft,
			stepBoth,
			stepRight,
			state.pids,
			$elm$core$Dict$fromList(newSubs),
			_Utils_Tuple3(_List_Nil, $elm$core$Dict$empty, _List_Nil));
		var deadPids = _v0.a;
		var livePids = _v0.b;
		var makeNewPids = _v0.c;
		return A2(
			$elm$core$Task$andThen,
			function (pids) {
				return $elm$core$Task$succeed(
					A2(
						$elm$browser$Browser$Events$State,
						newSubs,
						A2(
							$elm$core$Dict$union,
							livePids,
							$elm$core$Dict$fromList(pids))));
			},
			A2(
				$elm$core$Task$andThen,
				function (_v1) {
					return $elm$core$Task$sequence(makeNewPids);
				},
				$elm$core$Task$sequence(
					A2($elm$core$List$map, $elm$core$Process$kill, deadPids))));
	});
var $elm$browser$Browser$Events$onSelfMsg = F3(
	function (router, _v0, state) {
		var key = _v0.key;
		var event = _v0.event;
		var toMessage = function (_v2) {
			var subKey = _v2.a;
			var _v3 = _v2.b;
			var node = _v3.a;
			var name = _v3.b;
			var decoder = _v3.c;
			return _Utils_eq(subKey, key) ? A2(_Browser_decodeEvent, decoder, event) : $elm$core$Maybe$Nothing;
		};
		var messages = A2($elm$core$List$filterMap, toMessage, state.subs);
		return A2(
			$elm$core$Task$andThen,
			function (_v1) {
				return $elm$core$Task$succeed(state);
			},
			$elm$core$Task$sequence(
				A2(
					$elm$core$List$map,
					$elm$core$Platform$sendToApp(router),
					messages)));
	});
var $elm$browser$Browser$Events$subMap = F2(
	function (func, _v0) {
		var node = _v0.a;
		var name = _v0.b;
		var decoder = _v0.c;
		return A3(
			$elm$browser$Browser$Events$MySub,
			node,
			name,
			A2($elm$json$Json$Decode$map, func, decoder));
	});
_Platform_effectManagers['Browser.Events'] = _Platform_createManager($elm$browser$Browser$Events$init, $elm$browser$Browser$Events$onEffects, $elm$browser$Browser$Events$onSelfMsg, 0, $elm$browser$Browser$Events$subMap);
var $elm$browser$Browser$Events$subscription = _Platform_leaf('Browser.Events');
var $elm$browser$Browser$Events$on = F3(
	function (node, name, decoder) {
		return $elm$browser$Browser$Events$subscription(
			A3($elm$browser$Browser$Events$MySub, node, name, decoder));
	});
var $elm$browser$Browser$Events$onKeyDown = A2($elm$browser$Browser$Events$on, $elm$browser$Browser$Events$Document, 'keydown');
var $elm$browser$Browser$Events$onKeyUp = A2($elm$browser$Browser$Events$on, $elm$browser$Browser$Events$Document, 'keyup');
var $author$project$Main$sceneLoadedFromStorage = _Platform_incomingPort('sceneLoadedFromStorage', $elm$json$Json$Decode$value);
var $author$project$Main$sendSelectionToElm = _Platform_incomingPort(
	'sendSelectionToElm',
	$elm$json$Json$Decode$oneOf(
		_List_fromArray(
			[
				$elm$json$Json$Decode$null($elm$core$Maybe$Nothing),
				A2($elm$json$Json$Decode$map, $elm$core$Maybe$Just, $elm$json$Json$Decode$string)
			])));
var $author$project$Main$sendTransformUpdateToElm = _Platform_incomingPort(
	'sendTransformUpdateToElm',
	A2(
		$elm$json$Json$Decode$andThen,
		function (transform) {
			return A2(
				$elm$json$Json$Decode$andThen,
				function (objectId) {
					return $elm$json$Json$Decode$succeed(
						{objectId: objectId, transform: transform});
				},
				A2($elm$json$Json$Decode$field, 'objectId', $elm$json$Json$Decode$string));
		},
		A2(
			$elm$json$Json$Decode$field,
			'transform',
			A2(
				$elm$json$Json$Decode$andThen,
				function (scale) {
					return A2(
						$elm$json$Json$Decode$andThen,
						function (rotation) {
							return A2(
								$elm$json$Json$Decode$andThen,
								function (position) {
									return $elm$json$Json$Decode$succeed(
										{position: position, rotation: rotation, scale: scale});
								},
								A2(
									$elm$json$Json$Decode$field,
									'position',
									A2(
										$elm$json$Json$Decode$andThen,
										function (z) {
											return A2(
												$elm$json$Json$Decode$andThen,
												function (y) {
													return A2(
														$elm$json$Json$Decode$andThen,
														function (x) {
															return $elm$json$Json$Decode$succeed(
																{x: x, y: y, z: z});
														},
														A2($elm$json$Json$Decode$field, 'x', $elm$json$Json$Decode$float));
												},
												A2($elm$json$Json$Decode$field, 'y', $elm$json$Json$Decode$float));
										},
										A2($elm$json$Json$Decode$field, 'z', $elm$json$Json$Decode$float))));
						},
						A2(
							$elm$json$Json$Decode$field,
							'rotation',
							A2(
								$elm$json$Json$Decode$andThen,
								function (z) {
									return A2(
										$elm$json$Json$Decode$andThen,
										function (y) {
											return A2(
												$elm$json$Json$Decode$andThen,
												function (x) {
													return $elm$json$Json$Decode$succeed(
														{x: x, y: y, z: z});
												},
												A2($elm$json$Json$Decode$field, 'x', $elm$json$Json$Decode$float));
										},
										A2($elm$json$Json$Decode$field, 'y', $elm$json$Json$Decode$float));
								},
								A2($elm$json$Json$Decode$field, 'z', $elm$json$Json$Decode$float))));
				},
				A2(
					$elm$json$Json$Decode$field,
					'scale',
					A2(
						$elm$json$Json$Decode$andThen,
						function (z) {
							return A2(
								$elm$json$Json$Decode$andThen,
								function (y) {
									return A2(
										$elm$json$Json$Decode$andThen,
										function (x) {
											return $elm$json$Json$Decode$succeed(
												{x: x, y: y, z: z});
										},
										A2($elm$json$Json$Decode$field, 'x', $elm$json$Json$Decode$float));
								},
								A2($elm$json$Json$Decode$field, 'y', $elm$json$Json$Decode$float));
						},
						A2($elm$json$Json$Decode$field, 'z', $elm$json$Json$Decode$float)))))));
var $author$project$AudioDetail$PollTick = function (a) {
	return {$: 'PollTick', a: a};
};
var $elm$time$Time$Every = F2(
	function (a, b) {
		return {$: 'Every', a: a, b: b};
	});
var $elm$time$Time$State = F2(
	function (taggers, processes) {
		return {processes: processes, taggers: taggers};
	});
var $elm$time$Time$init = $elm$core$Task$succeed(
	A2($elm$time$Time$State, $elm$core$Dict$empty, $elm$core$Dict$empty));
var $elm$time$Time$addMySub = F2(
	function (_v0, state) {
		var interval = _v0.a;
		var tagger = _v0.b;
		var _v1 = A2($elm$core$Dict$get, interval, state);
		if (_v1.$ === 'Nothing') {
			return A3(
				$elm$core$Dict$insert,
				interval,
				_List_fromArray(
					[tagger]),
				state);
		} else {
			var taggers = _v1.a;
			return A3(
				$elm$core$Dict$insert,
				interval,
				A2($elm$core$List$cons, tagger, taggers),
				state);
		}
	});
var $elm$time$Time$Name = function (a) {
	return {$: 'Name', a: a};
};
var $elm$time$Time$Offset = function (a) {
	return {$: 'Offset', a: a};
};
var $elm$time$Time$Zone = F2(
	function (a, b) {
		return {$: 'Zone', a: a, b: b};
	});
var $elm$time$Time$customZone = $elm$time$Time$Zone;
var $elm$time$Time$setInterval = _Time_setInterval;
var $elm$time$Time$spawnHelp = F3(
	function (router, intervals, processes) {
		if (!intervals.b) {
			return $elm$core$Task$succeed(processes);
		} else {
			var interval = intervals.a;
			var rest = intervals.b;
			var spawnTimer = $elm$core$Process$spawn(
				A2(
					$elm$time$Time$setInterval,
					interval,
					A2($elm$core$Platform$sendToSelf, router, interval)));
			var spawnRest = function (id) {
				return A3(
					$elm$time$Time$spawnHelp,
					router,
					rest,
					A3($elm$core$Dict$insert, interval, id, processes));
			};
			return A2($elm$core$Task$andThen, spawnRest, spawnTimer);
		}
	});
var $elm$time$Time$onEffects = F3(
	function (router, subs, _v0) {
		var processes = _v0.processes;
		var rightStep = F3(
			function (_v6, id, _v7) {
				var spawns = _v7.a;
				var existing = _v7.b;
				var kills = _v7.c;
				return _Utils_Tuple3(
					spawns,
					existing,
					A2(
						$elm$core$Task$andThen,
						function (_v5) {
							return kills;
						},
						$elm$core$Process$kill(id)));
			});
		var newTaggers = A3($elm$core$List$foldl, $elm$time$Time$addMySub, $elm$core$Dict$empty, subs);
		var leftStep = F3(
			function (interval, taggers, _v4) {
				var spawns = _v4.a;
				var existing = _v4.b;
				var kills = _v4.c;
				return _Utils_Tuple3(
					A2($elm$core$List$cons, interval, spawns),
					existing,
					kills);
			});
		var bothStep = F4(
			function (interval, taggers, id, _v3) {
				var spawns = _v3.a;
				var existing = _v3.b;
				var kills = _v3.c;
				return _Utils_Tuple3(
					spawns,
					A3($elm$core$Dict$insert, interval, id, existing),
					kills);
			});
		var _v1 = A6(
			$elm$core$Dict$merge,
			leftStep,
			bothStep,
			rightStep,
			newTaggers,
			processes,
			_Utils_Tuple3(
				_List_Nil,
				$elm$core$Dict$empty,
				$elm$core$Task$succeed(_Utils_Tuple0)));
		var spawnList = _v1.a;
		var existingDict = _v1.b;
		var killTask = _v1.c;
		return A2(
			$elm$core$Task$andThen,
			function (newProcesses) {
				return $elm$core$Task$succeed(
					A2($elm$time$Time$State, newTaggers, newProcesses));
			},
			A2(
				$elm$core$Task$andThen,
				function (_v2) {
					return A3($elm$time$Time$spawnHelp, router, spawnList, existingDict);
				},
				killTask));
	});
var $elm$time$Time$Posix = function (a) {
	return {$: 'Posix', a: a};
};
var $elm$time$Time$millisToPosix = $elm$time$Time$Posix;
var $elm$time$Time$now = _Time_now($elm$time$Time$millisToPosix);
var $elm$time$Time$onSelfMsg = F3(
	function (router, interval, state) {
		var _v0 = A2($elm$core$Dict$get, interval, state.taggers);
		if (_v0.$ === 'Nothing') {
			return $elm$core$Task$succeed(state);
		} else {
			var taggers = _v0.a;
			var tellTaggers = function (time) {
				return $elm$core$Task$sequence(
					A2(
						$elm$core$List$map,
						function (tagger) {
							return A2(
								$elm$core$Platform$sendToApp,
								router,
								tagger(time));
						},
						taggers));
			};
			return A2(
				$elm$core$Task$andThen,
				function (_v1) {
					return $elm$core$Task$succeed(state);
				},
				A2($elm$core$Task$andThen, tellTaggers, $elm$time$Time$now));
		}
	});
var $elm$core$Basics$composeL = F3(
	function (g, f, x) {
		return g(
			f(x));
	});
var $elm$time$Time$subMap = F2(
	function (f, _v0) {
		var interval = _v0.a;
		var tagger = _v0.b;
		return A2(
			$elm$time$Time$Every,
			interval,
			A2($elm$core$Basics$composeL, f, tagger));
	});
_Platform_effectManagers['Time'] = _Platform_createManager($elm$time$Time$init, $elm$time$Time$onEffects, $elm$time$Time$onSelfMsg, 0, $elm$time$Time$subMap);
var $elm$time$Time$subscription = _Platform_leaf('Time');
var $elm$time$Time$every = F2(
	function (interval, tagger) {
		return $elm$time$Time$subscription(
			A2($elm$time$Time$Every, interval, tagger));
	});
var $author$project$AudioDetail$subscriptions = function (model) {
	return model.isPolling ? A2($elm$time$Time$every, 2000, $author$project$AudioDetail$PollTick) : $elm$core$Platform$Sub$none;
};
var $author$project$AudioGallery$Tick = function (a) {
	return {$: 'Tick', a: a};
};
var $author$project$AudioGallery$subscriptions = function (model) {
	return A2($elm$time$Time$every, 3000, $author$project$AudioGallery$Tick);
};
var $author$project$BriefGallery$subscriptions = function (model) {
	return $elm$core$Platform$Sub$none;
};
var $author$project$CreativeBriefEditor$FileLoaded = function (a) {
	return {$: 'FileLoaded', a: a};
};
var $author$project$Ports$fileLoaded = _Platform_incomingPort('fileLoaded', $elm$json$Json$Decode$string);
var $author$project$CreativeBriefEditor$subscriptions = function (model) {
	return $author$project$Ports$fileLoaded($author$project$CreativeBriefEditor$FileLoaded);
};
var $author$project$ImageDetail$PollTick = function (a) {
	return {$: 'PollTick', a: a};
};
var $author$project$ImageDetail$subscriptions = function (model) {
	return model.isPolling ? A2($elm$time$Time$every, 2000, $author$project$ImageDetail$PollTick) : $elm$core$Platform$Sub$none;
};
var $author$project$ImageGallery$Tick = function (a) {
	return {$: 'Tick', a: a};
};
var $author$project$ImageGallery$subscriptions = function (model) {
	return A2($elm$time$Time$every, 3000, $author$project$ImageGallery$Tick);
};
var $author$project$SimulationGallery$Tick = function (a) {
	return {$: 'Tick', a: a};
};
var $author$project$SimulationGallery$subscriptions = function (model) {
	return A2($elm$time$Time$every, 30000, $author$project$SimulationGallery$Tick);
};
var $author$project$VideoDetail$PollTick = function (a) {
	return {$: 'PollTick', a: a};
};
var $author$project$VideoDetail$subscriptions = function (model) {
	return model.isPolling ? A2($elm$time$Time$every, 2000, $author$project$VideoDetail$PollTick) : $elm$core$Platform$Sub$none;
};
var $author$project$VideoGallery$Tick = function (a) {
	return {$: 'Tick', a: a};
};
var $author$project$VideoGallery$subscriptions = function (model) {
	return A2($elm$time$Time$every, 3000, $author$project$VideoGallery$Tick);
};
var $author$project$VideoToTextGallery$Tick = function (a) {
	return {$: 'Tick', a: a};
};
var $author$project$VideoToTextGallery$subscriptions = function (model) {
	return A2($elm$time$Time$every, 3000, $author$project$VideoToTextGallery$Tick);
};
var $author$project$Main$subscriptions = function (model) {
	var videoToTextGallerySub = function () {
		var _v15 = model.route;
		if ((_v15.$ === 'Just') && (_v15.a.$ === 'VideoToTextGallery')) {
			var _v16 = _v15.a;
			return A2(
				$elm$core$Platform$Sub$map,
				$author$project$Main$VideoToTextGalleryMsg,
				$author$project$VideoToTextGallery$subscriptions(model.videoToTextGalleryModel));
		} else {
			return $elm$core$Platform$Sub$none;
		}
	}();
	var videoDetailSub = function () {
		var _v14 = _Utils_Tuple2(model.route, model.videoDetailModel);
		if (((_v14.a.$ === 'Just') && (_v14.a.a.$ === 'VideoDetail')) && (_v14.b.$ === 'Just')) {
			var videoDetailModel = _v14.b.a;
			return A2(
				$elm$core$Platform$Sub$map,
				$author$project$Main$VideoDetailMsg,
				$author$project$VideoDetail$subscriptions(videoDetailModel));
		} else {
			return $elm$core$Platform$Sub$none;
		}
	}();
	var simulationGallerySub = function () {
		var _v12 = model.route;
		if ((_v12.$ === 'Just') && (_v12.a.$ === 'SimulationGallery')) {
			var _v13 = _v12.a;
			return A2(
				$elm$core$Platform$Sub$map,
				$author$project$Main$SimulationGalleryMsg,
				$author$project$SimulationGallery$subscriptions(model.simulationGalleryModel));
		} else {
			return $elm$core$Platform$Sub$none;
		}
	}();
	var imageGallerySub = function () {
		var _v10 = model.route;
		if ((_v10.$ === 'Just') && (_v10.a.$ === 'ImageGallery')) {
			var _v11 = _v10.a;
			return A2(
				$elm$core$Platform$Sub$map,
				$author$project$Main$ImageGalleryMsg,
				$author$project$ImageGallery$subscriptions(model.imageGalleryModel));
		} else {
			return $elm$core$Platform$Sub$none;
		}
	}();
	var imageDetailSub = function () {
		var _v9 = _Utils_Tuple2(model.route, model.imageDetailModel);
		if (((_v9.a.$ === 'Just') && (_v9.a.a.$ === 'ImageDetail')) && (_v9.b.$ === 'Just')) {
			var imageDetailModel = _v9.b.a;
			return A2(
				$elm$core$Platform$Sub$map,
				$author$project$Main$ImageDetailMsg,
				$author$project$ImageDetail$subscriptions(imageDetailModel));
		} else {
			return $elm$core$Platform$Sub$none;
		}
	}();
	var gallerySub = function () {
		var _v7 = model.route;
		if ((_v7.$ === 'Just') && (_v7.a.$ === 'Gallery')) {
			var _v8 = _v7.a;
			return A2(
				$elm$core$Platform$Sub$map,
				$author$project$Main$GalleryMsg,
				$author$project$VideoGallery$subscriptions(model.galleryModel));
		} else {
			return $elm$core$Platform$Sub$none;
		}
	}();
	var creativeBriefEditorSub = function () {
		var _v5 = model.route;
		if ((_v5.$ === 'Just') && (_v5.a.$ === 'CreativeBriefEditor')) {
			var _v6 = _v5.a;
			return A2(
				$elm$core$Platform$Sub$map,
				$author$project$Main$CreativeBriefEditorMsg,
				$author$project$CreativeBriefEditor$subscriptions(model.creativeBriefEditorModel));
		} else {
			return $elm$core$Platform$Sub$none;
		}
	}();
	var briefGallerySub = function () {
		var _v3 = model.route;
		if ((_v3.$ === 'Just') && (_v3.a.$ === 'BriefGallery')) {
			var _v4 = _v3.a;
			return A2(
				$elm$core$Platform$Sub$map,
				$author$project$Main$BriefGalleryMsg,
				$author$project$BriefGallery$subscriptions(model.briefGalleryModel));
		} else {
			return $elm$core$Platform$Sub$none;
		}
	}();
	var audioGallerySub = function () {
		var _v1 = model.route;
		if ((_v1.$ === 'Just') && (_v1.a.$ === 'AudioGallery')) {
			var _v2 = _v1.a;
			return A2(
				$elm$core$Platform$Sub$map,
				$author$project$Main$AudioGalleryMsg,
				$author$project$AudioGallery$subscriptions(model.audioGalleryModel));
		} else {
			return $elm$core$Platform$Sub$none;
		}
	}();
	var audioDetailSub = function () {
		var _v0 = _Utils_Tuple2(model.route, model.audioDetailModel);
		if (((_v0.a.$ === 'Just') && (_v0.a.a.$ === 'AudioDetail')) && (_v0.b.$ === 'Just')) {
			var audioDetailModel = _v0.b.a;
			return A2(
				$elm$core$Platform$Sub$map,
				$author$project$Main$AudioDetailMsg,
				$author$project$AudioDetail$subscriptions(audioDetailModel));
		} else {
			return $elm$core$Platform$Sub$none;
		}
	}();
	return $elm$core$Platform$Sub$batch(
		_List_fromArray(
			[
				$author$project$Main$sendSelectionToElm($author$project$Main$SelectionChanged),
				$author$project$Main$sendTransformUpdateToElm($author$project$Main$TransformUpdated),
				$author$project$Main$sceneLoadedFromStorage($author$project$Main$SceneLoadedFromStorage),
				$elm$browser$Browser$Events$onKeyDown(
				A2($elm$json$Json$Decode$map, $author$project$Main$KeyDown, $author$project$Main$keyDecoder)),
				$elm$browser$Browser$Events$onKeyUp(
				A2($elm$json$Json$Decode$map, $author$project$Main$KeyUp, $author$project$Main$keyDecoder)),
				gallerySub,
				simulationGallerySub,
				videoDetailSub,
				imageGallerySub,
				imageDetailSub,
				audioGallerySub,
				audioDetailSub,
				videoToTextGallerySub,
				creativeBriefEditorSub,
				briefGallerySub
			]));
};
var $author$project$AudioGallery$FetchAudio = {$: 'FetchAudio'};
var $author$project$ImageGallery$FetchImages = {$: 'FetchImages'};
var $author$project$SimulationGallery$FetchVideos = {$: 'FetchVideos'};
var $author$project$VideoGallery$FetchVideos = {$: 'FetchVideos'};
var $author$project$VideoToTextGallery$FetchVideos = {$: 'FetchVideos'};
var $author$project$Video$SelectCollection = function (a) {
	return {$: 'SelectCollection', a: a};
};
var $author$project$Video$SelectModel = function (a) {
	return {$: 'SelectModel', a: a};
};
var $author$project$Video$UpdateParameter = F2(
	function (a, b) {
		return {$: 'UpdateParameter', a: a, b: b};
	});
var $elm$core$Basics$always = F2(
	function (a, _v0) {
		return a;
	});
var $author$project$Main$SceneGeneratedResult = function (a) {
	return {$: 'SceneGeneratedResult', a: a};
};
var $elm$http$Http$jsonBody = function (value) {
	return A2(
		_Http_pair,
		'application/json',
		A2($elm$json$Json$Encode$encode, 0, value));
};
var $elm$json$Json$Encode$object = function (pairs) {
	return _Json_wrap(
		A3(
			$elm$core$List$foldl,
			F2(
				function (_v0, obj) {
					var k = _v0.a;
					var v = _v0.b;
					return A3(_Json_addField, k, v, obj);
				}),
			_Json_emptyObject(_Utils_Tuple0),
			pairs));
};
var $elm$http$Http$post = function (r) {
	return $elm$http$Http$request(
		{body: r.body, expect: r.expect, headers: _List_Nil, method: 'POST', timeout: $elm$core$Maybe$Nothing, tracker: $elm$core$Maybe$Nothing, url: r.url});
};
var $author$project$Main$Scene = F2(
	function (objects, selectedObject) {
		return {objects: objects, selectedObject: selectedObject};
	});
var $elm$json$Json$Decode$keyValuePairs = _Json_decodeKeyValuePairs;
var $elm$json$Json$Decode$dict = function (decoder) {
	return A2(
		$elm$json$Json$Decode$map,
		$elm$core$Dict$fromList,
		$elm$json$Json$Decode$keyValuePairs(decoder));
};
var $author$project$Main$PhysicsObject = F5(
	function (id, transform, physicsProperties, visualProperties, description) {
		return {description: description, id: id, physicsProperties: physicsProperties, transform: transform, visualProperties: visualProperties};
	});
var $author$project$Main$PhysicsProperties = F3(
	function (mass, friction, restitution) {
		return {friction: friction, mass: mass, restitution: restitution};
	});
var $author$project$Main$physicsPropertiesDecoder = A4(
	$elm$json$Json$Decode$map3,
	$author$project$Main$PhysicsProperties,
	A2($elm$json$Json$Decode$field, 'mass', $elm$json$Json$Decode$float),
	A2($elm$json$Json$Decode$field, 'friction', $elm$json$Json$Decode$float),
	A2($elm$json$Json$Decode$field, 'restitution', $elm$json$Json$Decode$float));
var $author$project$Main$Transform = F3(
	function (position, rotation, scale) {
		return {position: position, rotation: rotation, scale: scale};
	});
var $author$project$Main$Vec3 = F3(
	function (x, y, z) {
		return {x: x, y: y, z: z};
	});
var $author$project$Main$vec3Decoder = A4(
	$elm$json$Json$Decode$map3,
	$author$project$Main$Vec3,
	A2($elm$json$Json$Decode$field, 'x', $elm$json$Json$Decode$float),
	A2($elm$json$Json$Decode$field, 'y', $elm$json$Json$Decode$float),
	A2($elm$json$Json$Decode$field, 'z', $elm$json$Json$Decode$float));
var $author$project$Main$transformDecoder = A4(
	$elm$json$Json$Decode$map3,
	$author$project$Main$Transform,
	A2($elm$json$Json$Decode$field, 'position', $author$project$Main$vec3Decoder),
	A2($elm$json$Json$Decode$field, 'rotation', $author$project$Main$vec3Decoder),
	A2($elm$json$Json$Decode$field, 'scale', $author$project$Main$vec3Decoder));
var $author$project$Main$VisualProperties = F2(
	function (color, shape) {
		return {color: color, shape: shape};
	});
var $author$project$Main$Box = {$: 'Box'};
var $author$project$Main$Cylinder = {$: 'Cylinder'};
var $author$project$Main$Sphere = {$: 'Sphere'};
var $elm$json$Json$Decode$fail = _Json_fail;
var $author$project$Main$shapeDecoder = A2(
	$elm$json$Json$Decode$andThen,
	function (shapeStr) {
		switch (shapeStr) {
			case 'Box':
				return $elm$json$Json$Decode$succeed($author$project$Main$Box);
			case 'Sphere':
				return $elm$json$Json$Decode$succeed($author$project$Main$Sphere);
			case 'Cylinder':
				return $elm$json$Json$Decode$succeed($author$project$Main$Cylinder);
			default:
				return $elm$json$Json$Decode$fail('Unknown shape: ' + shapeStr);
		}
	},
	$elm$json$Json$Decode$string);
var $author$project$Main$visualPropertiesDecoder = A3(
	$elm$json$Json$Decode$map2,
	$author$project$Main$VisualProperties,
	A2($elm$json$Json$Decode$field, 'color', $elm$json$Json$Decode$string),
	A2($elm$json$Json$Decode$field, 'shape', $author$project$Main$shapeDecoder));
var $author$project$Main$physicsObjectDecoder = A6(
	$elm$json$Json$Decode$map5,
	$author$project$Main$PhysicsObject,
	A2($elm$json$Json$Decode$field, 'id', $elm$json$Json$Decode$string),
	A2($elm$json$Json$Decode$field, 'transform', $author$project$Main$transformDecoder),
	A2($elm$json$Json$Decode$field, 'physicsProperties', $author$project$Main$physicsPropertiesDecoder),
	A2($elm$json$Json$Decode$field, 'visualProperties', $author$project$Main$visualPropertiesDecoder),
	$elm$json$Json$Decode$maybe(
		A2($elm$json$Json$Decode$field, 'description', $elm$json$Json$Decode$string)));
var $author$project$Main$sceneDecoder = A3(
	$elm$json$Json$Decode$map2,
	$author$project$Main$Scene,
	A2(
		$elm$json$Json$Decode$field,
		'objects',
		$elm$json$Json$Decode$dict($author$project$Main$physicsObjectDecoder)),
	$elm$json$Json$Decode$maybe(
		A2($elm$json$Json$Decode$field, 'selectedObject', $elm$json$Json$Decode$string)));
var $elm$json$Json$Encode$string = _Json_wrap;
var $author$project$Main$generateSceneRequest = function (prompt) {
	return $elm$http$Http$post(
		{
			body: $elm$http$Http$jsonBody(
				$elm$json$Json$Encode$object(
					_List_fromArray(
						[
							_Utils_Tuple2(
							'prompt',
							$elm$json$Json$Encode$string(prompt))
						]))),
			expect: A2($elm$http$Http$expectJson, $author$project$Main$SceneGeneratedResult, $author$project$Main$sceneDecoder),
			url: '/api/generate'
		});
};
var $author$project$AudioDetail$AudioFetched = function (a) {
	return {$: 'AudioFetched', a: a};
};
var $author$project$AudioDetail$AudioRecord = F8(
	function (id, prompt, audioUrl, modelId, createdAt, status, metadata, duration) {
		return {audioUrl: audioUrl, createdAt: createdAt, duration: duration, id: id, metadata: metadata, modelId: modelId, prompt: prompt, status: status};
	});
var $author$project$AudioDetail$audioDecoder = A9(
	$elm$json$Json$Decode$map8,
	$author$project$AudioDetail$AudioRecord,
	A2($elm$json$Json$Decode$field, 'id', $elm$json$Json$Decode$int),
	A2($elm$json$Json$Decode$field, 'prompt', $elm$json$Json$Decode$string),
	A2($elm$json$Json$Decode$field, 'audio_url', $elm$json$Json$Decode$string),
	A2($elm$json$Json$Decode$field, 'model_id', $elm$json$Json$Decode$string),
	A2($elm$json$Json$Decode$field, 'created_at', $elm$json$Json$Decode$string),
	A2($elm$json$Json$Decode$field, 'status', $elm$json$Json$Decode$string),
	$elm$json$Json$Decode$maybe(
		A2($elm$json$Json$Decode$field, 'metadata', $elm$json$Json$Decode$value)),
	$elm$json$Json$Decode$maybe(
		A2($elm$json$Json$Decode$field, 'duration', $elm$json$Json$Decode$float)));
var $author$project$AudioDetail$fetchAudio = function (audioId) {
	return $elm$http$Http$get(
		{
			expect: A2($elm$http$Http$expectJson, $author$project$AudioDetail$AudioFetched, $author$project$AudioDetail$audioDecoder),
			url: '/api/audio/' + $elm$core$String$fromInt(audioId)
		});
};
var $author$project$AudioDetail$init = function (audioId) {
	return _Utils_Tuple2(
		{audio: $elm$core$Maybe$Nothing, audioId: audioId, error: $elm$core$Maybe$Nothing, isPolling: true},
		$author$project$AudioDetail$fetchAudio(audioId));
};
var $author$project$ImageDetail$ImageFetched = function (a) {
	return {$: 'ImageFetched', a: a};
};
var $author$project$ImageDetail$ImageRecord = F7(
	function (id, prompt, imageUrl, modelId, createdAt, status, metadata) {
		return {createdAt: createdAt, id: id, imageUrl: imageUrl, metadata: metadata, modelId: modelId, prompt: prompt, status: status};
	});
var $elm$json$Json$Decode$map7 = _Json_map7;
var $author$project$ImageDetail$imageDecoder = A8(
	$elm$json$Json$Decode$map7,
	$author$project$ImageDetail$ImageRecord,
	A2($elm$json$Json$Decode$field, 'id', $elm$json$Json$Decode$int),
	A2($elm$json$Json$Decode$field, 'prompt', $elm$json$Json$Decode$string),
	A2($elm$json$Json$Decode$field, 'image_url', $elm$json$Json$Decode$string),
	A2($elm$json$Json$Decode$field, 'model_id', $elm$json$Json$Decode$string),
	A2($elm$json$Json$Decode$field, 'created_at', $elm$json$Json$Decode$string),
	A2($elm$json$Json$Decode$field, 'status', $elm$json$Json$Decode$string),
	$elm$json$Json$Decode$maybe(
		A2($elm$json$Json$Decode$field, 'metadata', $elm$json$Json$Decode$value)));
var $author$project$ImageDetail$fetchImage = function (imageId) {
	return $elm$http$Http$get(
		{
			expect: A2($elm$http$Http$expectJson, $author$project$ImageDetail$ImageFetched, $author$project$ImageDetail$imageDecoder),
			url: '/api/images/' + $elm$core$String$fromInt(imageId)
		});
};
var $author$project$ImageDetail$init = function (imageId) {
	return _Utils_Tuple2(
		{error: $elm$core$Maybe$Nothing, image: $elm$core$Maybe$Nothing, imageId: imageId, isPolling: true},
		$author$project$ImageDetail$fetchImage(imageId));
};
var $author$project$VideoDetail$VideoFetched = function (a) {
	return {$: 'VideoFetched', a: a};
};
var $author$project$VideoDetail$VideoRecord = F6(
	function (id, prompt, videoUrl, modelId, createdAt, status) {
		return {createdAt: createdAt, id: id, modelId: modelId, prompt: prompt, status: status, videoUrl: videoUrl};
	});
var $elm$json$Json$Decode$map6 = _Json_map6;
var $author$project$VideoDetail$videoDecoder = A7(
	$elm$json$Json$Decode$map6,
	$author$project$VideoDetail$VideoRecord,
	A2($elm$json$Json$Decode$field, 'id', $elm$json$Json$Decode$int),
	A2($elm$json$Json$Decode$field, 'prompt', $elm$json$Json$Decode$string),
	A2($elm$json$Json$Decode$field, 'video_url', $elm$json$Json$Decode$string),
	A2($elm$json$Json$Decode$field, 'model_id', $elm$json$Json$Decode$string),
	A2($elm$json$Json$Decode$field, 'created_at', $elm$json$Json$Decode$string),
	A2($elm$json$Json$Decode$field, 'status', $elm$json$Json$Decode$string));
var $author$project$VideoDetail$fetchVideo = function (videoId) {
	return $elm$http$Http$get(
		{
			expect: A2($elm$http$Http$expectJson, $author$project$VideoDetail$VideoFetched, $author$project$VideoDetail$videoDecoder),
			url: '/api/videos/' + $elm$core$String$fromInt(videoId)
		});
};
var $author$project$VideoDetail$init = function (videoId) {
	return _Utils_Tuple2(
		{error: $elm$core$Maybe$Nothing, isPolling: true, video: $elm$core$Maybe$Nothing, videoId: videoId},
		$author$project$VideoDetail$fetchVideo(videoId));
};
var $author$project$BriefGallery$initCmd = function (model) {
	return $author$project$BriefGallery$loadBriefs(1);
};
var $elm$browser$Browser$Navigation$load = _Browser_load;
var $elm$core$Dict$map = F2(
	function (func, dict) {
		if (dict.$ === 'RBEmpty_elm_builtin') {
			return $elm$core$Dict$RBEmpty_elm_builtin;
		} else {
			var color = dict.a;
			var key = dict.b;
			var value = dict.c;
			var left = dict.d;
			var right = dict.e;
			return A5(
				$elm$core$Dict$RBNode_elm_builtin,
				color,
				key,
				A2(func, key, value),
				A2($elm$core$Dict$map, func, left),
				A2($elm$core$Dict$map, func, right));
		}
	});
var $elm$core$Platform$Cmd$none = $elm$core$Platform$Cmd$batch(_List_Nil);
var $elm$core$Basics$not = _Basics_not;
var $elm$browser$Browser$Navigation$pushUrl = _Browser_pushUrl;
var $author$project$Main$SceneRefined = function (a) {
	return {$: 'SceneRefined', a: a};
};
var $elm$json$Json$Encode$dict = F3(
	function (toKey, toValue, dictionary) {
		return _Json_wrap(
			A3(
				$elm$core$Dict$foldl,
				F3(
					function (key, value, obj) {
						return A3(
							_Json_addField,
							toKey(key),
							toValue(value),
							obj);
					}),
				_Json_emptyObject(_Utils_Tuple0),
				dictionary));
	});
var $elm$json$Json$Encode$null = _Json_encodeNull;
var $author$project$Main$maybeEncoder = F2(
	function (encoder, maybeValue) {
		if (maybeValue.$ === 'Just') {
			var value = maybeValue.a;
			return encoder(value);
		} else {
			return $elm$json$Json$Encode$null;
		}
	});
var $elm$json$Json$Encode$float = _Json_wrap;
var $author$project$Main$physicsPropertiesEncoder = function (props) {
	return $elm$json$Json$Encode$object(
		_List_fromArray(
			[
				_Utils_Tuple2(
				'mass',
				$elm$json$Json$Encode$float(props.mass)),
				_Utils_Tuple2(
				'friction',
				$elm$json$Json$Encode$float(props.friction)),
				_Utils_Tuple2(
				'restitution',
				$elm$json$Json$Encode$float(props.restitution))
			]));
};
var $author$project$Main$vec3Encoder = function (vec3) {
	return $elm$json$Json$Encode$object(
		_List_fromArray(
			[
				_Utils_Tuple2(
				'x',
				$elm$json$Json$Encode$float(vec3.x)),
				_Utils_Tuple2(
				'y',
				$elm$json$Json$Encode$float(vec3.y)),
				_Utils_Tuple2(
				'z',
				$elm$json$Json$Encode$float(vec3.z))
			]));
};
var $author$project$Main$transformEncoder = function (transform) {
	return $elm$json$Json$Encode$object(
		_List_fromArray(
			[
				_Utils_Tuple2(
				'position',
				$author$project$Main$vec3Encoder(transform.position)),
				_Utils_Tuple2(
				'rotation',
				$author$project$Main$vec3Encoder(transform.rotation)),
				_Utils_Tuple2(
				'scale',
				$author$project$Main$vec3Encoder(transform.scale))
			]));
};
var $author$project$Main$shapeEncoder = function (shape) {
	return $elm$json$Json$Encode$string(
		function () {
			switch (shape.$) {
				case 'Box':
					return 'Box';
				case 'Sphere':
					return 'Sphere';
				default:
					return 'Cylinder';
			}
		}());
};
var $author$project$Main$visualPropertiesEncoder = function (props) {
	return $elm$json$Json$Encode$object(
		_List_fromArray(
			[
				_Utils_Tuple2(
				'color',
				$elm$json$Json$Encode$string(props.color)),
				_Utils_Tuple2(
				'shape',
				$author$project$Main$shapeEncoder(props.shape))
			]));
};
var $author$project$Main$physicsObjectEncoder = function (obj) {
	var descriptionField = function () {
		var _v0 = obj.description;
		if (_v0.$ === 'Just') {
			var desc = _v0.a;
			return _List_fromArray(
				[
					_Utils_Tuple2(
					'description',
					$elm$json$Json$Encode$string(desc))
				]);
		} else {
			return _List_Nil;
		}
	}();
	var baseFields = _List_fromArray(
		[
			_Utils_Tuple2(
			'id',
			$elm$json$Json$Encode$string(obj.id)),
			_Utils_Tuple2(
			'transform',
			$author$project$Main$transformEncoder(obj.transform)),
			_Utils_Tuple2(
			'physicsProperties',
			$author$project$Main$physicsPropertiesEncoder(obj.physicsProperties)),
			_Utils_Tuple2(
			'visualProperties',
			$author$project$Main$visualPropertiesEncoder(obj.visualProperties))
		]);
	return $elm$json$Json$Encode$object(
		_Utils_ap(baseFields, descriptionField));
};
var $author$project$Main$sceneEncoder = function (scene) {
	return $elm$json$Json$Encode$object(
		_List_fromArray(
			[
				_Utils_Tuple2(
				'objects',
				A3($elm$json$Json$Encode$dict, $elm$core$Basics$identity, $author$project$Main$physicsObjectEncoder, scene.objects)),
				_Utils_Tuple2(
				'selectedObject',
				A2($author$project$Main$maybeEncoder, $elm$json$Json$Encode$string, scene.selectedObject))
			]));
};
var $author$project$Main$refineSceneRequest = F2(
	function (scene, prompt) {
		return $elm$http$Http$post(
			{
				body: $elm$http$Http$jsonBody(
					$elm$json$Json$Encode$object(
						_List_fromArray(
							[
								_Utils_Tuple2(
								'scene',
								$author$project$Main$sceneEncoder(scene)),
								_Utils_Tuple2(
								'prompt',
								$elm$json$Json$Encode$string(prompt))
							]))),
				expect: A2($elm$http$Http$expectJson, $author$project$Main$SceneRefined, $author$project$Main$sceneDecoder),
				url: '/api/refine'
			});
	});
var $elm$core$List$takeReverse = F3(
	function (n, list, kept) {
		takeReverse:
		while (true) {
			if (n <= 0) {
				return kept;
			} else {
				if (!list.b) {
					return kept;
				} else {
					var x = list.a;
					var xs = list.b;
					var $temp$n = n - 1,
						$temp$list = xs,
						$temp$kept = A2($elm$core$List$cons, x, kept);
					n = $temp$n;
					list = $temp$list;
					kept = $temp$kept;
					continue takeReverse;
				}
			}
		}
	});
var $elm$core$List$takeTailRec = F2(
	function (n, list) {
		return $elm$core$List$reverse(
			A3($elm$core$List$takeReverse, n, list, _List_Nil));
	});
var $elm$core$List$takeFast = F3(
	function (ctr, n, list) {
		if (n <= 0) {
			return _List_Nil;
		} else {
			var _v0 = _Utils_Tuple2(n, list);
			_v0$1:
			while (true) {
				_v0$5:
				while (true) {
					if (!_v0.b.b) {
						return list;
					} else {
						if (_v0.b.b.b) {
							switch (_v0.a) {
								case 1:
									break _v0$1;
								case 2:
									var _v2 = _v0.b;
									var x = _v2.a;
									var _v3 = _v2.b;
									var y = _v3.a;
									return _List_fromArray(
										[x, y]);
								case 3:
									if (_v0.b.b.b.b) {
										var _v4 = _v0.b;
										var x = _v4.a;
										var _v5 = _v4.b;
										var y = _v5.a;
										var _v6 = _v5.b;
										var z = _v6.a;
										return _List_fromArray(
											[x, y, z]);
									} else {
										break _v0$5;
									}
								default:
									if (_v0.b.b.b.b && _v0.b.b.b.b.b) {
										var _v7 = _v0.b;
										var x = _v7.a;
										var _v8 = _v7.b;
										var y = _v8.a;
										var _v9 = _v8.b;
										var z = _v9.a;
										var _v10 = _v9.b;
										var w = _v10.a;
										var tl = _v10.b;
										return (ctr > 1000) ? A2(
											$elm$core$List$cons,
											x,
											A2(
												$elm$core$List$cons,
												y,
												A2(
													$elm$core$List$cons,
													z,
													A2(
														$elm$core$List$cons,
														w,
														A2($elm$core$List$takeTailRec, n - 4, tl))))) : A2(
											$elm$core$List$cons,
											x,
											A2(
												$elm$core$List$cons,
												y,
												A2(
													$elm$core$List$cons,
													z,
													A2(
														$elm$core$List$cons,
														w,
														A3($elm$core$List$takeFast, ctr + 1, n - 4, tl)))));
									} else {
										break _v0$5;
									}
							}
						} else {
							if (_v0.a === 1) {
								break _v0$1;
							} else {
								break _v0$5;
							}
						}
					}
				}
				return list;
			}
			var _v1 = _v0.b;
			var x = _v1.a;
			return _List_fromArray(
				[x]);
		}
	});
var $elm$core$List$take = F2(
	function (n, list) {
		return A3($elm$core$List$takeFast, 0, n, list);
	});
var $author$project$Main$saveToHistory = function (model) {
	return _Utils_update(
		model,
		{
			future: _List_Nil,
			history: A2(
				$elm$core$List$cons,
				model.scene,
				A2($elm$core$List$take, 49, model.history))
		});
};
var $author$project$Main$sendSceneToThreeJs = _Platform_outgoingPort('sendSceneToThreeJs', $elm$core$Basics$identity);
var $author$project$Main$sendSelectionToThreeJs = _Platform_outgoingPort('sendSelectionToThreeJs', $elm$json$Json$Encode$string);
var $author$project$Main$sendSimulationCommand = _Platform_outgoingPort('sendSimulationCommand', $elm$json$Json$Encode$string);
var $author$project$Main$sendTransformModeToThreeJs = _Platform_outgoingPort('sendTransformModeToThreeJs', $elm$json$Json$Encode$string);
var $elm$core$Process$sleep = _Process_sleep;
var $author$project$Route$toHref = function (route) {
	switch (route.$) {
		case 'Physics':
			return '/physics';
		case 'Videos':
			return '/videos';
		case 'VideoDetail':
			var id = route.a;
			return '/video/' + $elm$core$String$fromInt(id);
		case 'Gallery':
			return '/gallery';
		case 'SimulationGallery':
			return '/simulations';
		case 'Images':
			return '/images';
		case 'ImageDetail':
			var id = route.a;
			return '/image/' + $elm$core$String$fromInt(id);
		case 'ImageGallery':
			return '/image-gallery';
		case 'Audio':
			return '/audio';
		case 'AudioDetail':
			var id = route.a;
			return '/audio/' + $elm$core$String$fromInt(id);
		case 'AudioGallery':
			return '/audio-gallery';
		case 'VideoToText':
			return '/video-to-text';
		case 'VideoToTextGallery':
			return '/video-to-text-gallery';
		case 'Auth':
			return '/auth';
		case 'BriefGallery':
			return '/briefs';
		default:
			return '/creative';
	}
};
var $elm$url$Url$addPort = F2(
	function (maybePort, starter) {
		if (maybePort.$ === 'Nothing') {
			return starter;
		} else {
			var port_ = maybePort.a;
			return starter + (':' + $elm$core$String$fromInt(port_));
		}
	});
var $elm$url$Url$addPrefixed = F3(
	function (prefix, maybeSegment, starter) {
		if (maybeSegment.$ === 'Nothing') {
			return starter;
		} else {
			var segment = maybeSegment.a;
			return _Utils_ap(
				starter,
				_Utils_ap(prefix, segment));
		}
	});
var $elm$url$Url$toString = function (url) {
	var http = function () {
		var _v0 = url.protocol;
		if (_v0.$ === 'Http') {
			return 'http://';
		} else {
			return 'https://';
		}
	}();
	return A3(
		$elm$url$Url$addPrefixed,
		'#',
		url.fragment,
		A3(
			$elm$url$Url$addPrefixed,
			'?',
			url.query,
			_Utils_ap(
				A2(
					$elm$url$Url$addPort,
					url.port_,
					_Utils_ap(http, url.host)),
				url.path)));
};
var $author$project$Audio$NavigateToAudio = function (a) {
	return {$: 'NavigateToAudio', a: a};
};
var $author$project$Audio$Parameter = F9(
	function (key, value, paramType, _enum, description, _default, minimum, maximum, format) {
		return {_default: _default, description: description, _enum: _enum, format: format, key: key, maximum: maximum, minimum: minimum, paramType: paramType, value: value};
	});
var $author$project$Audio$ScrollToModel = function (a) {
	return {$: 'ScrollToModel', a: a};
};
var $elm$core$Task$onError = _Scheduler_onError;
var $elm$core$Task$attempt = F2(
	function (resultToMessage, task) {
		return $elm$core$Task$command(
			$elm$core$Task$Perform(
				A2(
					$elm$core$Task$onError,
					A2(
						$elm$core$Basics$composeL,
						A2($elm$core$Basics$composeL, $elm$core$Task$succeed, resultToMessage),
						$elm$core$Result$Err),
					A2(
						$elm$core$Task$andThen,
						A2(
							$elm$core$Basics$composeL,
							A2($elm$core$Basics$composeL, $elm$core$Task$succeed, resultToMessage),
							$elm$core$Result$Ok),
						task))));
	});
var $author$project$Audio$demoModels = _List_fromArray(
	[
		A4($author$project$Audio$AudioModel, 'meta/musicgen', 'MusicGen', 'Generate music from text prompts', $elm$core$Maybe$Nothing),
		A4($author$project$Audio$AudioModel, 'riffusion/riffusion', 'Riffusion', 'Generate music using Riffusion', $elm$core$Maybe$Nothing)
	]);
var $author$project$Audio$SchemaFetched = F2(
	function (a, b) {
		return {$: 'SchemaFetched', a: a, b: b};
	});
var $author$project$Audio$schemaResponseDecoder = A4(
	$elm$json$Json$Decode$map3,
	F3(
		function (s, r, v) {
			return {required: r, schema: s, version: v};
		}),
	A2($elm$json$Json$Decode$field, 'input_schema', $elm$json$Json$Decode$value),
	$elm$json$Json$Decode$oneOf(
		_List_fromArray(
			[
				A2(
				$elm$json$Json$Decode$field,
				'required',
				$elm$json$Json$Decode$list($elm$json$Json$Decode$string)),
				$elm$json$Json$Decode$succeed(_List_Nil)
			])),
	$elm$json$Json$Decode$maybe(
		A2($elm$json$Json$Decode$field, 'version', $elm$json$Json$Decode$string)));
var $author$project$Audio$fetchModelSchema = function (modelId) {
	var parts = A2($elm$core$String$split, '/', modelId);
	var url = function () {
		if ((parts.b && parts.b.b) && (!parts.b.b.b)) {
			var owner = parts.a;
			var _v1 = parts.b;
			var name = _v1.a;
			return '/api/audio-models/' + (owner + ('/' + (name + '/schema')));
		} else {
			return '';
		}
	}();
	return $elm$core$String$isEmpty(url) ? $elm$core$Platform$Cmd$none : $elm$http$Http$get(
		{
			expect: A2(
				$elm$http$Http$expectJson,
				$author$project$Audio$SchemaFetched(modelId),
				$author$project$Audio$schemaResponseDecoder),
			url: url
		});
};
var $elm$core$List$filter = F2(
	function (isGood, list) {
		return A3(
			$elm$core$List$foldr,
			F2(
				function (x, xs) {
					return isGood(x) ? A2($elm$core$List$cons, x, xs) : xs;
				}),
			_List_Nil,
			list);
	});
var $author$project$Audio$AudioGenerated = function (a) {
	return {$: 'AudioGenerated', a: a};
};
var $author$project$Audio$audioResponseDecoder = A3(
	$elm$json$Json$Decode$map2,
	F2(
		function (id, s) {
			return {audio_id: id, status: s};
		}),
	A2($elm$json$Json$Decode$field, 'audio_id', $elm$json$Json$Decode$int),
	A2($elm$json$Json$Decode$field, 'status', $elm$json$Json$Decode$string));
var $elm$json$Json$Encode$bool = _Json_wrap;
var $elm$json$Json$Encode$int = _Json_wrap;
var $elm$core$String$toFloat = _String_toFloat;
var $elm$core$String$toLower = _String_toLower;
var $elm$core$String$trim = _String_trim;
var $author$project$Audio$generateAudio = F4(
	function (modelId, parameters, collection, maybeVersion) {
		var encodeParameterValue = function (param) {
			if ($elm$core$String$isEmpty(
				$elm$core$String$trim(param.value))) {
				return $elm$core$Maybe$Nothing;
			} else {
				var encoded = function () {
					var _v1 = param.paramType;
					switch (_v1) {
						case 'integer':
							var _v2 = $elm$core$String$toInt(param.value);
							if (_v2.$ === 'Just') {
								var i = _v2.a;
								return $elm$json$Json$Encode$int(i);
							} else {
								return $elm$json$Json$Encode$string(param.value);
							}
						case 'number':
							var _v3 = $elm$core$String$toFloat(param.value);
							if (_v3.$ === 'Just') {
								var f = _v3.a;
								return $elm$json$Json$Encode$float(f);
							} else {
								return $elm$json$Json$Encode$string(param.value);
							}
						case 'boolean':
							var _v4 = $elm$core$String$toLower(param.value);
							switch (_v4) {
								case 'true':
									return $elm$json$Json$Encode$bool(true);
								case 'false':
									return $elm$json$Json$Encode$bool(false);
								default:
									return $elm$json$Json$Encode$string(param.value);
							}
						default:
							return $elm$json$Json$Encode$string(param.value);
					}
				}();
				return $elm$core$Maybe$Just(
					_Utils_Tuple2(param.key, encoded));
			}
		};
		var inputObject = $elm$json$Json$Encode$object(
			A2($elm$core$List$filterMap, encodeParameterValue, parameters));
		var requestFields = _Utils_ap(
			_List_fromArray(
				[
					_Utils_Tuple2(
					'model_id',
					$elm$json$Json$Encode$string(modelId)),
					_Utils_Tuple2('input', inputObject),
					_Utils_Tuple2(
					'collection',
					$elm$json$Json$Encode$string(collection))
				]),
			function () {
				if (maybeVersion.$ === 'Just') {
					var version = maybeVersion.a;
					return _List_fromArray(
						[
							_Utils_Tuple2(
							'version',
							$elm$json$Json$Encode$string(version))
						]);
				} else {
					return _List_Nil;
				}
			}());
		return $elm$http$Http$post(
			{
				body: $elm$http$Http$jsonBody(
					$elm$json$Json$Encode$object(requestFields)),
				expect: A2($elm$http$Http$expectJson, $author$project$Audio$AudioGenerated, $author$project$Audio$audioResponseDecoder),
				url: '/api/run-audio-model'
			});
	});
var $elm$browser$Browser$Dom$getElement = _Browser_getElement;
var $elm$core$List$head = function (list) {
	if (list.b) {
		var x = list.a;
		var xs = list.b;
		return $elm$core$Maybe$Just(x);
	} else {
		return $elm$core$Maybe$Nothing;
	}
};
var $author$project$Audio$httpErrorToString = function (error) {
	switch (error.$) {
		case 'BadUrl':
			var url = error.a;
			return 'Bad URL: ' + url;
		case 'Timeout':
			return 'Request timed out';
		case 'NetworkError':
			return 'Network error';
		case 'BadStatus':
			var status = error.a;
			return 'Server error: ' + $elm$core$String$fromInt(status);
		default:
			var body = error.a;
			return 'Invalid response: ' + body;
	}
};
var $elm$core$Basics$neq = _Utils_notEqual;
var $elm$core$Maybe$andThen = F2(
	function (callback, maybeValue) {
		if (maybeValue.$ === 'Just') {
			var value = maybeValue.a;
			return callback(value);
		} else {
			return $elm$core$Maybe$Nothing;
		}
	});
var $elm$core$String$fromFloat = _String_fromNumber;
var $elm$core$Result$toMaybe = function (result) {
	if (result.$ === 'Ok') {
		var v = result.a;
		return $elm$core$Maybe$Just(v);
	} else {
		return $elm$core$Maybe$Nothing;
	}
};
var $elm$core$Result$withDefault = F2(
	function (def, result) {
		if (result.$ === 'Ok') {
			var a = result.a;
			return a;
		} else {
			return def;
		}
	});
var $author$project$Audio$parseParameter = function (_v0) {
	var key = _v0.a;
	var value = _v0.b;
	var paramType = A2(
		$elm$core$Result$withDefault,
		'string',
		A2(
			$elm$json$Json$Decode$decodeValue,
			A2(
				$elm$json$Json$Decode$at,
				_List_fromArray(
					['type']),
				$elm$json$Json$Decode$string),
			value));
	var minimum = $elm$core$Result$toMaybe(
		A2(
			$elm$json$Json$Decode$decodeValue,
			A2($elm$json$Json$Decode$field, 'minimum', $elm$json$Json$Decode$float),
			value));
	var maximum = $elm$core$Result$toMaybe(
		A2(
			$elm$json$Json$Decode$decodeValue,
			A2($elm$json$Json$Decode$field, 'maximum', $elm$json$Json$Decode$float),
			value));
	var format = $elm$core$Result$toMaybe(
		A2(
			$elm$json$Json$Decode$decodeValue,
			A2($elm$json$Json$Decode$field, 'format', $elm$json$Json$Decode$string),
			value));
	var enumValues = $elm$core$Result$toMaybe(
		A2(
			$elm$json$Json$Decode$decodeValue,
			A2(
				$elm$json$Json$Decode$at,
				_List_fromArray(
					['enum']),
				$elm$json$Json$Decode$list($elm$json$Json$Decode$string)),
			value));
	var description = $elm$core$Result$toMaybe(
		A2(
			$elm$json$Json$Decode$decodeValue,
			A2(
				$elm$json$Json$Decode$at,
				_List_fromArray(
					['description']),
				$elm$json$Json$Decode$string),
			value));
	var _default = A2(
		$elm$core$Maybe$andThen,
		function (v) {
			var _v1 = A2($elm$json$Json$Decode$decodeValue, $elm$json$Json$Decode$string, v);
			if (_v1.$ === 'Ok') {
				var s = _v1.a;
				return $elm$core$Maybe$Just(s);
			} else {
				var _v2 = A2($elm$json$Json$Decode$decodeValue, $elm$json$Json$Decode$float, v);
				if (_v2.$ === 'Ok') {
					var f = _v2.a;
					return $elm$core$Maybe$Just(
						$elm$core$String$fromFloat(f));
				} else {
					var _v3 = A2($elm$json$Json$Decode$decodeValue, $elm$json$Json$Decode$int, v);
					if (_v3.$ === 'Ok') {
						var i = _v3.a;
						return $elm$core$Maybe$Just(
							$elm$core$String$fromInt(i));
					} else {
						return $elm$core$Maybe$Nothing;
					}
				}
			}
		},
		$elm$core$Result$toMaybe(
			A2(
				$elm$json$Json$Decode$decodeValue,
				A2($elm$json$Json$Decode$field, 'default', $elm$json$Json$Decode$value),
				value)));
	var initialValue = A2($elm$core$Maybe$withDefault, '', _default);
	return A9($author$project$Audio$Parameter, key, initialValue, paramType, enumValues, description, _default, minimum, maximum, format);
};
var $elm$browser$Browser$Dom$setViewport = _Browser_setViewport;
var $author$project$Audio$updateParameterInList = F3(
	function (key, value, params) {
		return A2(
			$elm$core$List$map,
			function (param) {
				return _Utils_eq(param.key, key) ? _Utils_update(
					param,
					{value: value}) : param;
			},
			params);
	});
var $author$project$Audio$update = F2(
	function (msg, model) {
		switch (msg.$) {
			case 'NoOp':
				return _Utils_Tuple2(model, $elm$core$Platform$Cmd$none);
			case 'FetchModels':
				return _Utils_Tuple2(
					model,
					$author$project$Audio$fetchModels(model.selectedCollection));
			case 'SelectCollection':
				var collection = msg.a;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{outputAudio: $elm$core$Maybe$Nothing, requiredFields: _List_Nil, selectedCollection: collection, selectedModel: $elm$core$Maybe$Nothing, selectedVersion: $elm$core$Maybe$Nothing}),
					$author$project$Audio$fetchModels(collection));
			case 'ModelsFetched':
				var result = msg.a;
				if (result.$ === 'Ok') {
					var models = result.a;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{error: $elm$core$Maybe$Nothing, models: models}),
						$elm$core$Platform$Cmd$none);
				} else {
					var error = result.a;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								error: $elm$core$Maybe$Just(
									'Failed to fetch models: ' + $author$project$Audio$httpErrorToString(error)),
								models: $author$project$Audio$demoModels
							}),
						$elm$core$Platform$Cmd$none);
				}
			case 'SelectModel':
				var modelId = msg.a;
				var selected = $elm$core$List$head(
					A2(
						$elm$core$List$filter,
						function (m) {
							return _Utils_eq(m.id, modelId);
						},
						model.models));
				if (selected.$ === 'Just') {
					var selectedModel = selected.a;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{error: $elm$core$Maybe$Nothing, outputAudio: $elm$core$Maybe$Nothing, parameters: _List_Nil, selectedModel: selected}),
						$author$project$Audio$fetchModelSchema(selectedModel.id));
				} else {
					return _Utils_Tuple2(model, $elm$core$Platform$Cmd$none);
				}
			case 'SchemaFetched':
				var modelId = msg.a;
				var result = msg.b;
				if (result.$ === 'Ok') {
					var schema = result.a.schema;
					var required = result.a.required;
					var version = result.a.version;
					var params = function () {
						var _v4 = A2(
							$elm$json$Json$Decode$decodeValue,
							$elm$json$Json$Decode$keyValuePairs($elm$json$Json$Decode$value),
							schema);
						if (_v4.$ === 'Ok') {
							var properties = _v4.a;
							return A2($elm$core$List$map, $author$project$Audio$parseParameter, properties);
						} else {
							return _List_fromArray(
								[
									A9($author$project$Audio$Parameter, 'prompt', '', 'string', $elm$core$Maybe$Nothing, $elm$core$Maybe$Nothing, $elm$core$Maybe$Nothing, $elm$core$Maybe$Nothing, $elm$core$Maybe$Nothing, $elm$core$Maybe$Nothing)
								]);
						}
					}();
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{parameters: params, requiredFields: required, selectedVersion: version}),
						A2(
							$elm$core$Task$attempt,
							$author$project$Audio$ScrollToModel,
							A2(
								$elm$core$Task$andThen,
								function (info) {
									return A2($elm$browser$Browser$Dom$setViewport, 0, info.element.y);
								},
								$elm$browser$Browser$Dom$getElement('selected-model-section'))));
				} else {
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								parameters: _List_fromArray(
									[
										A9($author$project$Audio$Parameter, 'prompt', '', 'string', $elm$core$Maybe$Nothing, $elm$core$Maybe$Nothing, $elm$core$Maybe$Nothing, $elm$core$Maybe$Nothing, $elm$core$Maybe$Nothing, $elm$core$Maybe$Nothing)
									]),
								requiredFields: _List_fromArray(
									['prompt']),
								selectedVersion: $elm$core$Maybe$Nothing
							}),
						A2(
							$elm$core$Task$attempt,
							$author$project$Audio$ScrollToModel,
							A2(
								$elm$core$Task$andThen,
								function (info) {
									return A2($elm$browser$Browser$Dom$setViewport, 0, info.element.y);
								},
								$elm$browser$Browser$Dom$getElement('selected-model-section'))));
				}
			case 'UpdateParameter':
				var key = msg.a;
				var value = msg.b;
				var updatedParams = A3($author$project$Audio$updateParameterInList, key, value, model.parameters);
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{parameters: updatedParams}),
					$elm$core$Platform$Cmd$none);
			case 'UpdateSearch':
				var query = msg.a;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{searchQuery: query}),
					$elm$core$Platform$Cmd$none);
			case 'GenerateAudio':
				var _v5 = model.selectedModel;
				if (_v5.$ === 'Just') {
					var selectedModel = _v5.a;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{error: $elm$core$Maybe$Nothing, isGenerating: true}),
						A4($author$project$Audio$generateAudio, selectedModel.id, model.parameters, model.selectedCollection, model.selectedVersion));
				} else {
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								error: $elm$core$Maybe$Just('No model selected')
							}),
						$elm$core$Platform$Cmd$none);
				}
			case 'AudioGenerated':
				var result = msg.a;
				if (result.$ === 'Ok') {
					var response = result.a;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								audioStatus: response.status,
								error: $elm$core$Maybe$Nothing,
								isGenerating: false,
								pollingAudioId: $elm$core$Maybe$Just(response.audio_id)
							}),
						A2(
							$elm$core$Task$perform,
							function (_v7) {
								return $author$project$Audio$NavigateToAudio(response.audio_id);
							},
							$elm$core$Task$succeed(_Utils_Tuple0)));
				} else {
					var error = result.a;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								error: $elm$core$Maybe$Just(
									$author$project$Audio$httpErrorToString(error)),
								isGenerating: false
							}),
						$elm$core$Platform$Cmd$none);
				}
			case 'NavigateToAudio':
				return _Utils_Tuple2(model, $elm$core$Platform$Cmd$none);
			case 'ScrollToModel':
				return _Utils_Tuple2(model, $elm$core$Platform$Cmd$none);
			case 'PollAudioStatus':
				return _Utils_Tuple2(model, $elm$core$Platform$Cmd$none);
			default:
				var result = msg.a;
				if (result.$ === 'Ok') {
					var audioRecord = result.a;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								audioStatus: audioRecord.status,
								isGenerating: (audioRecord.status !== 'completed') && (audioRecord.status !== 'failed'),
								outputAudio: (audioRecord.status === 'completed') ? $elm$core$Maybe$Just(audioRecord.audioUrl) : model.outputAudio
							}),
						$elm$core$Platform$Cmd$none);
				} else {
					var error = result.a;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								error: $elm$core$Maybe$Just(
									$author$project$Audio$httpErrorToString(error))
							}),
						$elm$core$Platform$Cmd$none);
				}
		}
	});
var $author$project$AudioDetail$httpErrorToString = function (error) {
	switch (error.$) {
		case 'BadUrl':
			var url = error.a;
			return 'Bad URL: ' + url;
		case 'Timeout':
			return 'Request timed out';
		case 'NetworkError':
			return 'Network error';
		case 'BadStatus':
			var status = error.a;
			return 'Server error: ' + $elm$core$String$fromInt(status);
		default:
			var body = error.a;
			return 'Invalid response: ' + body;
	}
};
var $author$project$AudioDetail$update = F2(
	function (msg, model) {
		if (msg.$ === 'AudioFetched') {
			var result = msg.a;
			if (result.$ === 'Ok') {
				var audio = result.a;
				var shouldStopPolling = (audio.status === 'completed') || ((audio.status === 'failed') || (audio.status === 'canceled'));
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{
							audio: $elm$core$Maybe$Just(audio),
							error: $elm$core$Maybe$Nothing,
							isPolling: !shouldStopPolling
						}),
					$elm$core$Platform$Cmd$none);
			} else {
				var error = result.a;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{
							error: $elm$core$Maybe$Just(
								$author$project$AudioDetail$httpErrorToString(error)),
							isPolling: false
						}),
					$elm$core$Platform$Cmd$none);
			}
		} else {
			return model.isPolling ? _Utils_Tuple2(
				model,
				$author$project$AudioDetail$fetchAudio(model.audioId)) : _Utils_Tuple2(model, $elm$core$Platform$Cmd$none);
		}
	});
var $author$project$AudioGallery$httpErrorToString = function (error) {
	switch (error.$) {
		case 'BadUrl':
			var url = error.a;
			return 'Bad URL: ' + url;
		case 'Timeout':
			return 'Request timed out';
		case 'NetworkError':
			return 'Network error';
		case 'BadStatus':
			var status = error.a;
			return 'Server error: ' + $elm$core$String$fromInt(status);
		default:
			var body = error.a;
			return 'Invalid response: ' + body;
	}
};
var $author$project$AudioGallery$update = F2(
	function (msg, model) {
		switch (msg.$) {
			case 'NoOp':
				return _Utils_Tuple2(model, $elm$core$Platform$Cmd$none);
			case 'FetchAudio':
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{loading: true}),
					$author$project$AudioGallery$fetchAudio);
			case 'AudioFetched':
				var result = msg.a;
				if (result.$ === 'Ok') {
					var audio = result.a;
					return _Utils_eq(audio, model.audio) ? _Utils_Tuple2(
						_Utils_update(
							model,
							{loading: false}),
						$elm$core$Platform$Cmd$none) : _Utils_Tuple2(
						_Utils_update(
							model,
							{audio: audio, error: $elm$core$Maybe$Nothing, loading: false}),
						$elm$core$Platform$Cmd$none);
				} else {
					var error = result.a;
					var errorMsg = function () {
						if ((error.$ === 'BadStatus') && (error.a === 401)) {
							return $elm$core$Maybe$Nothing;
						} else {
							return $elm$core$Maybe$Just(
								$author$project$AudioGallery$httpErrorToString(error));
						}
					}();
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{error: errorMsg, loading: false}),
						$elm$core$Platform$Cmd$none);
				}
			case 'SelectAudio':
				var audio = msg.a;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{
							selectedAudio: $elm$core$Maybe$Just(audio),
							showRawData: false
						}),
					$elm$core$Platform$Cmd$none);
			case 'CloseAudio':
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{selectedAudio: $elm$core$Maybe$Nothing, showRawData: false}),
					$elm$core$Platform$Cmd$none);
			case 'ToggleRawData':
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{showRawData: !model.showRawData}),
					$elm$core$Platform$Cmd$none);
			default:
				return _Utils_Tuple2(model, $author$project$AudioGallery$fetchAudio);
		}
	});
var $author$project$Auth$LoggedIn = {$: 'LoggedIn'};
var $author$project$Auth$LoggingIn = {$: 'LoggingIn'};
var $author$project$Auth$NotLoggedIn = {$: 'NotLoggedIn'};
var $author$project$Auth$LoginResponse = F2(
	function (message, username) {
		return {message: message, username: username};
	});
var $author$project$Auth$LoginResult = function (a) {
	return {$: 'LoginResult', a: a};
};
var $elm$http$Http$stringBody = _Http_pair;
var $author$project$Auth$login = F2(
	function (username, password) {
		var decoder = A3(
			$elm$json$Json$Decode$map2,
			$author$project$Auth$LoginResponse,
			A2($elm$json$Json$Decode$field, 'message', $elm$json$Json$Decode$string),
			A2($elm$json$Json$Decode$field, 'username', $elm$json$Json$Decode$string));
		var body = A2($elm$http$Http$stringBody, 'application/x-www-form-urlencoded', 'username=' + (username + ('&password=' + password)));
		return $elm$http$Http$post(
			{
				body: body,
				expect: A2($elm$http$Http$expectJson, $author$project$Auth$LoginResult, decoder),
				url: '/api/auth/login'
			});
	});
var $author$project$Auth$Logout = {$: 'Logout'};
var $author$project$Auth$logout = $elm$http$Http$post(
	{
		body: $elm$http$Http$emptyBody,
		expect: $elm$http$Http$expectWhatever(
			function (_v0) {
				return $author$project$Auth$Logout;
			}),
		url: '/api/auth/logout'
	});
var $author$project$Auth$update = F2(
	function (msg, model) {
		switch (msg.$) {
			case 'UpdateUsername':
				var username = msg.a;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{username: username}),
					$elm$core$Platform$Cmd$none);
			case 'UpdatePassword':
				var password = msg.a;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{password: password}),
					$elm$core$Platform$Cmd$none);
			case 'SubmitLogin':
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{error: $elm$core$Maybe$Nothing, loginState: $author$project$Auth$LoggingIn}),
					A2($author$project$Auth$login, model.username, model.password));
			case 'LoginResult':
				if (msg.a.$ === 'Ok') {
					var response = msg.a.a;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{error: $elm$core$Maybe$Nothing, loginState: $author$project$Auth$LoggedIn, password: ''}),
						$elm$core$Platform$Cmd$none);
				} else {
					var error = msg.a.a;
					var errorMessage = function () {
						switch (error.$) {
							case 'BadUrl':
								return 'Invalid URL';
							case 'Timeout':
								return 'Request timed out';
							case 'NetworkError':
								return 'Network error';
							case 'BadStatus':
								var status = error.a;
								return (status === 401) ? 'Invalid username or password' : ('Server error: ' + $elm$core$String$fromInt(status));
							default:
								var body = error.a;
								return 'Invalid response: ' + body;
						}
					}();
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								error: $elm$core$Maybe$Just(errorMessage),
								loginState: $author$project$Auth$NotLoggedIn
							}),
						$elm$core$Platform$Cmd$none);
				}
			case 'CheckAuthResult':
				if (msg.a.$ === 'Ok') {
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{loginState: $author$project$Auth$LoggedIn}),
						$elm$core$Platform$Cmd$none);
				} else {
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{loginState: $author$project$Auth$NotLoggedIn}),
						$elm$core$Platform$Cmd$none);
				}
			default:
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{error: $elm$core$Maybe$Nothing, loginState: $author$project$Auth$NotLoggedIn, password: '', username: ''}),
					$author$project$Auth$logout);
		}
	});
var $author$project$BriefGallery$LoadBriefs = function (a) {
	return {$: 'LoadBriefs', a: a};
};
var $author$project$BriefGallery$deleteBrief = F2(
	function (briefId, key) {
		return $elm$http$Http$request(
			{
				body: $elm$http$Http$emptyBody,
				expect: $elm$http$Http$expectWhatever(
					function (_v0) {
						return $author$project$BriefGallery$LoadBriefs(1);
					}),
				headers: _List_Nil,
				method: 'DELETE',
				timeout: $elm$core$Maybe$Nothing,
				tracker: $elm$core$Maybe$Nothing,
				url: '/api/creative/briefs/' + briefId
			});
	});
var $author$project$BriefGallery$GenerationResponse = function (a) {
	return {$: 'GenerationResponse', a: a};
};
var $author$project$BriefGallery$decodeImageGenerationResponse = A2(
	$elm$json$Json$Decode$map,
	function (id) {
		return 'Image generation started with ID: ' + $elm$core$String$fromInt(id);
	},
	A2($elm$json$Json$Decode$field, 'image_id', $elm$json$Json$Decode$int));
var $author$project$BriefGallery$generateImageFromBrief = function (briefId) {
	return $elm$http$Http$post(
		{
			body: $elm$http$Http$jsonBody(
				$elm$json$Json$Encode$object(
					_List_fromArray(
						[
							_Utils_Tuple2(
							'model_id',
							$elm$json$Json$Encode$string('stability-ai/sdxl')),
							_Utils_Tuple2(
							'input',
							$elm$json$Json$Encode$object(
								_List_fromArray(
									[
										_Utils_Tuple2(
										'prompt',
										$elm$json$Json$Encode$string('Generate image from creative brief'))
									]))),
							_Utils_Tuple2(
							'brief_id',
							$elm$json$Json$Encode$string(briefId))
						]))),
			expect: A2($elm$http$Http$expectJson, $author$project$BriefGallery$GenerationResponse, $author$project$BriefGallery$decodeImageGenerationResponse),
			url: '/api/run-image-model'
		});
};
var $author$project$BriefGallery$generateSceneFromBrief = function (briefId) {
	return $elm$http$Http$post(
		{
			body: $elm$http$Http$jsonBody(
				$elm$json$Json$Encode$object(
					_List_fromArray(
						[
							_Utils_Tuple2(
							'prompt',
							$elm$json$Json$Encode$string('Generate scene from brief')),
							_Utils_Tuple2(
							'brief_id',
							$elm$json$Json$Encode$string(briefId))
						]))),
			expect: $elm$http$Http$expectWhatever(
				function (_v0) {
					return $author$project$BriefGallery$LoadBriefs(1);
				}),
			url: '/api/generate'
		});
};
var $author$project$BriefGallery$decodeVideoGenerationResponse = A2(
	$elm$json$Json$Decode$map,
	function (id) {
		return 'Video generation started with ID: ' + $elm$core$String$fromInt(id);
	},
	A2($elm$json$Json$Decode$field, 'video_id', $elm$json$Json$Decode$int));
var $author$project$BriefGallery$generateVideoFromBrief = function (briefId) {
	return $elm$http$Http$post(
		{
			body: $elm$http$Http$jsonBody(
				$elm$json$Json$Encode$object(
					_List_fromArray(
						[
							_Utils_Tuple2(
							'model_id',
							$elm$json$Json$Encode$string('stability-ai/stable-video-diffusion')),
							_Utils_Tuple2(
							'input',
							$elm$json$Json$Encode$object(
								_List_fromArray(
									[
										_Utils_Tuple2(
										'prompt',
										$elm$json$Json$Encode$string('Generate video from creative brief'))
									]))),
							_Utils_Tuple2(
							'brief_id',
							$elm$json$Json$Encode$string(briefId))
						]))),
			expect: A2($elm$http$Http$expectJson, $author$project$BriefGallery$GenerationResponse, $author$project$BriefGallery$decodeVideoGenerationResponse),
			url: '/api/run-video-model'
		});
};
var $author$project$BriefGallery$httpErrorToString = function (error) {
	switch (error.$) {
		case 'BadUrl':
			var url = error.a;
			return 'Bad URL: ' + url;
		case 'Timeout':
			return 'Request timed out';
		case 'NetworkError':
			return 'Network error';
		case 'BadStatus':
			var status = error.a;
			return 'Bad status: ' + $elm$core$String$fromInt(status);
		default:
			var message = error.a;
			return 'Bad response: ' + message;
	}
};
var $author$project$BriefGallery$update = F2(
	function (msg, model) {
		switch (msg.$) {
			case 'LoadBriefs':
				var page = msg.a;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{currentPage: page, error: $elm$core$Maybe$Nothing, isLoading: true}),
					$author$project$BriefGallery$loadBriefs(page));
			case 'BriefsLoaded':
				var result = msg.a;
				if (result.$ === 'Ok') {
					var response = result.a;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{briefs: response.briefs, error: $elm$core$Maybe$Nothing, isLoading: false, totalPages: response.totalPages}),
						$elm$core$Platform$Cmd$none);
				} else {
					var error = result.a;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								error: $elm$core$Maybe$Just(
									$author$project$BriefGallery$httpErrorToString(error)),
								isLoading: false
							}),
						$elm$core$Platform$Cmd$none);
				}
			case 'SelectBrief':
				var briefId = msg.a;
				return _Utils_Tuple2(
					model,
					A2($elm$browser$Browser$Navigation$pushUrl, model.navigationKey, '/creative?brief=' + briefId));
			case 'RefineBrief':
				var briefId = msg.a;
				return _Utils_Tuple2(
					model,
					A2($elm$browser$Browser$Navigation$pushUrl, model.navigationKey, '/creative?refine=' + briefId));
			case 'DeleteBrief':
				var briefId = msg.a;
				return _Utils_Tuple2(
					model,
					A2($author$project$BriefGallery$deleteBrief, briefId, model.navigationKey));
			case 'NextPage':
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{currentPage: model.currentPage + 1}),
					$author$project$BriefGallery$loadBriefs(model.currentPage + 1));
			case 'PrevPage':
				return (model.currentPage > 1) ? _Utils_Tuple2(
					_Utils_update(
						model,
						{currentPage: model.currentPage - 1}),
					$author$project$BriefGallery$loadBriefs(model.currentPage - 1)) : _Utils_Tuple2(model, $elm$core$Platform$Cmd$none);
			case 'NavigateTo':
				var route = msg.a;
				return _Utils_Tuple2(
					model,
					A2(
						$elm$browser$Browser$Navigation$pushUrl,
						model.navigationKey,
						$author$project$Route$toHref(route)));
			case 'CloseBriefDetail':
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{selectedBrief: $elm$core$Maybe$Nothing}),
					$elm$core$Platform$Cmd$none);
			case 'GenerateFromBrief':
				var briefId = msg.a;
				return _Utils_Tuple2(
					model,
					$author$project$BriefGallery$generateSceneFromBrief(briefId));
			case 'GenerateImageFromBrief':
				var briefId = msg.a;
				return _Utils_Tuple2(
					model,
					$author$project$BriefGallery$generateImageFromBrief(briefId));
			case 'GenerateVideoFromBrief':
				var briefId = msg.a;
				return _Utils_Tuple2(
					model,
					$author$project$BriefGallery$generateVideoFromBrief(briefId));
			default:
				var result = msg.a;
				if (result.$ === 'Ok') {
					return _Utils_Tuple2(model, $elm$core$Platform$Cmd$none);
				} else {
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								error: $elm$core$Maybe$Just('Generation failed')
							}),
						$elm$core$Platform$Cmd$none);
				}
		}
	});
var $author$project$CreativeBriefEditor$ImagesGenerated = function (a) {
	return {$: 'ImagesGenerated', a: a};
};
var $author$project$CreativeBriefEditor$generateImagesFromBrief = F2(
	function (briefId, modelName) {
		var body = $elm$json$Json$Encode$object(
			_List_fromArray(
				[
					_Utils_Tuple2(
					'briefId',
					$elm$json$Json$Encode$string(briefId)),
					_Utils_Tuple2(
					'modelName',
					$elm$json$Json$Encode$string(modelName))
				]));
		return $elm$http$Http$post(
			{
				body: $elm$http$Http$jsonBody(body),
				expect: A2(
					$elm$http$Http$expectJson,
					$author$project$CreativeBriefEditor$ImagesGenerated,
					A2(
						$elm$json$Json$Decode$field,
						'imageIds',
						$elm$json$Json$Decode$list($elm$json$Json$Decode$int))),
				url: '/api/generate-images-from-brief'
			});
	});
var $author$project$CreativeBriefEditor$GotScene = function (a) {
	return {$: 'GotScene', a: a};
};
var $author$project$CreativeBriefEditor$SceneResponse = F2(
	function (sceneId, prompt) {
		return {prompt: prompt, sceneId: sceneId};
	});
var $author$project$CreativeBriefEditor$decodeSceneResponse = A3(
	$elm$json$Json$Decode$map2,
	$author$project$CreativeBriefEditor$SceneResponse,
	A2($elm$json$Json$Decode$field, 'sceneId', $elm$json$Json$Decode$string),
	A2($elm$json$Json$Decode$field, 'prompt', $elm$json$Json$Decode$string));
var $author$project$CreativeBriefEditor$generateScene = F3(
	function (briefId, prompt, provider) {
		var body = $elm$json$Json$Encode$object(
			_List_fromArray(
				[
					_Utils_Tuple2(
					'briefId',
					$elm$json$Json$Encode$string(briefId)),
					_Utils_Tuple2(
					'prompt',
					$elm$json$Json$Encode$string(prompt)),
					_Utils_Tuple2(
					'llm_provider',
					$elm$json$Json$Encode$string(provider))
				]));
		return $elm$http$Http$post(
			{
				body: $elm$http$Http$jsonBody(body),
				expect: A2($elm$http$Http$expectJson, $author$project$CreativeBriefEditor$GotScene, $author$project$CreativeBriefEditor$decodeSceneResponse),
				url: '/api/generate'
			});
	});
var $author$project$CreativeBriefEditor$GotVideo = function (a) {
	return {$: 'GotVideo', a: a};
};
var $author$project$CreativeBriefEditor$VideoResponse = F2(
	function (videoId, status) {
		return {status: status, videoId: videoId};
	});
var $author$project$CreativeBriefEditor$decodeVideoResponse = A3(
	$elm$json$Json$Decode$map2,
	$author$project$CreativeBriefEditor$VideoResponse,
	$elm$json$Json$Decode$oneOf(
		_List_fromArray(
			[
				A2($elm$json$Json$Decode$field, 'videoId', $elm$json$Json$Decode$string),
				A2(
				$elm$json$Json$Decode$field,
				'video_id',
				A2($elm$json$Json$Decode$map, $elm$core$String$fromInt, $elm$json$Json$Decode$int))
			])),
	A2($elm$json$Json$Decode$field, 'status', $elm$json$Json$Decode$string));
var $author$project$CreativeBriefEditor$generateVideo = function (briefId) {
	var body = $elm$json$Json$Encode$object(
		_List_fromArray(
			[
				_Utils_Tuple2(
				'model_id',
				$elm$json$Json$Encode$string('stability-ai/stable-video-diffusion')),
				_Utils_Tuple2(
				'input',
				$elm$json$Json$Encode$object(
					_List_fromArray(
						[
							_Utils_Tuple2(
							'prompt',
							$elm$json$Json$Encode$string('Generate video from creative brief'))
						]))),
				_Utils_Tuple2(
				'brief_id',
				$elm$json$Json$Encode$string(briefId))
			]));
	return $elm$http$Http$post(
		{
			body: $elm$http$Http$jsonBody(body),
			expect: A2($elm$http$Http$expectJson, $author$project$CreativeBriefEditor$GotVideo, $author$project$CreativeBriefEditor$decodeVideoResponse),
			url: '/api/run-video-model'
		});
};
var $author$project$CreativeBriefEditor$httpErrorToString = function (error) {
	switch (error.$) {
		case 'BadUrl':
			var url = error.a;
			return 'Bad URL: ' + url;
		case 'Timeout':
			return 'Request timed out';
		case 'NetworkError':
			return 'Network error';
		case 'BadStatus':
			var status = error.a;
			return 'Bad status: ' + $elm$core$String$fromInt(status);
		default:
			var message = error.a;
			return 'Bad response: ' + message;
	}
};
var $elm$core$Maybe$map = F2(
	function (f, maybe) {
		if (maybe.$ === 'Just') {
			var value = maybe.a;
			return $elm$core$Maybe$Just(
				f(value));
		} else {
			return $elm$core$Maybe$Nothing;
		}
	});
var $author$project$CreativeBriefEditor$GotRefine = function (a) {
	return {$: 'GotRefine', a: a};
};
var $author$project$CreativeBriefEditor$CreativeBriefResponse = F5(
	function (status, creativeDirection, scenes, metadata, briefId) {
		return {briefId: briefId, creativeDirection: creativeDirection, metadata: metadata, scenes: scenes, status: status};
	});
var $author$project$CreativeBriefEditor$Metadata = F3(
	function (cacheHit, confidenceScore, autoGeneratedScene) {
		return {autoGeneratedScene: autoGeneratedScene, cacheHit: cacheHit, confidenceScore: confidenceScore};
	});
var $elm$json$Json$Decode$bool = _Json_decodeBool;
var $author$project$CreativeBriefEditor$decodeMetadata = A4(
	$elm$json$Json$Decode$map3,
	$author$project$CreativeBriefEditor$Metadata,
	A2($elm$json$Json$Decode$field, 'cache_hit', $elm$json$Json$Decode$bool),
	$elm$json$Json$Decode$maybe(
		A2($elm$json$Json$Decode$field, 'confidence_score', $elm$json$Json$Decode$float)),
	$elm$json$Json$Decode$maybe(
		A2($elm$json$Json$Decode$field, 'auto_generated_scene', $elm$json$Json$Decode$value)));
var $author$project$CreativeBriefEditor$Scene = F5(
	function (id, sceneNumber, purpose, duration, visual) {
		return {duration: duration, id: id, purpose: purpose, sceneNumber: sceneNumber, visual: visual};
	});
var $author$project$CreativeBriefEditor$VisualDetails = F3(
	function (shotType, subject, generationPrompt) {
		return {generationPrompt: generationPrompt, shotType: shotType, subject: subject};
	});
var $author$project$CreativeBriefEditor$decodeVisualDetails = A4(
	$elm$json$Json$Decode$map3,
	$author$project$CreativeBriefEditor$VisualDetails,
	$elm$json$Json$Decode$maybe(
		A2($elm$json$Json$Decode$field, 'shot_type', $elm$json$Json$Decode$string)),
	$elm$json$Json$Decode$maybe(
		A2($elm$json$Json$Decode$field, 'subject', $elm$json$Json$Decode$string)),
	$elm$json$Json$Decode$maybe(
		A2($elm$json$Json$Decode$field, 'generation_prompt', $elm$json$Json$Decode$string)));
var $author$project$CreativeBriefEditor$decodeScene = A6(
	$elm$json$Json$Decode$map5,
	$author$project$CreativeBriefEditor$Scene,
	A2($elm$json$Json$Decode$field, 'id', $elm$json$Json$Decode$string),
	A2($elm$json$Json$Decode$field, 'scene_number', $elm$json$Json$Decode$int),
	A2($elm$json$Json$Decode$field, 'purpose', $elm$json$Json$Decode$string),
	A2($elm$json$Json$Decode$field, 'duration', $elm$json$Json$Decode$float),
	$elm$json$Json$Decode$maybe(
		A2($elm$json$Json$Decode$field, 'visual', $author$project$CreativeBriefEditor$decodeVisualDetails)));
var $author$project$CreativeBriefEditor$decodeBriefResponse = A6(
	$elm$json$Json$Decode$map5,
	$author$project$CreativeBriefEditor$CreativeBriefResponse,
	A2($elm$json$Json$Decode$field, 'status', $elm$json$Json$Decode$string),
	A2($elm$json$Json$Decode$field, 'creative_direction', $elm$json$Json$Decode$value),
	A2(
		$elm$json$Json$Decode$field,
		'scenes',
		$elm$json$Json$Decode$list($author$project$CreativeBriefEditor$decodeScene)),
	A2($elm$json$Json$Decode$field, 'metadata', $author$project$CreativeBriefEditor$decodeMetadata),
	A2($elm$json$Json$Decode$field, 'briefId', $elm$json$Json$Decode$string));
var $author$project$CreativeBriefEditor$refineBrief = F2(
	function (briefId, refinementText) {
		var body = $elm$json$Json$Encode$object(
			_List_fromArray(
				[
					_Utils_Tuple2(
					'refinement',
					$elm$json$Json$Encode$string(refinementText))
				]));
		return $elm$http$Http$post(
			{
				body: $elm$http$Http$jsonBody(body),
				expect: A2($elm$http$Http$expectJson, $author$project$CreativeBriefEditor$GotRefine, $author$project$CreativeBriefEditor$decodeBriefResponse),
				url: '/api/creative/briefs/' + (briefId + '/refine')
			});
	});
var $author$project$Ports$requestFileRead = _Platform_outgoingPort(
	'requestFileRead',
	function ($) {
		return $elm$json$Json$Encode$null;
	});
var $author$project$CreativeBriefEditor$BriefResponse = function (a) {
	return {$: 'BriefResponse', a: a};
};
var $author$project$CreativeBriefEditor$submitBrief = F2(
	function (model, bypass) {
		var url = '/api/creative/parse' + (bypass ? '?bypass_cache=true' : '');
		var expect = A2($elm$http$Http$expectJson, $author$project$CreativeBriefEditor$BriefResponse, $author$project$CreativeBriefEditor$decodeBriefResponse);
		var body = $elm$json$Json$Encode$object(
			_List_fromArray(
				[
					_Utils_Tuple2(
					'prompt',
					$elm$json$Json$Encode$object(
						_List_fromArray(
							[
								_Utils_Tuple2(
								'text',
								$elm$json$Json$Encode$string(model.text)),
								_Utils_Tuple2(
								'image_url',
								$elm$core$String$isEmpty(model.imageUrl) ? $elm$json$Json$Encode$null : $elm$json$Json$Encode$string(model.imageUrl)),
								_Utils_Tuple2(
								'video_url',
								$elm$core$String$isEmpty(model.videoUrl) ? $elm$json$Json$Encode$null : $elm$json$Json$Encode$string(model.videoUrl)),
								_Utils_Tuple2(
								'platform',
								$elm$json$Json$Encode$string(model.platform)),
								_Utils_Tuple2(
								'category',
								$elm$json$Json$Encode$string(model.category))
							]))),
					_Utils_Tuple2(
					'options',
					$elm$json$Json$Encode$object(
						_List_fromArray(
							[
								_Utils_Tuple2(
								'llm_provider',
								$elm$json$Json$Encode$string(model.llmProvider)),
								_Utils_Tuple2(
								'include_cost_estimate',
								$elm$json$Json$Encode$bool(false))
							])))
				]));
		return $elm$http$Http$post(
			{
				body: $elm$http$Http$jsonBody(body),
				expect: expect,
				url: url
			});
	});
var $author$project$CreativeBriefEditor$GotUpload = function (a) {
	return {$: 'GotUpload', a: a};
};
var $author$project$CreativeBriefEditor$UploadResponse = F2(
	function (url, id) {
		return {id: id, url: url};
	});
var $author$project$CreativeBriefEditor$decodeUploadResponse = A3(
	$elm$json$Json$Decode$map2,
	$author$project$CreativeBriefEditor$UploadResponse,
	A2($elm$json$Json$Decode$field, 'url', $elm$json$Json$Decode$string),
	A2($elm$json$Json$Decode$field, 'id', $elm$json$Json$Decode$string));
var $author$project$CreativeBriefEditor$uploadMedia = F2(
	function (model, base64) {
		var body = $elm$json$Json$Encode$object(
			_List_fromArray(
				[
					_Utils_Tuple2(
					'file',
					$elm$json$Json$Encode$string(base64)),
					_Utils_Tuple2(
					'type',
					A2($elm$core$String$contains, 'image', base64) ? $elm$json$Json$Encode$string('image') : $elm$json$Json$Encode$string('video'))
				]));
		return $elm$http$Http$post(
			{
				body: $elm$http$Http$jsonBody(body),
				expect: A2($elm$http$Http$expectJson, $author$project$CreativeBriefEditor$GotUpload, $author$project$CreativeBriefEditor$decodeUploadResponse),
				url: '/api/upload'
			});
	});
var $author$project$CreativeBriefEditor$update = F2(
	function (msg, model) {
		switch (msg.$) {
			case 'UpdateText':
				var text = msg.a;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{text: text}),
					$elm$core$Platform$Cmd$none);
			case 'UpdateImageUrl':
				var url = msg.a;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{imageUrl: url}),
					$elm$core$Platform$Cmd$none);
			case 'UpdateVideoUrl':
				var url = msg.a;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{videoUrl: url}),
					$elm$core$Platform$Cmd$none);
			case 'UpdatePlatform':
				var platform = msg.a;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{platform: platform}),
					$elm$core$Platform$Cmd$none);
			case 'UpdateCategory':
				var category = msg.a;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{category: category}),
					$elm$core$Platform$Cmd$none);
			case 'UpdateLLMProvider':
				var provider = msg.a;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{llmProvider: provider}),
					$elm$core$Platform$Cmd$none);
			case 'SubmitBrief':
				var bypass = msg.a;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{error: $elm$core$Maybe$Nothing, isLoading: true}),
					A2($author$project$CreativeBriefEditor$submitBrief, model, bypass));
			case 'BriefResponse':
				var result = msg.a;
				if (result.$ === 'Ok') {
					var response = result.a;
					var firstScenePrompt = A2(
						$elm$core$Maybe$withDefault,
						'',
						A2(
							$elm$core$Maybe$andThen,
							function ($) {
								return $.generationPrompt;
							},
							A2(
								$elm$core$Maybe$andThen,
								function ($) {
									return $.visual;
								},
								$elm$core$List$head(response.scenes))));
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								autoScenePrompt: firstScenePrompt,
								briefId: $elm$core$Maybe$Just(response.briefId),
								error: $elm$core$Maybe$Nothing,
								isLoading: false,
								response: $elm$core$Maybe$Just(response)
							}),
						$elm$core$Platform$Cmd$none);
				} else {
					var error = result.a;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								error: $elm$core$Maybe$Just(
									$author$project$CreativeBriefEditor$httpErrorToString(error)),
								isLoading: false
							}),
						$elm$core$Platform$Cmd$none);
				}
			case 'ClearError':
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{error: $elm$core$Maybe$Nothing}),
					$elm$core$Platform$Cmd$none);
			case 'FileSelected':
				var file = msg.a;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{
							selectedFile: $elm$core$Maybe$Just(file)
						}),
					$elm$core$Platform$Cmd$none);
			case 'FileLoaded':
				var base64 = msg.a;
				return _Utils_Tuple2(
					model,
					A2($author$project$CreativeBriefEditor$uploadMedia, model, base64));
			case 'UploadMedia':
				return _Utils_Tuple2(
					model,
					$author$project$Ports$requestFileRead(_Utils_Tuple0));
			case 'GotUpload':
				var result = msg.a;
				if (result.$ === 'Ok') {
					var uploadResponse = result.a;
					var updatedModel = A2($elm$core$String$contains, 'image', uploadResponse.url) ? _Utils_update(
						model,
						{error: $elm$core$Maybe$Nothing, imageUrl: uploadResponse.url}) : _Utils_update(
						model,
						{error: $elm$core$Maybe$Nothing, videoUrl: uploadResponse.url});
					return _Utils_Tuple2(
						updatedModel,
						A2($author$project$CreativeBriefEditor$submitBrief, updatedModel, false));
				} else {
					var error = result.a;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								error: $elm$core$Maybe$Just(
									$author$project$CreativeBriefEditor$httpErrorToString(error))
							}),
						$elm$core$Platform$Cmd$none);
				}
			case 'GenerateScene':
				var _v3 = model.briefId;
				if (_v3.$ === 'Just') {
					var id = _v3.a;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{isLoading: true}),
						A3($author$project$CreativeBriefEditor$generateScene, id, model.autoScenePrompt, model.llmProvider));
				} else {
					return _Utils_Tuple2(model, $elm$core$Platform$Cmd$none);
				}
			case 'GotScene':
				var result = msg.a;
				if (result.$ === 'Ok') {
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{isLoading: false}),
						A2($elm$browser$Browser$Navigation$pushUrl, model.navigationKey, '/simulations'));
				} else {
					var error = result.a;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								error: $elm$core$Maybe$Just(
									$author$project$CreativeBriefEditor$httpErrorToString(error)),
								isLoading: false
							}),
						$elm$core$Platform$Cmd$none);
				}
			case 'GenerateVideo':
				var _v5 = model.briefId;
				if (_v5.$ === 'Just') {
					var id = _v5.a;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{isLoading: true}),
						$author$project$CreativeBriefEditor$generateVideo(id));
				} else {
					return _Utils_Tuple2(model, $elm$core$Platform$Cmd$none);
				}
			case 'GotVideo':
				var result = msg.a;
				if (result.$ === 'Ok') {
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{isLoading: false}),
						A2($elm$browser$Browser$Navigation$pushUrl, model.navigationKey, '/videos'));
				} else {
					var error = result.a;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								error: $elm$core$Maybe$Just(
									$author$project$CreativeBriefEditor$httpErrorToString(error)),
								isLoading: false
							}),
						$elm$core$Platform$Cmd$none);
				}
			case 'RefineBrief':
				var _v7 = model.briefId;
				if (_v7.$ === 'Just') {
					var id = _v7.a;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{isLoading: true}),
						A2($author$project$CreativeBriefEditor$refineBrief, id, model.text));
				} else {
					return _Utils_Tuple2(model, $elm$core$Platform$Cmd$none);
				}
			case 'GotRefine':
				var result = msg.a;
				if (result.$ === 'Ok') {
					var response = result.a;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								error: $elm$core$Maybe$Nothing,
								isLoading: false,
								response: $elm$core$Maybe$Just(response)
							}),
						$elm$core$Platform$Cmd$none);
				} else {
					var error = result.a;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								error: $elm$core$Maybe$Just(
									$author$project$CreativeBriefEditor$httpErrorToString(error))
							}),
						$elm$core$Platform$Cmd$none);
				}
			case 'NavigateTo':
				var route = msg.a;
				return _Utils_Tuple2(
					model,
					A2(
						$elm$browser$Browser$Navigation$pushUrl,
						model.navigationKey,
						$author$project$Route$toHref(route)));
			case 'FetchImageModels':
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{loadingImageModels: true}),
					$author$project$CreativeBriefEditor$fetchImageModels);
			case 'ImageModelsFetched':
				var result = msg.a;
				if (result.$ === 'Ok') {
					var models = result.a;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								imageModels: models,
								loadingImageModels: false,
								selectedImageModel: A2(
									$elm$core$Maybe$map,
									function (m) {
										return m.owner + ('/' + m.name);
									},
									$elm$core$List$head(models))
							}),
						$elm$core$Platform$Cmd$none);
				} else {
					var error = result.a;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								error: $elm$core$Maybe$Just(
									'Failed to load image models: ' + $author$project$CreativeBriefEditor$httpErrorToString(error)),
								loadingImageModels: false
							}),
						$elm$core$Platform$Cmd$none);
				}
			case 'SelectImageModel':
				var modelName = msg.a;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{
							selectedImageModel: $elm$core$Maybe$Just(modelName)
						}),
					$elm$core$Platform$Cmd$none);
			case 'GenerateImages':
				var _v10 = _Utils_Tuple2(model.briefId, model.selectedImageModel);
				if ((_v10.a.$ === 'Just') && (_v10.b.$ === 'Just')) {
					var briefId = _v10.a.a;
					var modelName = _v10.b.a;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{error: $elm$core$Maybe$Nothing, generatingImages: true}),
						A2($author$project$CreativeBriefEditor$generateImagesFromBrief, briefId, modelName));
				} else {
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								error: $elm$core$Maybe$Just('Missing brief ID or image model')
							}),
						$elm$core$Platform$Cmd$none);
				}
			default:
				var result = msg.a;
				if (result.$ === 'Ok') {
					var imageIds = result.a;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{generatingImages: false}),
						A2($elm$browser$Browser$Navigation$pushUrl, model.navigationKey, '/images'));
				} else {
					var error = result.a;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								error: $elm$core$Maybe$Just(
									'Failed to generate images: ' + $author$project$CreativeBriefEditor$httpErrorToString(error)),
								generatingImages: false
							}),
						$elm$core$Platform$Cmd$none);
				}
		}
	});
var $author$project$Image$NavigateToImage = function (a) {
	return {$: 'NavigateToImage', a: a};
};
var $author$project$Image$Parameter = F9(
	function (key, value, paramType, _enum, description, _default, minimum, maximum, format) {
		return {_default: _default, description: description, _enum: _enum, format: format, key: key, maximum: maximum, minimum: minimum, paramType: paramType, value: value};
	});
var $author$project$Image$ScrollToModel = function (a) {
	return {$: 'ScrollToModel', a: a};
};
var $author$project$Image$demoModels = _List_fromArray(
	[
		A4($author$project$Image$ImageModel, 'demo/text-to-image', 'Demo Text-to-Video', 'Generates a demo video from text prompt', $elm$core$Maybe$Nothing),
		A4($author$project$Image$ImageModel, 'demo/image-to-video', 'Demo Image-to-Video', 'Generates a demo video from image and prompt', $elm$core$Maybe$Nothing)
	]);
var $author$project$Image$SchemaFetched = F2(
	function (a, b) {
		return {$: 'SchemaFetched', a: a, b: b};
	});
var $author$project$Image$schemaResponseDecoder = A4(
	$elm$json$Json$Decode$map3,
	F3(
		function (s, r, v) {
			return {required: r, schema: s, version: v};
		}),
	A2($elm$json$Json$Decode$field, 'input_schema', $elm$json$Json$Decode$value),
	$elm$json$Json$Decode$oneOf(
		_List_fromArray(
			[
				A2(
				$elm$json$Json$Decode$field,
				'required',
				$elm$json$Json$Decode$list($elm$json$Json$Decode$string)),
				$elm$json$Json$Decode$succeed(_List_Nil)
			])),
	$elm$json$Json$Decode$maybe(
		A2($elm$json$Json$Decode$field, 'version', $elm$json$Json$Decode$string)));
var $author$project$Image$fetchModelSchema = function (modelId) {
	var parts = A2($elm$core$String$split, '/', modelId);
	var url = function () {
		if ((parts.b && parts.b.b) && (!parts.b.b.b)) {
			var owner = parts.a;
			var _v1 = parts.b;
			var name = _v1.a;
			return '/api/image-models/' + (owner + ('/' + (name + '/schema')));
		} else {
			return '';
		}
	}();
	return $elm$core$String$isEmpty(url) ? $elm$core$Platform$Cmd$none : $elm$http$Http$get(
		{
			expect: A2(
				$elm$http$Http$expectJson,
				$author$project$Image$SchemaFetched(modelId),
				$author$project$Image$schemaResponseDecoder),
			url: url
		});
};
var $author$project$Image$ImageGenerated = function (a) {
	return {$: 'ImageGenerated', a: a};
};
var $elm$json$Json$Encode$list = F2(
	function (func, entries) {
		return _Json_wrap(
			A3(
				$elm$core$List$foldl,
				_Json_addEntry(func),
				_Json_emptyArray(_Utils_Tuple0),
				entries));
	});
var $author$project$Image$videoResponseDecoder = A3(
	$elm$json$Json$Decode$map2,
	F2(
		function (id, s) {
			return {image_id: id, status: s};
		}),
	A2($elm$json$Json$Decode$field, 'image_id', $elm$json$Json$Decode$int),
	A2($elm$json$Json$Decode$field, 'status', $elm$json$Json$Decode$string));
var $author$project$Image$generateVideo = F4(
	function (modelId, parameters, collection, maybeVersion) {
		var encodeParameterValue = function (param) {
			if ($elm$core$String$isEmpty(
				$elm$core$String$trim(param.value))) {
				return $elm$core$Maybe$Nothing;
			} else {
				var encoded = function () {
					var _v1 = param.paramType;
					switch (_v1) {
						case 'integer':
							var _v2 = $elm$core$String$toInt(param.value);
							if (_v2.$ === 'Just') {
								var i = _v2.a;
								return $elm$json$Json$Encode$int(i);
							} else {
								return $elm$json$Json$Encode$string(param.value);
							}
						case 'number':
							var _v3 = $elm$core$String$toFloat(param.value);
							if (_v3.$ === 'Just') {
								var f = _v3.a;
								return $elm$json$Json$Encode$float(f);
							} else {
								return $elm$json$Json$Encode$string(param.value);
							}
						case 'boolean':
							var _v4 = $elm$core$String$toLower(param.value);
							switch (_v4) {
								case 'true':
									return $elm$json$Json$Encode$bool(true);
								case 'false':
									return $elm$json$Json$Encode$bool(false);
								default:
									return $elm$json$Json$Encode$string(param.value);
							}
						case 'array':
							var _v5 = A2(
								$elm$json$Json$Decode$decodeString,
								$elm$json$Json$Decode$list($elm$json$Json$Decode$string),
								param.value);
							if (_v5.$ === 'Ok') {
								var strings = _v5.a;
								return A2($elm$json$Json$Encode$list, $elm$json$Json$Encode$string, strings);
							} else {
								return A2(
									$elm$json$Json$Encode$list,
									$elm$json$Json$Encode$string,
									_List_fromArray(
										[param.value]));
							}
						default:
							return $elm$json$Json$Encode$string(param.value);
					}
				}();
				return $elm$core$Maybe$Just(
					_Utils_Tuple2(param.key, encoded));
			}
		};
		var inputObject = $elm$json$Json$Encode$object(
			A2($elm$core$List$filterMap, encodeParameterValue, parameters));
		var requestFields = _Utils_ap(
			_List_fromArray(
				[
					_Utils_Tuple2(
					'model_id',
					$elm$json$Json$Encode$string(modelId)),
					_Utils_Tuple2('input', inputObject),
					_Utils_Tuple2(
					'collection',
					$elm$json$Json$Encode$string(collection))
				]),
			function () {
				if (maybeVersion.$ === 'Just') {
					var version = maybeVersion.a;
					return _List_fromArray(
						[
							_Utils_Tuple2(
							'version',
							$elm$json$Json$Encode$string(version))
						]);
				} else {
					return _List_Nil;
				}
			}());
		return $elm$http$Http$post(
			{
				body: $elm$http$Http$jsonBody(
					$elm$json$Json$Encode$object(requestFields)),
				expect: A2($elm$http$Http$expectJson, $author$project$Image$ImageGenerated, $author$project$Image$videoResponseDecoder),
				url: '/api/run-image-model'
			});
	});
var $author$project$Image$httpErrorToString = function (error) {
	switch (error.$) {
		case 'BadUrl':
			var url = error.a;
			return 'Bad URL: ' + url;
		case 'Timeout':
			return 'Request timed out';
		case 'NetworkError':
			return 'Network error';
		case 'BadStatus':
			var status = error.a;
			return 'Server error: ' + $elm$core$String$fromInt(status);
		default:
			var body = error.a;
			return 'Invalid response: ' + body;
	}
};
var $author$project$Image$parseParameter = function (_v0) {
	var key = _v0.a;
	var value = _v0.b;
	var paramType = A2(
		$elm$core$Result$withDefault,
		'string',
		A2(
			$elm$json$Json$Decode$decodeValue,
			A2(
				$elm$json$Json$Decode$at,
				_List_fromArray(
					['type']),
				$elm$json$Json$Decode$string),
			value));
	var minimum = $elm$core$Result$toMaybe(
		A2(
			$elm$json$Json$Decode$decodeValue,
			A2($elm$json$Json$Decode$field, 'minimum', $elm$json$Json$Decode$float),
			value));
	var maximum = $elm$core$Result$toMaybe(
		A2(
			$elm$json$Json$Decode$decodeValue,
			A2($elm$json$Json$Decode$field, 'maximum', $elm$json$Json$Decode$float),
			value));
	var format = $elm$core$Result$toMaybe(
		A2(
			$elm$json$Json$Decode$decodeValue,
			A2($elm$json$Json$Decode$field, 'format', $elm$json$Json$Decode$string),
			value));
	var enumValues = $elm$core$Result$toMaybe(
		A2(
			$elm$json$Json$Decode$decodeValue,
			A2(
				$elm$json$Json$Decode$at,
				_List_fromArray(
					['enum']),
				$elm$json$Json$Decode$list($elm$json$Json$Decode$string)),
			value));
	var description = $elm$core$Result$toMaybe(
		A2(
			$elm$json$Json$Decode$decodeValue,
			A2(
				$elm$json$Json$Decode$at,
				_List_fromArray(
					['description']),
				$elm$json$Json$Decode$string),
			value));
	var _default = A2(
		$elm$core$Maybe$andThen,
		function (v) {
			var _v1 = A2($elm$json$Json$Decode$decodeValue, $elm$json$Json$Decode$string, v);
			if (_v1.$ === 'Ok') {
				var s = _v1.a;
				return $elm$core$Maybe$Just(s);
			} else {
				var _v2 = A2($elm$json$Json$Decode$decodeValue, $elm$json$Json$Decode$float, v);
				if (_v2.$ === 'Ok') {
					var f = _v2.a;
					return $elm$core$Maybe$Just(
						$elm$core$String$fromFloat(f));
				} else {
					var _v3 = A2($elm$json$Json$Decode$decodeValue, $elm$json$Json$Decode$int, v);
					if (_v3.$ === 'Ok') {
						var i = _v3.a;
						return $elm$core$Maybe$Just(
							$elm$core$String$fromInt(i));
					} else {
						return $elm$core$Maybe$Nothing;
					}
				}
			}
		},
		$elm$core$Result$toMaybe(
			A2(
				$elm$json$Json$Decode$decodeValue,
				A2($elm$json$Json$Decode$field, 'default', $elm$json$Json$Decode$value),
				value)));
	var initialValue = A2($elm$core$Maybe$withDefault, '', _default);
	return A9($author$project$Image$Parameter, key, initialValue, paramType, enumValues, description, _default, minimum, maximum, format);
};
var $author$project$Image$updateParameterInList = F3(
	function (key, value, params) {
		return A2(
			$elm$core$List$map,
			function (param) {
				return _Utils_eq(param.key, key) ? _Utils_update(
					param,
					{value: value}) : param;
			},
			params);
	});
var $author$project$Image$ImageUploaded = F2(
	function (a, b) {
		return {$: 'ImageUploaded', a: a, b: b};
	});
var $elm$http$Http$filePart = _Http_pair;
var $elm$http$Http$multipartBody = function (parts) {
	return A2(
		_Http_pair,
		'',
		_Http_toFormData(parts));
};
var $author$project$Image$uploadResponseDecoder = A2($elm$json$Json$Decode$field, 'url', $elm$json$Json$Decode$string);
var $author$project$Image$uploadImage = F2(
	function (paramKey, file) {
		return $elm$http$Http$post(
			{
				body: $elm$http$Http$multipartBody(
					_List_fromArray(
						[
							A2($elm$http$Http$filePart, 'file', file)
						])),
				expect: A2(
					$elm$http$Http$expectJson,
					$author$project$Image$ImageUploaded(paramKey),
					$author$project$Image$uploadResponseDecoder),
				url: '/api/upload-image'
			});
	});
var $author$project$Image$update = F2(
	function (msg, model) {
		switch (msg.$) {
			case 'NoOp':
				return _Utils_Tuple2(model, $elm$core$Platform$Cmd$none);
			case 'FetchModels':
				return _Utils_Tuple2(
					model,
					$author$project$Image$fetchModels(model.selectedCollection));
			case 'SelectCollection':
				var collection = msg.a;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{outputImage: $elm$core$Maybe$Nothing, requiredFields: _List_Nil, selectedCollection: collection, selectedModel: $elm$core$Maybe$Nothing, selectedVersion: $elm$core$Maybe$Nothing}),
					$author$project$Image$fetchModels(collection));
			case 'ModelsFetched':
				var result = msg.a;
				if (result.$ === 'Ok') {
					var models = result.a;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{error: $elm$core$Maybe$Nothing, models: models}),
						$elm$core$Platform$Cmd$none);
				} else {
					var error = result.a;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								error: $elm$core$Maybe$Just(
									'Failed to fetch models: ' + $author$project$Image$httpErrorToString(error)),
								models: $author$project$Image$demoModels
							}),
						$elm$core$Platform$Cmd$none);
				}
			case 'SelectModel':
				var modelId = msg.a;
				var selected = $elm$core$List$head(
					A2(
						$elm$core$List$filter,
						function (m) {
							return _Utils_eq(m.id, modelId);
						},
						model.models));
				if (selected.$ === 'Just') {
					var selectedModel = selected.a;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{error: $elm$core$Maybe$Nothing, outputImage: $elm$core$Maybe$Nothing, parameters: _List_Nil, selectedModel: selected}),
						$author$project$Image$fetchModelSchema(selectedModel.id));
				} else {
					return _Utils_Tuple2(model, $elm$core$Platform$Cmd$none);
				}
			case 'SchemaFetched':
				var modelId = msg.a;
				var result = msg.b;
				if (result.$ === 'Ok') {
					var schema = result.a.schema;
					var required = result.a.required;
					var version = result.a.version;
					var params = function () {
						var _v4 = A2(
							$elm$json$Json$Decode$decodeValue,
							$elm$json$Json$Decode$keyValuePairs($elm$json$Json$Decode$value),
							schema);
						if (_v4.$ === 'Ok') {
							var properties = _v4.a;
							return A2($elm$core$List$map, $author$project$Image$parseParameter, properties);
						} else {
							return _List_fromArray(
								[
									A9($author$project$Image$Parameter, 'prompt', '', 'string', $elm$core$Maybe$Nothing, $elm$core$Maybe$Nothing, $elm$core$Maybe$Nothing, $elm$core$Maybe$Nothing, $elm$core$Maybe$Nothing, $elm$core$Maybe$Nothing)
								]);
						}
					}();
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{parameters: params, requiredFields: required, selectedVersion: version}),
						A2(
							$elm$core$Task$attempt,
							$author$project$Image$ScrollToModel,
							A2(
								$elm$core$Task$andThen,
								function (info) {
									return A2($elm$browser$Browser$Dom$setViewport, 0, info.element.y);
								},
								$elm$browser$Browser$Dom$getElement('selected-model-section'))));
				} else {
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								parameters: _List_fromArray(
									[
										A9($author$project$Image$Parameter, 'prompt', '', 'string', $elm$core$Maybe$Nothing, $elm$core$Maybe$Nothing, $elm$core$Maybe$Nothing, $elm$core$Maybe$Nothing, $elm$core$Maybe$Nothing, $elm$core$Maybe$Nothing)
									]),
								requiredFields: _List_fromArray(
									['prompt']),
								selectedVersion: $elm$core$Maybe$Nothing
							}),
						A2(
							$elm$core$Task$attempt,
							$author$project$Image$ScrollToModel,
							A2(
								$elm$core$Task$andThen,
								function (info) {
									return A2($elm$browser$Browser$Dom$setViewport, 0, info.element.y);
								},
								$elm$browser$Browser$Dom$getElement('selected-model-section'))));
				}
			case 'UpdateParameter':
				var key = msg.a;
				var value = msg.b;
				var updatedParams = A3($author$project$Image$updateParameterInList, key, value, model.parameters);
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{parameters: updatedParams}),
					$elm$core$Platform$Cmd$none);
			case 'UpdateSearch':
				var query = msg.a;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{searchQuery: query}),
					$elm$core$Platform$Cmd$none);
			case 'GenerateImage':
				var _v5 = model.selectedModel;
				if (_v5.$ === 'Just') {
					var selectedModel = _v5.a;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{error: $elm$core$Maybe$Nothing, isGenerating: true}),
						A4($author$project$Image$generateVideo, selectedModel.id, model.parameters, model.selectedCollection, model.selectedVersion));
				} else {
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								error: $elm$core$Maybe$Just('No model selected')
							}),
						$elm$core$Platform$Cmd$none);
				}
			case 'ImageGenerated':
				var result = msg.a;
				if (result.$ === 'Ok') {
					var response = result.a;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								error: $elm$core$Maybe$Nothing,
								imageStatus: response.status,
								isGenerating: false,
								pollingImageId: $elm$core$Maybe$Just(response.image_id)
							}),
						A2(
							$elm$core$Task$perform,
							function (_v7) {
								return $author$project$Image$NavigateToImage(response.image_id);
							},
							$elm$core$Task$succeed(_Utils_Tuple0)));
				} else {
					var error = result.a;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								error: $elm$core$Maybe$Just(
									$author$project$Image$httpErrorToString(error)),
								isGenerating: false
							}),
						$elm$core$Platform$Cmd$none);
				}
			case 'NavigateToImage':
				return _Utils_Tuple2(model, $elm$core$Platform$Cmd$none);
			case 'ScrollToModel':
				return _Utils_Tuple2(model, $elm$core$Platform$Cmd$none);
			case 'PollImageStatus':
				return _Utils_Tuple2(model, $elm$core$Platform$Cmd$none);
			case 'ImageStatusFetched':
				var result = msg.a;
				if (result.$ === 'Ok') {
					var videoRecord = result.a;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								imageStatus: videoRecord.status,
								isGenerating: (videoRecord.status !== 'completed') && (videoRecord.status !== 'failed'),
								outputImage: (videoRecord.status === 'completed') ? $elm$core$Maybe$Just(videoRecord.imageUrl) : model.outputImage
							}),
						$elm$core$Platform$Cmd$none);
				} else {
					var error = result.a;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								error: $elm$core$Maybe$Just(
									$author$project$Image$httpErrorToString(error))
							}),
						$elm$core$Platform$Cmd$none);
				}
			case 'FileSelected':
				var paramKey = msg.a;
				var file = msg.b;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{
							uploadingFile: $elm$core$Maybe$Just(paramKey)
						}),
					A2($author$project$Image$uploadImage, paramKey, file));
			default:
				var paramKey = msg.a;
				var result = msg.b;
				if (result.$ === 'Ok') {
					var imageUrl = result.a;
					var updatedParams = A3($author$project$Image$updateParameterInList, paramKey, imageUrl, model.parameters);
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{error: $elm$core$Maybe$Nothing, parameters: updatedParams, uploadingFile: $elm$core$Maybe$Nothing}),
						$elm$core$Platform$Cmd$none);
				} else {
					var error = result.a;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								error: $elm$core$Maybe$Just(
									'Upload failed: ' + $author$project$Image$httpErrorToString(error)),
								uploadingFile: $elm$core$Maybe$Nothing
							}),
						$elm$core$Platform$Cmd$none);
				}
		}
	});
var $author$project$ImageDetail$httpErrorToString = function (error) {
	switch (error.$) {
		case 'BadUrl':
			var url = error.a;
			return 'Bad URL: ' + url;
		case 'Timeout':
			return 'Request timed out';
		case 'NetworkError':
			return 'Network error';
		case 'BadStatus':
			var status = error.a;
			return 'Server error: ' + $elm$core$String$fromInt(status);
		default:
			var body = error.a;
			return 'Invalid response: ' + body;
	}
};
var $author$project$ImageDetail$update = F2(
	function (msg, model) {
		if (msg.$ === 'ImageFetched') {
			var result = msg.a;
			if (result.$ === 'Ok') {
				var image = result.a;
				var shouldStopPolling = (image.status === 'completed') || ((image.status === 'failed') || (image.status === 'canceled'));
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{
							error: $elm$core$Maybe$Nothing,
							image: $elm$core$Maybe$Just(image),
							isPolling: !shouldStopPolling
						}),
					$elm$core$Platform$Cmd$none);
			} else {
				var error = result.a;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{
							error: $elm$core$Maybe$Just(
								$author$project$ImageDetail$httpErrorToString(error)),
							isPolling: false
						}),
					$elm$core$Platform$Cmd$none);
			}
		} else {
			return model.isPolling ? _Utils_Tuple2(
				model,
				$author$project$ImageDetail$fetchImage(model.imageId)) : _Utils_Tuple2(model, $elm$core$Platform$Cmd$none);
		}
	});
var $author$project$ImageGallery$httpErrorToString = function (error) {
	switch (error.$) {
		case 'BadUrl':
			var url = error.a;
			return 'Bad URL: ' + url;
		case 'Timeout':
			return 'Request timed out';
		case 'NetworkError':
			return 'Network error';
		case 'BadStatus':
			var status = error.a;
			return 'Server error: ' + $elm$core$String$fromInt(status);
		default:
			var body = error.a;
			return 'Invalid response: ' + body;
	}
};
var $author$project$ImageGallery$update = F2(
	function (msg, model) {
		switch (msg.$) {
			case 'NoOp':
				return _Utils_Tuple2(model, $elm$core$Platform$Cmd$none);
			case 'FetchImages':
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{loading: true}),
					$author$project$ImageGallery$fetchImages);
			case 'ImagesFetched':
				var result = msg.a;
				if (result.$ === 'Ok') {
					var images = result.a;
					return _Utils_eq(images, model.images) ? _Utils_Tuple2(
						_Utils_update(
							model,
							{loading: false}),
						$elm$core$Platform$Cmd$none) : _Utils_Tuple2(
						_Utils_update(
							model,
							{error: $elm$core$Maybe$Nothing, images: images, loading: false}),
						$elm$core$Platform$Cmd$none);
				} else {
					var error = result.a;
					var errorMsg = function () {
						if ((error.$ === 'BadStatus') && (error.a === 401)) {
							return $elm$core$Maybe$Nothing;
						} else {
							return $elm$core$Maybe$Just(
								$author$project$ImageGallery$httpErrorToString(error));
						}
					}();
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{error: errorMsg, loading: false}),
						$elm$core$Platform$Cmd$none);
				}
			case 'SelectImage':
				var video = msg.a;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{
							selectedImage: $elm$core$Maybe$Just(video),
							showRawData: false
						}),
					$elm$core$Platform$Cmd$none);
			case 'CloseImage':
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{selectedImage: $elm$core$Maybe$Nothing, showRawData: false}),
					$elm$core$Platform$Cmd$none);
			case 'ToggleRawData':
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{showRawData: !model.showRawData}),
					$elm$core$Platform$Cmd$none);
			case 'Tick':
				return _Utils_Tuple2(model, $author$project$ImageGallery$fetchImages);
			case 'FetchVideoModels':
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{loadingModels: true}),
					$author$project$ImageGallery$fetchVideoModels);
			case 'VideoModelsFetched':
				var result = msg.a;
				if (result.$ === 'Ok') {
					var models = result.a;
					var firstModel = A2(
						$elm$core$Maybe$map,
						function ($) {
							return $.id;
						},
						$elm$core$List$head(models));
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{loadingModels: false, selectedVideoModel: firstModel, videoModels: models}),
						$elm$core$Platform$Cmd$none);
				} else {
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{loadingModels: false}),
						$elm$core$Platform$Cmd$none);
				}
			case 'SelectVideoModel':
				var modelId = msg.a;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{
							selectedVideoModel: $elm$core$Maybe$Just(modelId)
						}),
					$elm$core$Platform$Cmd$none);
			default:
				var modelId = msg.a;
				var imageUrl = msg.b;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{selectedImage: $elm$core$Maybe$Nothing}),
					$elm$core$Platform$Cmd$none);
		}
	});
var $author$project$SimulationGallery$httpErrorToString = function (error) {
	switch (error.$) {
		case 'BadUrl':
			var url = error.a;
			return 'Bad URL: ' + url;
		case 'Timeout':
			return 'Request timed out';
		case 'NetworkError':
			return 'Network error';
		case 'BadStatus':
			var code = error.a;
			return 'Server error: ' + $elm$core$String$fromInt(code);
		default:
			var message = error.a;
			return 'Invalid response: ' + message;
	}
};
var $author$project$SimulationGallery$update = F2(
	function (msg, model) {
		switch (msg.$) {
			case 'NoOp':
				return _Utils_Tuple2(model, $elm$core$Platform$Cmd$none);
			case 'FetchVideos':
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{loading: true}),
					$author$project$SimulationGallery$fetchVideos);
			case 'VideosFetched':
				var result = msg.a;
				if (result.$ === 'Ok') {
					var videos = result.a;
					return _Utils_eq(videos, model.videos) ? _Utils_Tuple2(
						_Utils_update(
							model,
							{loading: false}),
						$elm$core$Platform$Cmd$none) : _Utils_Tuple2(
						_Utils_update(
							model,
							{error: $elm$core$Maybe$Nothing, loading: false, videos: videos}),
						$elm$core$Platform$Cmd$none);
				} else {
					var error = result.a;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								error: $elm$core$Maybe$Just(
									$author$project$SimulationGallery$httpErrorToString(error)),
								loading: false
							}),
						$elm$core$Platform$Cmd$none);
				}
			case 'SelectVideo':
				var video = msg.a;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{
							selectedVideo: $elm$core$Maybe$Just(video),
							showRawData: false
						}),
					$elm$core$Platform$Cmd$none);
			case 'CloseVideo':
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{selectedVideo: $elm$core$Maybe$Nothing, showRawData: false}),
					$elm$core$Platform$Cmd$none);
			case 'ToggleRawData':
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{showRawData: !model.showRawData}),
					$elm$core$Platform$Cmd$none);
			default:
				return _Utils_Tuple2(model, $author$project$SimulationGallery$fetchVideos);
		}
	});
var $author$project$Video$NavigateToVideo = function (a) {
	return {$: 'NavigateToVideo', a: a};
};
var $author$project$Video$Parameter = F9(
	function (key, value, paramType, _enum, description, _default, minimum, maximum, format) {
		return {_default: _default, description: description, _enum: _enum, format: format, key: key, maximum: maximum, minimum: minimum, paramType: paramType, value: value};
	});
var $author$project$Video$ScrollToModel = function (a) {
	return {$: 'ScrollToModel', a: a};
};
var $author$project$Video$demoModels = _List_fromArray(
	[
		A4($author$project$Video$VideoModel, 'demo/text-to-video', 'Demo Text-to-Video', 'Generates a demo video from text prompt', $elm$core$Maybe$Nothing),
		A4($author$project$Video$VideoModel, 'demo/image-to-video', 'Demo Image-to-Video', 'Generates a demo video from image and prompt', $elm$core$Maybe$Nothing)
	]);
var $author$project$Video$SchemaFetched = F2(
	function (a, b) {
		return {$: 'SchemaFetched', a: a, b: b};
	});
var $author$project$Video$schemaResponseDecoder = A4(
	$elm$json$Json$Decode$map3,
	F3(
		function (s, r, v) {
			return {required: r, schema: s, version: v};
		}),
	A2($elm$json$Json$Decode$field, 'input_schema', $elm$json$Json$Decode$value),
	$elm$json$Json$Decode$oneOf(
		_List_fromArray(
			[
				A2(
				$elm$json$Json$Decode$field,
				'required',
				$elm$json$Json$Decode$list($elm$json$Json$Decode$string)),
				$elm$json$Json$Decode$succeed(_List_Nil)
			])),
	$elm$json$Json$Decode$maybe(
		A2($elm$json$Json$Decode$field, 'version', $elm$json$Json$Decode$string)));
var $author$project$Video$fetchModelSchema = function (modelId) {
	var parts = A2($elm$core$String$split, '/', modelId);
	var url = function () {
		if ((parts.b && parts.b.b) && (!parts.b.b.b)) {
			var owner = parts.a;
			var _v1 = parts.b;
			var name = _v1.a;
			return '/api/video-models/' + (owner + ('/' + (name + '/schema')));
		} else {
			return '';
		}
	}();
	return $elm$core$String$isEmpty(url) ? $elm$core$Platform$Cmd$none : $elm$http$Http$get(
		{
			expect: A2(
				$elm$http$Http$expectJson,
				$author$project$Video$SchemaFetched(modelId),
				$author$project$Video$schemaResponseDecoder),
			url: url
		});
};
var $author$project$Video$VideoGenerated = function (a) {
	return {$: 'VideoGenerated', a: a};
};
var $author$project$Video$videoResponseDecoder = A3(
	$elm$json$Json$Decode$map2,
	F2(
		function (id, s) {
			return {status: s, video_id: id};
		}),
	A2($elm$json$Json$Decode$field, 'video_id', $elm$json$Json$Decode$int),
	A2($elm$json$Json$Decode$field, 'status', $elm$json$Json$Decode$string));
var $author$project$Video$generateVideo = F4(
	function (modelId, parameters, collection, maybeVersion) {
		var encodeParameterValue = function (param) {
			if ($elm$core$String$isEmpty(
				$elm$core$String$trim(param.value))) {
				return $elm$core$Maybe$Nothing;
			} else {
				var encoded = function () {
					var _v1 = param.paramType;
					switch (_v1) {
						case 'integer':
							var _v2 = $elm$core$String$toInt(param.value);
							if (_v2.$ === 'Just') {
								var i = _v2.a;
								return $elm$json$Json$Encode$int(i);
							} else {
								return $elm$json$Json$Encode$string(param.value);
							}
						case 'number':
							var _v3 = $elm$core$String$toFloat(param.value);
							if (_v3.$ === 'Just') {
								var f = _v3.a;
								return $elm$json$Json$Encode$float(f);
							} else {
								return $elm$json$Json$Encode$string(param.value);
							}
						case 'boolean':
							var _v4 = $elm$core$String$toLower(param.value);
							switch (_v4) {
								case 'true':
									return $elm$json$Json$Encode$bool(true);
								case 'false':
									return $elm$json$Json$Encode$bool(false);
								default:
									return $elm$json$Json$Encode$string(param.value);
							}
						default:
							return $elm$json$Json$Encode$string(param.value);
					}
				}();
				return $elm$core$Maybe$Just(
					_Utils_Tuple2(param.key, encoded));
			}
		};
		var inputObject = $elm$json$Json$Encode$object(
			A2($elm$core$List$filterMap, encodeParameterValue, parameters));
		var requestFields = _Utils_ap(
			_List_fromArray(
				[
					_Utils_Tuple2(
					'model_id',
					$elm$json$Json$Encode$string(modelId)),
					_Utils_Tuple2('input', inputObject),
					_Utils_Tuple2(
					'collection',
					$elm$json$Json$Encode$string(collection))
				]),
			function () {
				if (maybeVersion.$ === 'Just') {
					var version = maybeVersion.a;
					return _List_fromArray(
						[
							_Utils_Tuple2(
							'version',
							$elm$json$Json$Encode$string(version))
						]);
				} else {
					return _List_Nil;
				}
			}());
		return $elm$http$Http$post(
			{
				body: $elm$http$Http$jsonBody(
					$elm$json$Json$Encode$object(requestFields)),
				expect: A2($elm$http$Http$expectJson, $author$project$Video$VideoGenerated, $author$project$Video$videoResponseDecoder),
				url: '/api/run-video-model'
			});
	});
var $author$project$Video$httpErrorToString = function (error) {
	switch (error.$) {
		case 'BadUrl':
			var url = error.a;
			return 'Bad URL: ' + url;
		case 'Timeout':
			return 'Request timed out';
		case 'NetworkError':
			return 'Network error';
		case 'BadStatus':
			var status = error.a;
			return 'Server error: ' + $elm$core$String$fromInt(status);
		default:
			var body = error.a;
			return 'Invalid response: ' + body;
	}
};
var $elm$core$List$isEmpty = function (xs) {
	if (!xs.b) {
		return true;
	} else {
		return false;
	}
};
var $author$project$Video$parseParameter = function (_v0) {
	var key = _v0.a;
	var value = _v0.b;
	var paramType = A2(
		$elm$core$Result$withDefault,
		'string',
		A2(
			$elm$json$Json$Decode$decodeValue,
			A2(
				$elm$json$Json$Decode$at,
				_List_fromArray(
					['type']),
				$elm$json$Json$Decode$string),
			value));
	var minimum = $elm$core$Result$toMaybe(
		A2(
			$elm$json$Json$Decode$decodeValue,
			A2($elm$json$Json$Decode$field, 'minimum', $elm$json$Json$Decode$float),
			value));
	var maximum = $elm$core$Result$toMaybe(
		A2(
			$elm$json$Json$Decode$decodeValue,
			A2($elm$json$Json$Decode$field, 'maximum', $elm$json$Json$Decode$float),
			value));
	var format = $elm$core$Result$toMaybe(
		A2(
			$elm$json$Json$Decode$decodeValue,
			A2($elm$json$Json$Decode$field, 'format', $elm$json$Json$Decode$string),
			value));
	var enumValues = $elm$core$Result$toMaybe(
		A2(
			$elm$json$Json$Decode$decodeValue,
			A2(
				$elm$json$Json$Decode$at,
				_List_fromArray(
					['enum']),
				$elm$json$Json$Decode$list($elm$json$Json$Decode$string)),
			value));
	var description = $elm$core$Result$toMaybe(
		A2(
			$elm$json$Json$Decode$decodeValue,
			A2(
				$elm$json$Json$Decode$at,
				_List_fromArray(
					['description']),
				$elm$json$Json$Decode$string),
			value));
	var _default = A2(
		$elm$core$Maybe$andThen,
		function (v) {
			var _v1 = A2($elm$json$Json$Decode$decodeValue, $elm$json$Json$Decode$string, v);
			if (_v1.$ === 'Ok') {
				var s = _v1.a;
				return $elm$core$Maybe$Just(s);
			} else {
				var _v2 = A2($elm$json$Json$Decode$decodeValue, $elm$json$Json$Decode$float, v);
				if (_v2.$ === 'Ok') {
					var f = _v2.a;
					return $elm$core$Maybe$Just(
						$elm$core$String$fromFloat(f));
				} else {
					var _v3 = A2($elm$json$Json$Decode$decodeValue, $elm$json$Json$Decode$int, v);
					if (_v3.$ === 'Ok') {
						var i = _v3.a;
						return $elm$core$Maybe$Just(
							$elm$core$String$fromInt(i));
					} else {
						return $elm$core$Maybe$Nothing;
					}
				}
			}
		},
		$elm$core$Result$toMaybe(
			A2(
				$elm$json$Json$Decode$decodeValue,
				A2($elm$json$Json$Decode$field, 'default', $elm$json$Json$Decode$value),
				value)));
	var initialValue = A2($elm$core$Maybe$withDefault, '', _default);
	return A9($author$project$Video$Parameter, key, initialValue, paramType, enumValues, description, _default, minimum, maximum, format);
};
var $author$project$Video$updateParameterInList = F3(
	function (key, value, params) {
		return A2(
			$elm$core$List$map,
			function (param) {
				return _Utils_eq(param.key, key) ? _Utils_update(
					param,
					{value: value}) : param;
			},
			params);
	});
var $author$project$Video$ImageUploaded = F2(
	function (a, b) {
		return {$: 'ImageUploaded', a: a, b: b};
	});
var $author$project$Video$uploadResponseDecoder = A2($elm$json$Json$Decode$field, 'url', $elm$json$Json$Decode$string);
var $author$project$Video$uploadImage = F2(
	function (paramKey, file) {
		return $elm$http$Http$post(
			{
				body: $elm$http$Http$multipartBody(
					_List_fromArray(
						[
							A2($elm$http$Http$filePart, 'file', file)
						])),
				expect: A2(
					$elm$http$Http$expectJson,
					$author$project$Video$ImageUploaded(paramKey),
					$author$project$Video$uploadResponseDecoder),
				url: '/api/upload-image'
			});
	});
var $author$project$Video$update = F2(
	function (msg, model) {
		switch (msg.$) {
			case 'NoOp':
				return _Utils_Tuple2(model, $elm$core$Platform$Cmd$none);
			case 'FetchModels':
				return _Utils_Tuple2(
					model,
					$author$project$Video$fetchModels(model.selectedCollection));
			case 'SelectCollection':
				var collection = msg.a;
				return _Utils_eq(model.selectedCollection, collection) ? _Utils_Tuple2(model, $elm$core$Platform$Cmd$none) : _Utils_Tuple2(
					_Utils_update(
						model,
						{outputVideo: $elm$core$Maybe$Nothing, pendingModelSelection: $elm$core$Maybe$Nothing, pendingParameters: _List_Nil, requiredFields: _List_Nil, selectedCollection: collection, selectedModel: $elm$core$Maybe$Nothing, selectedVersion: $elm$core$Maybe$Nothing}),
					$author$project$Video$fetchModels(collection));
			case 'ModelsFetched':
				var result = msg.a;
				if (result.$ === 'Ok') {
					var models = result.a;
					var _v2 = model.pendingModelSelection;
					if (_v2.$ === 'Just') {
						var modelId = _v2.a;
						var selected = $elm$core$List$head(
							A2(
								$elm$core$List$filter,
								function (m) {
									return _Utils_eq(m.id, modelId);
								},
								models));
						if (selected.$ === 'Just') {
							var selectedModel = selected.a;
							return _Utils_Tuple2(
								_Utils_update(
									model,
									{error: $elm$core$Maybe$Nothing, models: models, pendingModelSelection: $elm$core$Maybe$Nothing, selectedModel: selected}),
								$author$project$Video$fetchModelSchema(selectedModel.id));
						} else {
							return _Utils_Tuple2(
								_Utils_update(
									model,
									{error: $elm$core$Maybe$Nothing, models: models, pendingModelSelection: $elm$core$Maybe$Nothing}),
								$elm$core$Platform$Cmd$none);
						}
					} else {
						return _Utils_Tuple2(
							_Utils_update(
								model,
								{error: $elm$core$Maybe$Nothing, models: models}),
							$elm$core$Platform$Cmd$none);
					}
				} else {
					var error = result.a;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								error: $elm$core$Maybe$Just(
									'Failed to fetch models: ' + $author$project$Video$httpErrorToString(error)),
								models: $author$project$Video$demoModels
							}),
						$elm$core$Platform$Cmd$none);
				}
			case 'SelectModel':
				var modelId = msg.a;
				if ($elm$core$List$isEmpty(model.models)) {
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								pendingModelSelection: $elm$core$Maybe$Just(modelId)
							}),
						$elm$core$Platform$Cmd$none);
				} else {
					var selected = $elm$core$List$head(
						A2(
							$elm$core$List$filter,
							function (m) {
								return _Utils_eq(m.id, modelId);
							},
							model.models));
					if (selected.$ === 'Just') {
						var selectedModel = selected.a;
						return _Utils_Tuple2(
							_Utils_update(
								model,
								{error: $elm$core$Maybe$Nothing, outputVideo: $elm$core$Maybe$Nothing, parameters: _List_Nil, selectedModel: selected}),
							$author$project$Video$fetchModelSchema(selectedModel.id));
					} else {
						return _Utils_Tuple2(model, $elm$core$Platform$Cmd$none);
					}
				}
			case 'SchemaFetched':
				var modelId = msg.a;
				var result = msg.b;
				if (result.$ === 'Ok') {
					var schema = result.a.schema;
					var required = result.a.required;
					var version = result.a.version;
					var params = function () {
						var _v8 = A2(
							$elm$json$Json$Decode$decodeValue,
							$elm$json$Json$Decode$keyValuePairs($elm$json$Json$Decode$value),
							schema);
						if (_v8.$ === 'Ok') {
							var properties = _v8.a;
							return A2($elm$core$List$map, $author$project$Video$parseParameter, properties);
						} else {
							return _List_fromArray(
								[
									A9($author$project$Video$Parameter, 'prompt', '', 'string', $elm$core$Maybe$Nothing, $elm$core$Maybe$Nothing, $elm$core$Maybe$Nothing, $elm$core$Maybe$Nothing, $elm$core$Maybe$Nothing, $elm$core$Maybe$Nothing)
								]);
						}
					}();
					var paramsWithPending = A3(
						$elm$core$List$foldl,
						F2(
							function (_v7, accParams) {
								var key = _v7.a;
								var value = _v7.b;
								return A3($author$project$Video$updateParameterInList, key, value, accParams);
							}),
						params,
						model.pendingParameters);
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{parameters: paramsWithPending, pendingParameters: _List_Nil, requiredFields: required, selectedVersion: version}),
						A2(
							$elm$core$Task$attempt,
							$author$project$Video$ScrollToModel,
							A2(
								$elm$core$Task$andThen,
								function (info) {
									return A2($elm$browser$Browser$Dom$setViewport, 0, info.element.y);
								},
								A2(
									$elm$core$Task$andThen,
									function (_v6) {
										return $elm$browser$Browser$Dom$getElement('selected-model-section');
									},
									$elm$core$Process$sleep(100)))));
				} else {
					var defaultParams = _List_fromArray(
						[
							A9($author$project$Video$Parameter, 'prompt', '', 'string', $elm$core$Maybe$Nothing, $elm$core$Maybe$Nothing, $elm$core$Maybe$Nothing, $elm$core$Maybe$Nothing, $elm$core$Maybe$Nothing, $elm$core$Maybe$Nothing)
						]);
					var paramsWithPending = A3(
						$elm$core$List$foldl,
						F2(
							function (_v10, accParams) {
								var key = _v10.a;
								var value = _v10.b;
								return A3($author$project$Video$updateParameterInList, key, value, accParams);
							}),
						defaultParams,
						model.pendingParameters);
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								parameters: paramsWithPending,
								pendingParameters: _List_Nil,
								requiredFields: _List_fromArray(
									['prompt']),
								selectedVersion: $elm$core$Maybe$Nothing
							}),
						A2(
							$elm$core$Task$attempt,
							$author$project$Video$ScrollToModel,
							A2(
								$elm$core$Task$andThen,
								function (info) {
									return A2($elm$browser$Browser$Dom$setViewport, 0, info.element.y);
								},
								A2(
									$elm$core$Task$andThen,
									function (_v9) {
										return $elm$browser$Browser$Dom$getElement('selected-model-section');
									},
									$elm$core$Process$sleep(100)))));
				}
			case 'UpdateParameter':
				var key = msg.a;
				var value = msg.b;
				if ($elm$core$List$isEmpty(model.parameters)) {
					var updatedPending = A2(
						$elm$core$List$cons,
						_Utils_Tuple2(key, value),
						A2(
							$elm$core$List$filter,
							function (_v11) {
								var k = _v11.a;
								return !_Utils_eq(k, key);
							},
							model.pendingParameters));
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{pendingParameters: updatedPending}),
						$elm$core$Platform$Cmd$none);
				} else {
					var updatedParams = A3($author$project$Video$updateParameterInList, key, value, model.parameters);
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{parameters: updatedParams}),
						$elm$core$Platform$Cmd$none);
				}
			case 'UpdateSearch':
				var query = msg.a;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{searchQuery: query}),
					$elm$core$Platform$Cmd$none);
			case 'GenerateVideo':
				var _v12 = model.selectedModel;
				if (_v12.$ === 'Just') {
					var selectedModel = _v12.a;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{error: $elm$core$Maybe$Nothing, isGenerating: true}),
						A4($author$project$Video$generateVideo, selectedModel.id, model.parameters, model.selectedCollection, model.selectedVersion));
				} else {
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								error: $elm$core$Maybe$Just('No model selected')
							}),
						$elm$core$Platform$Cmd$none);
				}
			case 'VideoGenerated':
				var result = msg.a;
				if (result.$ === 'Ok') {
					var response = result.a;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								error: $elm$core$Maybe$Nothing,
								isGenerating: false,
								pollingVideoId: $elm$core$Maybe$Just(response.video_id),
								videoStatus: response.status
							}),
						A2(
							$elm$core$Task$perform,
							function (_v14) {
								return $author$project$Video$NavigateToVideo(response.video_id);
							},
							$elm$core$Task$succeed(_Utils_Tuple0)));
				} else {
					var error = result.a;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								error: $elm$core$Maybe$Just(
									$author$project$Video$httpErrorToString(error)),
								isGenerating: false
							}),
						$elm$core$Platform$Cmd$none);
				}
			case 'NavigateToVideo':
				return _Utils_Tuple2(model, $elm$core$Platform$Cmd$none);
			case 'ScrollToModel':
				return _Utils_Tuple2(model, $elm$core$Platform$Cmd$none);
			case 'PollVideoStatus':
				return _Utils_Tuple2(model, $elm$core$Platform$Cmd$none);
			case 'VideoStatusFetched':
				var result = msg.a;
				if (result.$ === 'Ok') {
					var videoRecord = result.a;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								isGenerating: (videoRecord.status !== 'completed') && (videoRecord.status !== 'failed'),
								outputVideo: (videoRecord.status === 'completed') ? $elm$core$Maybe$Just(videoRecord.videoUrl) : model.outputVideo,
								videoStatus: videoRecord.status
							}),
						$elm$core$Platform$Cmd$none);
				} else {
					var error = result.a;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								error: $elm$core$Maybe$Just(
									$author$project$Video$httpErrorToString(error))
							}),
						$elm$core$Platform$Cmd$none);
				}
			case 'FileSelected':
				var paramKey = msg.a;
				var file = msg.b;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{
							uploadingFile: $elm$core$Maybe$Just(paramKey)
						}),
					A2($author$project$Video$uploadImage, paramKey, file));
			default:
				var paramKey = msg.a;
				var result = msg.b;
				if (result.$ === 'Ok') {
					var imageUrl = result.a;
					var updatedParams = A3($author$project$Video$updateParameterInList, paramKey, imageUrl, model.parameters);
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{error: $elm$core$Maybe$Nothing, parameters: updatedParams, uploadingFile: $elm$core$Maybe$Nothing}),
						$elm$core$Platform$Cmd$none);
				} else {
					var error = result.a;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								error: $elm$core$Maybe$Just(
									'Upload failed: ' + $author$project$Video$httpErrorToString(error)),
								uploadingFile: $elm$core$Maybe$Nothing
							}),
						$elm$core$Platform$Cmd$none);
				}
		}
	});
var $author$project$VideoDetail$httpErrorToString = function (error) {
	switch (error.$) {
		case 'BadUrl':
			var url = error.a;
			return 'Bad URL: ' + url;
		case 'Timeout':
			return 'Request timed out';
		case 'NetworkError':
			return 'Network error';
		case 'BadStatus':
			var status = error.a;
			return 'Server error: ' + $elm$core$String$fromInt(status);
		default:
			var body = error.a;
			return 'Invalid response: ' + body;
	}
};
var $author$project$VideoDetail$update = F2(
	function (msg, model) {
		if (msg.$ === 'VideoFetched') {
			var result = msg.a;
			if (result.$ === 'Ok') {
				var video = result.a;
				var shouldStopPolling = (video.status === 'completed') || ((video.status === 'failed') || (video.status === 'canceled'));
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{
							error: $elm$core$Maybe$Nothing,
							isPolling: !shouldStopPolling,
							video: $elm$core$Maybe$Just(video)
						}),
					$elm$core$Platform$Cmd$none);
			} else {
				var error = result.a;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{
							error: $elm$core$Maybe$Just(
								$author$project$VideoDetail$httpErrorToString(error)),
							isPolling: false
						}),
					$elm$core$Platform$Cmd$none);
			}
		} else {
			return model.isPolling ? _Utils_Tuple2(
				model,
				$author$project$VideoDetail$fetchVideo(model.videoId)) : _Utils_Tuple2(model, $elm$core$Platform$Cmd$none);
		}
	});
var $elm$core$Basics$clamp = F3(
	function (low, high, number) {
		return (_Utils_cmp(number, low) < 0) ? low : ((_Utils_cmp(number, high) > 0) ? high : number);
	});
var $author$project$VideoGallery$httpErrorToString = function (error) {
	switch (error.$) {
		case 'BadUrl':
			var url = error.a;
			return 'Bad URL: ' + url;
		case 'Timeout':
			return 'Request timed out';
		case 'NetworkError':
			return 'Network error';
		case 'BadStatus':
			var status = error.a;
			return 'Server error: ' + $elm$core$String$fromInt(status);
		default:
			var body = error.a;
			return 'Invalid response: ' + body;
	}
};
var $elm$core$Basics$min = F2(
	function (x, y) {
		return (_Utils_cmp(x, y) < 0) ? x : y;
	});
var $author$project$VideoGallery$update = F2(
	function (msg, model) {
		switch (msg.$) {
			case 'NoOp':
				return _Utils_Tuple2(model, $elm$core$Platform$Cmd$none);
			case 'FetchVideos':
				var offset = (model.currentPage - 1) * model.pageSize;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{loading: true}),
					A2($author$project$VideoGallery$fetchVideos, model.pageSize, offset));
			case 'VideosFetched':
				var result = msg.a;
				if (result.$ === 'Ok') {
					var _v2 = result.a;
					var videos = _v2.a;
					var total = _v2.b;
					return _Utils_eq(videos, model.videos) ? _Utils_Tuple2(
						_Utils_update(
							model,
							{loading: false, totalVideos: total}),
						$elm$core$Platform$Cmd$none) : _Utils_Tuple2(
						_Utils_update(
							model,
							{error: $elm$core$Maybe$Nothing, loading: false, totalVideos: total, videos: videos}),
						$elm$core$Platform$Cmd$none);
				} else {
					var error = result.a;
					var errorMsg = function () {
						if ((error.$ === 'BadStatus') && (error.a === 401)) {
							return $elm$core$Maybe$Nothing;
						} else {
							return $elm$core$Maybe$Just(
								$author$project$VideoGallery$httpErrorToString(error));
						}
					}();
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{error: errorMsg, loading: false}),
						$elm$core$Platform$Cmd$none);
				}
			case 'SelectVideo':
				var video = msg.a;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{
							selectedVideo: $elm$core$Maybe$Just(video),
							showRawData: false
						}),
					$elm$core$Platform$Cmd$none);
			case 'CloseVideo':
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{selectedVideo: $elm$core$Maybe$Nothing, showRawData: false}),
					$elm$core$Platform$Cmd$none);
			case 'ToggleRawData':
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{showRawData: !model.showRawData}),
					$elm$core$Platform$Cmd$none);
			case 'Tick':
				var offset = (model.currentPage - 1) * model.pageSize;
				return _Utils_Tuple2(
					model,
					A2($author$project$VideoGallery$fetchVideos, model.pageSize, offset));
			case 'NextPage':
				var maxPage = $elm$core$Basics$ceiling(model.totalVideos / model.pageSize);
				var newPage = A2($elm$core$Basics$min, model.currentPage + 1, maxPage);
				var offset = (newPage - 1) * model.pageSize;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{currentPage: newPage, loading: true}),
					A2($author$project$VideoGallery$fetchVideos, model.pageSize, offset));
			case 'PrevPage':
				var newPage = A2($elm$core$Basics$max, model.currentPage - 1, 1);
				var offset = (newPage - 1) * model.pageSize;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{currentPage: newPage, loading: true}),
					A2($author$project$VideoGallery$fetchVideos, model.pageSize, offset));
			default:
				var page = msg.a;
				var maxPage = $elm$core$Basics$ceiling(model.totalVideos / model.pageSize);
				var newPage = A3($elm$core$Basics$clamp, 1, maxPage, page);
				var offset = (newPage - 1) * model.pageSize;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{currentPage: newPage, loading: true}),
					A2($author$project$VideoGallery$fetchVideos, model.pageSize, offset));
		}
	});
var $author$project$VideoToText$NavigateToResult = function (a) {
	return {$: 'NavigateToResult', a: a};
};
var $author$project$VideoToText$Parameter = F9(
	function (key, value, paramType, _enum, description, _default, minimum, maximum, format) {
		return {_default: _default, description: description, _enum: _enum, format: format, key: key, maximum: maximum, minimum: minimum, paramType: paramType, value: value};
	});
var $author$project$VideoToText$ScrollToModel = function (a) {
	return {$: 'ScrollToModel', a: a};
};
var $author$project$VideoToText$demoModels = _List_fromArray(
	[
		A4($author$project$VideoToText$VideoToTextModel, 'demo/video-to-text', 'Demo Video-to-Text', 'Generates text from video content', $elm$core$Maybe$Nothing)
	]);
var $author$project$VideoToText$SchemaFetched = F2(
	function (a, b) {
		return {$: 'SchemaFetched', a: a, b: b};
	});
var $author$project$VideoToText$schemaResponseDecoder = A4(
	$elm$json$Json$Decode$map3,
	F3(
		function (s, r, v) {
			return {required: r, schema: s, version: v};
		}),
	A2($elm$json$Json$Decode$field, 'input_schema', $elm$json$Json$Decode$value),
	$elm$json$Json$Decode$oneOf(
		_List_fromArray(
			[
				A2(
				$elm$json$Json$Decode$field,
				'required',
				$elm$json$Json$Decode$list($elm$json$Json$Decode$string)),
				$elm$json$Json$Decode$succeed(_List_Nil)
			])),
	$elm$json$Json$Decode$maybe(
		A2($elm$json$Json$Decode$field, 'version', $elm$json$Json$Decode$string)));
var $author$project$VideoToText$fetchModelSchema = function (modelId) {
	var parts = A2($elm$core$String$split, '/', modelId);
	var url = function () {
		if ((parts.b && parts.b.b) && (!parts.b.b.b)) {
			var owner = parts.a;
			var _v1 = parts.b;
			var name = _v1.a;
			return '/api/video-models/' + (owner + ('/' + (name + '/schema')));
		} else {
			return '';
		}
	}();
	return $elm$core$String$isEmpty(url) ? $elm$core$Platform$Cmd$none : $elm$http$Http$get(
		{
			expect: A2(
				$elm$http$Http$expectJson,
				$author$project$VideoToText$SchemaFetched(modelId),
				$author$project$VideoToText$schemaResponseDecoder),
			url: url
		});
};
var $author$project$VideoToText$TextGenerated = function (a) {
	return {$: 'TextGenerated', a: a};
};
var $author$project$VideoToText$textResponseDecoder = A3(
	$elm$json$Json$Decode$map2,
	F2(
		function (id, s) {
			return {status: s, video_id: id};
		}),
	A2($elm$json$Json$Decode$field, 'video_id', $elm$json$Json$Decode$int),
	A2($elm$json$Json$Decode$field, 'status', $elm$json$Json$Decode$string));
var $author$project$VideoToText$generateText = F4(
	function (modelId, parameters, collection, maybeVersion) {
		var encodeParameterValue = function (param) {
			if ($elm$core$String$isEmpty(
				$elm$core$String$trim(param.value))) {
				return $elm$core$Maybe$Nothing;
			} else {
				var encoded = function () {
					var _v1 = param.paramType;
					switch (_v1) {
						case 'integer':
							var _v2 = $elm$core$String$toInt(param.value);
							if (_v2.$ === 'Just') {
								var i = _v2.a;
								return $elm$json$Json$Encode$int(i);
							} else {
								return $elm$json$Json$Encode$string(param.value);
							}
						case 'number':
							var _v3 = $elm$core$String$toFloat(param.value);
							if (_v3.$ === 'Just') {
								var f = _v3.a;
								return $elm$json$Json$Encode$float(f);
							} else {
								return $elm$json$Json$Encode$string(param.value);
							}
						case 'boolean':
							var _v4 = $elm$core$String$toLower(param.value);
							switch (_v4) {
								case 'true':
									return $elm$json$Json$Encode$bool(true);
								case 'false':
									return $elm$json$Json$Encode$bool(false);
								default:
									return $elm$json$Json$Encode$string(param.value);
							}
						default:
							return $elm$json$Json$Encode$string(param.value);
					}
				}();
				return $elm$core$Maybe$Just(
					_Utils_Tuple2(param.key, encoded));
			}
		};
		var inputObject = $elm$json$Json$Encode$object(
			A2($elm$core$List$filterMap, encodeParameterValue, parameters));
		var requestFields = _Utils_ap(
			_List_fromArray(
				[
					_Utils_Tuple2(
					'model_id',
					$elm$json$Json$Encode$string(modelId)),
					_Utils_Tuple2('input', inputObject),
					_Utils_Tuple2(
					'collection',
					$elm$json$Json$Encode$string(collection))
				]),
			function () {
				if (maybeVersion.$ === 'Just') {
					var version = maybeVersion.a;
					return _List_fromArray(
						[
							_Utils_Tuple2(
							'version',
							$elm$json$Json$Encode$string(version))
						]);
				} else {
					return _List_Nil;
				}
			}());
		return $elm$http$Http$post(
			{
				body: $elm$http$Http$jsonBody(
					$elm$json$Json$Encode$object(requestFields)),
				expect: A2($elm$http$Http$expectJson, $author$project$VideoToText$TextGenerated, $author$project$VideoToText$textResponseDecoder),
				url: '/api/run-video-to-text-model'
			});
	});
var $author$project$VideoToText$httpErrorToString = function (error) {
	switch (error.$) {
		case 'BadUrl':
			var url = error.a;
			return 'Bad URL: ' + url;
		case 'Timeout':
			return 'Request timed out';
		case 'NetworkError':
			return 'Network error';
		case 'BadStatus':
			var status = error.a;
			return 'Server error: ' + $elm$core$String$fromInt(status);
		default:
			var body = error.a;
			return 'Invalid response: ' + body;
	}
};
var $author$project$VideoToText$parseParameter = function (_v0) {
	var key = _v0.a;
	var value = _v0.b;
	var paramType = A2(
		$elm$core$Result$withDefault,
		'string',
		A2(
			$elm$json$Json$Decode$decodeValue,
			A2(
				$elm$json$Json$Decode$at,
				_List_fromArray(
					['type']),
				$elm$json$Json$Decode$string),
			value));
	var minimum = $elm$core$Result$toMaybe(
		A2(
			$elm$json$Json$Decode$decodeValue,
			A2($elm$json$Json$Decode$field, 'minimum', $elm$json$Json$Decode$float),
			value));
	var maximum = $elm$core$Result$toMaybe(
		A2(
			$elm$json$Json$Decode$decodeValue,
			A2($elm$json$Json$Decode$field, 'maximum', $elm$json$Json$Decode$float),
			value));
	var format = $elm$core$Result$toMaybe(
		A2(
			$elm$json$Json$Decode$decodeValue,
			A2($elm$json$Json$Decode$field, 'format', $elm$json$Json$Decode$string),
			value));
	var enumValues = $elm$core$Result$toMaybe(
		A2(
			$elm$json$Json$Decode$decodeValue,
			A2(
				$elm$json$Json$Decode$at,
				_List_fromArray(
					['enum']),
				$elm$json$Json$Decode$list($elm$json$Json$Decode$string)),
			value));
	var description = $elm$core$Result$toMaybe(
		A2(
			$elm$json$Json$Decode$decodeValue,
			A2(
				$elm$json$Json$Decode$at,
				_List_fromArray(
					['description']),
				$elm$json$Json$Decode$string),
			value));
	var _default = A2(
		$elm$core$Maybe$andThen,
		function (v) {
			var _v1 = A2($elm$json$Json$Decode$decodeValue, $elm$json$Json$Decode$string, v);
			if (_v1.$ === 'Ok') {
				var s = _v1.a;
				return $elm$core$Maybe$Just(s);
			} else {
				var _v2 = A2($elm$json$Json$Decode$decodeValue, $elm$json$Json$Decode$float, v);
				if (_v2.$ === 'Ok') {
					var f = _v2.a;
					return $elm$core$Maybe$Just(
						$elm$core$String$fromFloat(f));
				} else {
					var _v3 = A2($elm$json$Json$Decode$decodeValue, $elm$json$Json$Decode$int, v);
					if (_v3.$ === 'Ok') {
						var i = _v3.a;
						return $elm$core$Maybe$Just(
							$elm$core$String$fromInt(i));
					} else {
						return $elm$core$Maybe$Nothing;
					}
				}
			}
		},
		$elm$core$Result$toMaybe(
			A2(
				$elm$json$Json$Decode$decodeValue,
				A2($elm$json$Json$Decode$field, 'default', $elm$json$Json$Decode$value),
				value)));
	var initialValue = A2($elm$core$Maybe$withDefault, '', _default);
	return A9($author$project$VideoToText$Parameter, key, initialValue, paramType, enumValues, description, _default, minimum, maximum, format);
};
var $author$project$VideoToText$updateParameterInList = F3(
	function (key, value, params) {
		return A2(
			$elm$core$List$map,
			function (param) {
				return _Utils_eq(param.key, key) ? _Utils_update(
					param,
					{value: value}) : param;
			},
			params);
	});
var $author$project$VideoToText$VideoUploaded = F2(
	function (a, b) {
		return {$: 'VideoUploaded', a: a, b: b};
	});
var $author$project$VideoToText$uploadResponseDecoder = A2($elm$json$Json$Decode$field, 'url', $elm$json$Json$Decode$string);
var $author$project$VideoToText$uploadVideo = F2(
	function (paramKey, file) {
		return $elm$http$Http$post(
			{
				body: $elm$http$Http$multipartBody(
					_List_fromArray(
						[
							A2($elm$http$Http$filePart, 'file', file)
						])),
				expect: A2(
					$elm$http$Http$expectJson,
					$author$project$VideoToText$VideoUploaded(paramKey),
					$author$project$VideoToText$uploadResponseDecoder),
				url: '/api/upload-video'
			});
	});
var $author$project$VideoToText$update = F2(
	function (msg, model) {
		switch (msg.$) {
			case 'NoOp':
				return _Utils_Tuple2(model, $elm$core$Platform$Cmd$none);
			case 'FetchModels':
				return _Utils_Tuple2(
					model,
					$author$project$VideoToText$fetchModels(model.selectedCollection));
			case 'SelectCollection':
				var collection = msg.a;
				return _Utils_eq(model.selectedCollection, collection) ? _Utils_Tuple2(model, $elm$core$Platform$Cmd$none) : _Utils_Tuple2(
					_Utils_update(
						model,
						{outputText: $elm$core$Maybe$Nothing, pendingModelSelection: $elm$core$Maybe$Nothing, pendingParameters: _List_Nil, requiredFields: _List_Nil, selectedCollection: collection, selectedModel: $elm$core$Maybe$Nothing, selectedVersion: $elm$core$Maybe$Nothing}),
					$author$project$VideoToText$fetchModels(collection));
			case 'ModelsFetched':
				var result = msg.a;
				if (result.$ === 'Ok') {
					var models = result.a;
					var _v2 = model.pendingModelSelection;
					if (_v2.$ === 'Just') {
						var modelId = _v2.a;
						var selected = $elm$core$List$head(
							A2(
								$elm$core$List$filter,
								function (m) {
									return _Utils_eq(m.id, modelId);
								},
								models));
						if (selected.$ === 'Just') {
							var selectedModel = selected.a;
							return _Utils_Tuple2(
								_Utils_update(
									model,
									{error: $elm$core$Maybe$Nothing, models: models, pendingModelSelection: $elm$core$Maybe$Nothing, selectedModel: selected}),
								$author$project$VideoToText$fetchModelSchema(selectedModel.id));
						} else {
							return _Utils_Tuple2(
								_Utils_update(
									model,
									{error: $elm$core$Maybe$Nothing, models: models, pendingModelSelection: $elm$core$Maybe$Nothing}),
								$elm$core$Platform$Cmd$none);
						}
					} else {
						return _Utils_Tuple2(
							_Utils_update(
								model,
								{error: $elm$core$Maybe$Nothing, models: models}),
							$elm$core$Platform$Cmd$none);
					}
				} else {
					var error = result.a;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								error: $elm$core$Maybe$Just(
									'Failed to fetch models: ' + $author$project$VideoToText$httpErrorToString(error)),
								models: $author$project$VideoToText$demoModels
							}),
						$elm$core$Platform$Cmd$none);
				}
			case 'SelectModel':
				var modelId = msg.a;
				if ($elm$core$List$isEmpty(model.models)) {
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								pendingModelSelection: $elm$core$Maybe$Just(modelId)
							}),
						$elm$core$Platform$Cmd$none);
				} else {
					var selected = $elm$core$List$head(
						A2(
							$elm$core$List$filter,
							function (m) {
								return _Utils_eq(m.id, modelId);
							},
							model.models));
					if (selected.$ === 'Just') {
						var selectedModel = selected.a;
						return _Utils_Tuple2(
							_Utils_update(
								model,
								{error: $elm$core$Maybe$Nothing, outputText: $elm$core$Maybe$Nothing, parameters: _List_Nil, selectedModel: selected}),
							$author$project$VideoToText$fetchModelSchema(selectedModel.id));
					} else {
						return _Utils_Tuple2(model, $elm$core$Platform$Cmd$none);
					}
				}
			case 'SchemaFetched':
				var modelId = msg.a;
				var result = msg.b;
				if (result.$ === 'Ok') {
					var schema = result.a.schema;
					var required = result.a.required;
					var version = result.a.version;
					var params = function () {
						var _v8 = A2(
							$elm$json$Json$Decode$decodeValue,
							$elm$json$Json$Decode$keyValuePairs($elm$json$Json$Decode$value),
							schema);
						if (_v8.$ === 'Ok') {
							var properties = _v8.a;
							return A2($elm$core$List$map, $author$project$VideoToText$parseParameter, properties);
						} else {
							return _List_fromArray(
								[
									A9($author$project$VideoToText$Parameter, 'prompt', '', 'string', $elm$core$Maybe$Nothing, $elm$core$Maybe$Nothing, $elm$core$Maybe$Nothing, $elm$core$Maybe$Nothing, $elm$core$Maybe$Nothing, $elm$core$Maybe$Nothing)
								]);
						}
					}();
					var paramsWithPending = A3(
						$elm$core$List$foldl,
						F2(
							function (_v7, accParams) {
								var key = _v7.a;
								var value = _v7.b;
								return A3($author$project$VideoToText$updateParameterInList, key, value, accParams);
							}),
						params,
						model.pendingParameters);
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{parameters: paramsWithPending, pendingParameters: _List_Nil, requiredFields: required, selectedVersion: version}),
						A2(
							$elm$core$Task$attempt,
							$author$project$VideoToText$ScrollToModel,
							A2(
								$elm$core$Task$andThen,
								function (info) {
									return A2($elm$browser$Browser$Dom$setViewport, 0, info.element.y);
								},
								A2(
									$elm$core$Task$andThen,
									function (_v6) {
										return $elm$browser$Browser$Dom$getElement('selected-model-section');
									},
									$elm$core$Process$sleep(100)))));
				} else {
					var defaultParams = _List_fromArray(
						[
							A9($author$project$VideoToText$Parameter, 'prompt', '', 'string', $elm$core$Maybe$Nothing, $elm$core$Maybe$Nothing, $elm$core$Maybe$Nothing, $elm$core$Maybe$Nothing, $elm$core$Maybe$Nothing, $elm$core$Maybe$Nothing)
						]);
					var paramsWithPending = A3(
						$elm$core$List$foldl,
						F2(
							function (_v10, accParams) {
								var key = _v10.a;
								var value = _v10.b;
								return A3($author$project$VideoToText$updateParameterInList, key, value, accParams);
							}),
						defaultParams,
						model.pendingParameters);
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								parameters: paramsWithPending,
								pendingParameters: _List_Nil,
								requiredFields: _List_fromArray(
									['prompt']),
								selectedVersion: $elm$core$Maybe$Nothing
							}),
						A2(
							$elm$core$Task$attempt,
							$author$project$VideoToText$ScrollToModel,
							A2(
								$elm$core$Task$andThen,
								function (info) {
									return A2($elm$browser$Browser$Dom$setViewport, 0, info.element.y);
								},
								A2(
									$elm$core$Task$andThen,
									function (_v9) {
										return $elm$browser$Browser$Dom$getElement('selected-model-section');
									},
									$elm$core$Process$sleep(100)))));
				}
			case 'UpdateParameter':
				var key = msg.a;
				var value = msg.b;
				if ($elm$core$List$isEmpty(model.parameters)) {
					var updatedPending = A2(
						$elm$core$List$cons,
						_Utils_Tuple2(key, value),
						A2(
							$elm$core$List$filter,
							function (_v11) {
								var k = _v11.a;
								return !_Utils_eq(k, key);
							},
							model.pendingParameters));
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{pendingParameters: updatedPending}),
						$elm$core$Platform$Cmd$none);
				} else {
					var updatedParams = A3($author$project$VideoToText$updateParameterInList, key, value, model.parameters);
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{parameters: updatedParams}),
						$elm$core$Platform$Cmd$none);
				}
			case 'UpdateSearch':
				var query = msg.a;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{searchQuery: query}),
					$elm$core$Platform$Cmd$none);
			case 'GenerateText':
				var _v12 = model.selectedModel;
				if (_v12.$ === 'Just') {
					var selectedModel = _v12.a;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{error: $elm$core$Maybe$Nothing, isGenerating: true}),
						A4($author$project$VideoToText$generateText, selectedModel.id, model.parameters, model.selectedCollection, model.selectedVersion));
				} else {
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								error: $elm$core$Maybe$Just('No model selected')
							}),
						$elm$core$Platform$Cmd$none);
				}
			case 'TextGenerated':
				var result = msg.a;
				if (result.$ === 'Ok') {
					var response = result.a;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								error: $elm$core$Maybe$Nothing,
								generationStatus: response.status,
								isGenerating: false,
								pollingVideoId: $elm$core$Maybe$Just(response.video_id)
							}),
						A2(
							$elm$core$Task$perform,
							function (_v14) {
								return $author$project$VideoToText$NavigateToResult(response.video_id);
							},
							$elm$core$Task$succeed(_Utils_Tuple0)));
				} else {
					var error = result.a;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								error: $elm$core$Maybe$Just(
									$author$project$VideoToText$httpErrorToString(error)),
								isGenerating: false
							}),
						$elm$core$Platform$Cmd$none);
				}
			case 'NavigateToResult':
				return _Utils_Tuple2(model, $elm$core$Platform$Cmd$none);
			case 'ScrollToModel':
				return _Utils_Tuple2(model, $elm$core$Platform$Cmd$none);
			case 'PollStatus':
				return _Utils_Tuple2(model, $elm$core$Platform$Cmd$none);
			case 'StatusFetched':
				var result = msg.a;
				if (result.$ === 'Ok') {
					var record = result.a;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								generationStatus: record.status,
								isGenerating: (record.status !== 'completed') && (record.status !== 'failed'),
								outputText: (record.status === 'completed') ? $elm$core$Maybe$Just(record.outputText) : model.outputText
							}),
						$elm$core$Platform$Cmd$none);
				} else {
					var error = result.a;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								error: $elm$core$Maybe$Just(
									$author$project$VideoToText$httpErrorToString(error))
							}),
						$elm$core$Platform$Cmd$none);
				}
			case 'FileSelected':
				var paramKey = msg.a;
				var file = msg.b;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{
							uploadingFile: $elm$core$Maybe$Just(paramKey)
						}),
					A2($author$project$VideoToText$uploadVideo, paramKey, file));
			default:
				var paramKey = msg.a;
				var result = msg.b;
				if (result.$ === 'Ok') {
					var videoUrl = result.a;
					var updatedParams = A3($author$project$VideoToText$updateParameterInList, paramKey, videoUrl, model.parameters);
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{error: $elm$core$Maybe$Nothing, parameters: updatedParams, uploadingFile: $elm$core$Maybe$Nothing}),
						$elm$core$Platform$Cmd$none);
				} else {
					var error = result.a;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								error: $elm$core$Maybe$Just(
									'Upload failed: ' + $author$project$VideoToText$httpErrorToString(error)),
								uploadingFile: $elm$core$Maybe$Nothing
							}),
						$elm$core$Platform$Cmd$none);
				}
		}
	});
var $author$project$VideoToTextGallery$httpErrorToString = function (error) {
	switch (error.$) {
		case 'BadUrl':
			var url = error.a;
			return 'Bad URL: ' + url;
		case 'Timeout':
			return 'Request timed out';
		case 'NetworkError':
			return 'Network error';
		case 'BadStatus':
			var status = error.a;
			return 'Server error: ' + $elm$core$String$fromInt(status);
		default:
			var body = error.a;
			return 'Invalid response: ' + body;
	}
};
var $author$project$VideoToTextGallery$update = F2(
	function (msg, model) {
		switch (msg.$) {
			case 'NoOp':
				return _Utils_Tuple2(model, $elm$core$Platform$Cmd$none);
			case 'FetchVideos':
				var offset = (model.currentPage - 1) * model.pageSize;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{loading: true}),
					A2($author$project$VideoToTextGallery$fetchVideos, model.pageSize, offset));
			case 'VideosFetched':
				var result = msg.a;
				if (result.$ === 'Ok') {
					var _v2 = result.a;
					var videos = _v2.a;
					var total = _v2.b;
					return _Utils_eq(videos, model.videos) ? _Utils_Tuple2(
						_Utils_update(
							model,
							{loading: false, totalVideos: total}),
						$elm$core$Platform$Cmd$none) : _Utils_Tuple2(
						_Utils_update(
							model,
							{error: $elm$core$Maybe$Nothing, loading: false, totalVideos: total, videos: videos}),
						$elm$core$Platform$Cmd$none);
				} else {
					var error = result.a;
					var errorMsg = function () {
						if ((error.$ === 'BadStatus') && (error.a === 401)) {
							return $elm$core$Maybe$Nothing;
						} else {
							return $elm$core$Maybe$Just(
								$author$project$VideoToTextGallery$httpErrorToString(error));
						}
					}();
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{error: errorMsg, loading: false}),
						$elm$core$Platform$Cmd$none);
				}
			case 'SelectVideo':
				var video = msg.a;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{
							selectedVideo: $elm$core$Maybe$Just(video),
							showRawData: false
						}),
					$elm$core$Platform$Cmd$none);
			case 'CloseVideo':
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{selectedVideo: $elm$core$Maybe$Nothing, showRawData: false}),
					$elm$core$Platform$Cmd$none);
			case 'ToggleRawData':
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{showRawData: !model.showRawData}),
					$elm$core$Platform$Cmd$none);
			case 'Tick':
				var offset = (model.currentPage - 1) * model.pageSize;
				return _Utils_Tuple2(
					model,
					A2($author$project$VideoToTextGallery$fetchVideos, model.pageSize, offset));
			case 'NextPage':
				var maxPage = $elm$core$Basics$ceiling(model.totalVideos / model.pageSize);
				var newPage = A2($elm$core$Basics$min, model.currentPage + 1, maxPage);
				var offset = (newPage - 1) * model.pageSize;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{currentPage: newPage, loading: true}),
					A2($author$project$VideoToTextGallery$fetchVideos, model.pageSize, offset));
			case 'PrevPage':
				var newPage = A2($elm$core$Basics$max, model.currentPage - 1, 1);
				var offset = (newPage - 1) * model.pageSize;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{currentPage: newPage, loading: true}),
					A2($author$project$VideoToTextGallery$fetchVideos, model.pageSize, offset));
			default:
				var page = msg.a;
				var maxPage = $elm$core$Basics$ceiling(model.totalVideos / model.pageSize);
				var newPage = A3($elm$core$Basics$clamp, 1, maxPage, page);
				var offset = (newPage - 1) * model.pageSize;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{currentPage: newPage, loading: true}),
					A2($author$project$VideoToTextGallery$fetchVideos, model.pageSize, offset));
		}
	});
var $author$project$Main$update = F2(
	function (msg, model) {
		switch (msg.$) {
			case 'NoOp':
				return _Utils_Tuple2(model, $elm$core$Platform$Cmd$none);
			case 'LinkClicked':
				var urlRequest = msg.a;
				if (urlRequest.$ === 'Internal') {
					var url = urlRequest.a;
					return _Utils_Tuple2(
						model,
						A2(
							$elm$browser$Browser$Navigation$pushUrl,
							model.key,
							$elm$url$Url$toString(url)));
				} else {
					var href = urlRequest.a;
					return _Utils_Tuple2(
						model,
						$elm$browser$Browser$Navigation$load(href));
				}
			case 'UrlChanged':
				var url = msg.a;
				var videoDetailCmd = $elm$core$Platform$Cmd$none;
				var newRoute = $author$project$Route$fromUrl(url);
				var videoDetailModel = function () {
					if ((newRoute.$ === 'Just') && (newRoute.a.$ === 'VideoDetail')) {
						var videoId = newRoute.a.a;
						var _v29 = $author$project$VideoDetail$init(videoId);
						var detailModel = _v29.a;
						var detailCmd = _v29.b;
						return $elm$core$Maybe$Just(detailModel);
					} else {
						return $elm$core$Maybe$Nothing;
					}
				}();
				var videoPrefillCmd = function () {
					var _v24 = _Utils_Tuple2(newRoute, model.pendingVideoFromImage);
					if (((_v24.a.$ === 'Just') && (_v24.a.a.$ === 'Videos')) && (_v24.b.$ === 'Just')) {
						var _v25 = _v24.a.a;
						var modelId = _v24.b.a.modelId;
						var imageUrl = _v24.b.a.imageUrl;
						return $elm$core$Platform$Cmd$batch(
							_List_fromArray(
								[
									A2(
									$elm$core$Task$perform,
									$elm$core$Basics$always(
										$author$project$Main$VideoMsg(
											$author$project$Video$SelectCollection('image-to-video'))),
									$elm$core$Task$succeed(_Utils_Tuple0)),
									A2(
									$elm$core$Task$perform,
									$elm$core$Basics$identity,
									A2(
										$elm$core$Task$andThen,
										function (_v26) {
											return $elm$core$Task$succeed(
												$author$project$Main$VideoMsg(
													$author$project$Video$SelectModel(modelId)));
										},
										$elm$core$Process$sleep(50))),
									A2(
									$elm$core$Task$perform,
									$elm$core$Basics$identity,
									A2(
										$elm$core$Task$andThen,
										function (_v27) {
											return $elm$core$Task$succeed(
												$author$project$Main$VideoMsg(
													A2($author$project$Video$UpdateParameter, 'image', imageUrl)));
										},
										$elm$core$Process$sleep(100)))
								]));
					} else {
						return $elm$core$Platform$Cmd$none;
					}
				}();
				var videoToTextGalleryCmd = function () {
					if ((newRoute.$ === 'Just') && (newRoute.a.$ === 'VideoToTextGallery')) {
						var _v23 = newRoute.a;
						return A2(
							$elm$core$Task$perform,
							$elm$core$Basics$always(
								$author$project$Main$VideoToTextGalleryMsg($author$project$VideoToTextGallery$FetchVideos)),
							$elm$core$Task$succeed(_Utils_Tuple0));
					} else {
						return $elm$core$Platform$Cmd$none;
					}
				}();
				var imageGalleryCmd = function () {
					if ((newRoute.$ === 'Just') && (newRoute.a.$ === 'ImageGallery')) {
						var _v21 = newRoute.a;
						return A2(
							$elm$core$Task$perform,
							$elm$core$Basics$always(
								$author$project$Main$ImageGalleryMsg($author$project$ImageGallery$FetchImages)),
							$elm$core$Task$succeed(_Utils_Tuple0));
					} else {
						return $elm$core$Platform$Cmd$none;
					}
				}();
				var imageDetailModel = function () {
					if ((newRoute.$ === 'Just') && (newRoute.a.$ === 'ImageDetail')) {
						var imageId = newRoute.a.a;
						var _v19 = $author$project$ImageDetail$init(imageId);
						var detailModel = _v19.a;
						var detailCmd = _v19.b;
						return $elm$core$Maybe$Just(detailModel);
					} else {
						return $elm$core$Maybe$Nothing;
					}
				}();
				var imageDetailCmd = $elm$core$Platform$Cmd$none;
				var galleryCmd = function () {
					if ((newRoute.$ === 'Just') && (newRoute.a.$ === 'Gallery')) {
						var _v17 = newRoute.a;
						return A2(
							$elm$core$Task$perform,
							$elm$core$Basics$always(
								$author$project$Main$GalleryMsg($author$project$VideoGallery$FetchVideos)),
							$elm$core$Task$succeed(_Utils_Tuple0));
					} else {
						return $elm$core$Platform$Cmd$none;
					}
				}();
				var creativeBriefEditorModel = function () {
					if ((newRoute.$ === 'Just') && (newRoute.a.$ === 'CreativeBriefEditor')) {
						var _v14 = newRoute.a;
						var _v15 = $author$project$CreativeBriefEditor$init(model.key);
						var editorModel = _v15.a;
						var editorCmd = _v15.b;
						return editorModel;
					} else {
						return model.creativeBriefEditorModel;
					}
				}();
				var creativeBriefEditorCmd = $elm$core$Platform$Cmd$none;
				var clearedPending = function () {
					var _v11 = _Utils_Tuple2(newRoute, model.pendingVideoFromImage);
					if (((_v11.a.$ === 'Just') && (_v11.a.a.$ === 'Videos')) && (_v11.b.$ === 'Just')) {
						var _v12 = _v11.a.a;
						return $elm$core$Maybe$Nothing;
					} else {
						return model.pendingVideoFromImage;
					}
				}();
				var audioGalleryCmd = function () {
					if ((newRoute.$ === 'Just') && (newRoute.a.$ === 'AudioGallery')) {
						var _v10 = newRoute.a;
						return A2(
							$elm$core$Task$perform,
							$elm$core$Basics$always(
								$author$project$Main$AudioGalleryMsg($author$project$AudioGallery$FetchAudio)),
							$elm$core$Task$succeed(_Utils_Tuple0));
					} else {
						return $elm$core$Platform$Cmd$none;
					}
				}();
				var audioDetailModel = function () {
					if ((newRoute.$ === 'Just') && (newRoute.a.$ === 'AudioDetail')) {
						var audioId = newRoute.a.a;
						var _v8 = $author$project$AudioDetail$init(audioId);
						var detailModel = _v8.a;
						var detailCmd = _v8.b;
						return $elm$core$Maybe$Just(detailModel);
					} else {
						return $elm$core$Maybe$Nothing;
					}
				}();
				var audioDetailCmd = $elm$core$Platform$Cmd$none;
				var _v2 = function () {
					if ((newRoute.$ === 'Just') && (newRoute.a.$ === 'BriefGallery')) {
						var _v4 = newRoute.a;
						return $author$project$BriefGallery$init(model.key);
					} else {
						return _Utils_Tuple2(model.briefGalleryModel, $elm$core$Platform$Cmd$none);
					}
				}();
				var briefGalleryModel = _v2.a;
				var briefGalleryInitCmd = _v2.b;
				var briefGalleryCmd = function () {
					if ((newRoute.$ === 'Just') && (newRoute.a.$ === 'BriefGallery')) {
						var _v6 = newRoute.a;
						return A2(
							$elm$core$Platform$Cmd$map,
							$author$project$Main$BriefGalleryMsg,
							$author$project$BriefGallery$initCmd(briefGalleryModel));
					} else {
						return $elm$core$Platform$Cmd$none;
					}
				}();
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{audioDetailModel: audioDetailModel, briefGalleryModel: briefGalleryModel, creativeBriefEditorModel: creativeBriefEditorModel, imageDetailModel: imageDetailModel, pendingVideoFromImage: clearedPending, route: newRoute, url: url, videoDetailModel: videoDetailModel}),
					$elm$core$Platform$Cmd$batch(
						_List_fromArray(
							[videoDetailCmd, imageDetailCmd, audioDetailCmd, creativeBriefEditorCmd, briefGalleryCmd, galleryCmd, imageGalleryCmd, audioGalleryCmd, videoToTextGalleryCmd, videoPrefillCmd])));
			case 'UpdateTextInput':
				var text = msg.a;
				var uiState = model.uiState;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{
							uiState: _Utils_update(
								uiState,
								{textInput: text})
						}),
					$elm$core$Platform$Cmd$none);
			case 'GenerateScene':
				var uiState = model.uiState;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{
							uiState: _Utils_update(
								uiState,
								{errorMessage: $elm$core$Maybe$Nothing, isGenerating: true})
						}),
					$author$project$Main$generateSceneRequest(model.uiState.textInput));
			case 'SceneGenerated':
				var sceneJson = msg.a;
				var _v30 = A2($elm$json$Json$Decode$decodeValue, $author$project$Main$sceneDecoder, sceneJson);
				if (_v30.$ === 'Ok') {
					var newScene = _v30.a;
					var uiState = model.uiState;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								initialScene: $elm$core$Maybe$Just(newScene),
								scene: newScene,
								uiState: _Utils_update(
									uiState,
									{isGenerating: false, textInput: ''})
							}),
						$elm$core$Platform$Cmd$none);
				} else {
					var error = _v30.a;
					var uiState = model.uiState;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								uiState: _Utils_update(
									uiState,
									{
										errorMessage: $elm$core$Maybe$Just(
											$elm$json$Json$Decode$errorToString(error)),
										isGenerating: false
									})
							}),
						$elm$core$Platform$Cmd$none);
				}
			case 'SceneGeneratedResult':
				var result = msg.a;
				if (result.$ === 'Ok') {
					var scene = result.a;
					var uiState = model.uiState;
					var modelWithHistory = $author$project$Main$saveToHistory(model);
					return _Utils_Tuple2(
						_Utils_update(
							modelWithHistory,
							{
								initialScene: $elm$core$Maybe$Just(scene),
								scene: scene,
								uiState: _Utils_update(
									uiState,
									{isGenerating: false, textInput: ''})
							}),
						$author$project$Main$sendSceneToThreeJs(
							$author$project$Main$sceneEncoder(scene)));
				} else {
					var error = result.a;
					var uiState = model.uiState;
					var errorMessage = function () {
						switch (error.$) {
							case 'BadUrl':
								var url = error.a;
								return 'Bad URL: ' + url;
							case 'Timeout':
								return 'Request timed out';
							case 'NetworkError':
								return 'Network error';
							case 'BadStatus':
								var status = error.a;
								return 'Server error: ' + $elm$core$String$fromInt(status);
							default:
								var body = error.a;
								return 'Invalid response: ' + body;
						}
					}();
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								uiState: _Utils_update(
									uiState,
									{
										errorMessage: $elm$core$Maybe$Just(errorMessage),
										isGenerating: false
									})
							}),
						$elm$core$Platform$Cmd$none);
				}
			case 'ObjectClicked':
				var objectId = msg.a;
				var scene = model.scene;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{
							scene: _Utils_update(
								scene,
								{
									selectedObject: $elm$core$Maybe$Just(objectId)
								})
						}),
					$author$project$Main$sendSelectionToThreeJs(objectId));
			case 'UpdateObjectTransform':
				var objectId = msg.a;
				var newTransform = msg.b;
				var updateObject = function (obj) {
					return _Utils_eq(obj.id, objectId) ? _Utils_update(
						obj,
						{transform: newTransform}) : obj;
				};
				var scene = model.scene;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{
							scene: _Utils_update(
								scene,
								{
									objects: A2(
										$elm$core$Dict$map,
										F2(
											function (_v33, obj) {
												return updateObject(obj);
											}),
										scene.objects)
								})
						}),
					$elm$core$Platform$Cmd$none);
			case 'UpdateObjectProperty':
				var objectId = msg.a;
				var propertyName = msg.b;
				var value = msg.c;
				var updatePhysicsProperty = F3(
					function (props, propName, propValue) {
						switch (propName) {
							case 'mass':
								return _Utils_update(
									props,
									{mass: propValue});
							case 'friction':
								return _Utils_update(
									props,
									{friction: propValue});
							case 'restitution':
								return _Utils_update(
									props,
									{restitution: propValue});
							default:
								return props;
						}
					});
				var updateObject = function (obj) {
					return _Utils_eq(obj.id, objectId) ? _Utils_update(
						obj,
						{
							physicsProperties: A3(updatePhysicsProperty, obj.physicsProperties, propertyName, value)
						}) : obj;
				};
				var scene = model.scene;
				var updatedScene = _Utils_update(
					scene,
					{
						objects: A2(
							$elm$core$Dict$map,
							F2(
								function (_v34, obj) {
									return updateObject(obj);
								}),
							scene.objects)
					});
				var modelWithHistory = $author$project$Main$saveToHistory(model);
				return _Utils_Tuple2(
					_Utils_update(
						modelWithHistory,
						{scene: updatedScene}),
					$author$project$Main$sendSceneToThreeJs(
						$author$project$Main$sceneEncoder(updatedScene)));
			case 'UpdateObjectDescription':
				var objectId = msg.a;
				var desc = msg.b;
				var updateObject = function (obj) {
					return _Utils_eq(obj.id, objectId) ? _Utils_update(
						obj,
						{
							description: $elm$core$String$isEmpty(desc) ? $elm$core$Maybe$Nothing : $elm$core$Maybe$Just(desc)
						}) : obj;
				};
				var scene = model.scene;
				var updatedScene = _Utils_update(
					scene,
					{
						objects: A2(
							$elm$core$Dict$map,
							F2(
								function (_v36, obj) {
									return updateObject(obj);
								}),
							scene.objects)
					});
				var modelWithHistory = $author$project$Main$saveToHistory(model);
				return _Utils_Tuple2(
					_Utils_update(
						modelWithHistory,
						{scene: updatedScene}),
					$author$project$Main$sendSceneToThreeJs(
						$author$project$Main$sceneEncoder(updatedScene)));
			case 'ToggleSimulation':
				var simulationState = model.simulationState;
				var newIsRunning = !simulationState.isRunning;
				var command = newIsRunning ? 'start' : 'pause';
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{
							simulationState: _Utils_update(
								simulationState,
								{isRunning: newIsRunning})
						}),
					$author$project$Main$sendSimulationCommand(command));
			case 'ResetSimulation':
				var _v37 = model.initialScene;
				if (_v37.$ === 'Just') {
					var initial = _v37.a;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{scene: initial}),
						$author$project$Main$sendSimulationCommand('reset'));
				} else {
					return _Utils_Tuple2(model, $elm$core$Platform$Cmd$none);
				}
			case 'SetTransformMode':
				var mode = msg.a;
				var simulationState = model.simulationState;
				var modeString = function () {
					switch (mode.$) {
						case 'Translate':
							return 'translate';
						case 'Rotate':
							return 'rotate';
						default:
							return 'scale';
					}
				}();
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{
							simulationState: _Utils_update(
								simulationState,
								{transformMode: mode})
						}),
					$author$project$Main$sendTransformModeToThreeJs(modeString));
			case 'ClearError':
				var uiState = model.uiState;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{
							uiState: _Utils_update(
								uiState,
								{errorMessage: $elm$core$Maybe$Nothing})
						}),
					$elm$core$Platform$Cmd$none);
			case 'SelectionChanged':
				var maybeObjectId = msg.a;
				var scene = model.scene;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{
							scene: _Utils_update(
								scene,
								{selectedObject: maybeObjectId})
						}),
					$elm$core$Platform$Cmd$none);
			case 'TransformUpdated':
				var objectId = msg.a.objectId;
				var transform = msg.a.transform;
				var updateObject = function (obj) {
					return _Utils_eq(obj.id, objectId) ? _Utils_update(
						obj,
						{transform: transform}) : obj;
				};
				var scene = model.scene;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{
							scene: _Utils_update(
								scene,
								{
									objects: A2(
										$elm$core$Dict$map,
										F2(
											function (_v39, obj) {
												return updateObject(obj);
											}),
										scene.objects)
								})
						}),
					$elm$core$Platform$Cmd$none);
			case 'UpdateRefineInput':
				var text = msg.a;
				var uiState = model.uiState;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{
							uiState: _Utils_update(
								uiState,
								{refineInput: text})
						}),
					$elm$core$Platform$Cmd$none);
			case 'RefineScene':
				var uiState = model.uiState;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{
							uiState: _Utils_update(
								uiState,
								{isRefining: true})
						}),
					A2($author$project$Main$refineSceneRequest, model.scene, model.uiState.refineInput));
			case 'SceneRefined':
				var result = msg.a;
				if (result.$ === 'Ok') {
					var newScene = result.a;
					var uiState = model.uiState;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								future: _List_Nil,
								history: A2($elm$core$List$cons, model.scene, model.history),
								scene: newScene,
								uiState: _Utils_update(
									uiState,
									{isRefining: false})
							}),
						$elm$core$Platform$Cmd$none);
				} else {
					var error = result.a;
					var uiState = model.uiState;
					var errorMessage = function () {
						switch (error.$) {
							case 'BadUrl':
								var url = error.a;
								return 'Bad URL: ' + url;
							case 'Timeout':
								return 'Request timed out';
							case 'NetworkError':
								return 'Network error';
							case 'BadStatus':
								var status = error.a;
								return 'Bad status: ' + $elm$core$String$fromInt(status);
							default:
								var message = error.a;
								return 'Bad response: ' + message;
						}
					}();
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								uiState: _Utils_update(
									uiState,
									{
										errorMessage: $elm$core$Maybe$Just(errorMessage),
										isRefining: false
									})
							}),
						$elm$core$Platform$Cmd$none);
				}
			case 'Undo':
				var _v42 = model.history;
				if (_v42.b) {
					var prevScene = _v42.a;
					var restHistory = _v42.b;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								future: A2($elm$core$List$cons, model.scene, model.future),
								history: restHistory,
								scene: prevScene
							}),
						$elm$core$Platform$Cmd$none);
				} else {
					return _Utils_Tuple2(model, $elm$core$Platform$Cmd$none);
				}
			case 'Redo':
				var _v43 = model.future;
				if (_v43.b) {
					var nextScene = _v43.a;
					var restFuture = _v43.b;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								future: restFuture,
								history: A2($elm$core$List$cons, model.scene, model.history),
								scene: nextScene
							}),
						$elm$core$Platform$Cmd$none);
				} else {
					return _Utils_Tuple2(model, $elm$core$Platform$Cmd$none);
				}
			case 'SaveScene':
				return _Utils_Tuple2(model, $elm$core$Platform$Cmd$none);
			case 'LoadScene':
				return _Utils_Tuple2(model, $elm$core$Platform$Cmd$none);
			case 'SceneLoadedFromStorage':
				var result = msg.a;
				return _Utils_Tuple2(model, $elm$core$Platform$Cmd$none);
			case 'KeyDown':
				var key = msg.a;
				if (key === 'Control') {
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{ctrlPressed: true}),
						$elm$core$Platform$Cmd$none);
				} else {
					return _Utils_Tuple2(model, $elm$core$Platform$Cmd$none);
				}
			case 'KeyUp':
				var key = msg.a;
				if (key === 'Control') {
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{ctrlPressed: false}),
						$elm$core$Platform$Cmd$none);
				} else {
					return _Utils_Tuple2(model, $elm$core$Platform$Cmd$none);
				}
			case 'VideoMsg':
				var videoMsg = msg.a;
				var navCmd = function () {
					if (videoMsg.$ === 'NavigateToVideo') {
						var videoId = videoMsg.a;
						return A2(
							$elm$browser$Browser$Navigation$pushUrl,
							model.key,
							$author$project$Route$toHref(
								$author$project$Route$VideoDetail(videoId)));
					} else {
						return $elm$core$Platform$Cmd$none;
					}
				}();
				var _v46 = A2($author$project$Video$update, videoMsg, model.videoModel);
				var updatedVideoModel = _v46.a;
				var videoCmd = _v46.b;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{videoModel: updatedVideoModel}),
					$elm$core$Platform$Cmd$batch(
						_List_fromArray(
							[
								A2($elm$core$Platform$Cmd$map, $author$project$Main$VideoMsg, videoCmd),
								navCmd
							])));
			case 'VideoDetailMsg':
				var videoDetailMsg = msg.a;
				var _v48 = model.videoDetailModel;
				if (_v48.$ === 'Just') {
					var videoDetailModel = _v48.a;
					var _v49 = A2($author$project$VideoDetail$update, videoDetailMsg, videoDetailModel);
					var updatedVideoDetailModel = _v49.a;
					var videoDetailCmd = _v49.b;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								videoDetailModel: $elm$core$Maybe$Just(updatedVideoDetailModel)
							}),
						A2($elm$core$Platform$Cmd$map, $author$project$Main$VideoDetailMsg, videoDetailCmd));
				} else {
					return _Utils_Tuple2(model, $elm$core$Platform$Cmd$none);
				}
			case 'GalleryMsg':
				var galleryMsg = msg.a;
				var _v50 = A2($author$project$VideoGallery$update, galleryMsg, model.galleryModel);
				var updatedGalleryModel = _v50.a;
				var galleryCmd = _v50.b;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{galleryModel: updatedGalleryModel}),
					A2($elm$core$Platform$Cmd$map, $author$project$Main$GalleryMsg, galleryCmd));
			case 'SimulationGalleryMsg':
				var simulationGalleryMsg = msg.a;
				var _v51 = A2($author$project$SimulationGallery$update, simulationGalleryMsg, model.simulationGalleryModel);
				var updatedSimulationGalleryModel = _v51.a;
				var simulationGalleryCmd = _v51.b;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{simulationGalleryModel: updatedSimulationGalleryModel}),
					A2($elm$core$Platform$Cmd$map, $author$project$Main$SimulationGalleryMsg, simulationGalleryCmd));
			case 'ImageMsg':
				var imageMsg = msg.a;
				var navCmd = function () {
					if (imageMsg.$ === 'NavigateToImage') {
						var imageId = imageMsg.a;
						return A2(
							$elm$browser$Browser$Navigation$pushUrl,
							model.key,
							$author$project$Route$toHref(
								$author$project$Route$ImageDetail(imageId)));
					} else {
						return $elm$core$Platform$Cmd$none;
					}
				}();
				var _v52 = A2($author$project$Image$update, imageMsg, model.imageModel);
				var updatedImageModel = _v52.a;
				var imageCmd = _v52.b;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{imageModel: updatedImageModel}),
					$elm$core$Platform$Cmd$batch(
						_List_fromArray(
							[
								A2($elm$core$Platform$Cmd$map, $author$project$Main$ImageMsg, imageCmd),
								navCmd
							])));
			case 'ImageDetailMsg':
				var imageDetailMsg = msg.a;
				var _v54 = model.imageDetailModel;
				if (_v54.$ === 'Just') {
					var imageDetailModel = _v54.a;
					var _v55 = A2($author$project$ImageDetail$update, imageDetailMsg, imageDetailModel);
					var updatedImageDetailModel = _v55.a;
					var imageDetailCmd = _v55.b;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								imageDetailModel: $elm$core$Maybe$Just(updatedImageDetailModel)
							}),
						A2($elm$core$Platform$Cmd$map, $author$project$Main$ImageDetailMsg, imageDetailCmd));
				} else {
					return _Utils_Tuple2(model, $elm$core$Platform$Cmd$none);
				}
			case 'ImageGalleryMsg':
				var imageGalleryMsg = msg.a;
				var _v56 = A2($author$project$ImageGallery$update, imageGalleryMsg, model.imageGalleryModel);
				var updatedImageGalleryModel = _v56.a;
				var imageGalleryCmd = _v56.b;
				var _v57 = function () {
					if (imageGalleryMsg.$ === 'CreateVideoFromImage') {
						var modelId = imageGalleryMsg.a;
						var imageUrl = imageGalleryMsg.b;
						return _Utils_Tuple2(
							A2($elm$browser$Browser$Navigation$pushUrl, model.key, '/videos'),
							_Utils_update(
								model,
								{
									imageGalleryModel: updatedImageGalleryModel,
									pendingVideoFromImage: $elm$core$Maybe$Just(
										{imageUrl: imageUrl, modelId: modelId})
								}));
					} else {
						return _Utils_Tuple2(
							$elm$core$Platform$Cmd$none,
							_Utils_update(
								model,
								{imageGalleryModel: updatedImageGalleryModel}));
					}
				}();
				var navCmd = _v57.a;
				var updatedModel = _v57.b;
				return _Utils_Tuple2(
					updatedModel,
					$elm$core$Platform$Cmd$batch(
						_List_fromArray(
							[
								A2($elm$core$Platform$Cmd$map, $author$project$Main$ImageGalleryMsg, imageGalleryCmd),
								navCmd
							])));
			case 'AudioMsg':
				var audioMsg = msg.a;
				var navCmd = function () {
					if (audioMsg.$ === 'NavigateToAudio') {
						var audioId = audioMsg.a;
						return A2(
							$elm$browser$Browser$Navigation$pushUrl,
							model.key,
							$author$project$Route$toHref(
								$author$project$Route$AudioDetail(audioId)));
					} else {
						return $elm$core$Platform$Cmd$none;
					}
				}();
				var _v59 = A2($author$project$Audio$update, audioMsg, model.audioModel);
				var updatedAudioModel = _v59.a;
				var audioCmd = _v59.b;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{audioModel: updatedAudioModel}),
					$elm$core$Platform$Cmd$batch(
						_List_fromArray(
							[
								A2($elm$core$Platform$Cmd$map, $author$project$Main$AudioMsg, audioCmd),
								navCmd
							])));
			case 'AudioDetailMsg':
				var audioDetailMsg = msg.a;
				var _v61 = model.audioDetailModel;
				if (_v61.$ === 'Just') {
					var audioDetailModel = _v61.a;
					var _v62 = A2($author$project$AudioDetail$update, audioDetailMsg, audioDetailModel);
					var updatedAudioDetailModel = _v62.a;
					var audioDetailCmd = _v62.b;
					return _Utils_Tuple2(
						_Utils_update(
							model,
							{
								audioDetailModel: $elm$core$Maybe$Just(updatedAudioDetailModel)
							}),
						A2($elm$core$Platform$Cmd$map, $author$project$Main$AudioDetailMsg, audioDetailCmd));
				} else {
					return _Utils_Tuple2(model, $elm$core$Platform$Cmd$none);
				}
			case 'AudioGalleryMsg':
				var audioGalleryMsg = msg.a;
				var _v63 = A2($author$project$AudioGallery$update, audioGalleryMsg, model.audioGalleryModel);
				var updatedAudioGalleryModel = _v63.a;
				var audioGalleryCmd = _v63.b;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{audioGalleryModel: updatedAudioGalleryModel}),
					A2($elm$core$Platform$Cmd$map, $author$project$Main$AudioGalleryMsg, audioGalleryCmd));
			case 'VideoToTextMsg':
				var videoToTextMsg = msg.a;
				var navCmd = function () {
					if (videoToTextMsg.$ === 'NavigateToResult') {
						var videoId = videoToTextMsg.a;
						return A2(
							$elm$browser$Browser$Navigation$pushUrl,
							model.key,
							$author$project$Route$toHref($author$project$Route$VideoToTextGallery));
					} else {
						return $elm$core$Platform$Cmd$none;
					}
				}();
				var _v64 = A2($author$project$VideoToText$update, videoToTextMsg, model.videoToTextModel);
				var updatedVideoToTextModel = _v64.a;
				var videoToTextCmd = _v64.b;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{videoToTextModel: updatedVideoToTextModel}),
					$elm$core$Platform$Cmd$batch(
						_List_fromArray(
							[
								A2($elm$core$Platform$Cmd$map, $author$project$Main$VideoToTextMsg, videoToTextCmd),
								navCmd
							])));
			case 'VideoToTextGalleryMsg':
				var videoToTextGalleryMsg = msg.a;
				var _v66 = A2($author$project$VideoToTextGallery$update, videoToTextGalleryMsg, model.videoToTextGalleryModel);
				var updatedVideoToTextGalleryModel = _v66.a;
				var videoToTextGalleryCmd = _v66.b;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{videoToTextGalleryModel: updatedVideoToTextGalleryModel}),
					A2($elm$core$Platform$Cmd$map, $author$project$Main$VideoToTextGalleryMsg, videoToTextGalleryCmd));
			case 'AuthMsg':
				var authMsg = msg.a;
				var fetchCmd = function () {
					if ((authMsg.$ === 'LoginResult') && (authMsg.a.$ === 'Ok')) {
						return $elm$core$Platform$Cmd$batch(
							_List_fromArray(
								[
									A2(
									$elm$core$Platform$Cmd$map,
									$author$project$Main$GalleryMsg,
									A2(
										$elm$core$Task$perform,
										$elm$core$Basics$always($author$project$VideoGallery$FetchVideos),
										$elm$core$Task$succeed(_Utils_Tuple0))),
									A2(
									$elm$core$Platform$Cmd$map,
									$author$project$Main$SimulationGalleryMsg,
									A2(
										$elm$core$Task$perform,
										$elm$core$Basics$always($author$project$SimulationGallery$FetchVideos),
										$elm$core$Task$succeed(_Utils_Tuple0))),
									A2(
									$elm$core$Platform$Cmd$map,
									$author$project$Main$ImageGalleryMsg,
									A2(
										$elm$core$Task$perform,
										$elm$core$Basics$always($author$project$ImageGallery$FetchImages),
										$elm$core$Task$succeed(_Utils_Tuple0))),
									A2(
									$elm$core$Platform$Cmd$map,
									$author$project$Main$AudioGalleryMsg,
									A2(
										$elm$core$Task$perform,
										$elm$core$Basics$always($author$project$AudioGallery$FetchAudio),
										$elm$core$Task$succeed(_Utils_Tuple0))),
									A2(
									$elm$core$Platform$Cmd$map,
									$author$project$Main$VideoToTextGalleryMsg,
									A2(
										$elm$core$Task$perform,
										$elm$core$Basics$always($author$project$VideoToTextGallery$FetchVideos),
										$elm$core$Task$succeed(_Utils_Tuple0)))
								]));
					} else {
						return $elm$core$Platform$Cmd$none;
					}
				}();
				var _v67 = A2($author$project$Auth$update, authMsg, model.authModel);
				var updatedAuthModel = _v67.a;
				var authCmd = _v67.b;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{authModel: updatedAuthModel}),
					$elm$core$Platform$Cmd$batch(
						_List_fromArray(
							[
								A2($elm$core$Platform$Cmd$map, $author$project$Main$AuthMsg, authCmd),
								fetchCmd
							])));
			case 'CreativeBriefEditorMsg':
				var briefMsg = msg.a;
				var _v69 = A2($author$project$CreativeBriefEditor$update, briefMsg, model.creativeBriefEditorModel);
				var updatedModel = _v69.a;
				var cmd = _v69.b;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{creativeBriefEditorModel: updatedModel}),
					A2($elm$core$Platform$Cmd$map, $author$project$Main$CreativeBriefEditorMsg, cmd));
			case 'BriefGalleryMsg':
				var galleryMsg = msg.a;
				var _v70 = A2($author$project$BriefGallery$update, galleryMsg, model.briefGalleryModel);
				var updatedModel = _v70.a;
				var cmd = _v70.b;
				return _Utils_Tuple2(
					_Utils_update(
						model,
						{briefGalleryModel: updatedModel}),
					A2($elm$core$Platform$Cmd$map, $author$project$Main$BriefGalleryMsg, cmd));
			default:
				var route = msg.a;
				return _Utils_Tuple2(
					model,
					A2(
						$elm$browser$Browser$Navigation$pushUrl,
						model.key,
						$author$project$Route$toHref(route)));
		}
	});
var $elm$html$Html$div = _VirtualDom_node('div');
var $elm$virtual_dom$VirtualDom$map = _VirtualDom_map;
var $elm$html$Html$map = $elm$virtual_dom$VirtualDom$map;
var $elm$virtual_dom$VirtualDom$style = _VirtualDom_style;
var $elm$html$Html$Attributes$style = $elm$virtual_dom$VirtualDom$style;
var $author$project$Auth$SubmitLogin = {$: 'SubmitLogin'};
var $author$project$Auth$UpdatePassword = function (a) {
	return {$: 'UpdatePassword', a: a};
};
var $author$project$Auth$UpdateUsername = function (a) {
	return {$: 'UpdateUsername', a: a};
};
var $elm$html$Html$button = _VirtualDom_node('button');
var $elm$html$Html$Attributes$stringProperty = F2(
	function (key, string) {
		return A2(
			_VirtualDom_property,
			key,
			$elm$json$Json$Encode$string(string));
	});
var $elm$html$Html$Attributes$class = $elm$html$Html$Attributes$stringProperty('className');
var $elm$html$Html$Attributes$boolProperty = F2(
	function (key, bool) {
		return A2(
			_VirtualDom_property,
			key,
			$elm$json$Json$Encode$bool(bool));
	});
var $elm$html$Html$Attributes$disabled = $elm$html$Html$Attributes$boolProperty('disabled');
var $elm$html$Html$form = _VirtualDom_node('form');
var $elm$html$Html$h2 = _VirtualDom_node('h2');
var $elm$html$Html$h3 = _VirtualDom_node('h3');
var $elm$html$Html$input = _VirtualDom_node('input');
var $elm$html$Html$label = _VirtualDom_node('label');
var $elm$html$Html$Events$alwaysStop = function (x) {
	return _Utils_Tuple2(x, true);
};
var $elm$virtual_dom$VirtualDom$MayStopPropagation = function (a) {
	return {$: 'MayStopPropagation', a: a};
};
var $elm$virtual_dom$VirtualDom$on = _VirtualDom_on;
var $elm$html$Html$Events$stopPropagationOn = F2(
	function (event, decoder) {
		return A2(
			$elm$virtual_dom$VirtualDom$on,
			event,
			$elm$virtual_dom$VirtualDom$MayStopPropagation(decoder));
	});
var $elm$html$Html$Events$targetValue = A2(
	$elm$json$Json$Decode$at,
	_List_fromArray(
		['target', 'value']),
	$elm$json$Json$Decode$string);
var $elm$html$Html$Events$onInput = function (tagger) {
	return A2(
		$elm$html$Html$Events$stopPropagationOn,
		'input',
		A2(
			$elm$json$Json$Decode$map,
			$elm$html$Html$Events$alwaysStop,
			A2($elm$json$Json$Decode$map, tagger, $elm$html$Html$Events$targetValue)));
};
var $elm$html$Html$Events$alwaysPreventDefault = function (msg) {
	return _Utils_Tuple2(msg, true);
};
var $elm$virtual_dom$VirtualDom$MayPreventDefault = function (a) {
	return {$: 'MayPreventDefault', a: a};
};
var $elm$html$Html$Events$preventDefaultOn = F2(
	function (event, decoder) {
		return A2(
			$elm$virtual_dom$VirtualDom$on,
			event,
			$elm$virtual_dom$VirtualDom$MayPreventDefault(decoder));
	});
var $elm$html$Html$Events$onSubmit = function (msg) {
	return A2(
		$elm$html$Html$Events$preventDefaultOn,
		'submit',
		A2(
			$elm$json$Json$Decode$map,
			$elm$html$Html$Events$alwaysPreventDefault,
			$elm$json$Json$Decode$succeed(msg)));
};
var $elm$html$Html$Attributes$placeholder = $elm$html$Html$Attributes$stringProperty('placeholder');
var $elm$virtual_dom$VirtualDom$text = _VirtualDom_text;
var $elm$html$Html$text = $elm$virtual_dom$VirtualDom$text;
var $elm$html$Html$Attributes$type_ = $elm$html$Html$Attributes$stringProperty('type');
var $elm$html$Html$Attributes$value = $elm$html$Html$Attributes$stringProperty('value');
var $author$project$Auth$view = function (model) {
	return A2(
		$elm$html$Html$div,
		_List_fromArray(
			[
				$elm$html$Html$Attributes$class('login-container'),
				A2($elm$html$Html$Attributes$style, 'position', 'fixed'),
				A2($elm$html$Html$Attributes$style, 'top', '0'),
				A2($elm$html$Html$Attributes$style, 'left', '0'),
				A2($elm$html$Html$Attributes$style, 'width', '100%'),
				A2($elm$html$Html$Attributes$style, 'height', '100%'),
				A2($elm$html$Html$Attributes$style, 'display', 'flex'),
				A2($elm$html$Html$Attributes$style, 'align-items', 'center'),
				A2($elm$html$Html$Attributes$style, 'justify-content', 'center'),
				A2($elm$html$Html$Attributes$style, 'background', 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'),
				A2($elm$html$Html$Attributes$style, 'z-index', '9999')
			]),
		_List_fromArray(
			[
				A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('login-box'),
						A2($elm$html$Html$Attributes$style, 'background', 'white'),
						A2($elm$html$Html$Attributes$style, 'padding', '2rem'),
						A2($elm$html$Html$Attributes$style, 'border-radius', '8px'),
						A2($elm$html$Html$Attributes$style, 'box-shadow', '0 10px 25px rgba(0,0,0,0.2)'),
						A2($elm$html$Html$Attributes$style, 'width', '100%'),
						A2($elm$html$Html$Attributes$style, 'max-width', '400px')
					]),
				_List_fromArray(
					[
						A2(
						$elm$html$Html$h2,
						_List_fromArray(
							[
								A2($elm$html$Html$Attributes$style, 'margin-top', '0'),
								A2($elm$html$Html$Attributes$style, 'color', '#333'),
								A2($elm$html$Html$Attributes$style, 'text-align', 'center')
							]),
						_List_fromArray(
							[
								$elm$html$Html$text('Best Video Project')
							])),
						A2(
						$elm$html$Html$h3,
						_List_fromArray(
							[
								A2($elm$html$Html$Attributes$style, 'margin-top', '0'),
								A2($elm$html$Html$Attributes$style, 'color', '#666'),
								A2($elm$html$Html$Attributes$style, 'font-weight', 'normal'),
								A2($elm$html$Html$Attributes$style, 'text-align', 'center')
							]),
						_List_fromArray(
							[
								$elm$html$Html$text('Sign In')
							])),
						function () {
						var _v0 = model.error;
						if (_v0.$ === 'Just') {
							var errorMsg = _v0.a;
							return A2(
								$elm$html$Html$div,
								_List_fromArray(
									[
										A2($elm$html$Html$Attributes$style, 'background', '#fee'),
										A2($elm$html$Html$Attributes$style, 'color', '#c33'),
										A2($elm$html$Html$Attributes$style, 'padding', '0.75rem'),
										A2($elm$html$Html$Attributes$style, 'border-radius', '4px'),
										A2($elm$html$Html$Attributes$style, 'margin-bottom', '1rem'),
										A2($elm$html$Html$Attributes$style, 'border', '1px solid #fcc')
									]),
								_List_fromArray(
									[
										$elm$html$Html$text(errorMsg)
									]));
						} else {
							return $elm$html$Html$text('');
						}
					}(),
						A2(
						$elm$html$Html$form,
						_List_fromArray(
							[
								$elm$html$Html$Events$onSubmit($author$project$Auth$SubmitLogin)
							]),
						_List_fromArray(
							[
								A2(
								$elm$html$Html$div,
								_List_fromArray(
									[
										A2($elm$html$Html$Attributes$style, 'margin-bottom', '1rem')
									]),
								_List_fromArray(
									[
										A2(
										$elm$html$Html$label,
										_List_fromArray(
											[
												A2($elm$html$Html$Attributes$style, 'display', 'block'),
												A2($elm$html$Html$Attributes$style, 'margin-bottom', '0.5rem'),
												A2($elm$html$Html$Attributes$style, 'color', '#555'),
												A2($elm$html$Html$Attributes$style, 'font-weight', '500')
											]),
										_List_fromArray(
											[
												$elm$html$Html$text('Username')
											])),
										A2(
										$elm$html$Html$input,
										_List_fromArray(
											[
												$elm$html$Html$Attributes$type_('text'),
												$elm$html$Html$Attributes$value(model.username),
												$elm$html$Html$Events$onInput($author$project$Auth$UpdateUsername),
												$elm$html$Html$Attributes$placeholder('Enter username'),
												$elm$html$Html$Attributes$disabled(
												_Utils_eq(model.loginState, $author$project$Auth$LoggingIn)),
												A2($elm$html$Html$Attributes$style, 'width', '100%'),
												A2($elm$html$Html$Attributes$style, 'padding', '0.75rem'),
												A2($elm$html$Html$Attributes$style, 'border', '1px solid #ddd'),
												A2($elm$html$Html$Attributes$style, 'border-radius', '4px'),
												A2($elm$html$Html$Attributes$style, 'font-size', '1rem'),
												A2($elm$html$Html$Attributes$style, 'box-sizing', 'border-box')
											]),
										_List_Nil)
									])),
								A2(
								$elm$html$Html$div,
								_List_fromArray(
									[
										A2($elm$html$Html$Attributes$style, 'margin-bottom', '1.5rem')
									]),
								_List_fromArray(
									[
										A2(
										$elm$html$Html$label,
										_List_fromArray(
											[
												A2($elm$html$Html$Attributes$style, 'display', 'block'),
												A2($elm$html$Html$Attributes$style, 'margin-bottom', '0.5rem'),
												A2($elm$html$Html$Attributes$style, 'color', '#555'),
												A2($elm$html$Html$Attributes$style, 'font-weight', '500')
											]),
										_List_fromArray(
											[
												$elm$html$Html$text('Password')
											])),
										A2(
										$elm$html$Html$input,
										_List_fromArray(
											[
												$elm$html$Html$Attributes$type_('password'),
												$elm$html$Html$Attributes$value(model.password),
												$elm$html$Html$Events$onInput($author$project$Auth$UpdatePassword),
												$elm$html$Html$Attributes$placeholder('Enter password'),
												$elm$html$Html$Attributes$disabled(
												_Utils_eq(model.loginState, $author$project$Auth$LoggingIn)),
												A2($elm$html$Html$Attributes$style, 'width', '100%'),
												A2($elm$html$Html$Attributes$style, 'padding', '0.75rem'),
												A2($elm$html$Html$Attributes$style, 'border', '1px solid #ddd'),
												A2($elm$html$Html$Attributes$style, 'border-radius', '4px'),
												A2($elm$html$Html$Attributes$style, 'font-size', '1rem'),
												A2($elm$html$Html$Attributes$style, 'box-sizing', 'border-box')
											]),
										_List_Nil)
									])),
								A2(
								$elm$html$Html$button,
								_List_fromArray(
									[
										$elm$html$Html$Attributes$type_('submit'),
										$elm$html$Html$Attributes$disabled(
										_Utils_eq(model.loginState, $author$project$Auth$LoggingIn) || ($elm$core$String$isEmpty(model.username) || $elm$core$String$isEmpty(model.password))),
										A2($elm$html$Html$Attributes$style, 'width', '100%'),
										A2($elm$html$Html$Attributes$style, 'padding', '0.75rem'),
										A2($elm$html$Html$Attributes$style, 'background', '#667eea'),
										A2($elm$html$Html$Attributes$style, 'color', 'white'),
										A2($elm$html$Html$Attributes$style, 'border', 'none'),
										A2($elm$html$Html$Attributes$style, 'border-radius', '4px'),
										A2($elm$html$Html$Attributes$style, 'font-size', '1rem'),
										A2($elm$html$Html$Attributes$style, 'font-weight', '500'),
										A2($elm$html$Html$Attributes$style, 'cursor', 'pointer'),
										A2($elm$html$Html$Attributes$style, 'transition', 'background 0.2s')
									]),
								_List_fromArray(
									[
										$elm$html$Html$text(
										_Utils_eq(model.loginState, $author$project$Auth$LoggingIn) ? 'Signing in...' : 'Sign In')
									]))
							])),
						A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								A2($elm$html$Html$Attributes$style, 'margin-top', '1rem'),
								A2($elm$html$Html$Attributes$style, 'text-align', 'center'),
								A2($elm$html$Html$Attributes$style, 'color', '#888'),
								A2($elm$html$Html$Attributes$style, 'font-size', '0.875rem')
							]),
						_List_fromArray(
							[
								$elm$html$Html$text('Team members: reuben, mike, harrison')
							]))
					]))
			]));
};
var $author$project$Audio$FetchModels = {$: 'FetchModels'};
var $author$project$Audio$GenerateAudio = {$: 'GenerateAudio'};
var $author$project$Audio$UpdateSearch = function (a) {
	return {$: 'UpdateSearch', a: a};
};
var $elm$virtual_dom$VirtualDom$attribute = F2(
	function (key, value) {
		return A2(
			_VirtualDom_attribute,
			_VirtualDom_noOnOrFormAction(key),
			_VirtualDom_noJavaScriptOrHtmlUri(value));
	});
var $elm$html$Html$Attributes$attribute = $elm$virtual_dom$VirtualDom$attribute;
var $elm$html$Html$Attributes$controls = $elm$html$Html$Attributes$boolProperty('controls');
var $elm$html$Html$h1 = _VirtualDom_node('h1');
var $elm$core$List$any = F2(
	function (isOkay, list) {
		any:
		while (true) {
			if (!list.b) {
				return false;
			} else {
				var x = list.a;
				var xs = list.b;
				if (isOkay(x)) {
					return true;
				} else {
					var $temp$isOkay = isOkay,
						$temp$list = xs;
					isOkay = $temp$isOkay;
					list = $temp$list;
					continue any;
				}
			}
		}
	});
var $elm$core$List$member = F2(
	function (x, xs) {
		return A2(
			$elm$core$List$any,
			function (a) {
				return _Utils_eq(a, x);
			},
			xs);
	});
var $author$project$Audio$hasEmptyRequiredParameters = F2(
	function (params, requiredFields) {
		return A2(
			$elm$core$List$any,
			function (param) {
				return A2($elm$core$List$member, param.key, requiredFields) && $elm$core$String$isEmpty(
					$elm$core$String$trim(param.value));
			},
			params);
	});
var $elm$html$Html$Attributes$id = $elm$html$Html$Attributes$stringProperty('id');
var $elm$virtual_dom$VirtualDom$node = function (tag) {
	return _VirtualDom_node(
		_VirtualDom_noScript(tag));
};
var $elm$html$Html$node = $elm$virtual_dom$VirtualDom$node;
var $elm$virtual_dom$VirtualDom$Normal = function (a) {
	return {$: 'Normal', a: a};
};
var $elm$html$Html$Events$on = F2(
	function (event, decoder) {
		return A2(
			$elm$virtual_dom$VirtualDom$on,
			event,
			$elm$virtual_dom$VirtualDom$Normal(decoder));
	});
var $elm$html$Html$Events$onClick = function (msg) {
	return A2(
		$elm$html$Html$Events$on,
		'click',
		$elm$json$Json$Decode$succeed(msg));
};
var $elm$html$Html$p = _VirtualDom_node('p');
var $elm$html$Html$Attributes$src = function (url) {
	return A2(
		$elm$html$Html$Attributes$stringProperty,
		'src',
		_VirtualDom_noJavaScriptOrHtmlUri(url));
};
var $author$project$Audio$SelectModel = function (a) {
	return {$: 'SelectModel', a: a};
};
var $author$project$Audio$viewModelOption = function (model) {
	return A2(
		$elm$html$Html$div,
		_List_fromArray(
			[
				$elm$html$Html$Attributes$class('model-option'),
				$elm$html$Html$Events$onClick(
				$author$project$Audio$SelectModel(model.id))
			]),
		_List_fromArray(
			[
				A2(
				$elm$html$Html$h3,
				_List_Nil,
				_List_fromArray(
					[
						$elm$html$Html$text(model.name)
					])),
				A2(
				$elm$html$Html$p,
				_List_Nil,
				_List_fromArray(
					[
						$elm$html$Html$text(model.description)
					]))
			]));
};
var $author$project$Audio$UpdateParameter = F2(
	function (a, b) {
		return {$: 'UpdateParameter', a: a, b: b};
	});
var $elm$core$String$cons = _String_cons;
var $elm$core$String$fromChar = function (_char) {
	return A2($elm$core$String$cons, _char, '');
};
var $elm$core$Char$toUpper = _Char_toUpper;
var $author$project$Audio$capitalize = function (str) {
	var _v0 = $elm$core$String$uncons(str);
	if (_v0.$ === 'Just') {
		var _v1 = _v0.a;
		var first = _v1.a;
		var rest = _v1.b;
		return _Utils_ap(
			$elm$core$String$fromChar(
				$elm$core$Char$toUpper(first)),
			rest);
	} else {
		return str;
	}
};
var $author$project$Audio$formatParameterName = function (name) {
	return A2(
		$elm$core$String$join,
		' ',
		A2(
			$elm$core$List$map,
			$author$project$Audio$capitalize,
			A2($elm$core$String$split, '_', name)));
};
var $elm$html$Html$option = _VirtualDom_node('option');
var $elm$html$Html$select = _VirtualDom_node('select');
var $elm$html$Html$span = _VirtualDom_node('span');
var $elm$html$Html$textarea = _VirtualDom_node('textarea');
var $author$project$Audio$viewParameter = F2(
	function (model, param) {
		var rangeText = function () {
			var _v3 = _Utils_Tuple2(param.minimum, param.maximum);
			if (_v3.a.$ === 'Just') {
				if (_v3.b.$ === 'Just') {
					var min = _v3.a.a;
					var max = _v3.b.a;
					return ' (' + ($elm$core$String$fromFloat(min) + (' - ' + ($elm$core$String$fromFloat(max) + ')')));
				} else {
					var min = _v3.a.a;
					var _v4 = _v3.b;
					return ' (min: ' + ($elm$core$String$fromFloat(min) + ')');
				}
			} else {
				if (_v3.b.$ === 'Just') {
					var _v5 = _v3.a;
					var max = _v3.b.a;
					return ' (max: ' + ($elm$core$String$fromFloat(max) + ')');
				} else {
					var _v6 = _v3.a;
					var _v7 = _v3.b;
					return '';
				}
			}
		}();
		var isRequired = A2($elm$core$List$member, param.key, model.requiredFields);
		var labelText = _Utils_ap(
			$author$project$Audio$formatParameterName(param.key),
			isRequired ? ' *' : '');
		var isDisabled = model.isGenerating;
		var fullDescription = function () {
			var _v2 = param.description;
			if (_v2.$ === 'Just') {
				var desc = _v2.a;
				return _Utils_ap(desc, rangeText);
			} else {
				return (rangeText !== '') ? $elm$core$String$trim(rangeText) : '';
			}
		}();
		var defaultHint = function () {
			var _v1 = param._default;
			if (_v1.$ === 'Just') {
				var def = _v1.a;
				return (fullDescription !== '') ? (fullDescription + (' (default: ' + (def + ')'))) : ('default: ' + def);
			} else {
				return fullDescription;
			}
		}();
		return A2(
			$elm$html$Html$div,
			_List_fromArray(
				[
					$elm$html$Html$Attributes$class('parameter-field')
				]),
			_List_fromArray(
				[
					A2(
					$elm$html$Html$label,
					_List_fromArray(
						[
							$elm$html$Html$Attributes$class('parameter-label')
						]),
					_List_fromArray(
						[
							$elm$html$Html$text(labelText),
							(defaultHint !== '') ? A2(
							$elm$html$Html$span,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$class('parameter-hint')
								]),
							_List_fromArray(
								[
									$elm$html$Html$text(' — ' + defaultHint)
								])) : $elm$html$Html$text('')
						])),
					function () {
					var _v0 = param._enum;
					if (_v0.$ === 'Just') {
						var options = _v0.a;
						return A2(
							$elm$html$Html$select,
							_List_fromArray(
								[
									$elm$html$Html$Events$onInput(
									$author$project$Audio$UpdateParameter(param.key)),
									$elm$html$Html$Attributes$disabled(isDisabled),
									$elm$html$Html$Attributes$class('parameter-select'),
									$elm$html$Html$Attributes$value(param.value)
								]),
							A2(
								$elm$core$List$cons,
								A2(
									$elm$html$Html$option,
									_List_fromArray(
										[
											$elm$html$Html$Attributes$value('')
										]),
									_List_fromArray(
										[
											$elm$html$Html$text('-- Select --')
										])),
								A2(
									$elm$core$List$map,
									function (opt) {
										return A2(
											$elm$html$Html$option,
											_List_fromArray(
												[
													$elm$html$Html$Attributes$value(opt)
												]),
											_List_fromArray(
												[
													$elm$html$Html$text(opt)
												]));
									},
									options)));
					} else {
						return (param.key === 'prompt') ? A2(
							$elm$html$Html$textarea,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$placeholder(
									A2($elm$core$Maybe$withDefault, 'Enter prompt...', param._default)),
									$elm$html$Html$Attributes$value(param.value),
									$elm$html$Html$Events$onInput(
									$author$project$Audio$UpdateParameter(param.key)),
									$elm$html$Html$Attributes$disabled(isDisabled),
									$elm$html$Html$Attributes$class('parameter-input parameter-textarea')
								]),
							_List_Nil) : A2(
							$elm$html$Html$input,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$type_(
									((param.paramType === 'number') || (param.paramType === 'integer')) ? 'number' : 'text'),
									$elm$html$Html$Attributes$placeholder(
									A2($elm$core$Maybe$withDefault, 'Enter ' + (param.key + '...'), param._default)),
									$elm$html$Html$Attributes$value(param.value),
									$elm$html$Html$Events$onInput(
									$author$project$Audio$UpdateParameter(param.key)),
									$elm$html$Html$Attributes$disabled(isDisabled),
									$elm$html$Html$Attributes$class('parameter-input')
								]),
							_List_Nil);
					}
				}()
				]));
	});
var $author$project$Audio$view = function (model) {
	return A2(
		$elm$html$Html$div,
		_List_fromArray(
			[
				$elm$html$Html$Attributes$class('audio-page')
			]),
		_List_fromArray(
			[
				A2(
				$elm$html$Html$h1,
				_List_Nil,
				_List_fromArray(
					[
						$elm$html$Html$text('Audio Models Explorer')
					])),
				A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('search-section')
					]),
				_List_fromArray(
					[
						A2(
						$elm$html$Html$input,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$type_('text'),
								$elm$html$Html$Attributes$placeholder('Search audio models...'),
								$elm$html$Html$Attributes$value(model.searchQuery),
								$elm$html$Html$Events$onInput($author$project$Audio$UpdateSearch)
							]),
						_List_Nil),
						A2(
						$elm$html$Html$button,
						_List_fromArray(
							[
								$elm$html$Html$Events$onClick($author$project$Audio$FetchModels),
								$elm$html$Html$Attributes$disabled(
								!_Utils_eq(model.models, _List_Nil))
							]),
						_List_fromArray(
							[
								$elm$html$Html$text(
								_Utils_eq(model.models, _List_Nil) ? 'Loading...' : 'Refresh Models')
							]))
					])),
				$elm$core$List$isEmpty(model.models) ? A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('loading-text')
					]),
				_List_fromArray(
					[
						$elm$html$Html$text('Loading models...')
					])) : A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('models-list')
					]),
				A2(
					$elm$core$List$map,
					$author$project$Audio$viewModelOption,
					A2(
						$elm$core$List$filter,
						function (m) {
							return A2(
								$elm$core$String$contains,
								$elm$core$String$toLower(model.searchQuery),
								$elm$core$String$toLower(m.name));
						},
						model.models))),
				function () {
				var _v0 = model.selectedModel;
				if (_v0.$ === 'Just') {
					var selected = _v0.a;
					return A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('selected-model'),
								$elm$html$Html$Attributes$id('selected-model-section')
							]),
						_List_fromArray(
							[
								A2(
								$elm$html$Html$h2,
								_List_Nil,
								_List_fromArray(
									[
										$elm$html$Html$text(selected.name)
									])),
								A2(
								$elm$html$Html$p,
								_List_Nil,
								_List_fromArray(
									[
										$elm$html$Html$text(selected.description)
									])),
								A2(
								$elm$html$Html$div,
								_List_fromArray(
									[
										$elm$html$Html$Attributes$class('parameters-form-grid')
									]),
								A2(
									$elm$core$List$map,
									$author$project$Audio$viewParameter(model),
									model.parameters)),
								A2(
								$elm$html$Html$button,
								_List_fromArray(
									[
										$elm$html$Html$Events$onClick($author$project$Audio$GenerateAudio),
										$elm$html$Html$Attributes$disabled(
										A2($author$project$Audio$hasEmptyRequiredParameters, model.parameters, model.requiredFields) || model.isGenerating),
										$elm$html$Html$Attributes$class('generate-button')
									]),
								_List_fromArray(
									[
										$elm$html$Html$text(
										model.isGenerating ? 'Generating...' : 'Generate Audio')
									]))
							]));
				} else {
					return (!$elm$core$List$isEmpty(model.models)) ? A2(
						$elm$html$Html$div,
						_List_Nil,
						_List_fromArray(
							[
								$elm$html$Html$text('Select a model from the list above')
							])) : $elm$html$Html$text('');
				}
			}(),
				function () {
				var _v1 = model.outputAudio;
				if (_v1.$ === 'Just') {
					var url = _v1.a;
					return A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('audio-output')
							]),
						_List_fromArray(
							[
								A3(
								$elm$html$Html$node,
								'audio',
								_List_fromArray(
									[
										$elm$html$Html$Attributes$src(url),
										$elm$html$Html$Attributes$controls(true),
										A2($elm$html$Html$Attributes$attribute, 'style', 'width: 100%; max-width: 600px;')
									]),
								_List_Nil)
							]));
				} else {
					return $elm$html$Html$text('');
				}
			}(),
				function () {
				var _v2 = model.error;
				if (_v2.$ === 'Just') {
					var err = _v2.a;
					return A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('error')
							]),
						_List_fromArray(
							[
								$elm$html$Html$text(err)
							]));
				} else {
					return $elm$html$Html$text('');
				}
			}()
			]));
};
var $elm$html$Html$a = _VirtualDom_node('a');
var $elm$html$Html$Attributes$download = function (fileName) {
	return A2($elm$html$Html$Attributes$stringProperty, 'download', fileName);
};
var $author$project$AudioDetail$extractErrorMessage = function (audioRecord) {
	var _v0 = audioRecord.metadata;
	if (_v0.$ === 'Just') {
		var metadataValue = _v0.a;
		return $elm$core$Result$toMaybe(
			A2(
				$elm$json$Json$Decode$decodeValue,
				A2($elm$json$Json$Decode$field, 'error', $elm$json$Json$Decode$string),
				metadataValue));
	} else {
		return $elm$core$Maybe$Nothing;
	}
};
var $author$project$AudioDetail$formatDuration = function (seconds) {
	var mins = $elm$core$Basics$floor(seconds / 60);
	var secs = $elm$core$Basics$floor(seconds) - (mins * 60);
	var secsStr = (secs < 10) ? ('0' + $elm$core$String$fromInt(secs)) : $elm$core$String$fromInt(secs);
	return $elm$core$String$fromInt(mins) + (':' + secsStr);
};
var $elm$html$Html$Attributes$href = function (url) {
	return A2(
		$elm$html$Html$Attributes$stringProperty,
		'href',
		_VirtualDom_noJavaScriptUri(url));
};
var $author$project$AudioDetail$statusText = function (status) {
	switch (status) {
		case 'processing':
			return '⏳ Processing...';
		case 'completed':
			return '✅ Completed';
		case 'failed':
			return '❌ Failed';
		case 'canceled':
			return '🚫 Canceled';
		default:
			return status;
	}
};
var $author$project$AudioDetail$viewAudioDetail = function (audio) {
	return A2(
		$elm$html$Html$div,
		_List_fromArray(
			[
				$elm$html$Html$Attributes$class('audio-detail')
			]),
		_List_fromArray(
			[
				A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('audio-info')
					]),
				_List_fromArray(
					[
						A2(
						$elm$html$Html$h2,
						_List_Nil,
						_List_fromArray(
							[
								$elm$html$Html$text('Audio Details')
							])),
						A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('info-row')
							]),
						_List_fromArray(
							[
								A2(
								$elm$html$Html$span,
								_List_fromArray(
									[
										$elm$html$Html$Attributes$class('label')
									]),
								_List_fromArray(
									[
										$elm$html$Html$text('Status: ')
									])),
								A2(
								$elm$html$Html$span,
								_List_fromArray(
									[
										$elm$html$Html$Attributes$class(
										'status status-' + $elm$core$String$toLower(audio.status))
									]),
								_List_fromArray(
									[
										$elm$html$Html$text(
										$author$project$AudioDetail$statusText(audio.status))
									]))
							])),
						A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('info-row')
							]),
						_List_fromArray(
							[
								A2(
								$elm$html$Html$span,
								_List_fromArray(
									[
										$elm$html$Html$Attributes$class('label')
									]),
								_List_fromArray(
									[
										$elm$html$Html$text('Model: ')
									])),
								A2(
								$elm$html$Html$span,
								_List_Nil,
								_List_fromArray(
									[
										$elm$html$Html$text(audio.modelId)
									]))
							])),
						A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('info-row')
							]),
						_List_fromArray(
							[
								A2(
								$elm$html$Html$span,
								_List_fromArray(
									[
										$elm$html$Html$Attributes$class('label')
									]),
								_List_fromArray(
									[
										$elm$html$Html$text('Prompt: ')
									])),
								A2(
								$elm$html$Html$p,
								_List_fromArray(
									[
										$elm$html$Html$Attributes$class('prompt')
									]),
								_List_fromArray(
									[
										$elm$html$Html$text(audio.prompt)
									]))
							])),
						function () {
						var _v0 = audio.duration;
						if (_v0.$ === 'Just') {
							var dur = _v0.a;
							return A2(
								$elm$html$Html$div,
								_List_fromArray(
									[
										$elm$html$Html$Attributes$class('info-row')
									]),
								_List_fromArray(
									[
										A2(
										$elm$html$Html$span,
										_List_fromArray(
											[
												$elm$html$Html$Attributes$class('label')
											]),
										_List_fromArray(
											[
												$elm$html$Html$text('Duration: ')
											])),
										A2(
										$elm$html$Html$span,
										_List_Nil,
										_List_fromArray(
											[
												$elm$html$Html$text(
												$author$project$AudioDetail$formatDuration(dur))
											]))
									]));
						} else {
							return $elm$html$Html$text('');
						}
					}(),
						A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('info-row')
							]),
						_List_fromArray(
							[
								A2(
								$elm$html$Html$span,
								_List_fromArray(
									[
										$elm$html$Html$Attributes$class('label')
									]),
								_List_fromArray(
									[
										$elm$html$Html$text('Created: ')
									])),
								A2(
								$elm$html$Html$span,
								_List_Nil,
								_List_fromArray(
									[
										$elm$html$Html$text(audio.createdAt)
									]))
							]))
					])),
				function () {
				var _v1 = audio.status;
				switch (_v1) {
					case 'completed':
						return $elm$core$String$isEmpty(audio.audioUrl) ? A2(
							$elm$html$Html$div,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$class('error')
								]),
							_List_fromArray(
								[
									$elm$html$Html$text('Audio completed but no URL available')
								])) : A2(
							$elm$html$Html$div,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$class('audio-viewer')
								]),
							_List_fromArray(
								[
									A2(
									$elm$html$Html$h3,
									_List_Nil,
									_List_fromArray(
										[
											$elm$html$Html$text('Generated Audio')
										])),
									A3(
									$elm$html$Html$node,
									'audio',
									_List_fromArray(
										[
											$elm$html$Html$Attributes$src(audio.audioUrl),
											$elm$html$Html$Attributes$controls(true),
											A2($elm$html$Html$Attributes$attribute, 'style', 'width: 100%; max-width: 600px;')
										]),
									_List_Nil),
									A2(
									$elm$html$Html$div,
									_List_fromArray(
										[
											$elm$html$Html$Attributes$class('audio-actions')
										]),
									_List_fromArray(
										[
											A2(
											$elm$html$Html$a,
											_List_fromArray(
												[
													$elm$html$Html$Attributes$href(audio.audioUrl),
													$elm$html$Html$Attributes$download(''),
													$elm$html$Html$Attributes$class('download-button')
												]),
											_List_fromArray(
												[
													$elm$html$Html$text('Download Audio')
												]))
										]))
								]));
					case 'processing':
						return A2(
							$elm$html$Html$div,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$class('processing')
								]),
							_List_fromArray(
								[
									A2(
									$elm$html$Html$div,
									_List_fromArray(
										[
											$elm$html$Html$Attributes$class('spinner')
										]),
									_List_Nil),
									A2(
									$elm$html$Html$p,
									_List_Nil,
									_List_fromArray(
										[
											$elm$html$Html$text('Your audio is being generated... This may take 30-60 seconds.')
										]))
								]));
					case 'failed':
						return A2(
							$elm$html$Html$div,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$class('error')
								]),
							_List_fromArray(
								[
									$elm$html$Html$text(
									function () {
										var _v2 = $author$project$AudioDetail$extractErrorMessage(audio);
										if (_v2.$ === 'Just') {
											var errorMsg = _v2.a;
											return 'Audio generation failed: ' + errorMsg;
										} else {
											return 'Audio generation failed. Please try again with different parameters.';
										}
									}())
								]));
					case 'canceled':
						return A2(
							$elm$html$Html$div,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$class('info')
								]),
							_List_fromArray(
								[
									$elm$html$Html$text('Audio generation was canceled.')
								]));
					default:
						return A2(
							$elm$html$Html$div,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$class('info')
								]),
							_List_fromArray(
								[
									$elm$html$Html$text('Status: ' + audio.status)
								]));
				}
			}()
			]));
};
var $author$project$AudioDetail$view = function (model) {
	return A2(
		$elm$html$Html$div,
		_List_fromArray(
			[
				$elm$html$Html$Attributes$class('audio-detail-page')
			]),
		_List_fromArray(
			[
				A2(
				$elm$html$Html$h1,
				_List_Nil,
				_List_fromArray(
					[
						$elm$html$Html$text('Audio Generation Status')
					])),
				function () {
				var _v0 = model.error;
				if (_v0.$ === 'Just') {
					var err = _v0.a;
					return A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('error')
							]),
						_List_fromArray(
							[
								$elm$html$Html$text(err)
							]));
				} else {
					return $elm$html$Html$text('');
				}
			}(),
				function () {
				var _v1 = model.audio;
				if (_v1.$ === 'Just') {
					var audio = _v1.a;
					return $author$project$AudioDetail$viewAudioDetail(audio);
				} else {
					return A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('loading')
							]),
						_List_fromArray(
							[
								$elm$html$Html$text('Loading audio information...')
							]));
				}
			}()
			]));
};
var $author$project$AudioGallery$SelectAudio = function (a) {
	return {$: 'SelectAudio', a: a};
};
var $author$project$AudioGallery$extractErrorMessage = function (audioRecord) {
	var _v0 = audioRecord.metadata;
	if (_v0.$ === 'Just') {
		var metadataValue = _v0.a;
		return $elm$core$Result$toMaybe(
			A2(
				$elm$json$Json$Decode$decodeValue,
				A2($elm$json$Json$Decode$field, 'error', $elm$json$Json$Decode$string),
				metadataValue));
	} else {
		return $elm$core$Maybe$Nothing;
	}
};
var $author$project$AudioGallery$formatDate = function (dateStr) {
	return A2($elm$core$String$left, 19, dateStr);
};
var $author$project$AudioGallery$formatDuration = function (seconds) {
	var mins = $elm$core$Basics$floor(seconds / 60);
	var secs = $elm$core$Basics$floor(seconds) - (mins * 60);
	var secsStr = (secs < 10) ? ('0' + $elm$core$String$fromInt(secs)) : $elm$core$String$fromInt(secs);
	return $elm$core$String$fromInt(mins) + (':' + secsStr);
};
var $elm$core$String$toUpper = _String_toUpper;
var $author$project$AudioGallery$truncateString = F2(
	function (maxLength, str) {
		return (_Utils_cmp(
			$elm$core$String$length(str),
			maxLength) < 1) ? str : (A2($elm$core$String$left, maxLength - 3, str) + '...');
	});
var $author$project$AudioGallery$viewAudioCard = function (audioRecord) {
	var errorMessage = $author$project$AudioGallery$extractErrorMessage(audioRecord);
	return A2(
		$elm$html$Html$div,
		_List_fromArray(
			[
				$elm$html$Html$Attributes$class('audio-card'),
				$elm$html$Html$Events$onClick(
				$author$project$AudioGallery$SelectAudio(audioRecord))
			]),
		_List_fromArray(
			[
				A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('audio-thumbnail')
					]),
				_List_fromArray(
					[
						$elm$core$String$isEmpty(audioRecord.audioUrl) ? A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								A2($elm$html$Html$Attributes$style, 'width', '100%'),
								A2($elm$html$Html$Attributes$style, 'height', '100%'),
								A2($elm$html$Html$Attributes$style, 'display', 'flex'),
								A2($elm$html$Html$Attributes$style, 'flex-direction', 'column'),
								A2($elm$html$Html$Attributes$style, 'align-items', 'center'),
								A2($elm$html$Html$Attributes$style, 'justify-content', 'center'),
								A2(
								$elm$html$Html$Attributes$style,
								'background',
								(audioRecord.status === 'failed') ? '#c33' : '#333'),
								A2($elm$html$Html$Attributes$style, 'color', '#fff'),
								A2($elm$html$Html$Attributes$style, 'padding', '10px')
							]),
						_List_fromArray(
							[
								A2(
								$elm$html$Html$div,
								_List_fromArray(
									[
										A2($elm$html$Html$Attributes$style, 'font-weight', 'bold'),
										A2($elm$html$Html$Attributes$style, 'margin-bottom', '5px')
									]),
								_List_fromArray(
									[
										$elm$html$Html$text(
										$elm$core$String$toUpper(audioRecord.status))
									])),
								function () {
								if (errorMessage.$ === 'Just') {
									var err = errorMessage.a;
									return A2(
										$elm$html$Html$div,
										_List_fromArray(
											[
												A2($elm$html$Html$Attributes$style, 'font-size', '12px'),
												A2($elm$html$Html$Attributes$style, 'text-align', 'center')
											]),
										_List_fromArray(
											[
												$elm$html$Html$text(
												A2($author$project$AudioGallery$truncateString, 60, err))
											]));
								} else {
									return $elm$html$Html$text('');
								}
							}()
							])) : A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								A2($elm$html$Html$Attributes$style, 'width', '100%'),
								A2($elm$html$Html$Attributes$style, 'height', '100%'),
								A2($elm$html$Html$Attributes$style, 'display', 'flex'),
								A2($elm$html$Html$Attributes$style, 'flex-direction', 'column'),
								A2($elm$html$Html$Attributes$style, 'align-items', 'center'),
								A2($elm$html$Html$Attributes$style, 'justify-content', 'center'),
								A2($elm$html$Html$Attributes$style, 'background', 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'),
								A2($elm$html$Html$Attributes$style, 'color', '#fff'),
								A2($elm$html$Html$Attributes$style, 'padding', '20px')
							]),
						_List_fromArray(
							[
								A2(
								$elm$html$Html$div,
								_List_fromArray(
									[
										A2($elm$html$Html$Attributes$style, 'font-size', '48px'),
										A2($elm$html$Html$Attributes$style, 'margin-bottom', '10px')
									]),
								_List_fromArray(
									[
										$elm$html$Html$text('♪')
									])),
								function () {
								var _v1 = audioRecord.duration;
								if (_v1.$ === 'Just') {
									var dur = _v1.a;
									return A2(
										$elm$html$Html$div,
										_List_fromArray(
											[
												A2($elm$html$Html$Attributes$style, 'font-size', '14px')
											]),
										_List_fromArray(
											[
												$elm$html$Html$text(
												$author$project$AudioGallery$formatDuration(dur))
											]));
								} else {
									return $elm$html$Html$text('');
								}
							}()
							]))
					])),
				A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('audio-card-info')
					]),
				_List_fromArray(
					[
						A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('audio-prompt')
							]),
						_List_fromArray(
							[
								$elm$html$Html$text(audioRecord.prompt)
							])),
						A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('audio-meta')
							]),
						_List_fromArray(
							[
								A2(
								$elm$html$Html$span,
								_List_fromArray(
									[
										$elm$html$Html$Attributes$class('audio-model')
									]),
								_List_fromArray(
									[
										$elm$html$Html$text(audioRecord.modelId)
									])),
								A2(
								$elm$html$Html$span,
								_List_fromArray(
									[
										$elm$html$Html$Attributes$class('audio-date')
									]),
								_List_fromArray(
									[
										$elm$html$Html$text(
										$author$project$AudioGallery$formatDate(audioRecord.createdAt))
									]))
							]))
					]))
			]));
};
var $author$project$AudioGallery$CloseAudio = {$: 'CloseAudio'};
var $author$project$AudioGallery$ToggleRawData = {$: 'ToggleRawData'};
var $author$project$AudioGallery$NoOp = {$: 'NoOp'};
var $author$project$AudioGallery$onClickNoBubble = A2(
	$elm$html$Html$Events$stopPropagationOn,
	'click',
	$elm$json$Json$Decode$succeed(
		_Utils_Tuple2($author$project$AudioGallery$NoOp, true)));
var $elm$html$Html$strong = _VirtualDom_node('strong');
var $elm$html$Html$h4 = _VirtualDom_node('h4');
var $elm$core$Result$map = F2(
	function (func, ra) {
		if (ra.$ === 'Ok') {
			var a = ra.a;
			return $elm$core$Result$Ok(
				func(a));
		} else {
			var e = ra.a;
			return $elm$core$Result$Err(e);
		}
	});
var $elm$html$Html$pre = _VirtualDom_node('pre');
var $author$project$AudioGallery$viewRawDataField = F2(
	function (label, maybeValue) {
		if (maybeValue.$ === 'Just') {
			var value = maybeValue.a;
			return A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('raw-data-field')
					]),
				_List_fromArray(
					[
						A2(
						$elm$html$Html$h4,
						_List_Nil,
						_List_fromArray(
							[
								$elm$html$Html$text(label)
							])),
						A2(
						$elm$html$Html$pre,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('raw-json')
							]),
						_List_fromArray(
							[
								$elm$html$Html$text(
								A2(
									$elm$core$Result$withDefault,
									'Invalid JSON',
									A2(
										$elm$core$Result$map,
										$elm$json$Json$Encode$encode(2),
										A2($elm$json$Json$Decode$decodeValue, $elm$json$Json$Decode$value, value))))
							]))
					]));
		} else {
			return $elm$html$Html$text('');
		}
	});
var $author$project$AudioGallery$viewAudioModal = F2(
	function (model, audioRecord) {
		var errorMessage = $author$project$AudioGallery$extractErrorMessage(audioRecord);
		return A2(
			$elm$html$Html$div,
			_List_fromArray(
				[
					$elm$html$Html$Attributes$class('modal-overlay'),
					$elm$html$Html$Events$onClick($author$project$AudioGallery$CloseAudio)
				]),
			_List_fromArray(
				[
					A2(
					$elm$html$Html$div,
					_List_fromArray(
						[
							$elm$html$Html$Attributes$class('modal-content'),
							$author$project$AudioGallery$onClickNoBubble
						]),
					_List_fromArray(
						[
							A2(
							$elm$html$Html$button,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$class('modal-close'),
									$elm$html$Html$Events$onClick($author$project$AudioGallery$CloseAudio)
								]),
							_List_fromArray(
								[
									$elm$html$Html$text('×')
								])),
							A2(
							$elm$html$Html$h2,
							_List_Nil,
							_List_fromArray(
								[
									$elm$html$Html$text('Generated Audio')
								])),
							function () {
							if (errorMessage.$ === 'Just') {
								var err = errorMessage.a;
								return A2(
									$elm$html$Html$div,
									_List_fromArray(
										[
											A2($elm$html$Html$Attributes$style, 'background', '#fee'),
											A2($elm$html$Html$Attributes$style, 'color', '#c33'),
											A2($elm$html$Html$Attributes$style, 'padding', '15px'),
											A2($elm$html$Html$Attributes$style, 'border-radius', '4px'),
											A2($elm$html$Html$Attributes$style, 'margin-bottom', '15px'),
											A2($elm$html$Html$Attributes$style, 'border', '1px solid #fcc')
										]),
									_List_fromArray(
										[
											A2(
											$elm$html$Html$strong,
											_List_Nil,
											_List_fromArray(
												[
													$elm$html$Html$text('Error: ')
												])),
											$elm$html$Html$text(err)
										]));
							} else {
								return $elm$html$Html$text('');
							}
						}(),
							(!$elm$core$String$isEmpty(audioRecord.audioUrl)) ? A2(
							$elm$html$Html$div,
							_List_fromArray(
								[
									A2($elm$html$Html$Attributes$style, 'margin-bottom', '20px')
								]),
							_List_fromArray(
								[
									A3(
									$elm$html$Html$node,
									'audio',
									_List_fromArray(
										[
											$elm$html$Html$Attributes$src(audioRecord.audioUrl),
											$elm$html$Html$Attributes$controls(true),
											A2($elm$html$Html$Attributes$attribute, 'style', 'width: 100%; max-width: 600px;'),
											$elm$html$Html$Attributes$class('modal-audio')
										]),
									_List_Nil)
								])) : A2(
							$elm$html$Html$div,
							_List_fromArray(
								[
									A2($elm$html$Html$Attributes$style, 'background', '#333'),
									A2($elm$html$Html$Attributes$style, 'color', '#fff'),
									A2($elm$html$Html$Attributes$style, 'padding', '40px'),
									A2($elm$html$Html$Attributes$style, 'text-align', 'center'),
									A2($elm$html$Html$Attributes$style, 'border-radius', '4px'),
									A2($elm$html$Html$Attributes$style, 'margin-bottom', '15px')
								]),
							_List_fromArray(
								[
									$elm$html$Html$text(
									'Audio ' + $elm$core$String$toUpper(audioRecord.status))
								])),
							A2(
							$elm$html$Html$div,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$class('modal-details')
								]),
							_List_fromArray(
								[
									A2(
									$elm$html$Html$div,
									_List_fromArray(
										[
											$elm$html$Html$Attributes$class('detail-row')
										]),
									_List_fromArray(
										[
											A2(
											$elm$html$Html$strong,
											_List_Nil,
											_List_fromArray(
												[
													$elm$html$Html$text('Prompt: ')
												])),
											$elm$html$Html$text(audioRecord.prompt)
										])),
									A2(
									$elm$html$Html$div,
									_List_fromArray(
										[
											$elm$html$Html$Attributes$class('detail-row')
										]),
									_List_fromArray(
										[
											A2(
											$elm$html$Html$strong,
											_List_Nil,
											_List_fromArray(
												[
													$elm$html$Html$text('Model: ')
												])),
											$elm$html$Html$text(audioRecord.modelId)
										])),
									function () {
									var _v1 = audioRecord.collection;
									if (_v1.$ === 'Just') {
										var coll = _v1.a;
										return A2(
											$elm$html$Html$div,
											_List_fromArray(
												[
													$elm$html$Html$Attributes$class('detail-row')
												]),
											_List_fromArray(
												[
													A2(
													$elm$html$Html$strong,
													_List_Nil,
													_List_fromArray(
														[
															$elm$html$Html$text('Collection: ')
														])),
													$elm$html$Html$text(coll)
												]));
									} else {
										return $elm$html$Html$text('');
									}
								}(),
									function () {
									var _v2 = audioRecord.duration;
									if (_v2.$ === 'Just') {
										var dur = _v2.a;
										return A2(
											$elm$html$Html$div,
											_List_fromArray(
												[
													$elm$html$Html$Attributes$class('detail-row')
												]),
											_List_fromArray(
												[
													A2(
													$elm$html$Html$strong,
													_List_Nil,
													_List_fromArray(
														[
															$elm$html$Html$text('Duration: ')
														])),
													$elm$html$Html$text(
													$author$project$AudioGallery$formatDuration(dur))
												]));
									} else {
										return $elm$html$Html$text('');
									}
								}(),
									A2(
									$elm$html$Html$div,
									_List_fromArray(
										[
											$elm$html$Html$Attributes$class('detail-row')
										]),
									_List_fromArray(
										[
											A2(
											$elm$html$Html$strong,
											_List_Nil,
											_List_fromArray(
												[
													$elm$html$Html$text('Created: ')
												])),
											$elm$html$Html$text(audioRecord.createdAt)
										])),
									A2(
									$elm$html$Html$div,
									_List_fromArray(
										[
											$elm$html$Html$Attributes$class('detail-row')
										]),
									_List_fromArray(
										[
											A2(
											$elm$html$Html$strong,
											_List_Nil,
											_List_fromArray(
												[
													$elm$html$Html$text('Status: ')
												])),
											A2(
											$elm$html$Html$span,
											_List_fromArray(
												[
													A2(
													$elm$html$Html$Attributes$style,
													'color',
													(audioRecord.status === 'failed') ? '#c33' : 'inherit'),
													A2(
													$elm$html$Html$Attributes$style,
													'font-weight',
													(audioRecord.status === 'failed') ? 'bold' : 'normal')
												]),
											_List_fromArray(
												[
													$elm$html$Html$text(audioRecord.status)
												]))
										]))
								])),
							A2(
							$elm$html$Html$div,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$class('raw-data-section')
								]),
							_List_fromArray(
								[
									A2(
									$elm$html$Html$button,
									_List_fromArray(
										[
											$elm$html$Html$Events$onClick($author$project$AudioGallery$ToggleRawData),
											$elm$html$Html$Attributes$class('toggle-raw-data')
										]),
									_List_fromArray(
										[
											$elm$html$Html$text(
											model.showRawData ? '▼ Hide Raw Data' : '▶ Show Raw Data')
										])),
									model.showRawData ? A2(
									$elm$html$Html$div,
									_List_fromArray(
										[
											$elm$html$Html$Attributes$class('raw-data-content')
										]),
									_List_fromArray(
										[
											A2($author$project$AudioGallery$viewRawDataField, 'Parameters', audioRecord.parameters),
											A2($author$project$AudioGallery$viewRawDataField, 'Metadata', audioRecord.metadata)
										])) : $elm$html$Html$text('')
								]))
						]))
				]));
	});
var $author$project$AudioGallery$view = function (model) {
	return A2(
		$elm$html$Html$div,
		_List_fromArray(
			[
				$elm$html$Html$Attributes$class('audio-gallery-page')
			]),
		_List_fromArray(
			[
				A2(
				$elm$html$Html$h1,
				_List_Nil,
				_List_fromArray(
					[
						$elm$html$Html$text('Generated Audio')
					])),
				A2(
				$elm$html$Html$button,
				_List_fromArray(
					[
						$elm$html$Html$Events$onClick($author$project$AudioGallery$FetchAudio),
						$elm$html$Html$Attributes$disabled(model.loading),
						$elm$html$Html$Attributes$class('refresh-button')
					]),
				_List_fromArray(
					[
						$elm$html$Html$text(
						model.loading ? 'Loading...' : 'Refresh')
					])),
				function () {
				var _v0 = model.error;
				if (_v0.$ === 'Just') {
					var err = _v0.a;
					return A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('error')
							]),
						_List_fromArray(
							[
								$elm$html$Html$text(err)
							]));
				} else {
					return $elm$html$Html$text('');
				}
			}(),
				(model.loading && $elm$core$List$isEmpty(model.audio)) ? A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('loading-text')
					]),
				_List_fromArray(
					[
						$elm$html$Html$text('Loading audio...')
					])) : ($elm$core$List$isEmpty(model.audio) ? A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('empty-state')
					]),
				_List_fromArray(
					[
						$elm$html$Html$text('No audio generated yet. Go to the Audio Models page to generate some!')
					])) : A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('audio-grid')
					]),
				A2($elm$core$List$map, $author$project$AudioGallery$viewAudioCard, model.audio))),
				function () {
				var _v1 = model.selectedAudio;
				if (_v1.$ === 'Just') {
					var audio = _v1.a;
					return A2($author$project$AudioGallery$viewAudioModal, model, audio);
				} else {
					return $elm$html$Html$text('');
				}
			}()
			]));
};
var $author$project$BriefGallery$NavigateTo = function (a) {
	return {$: 'NavigateTo', a: a};
};
var $author$project$BriefGallery$NextPage = {$: 'NextPage'};
var $author$project$BriefGallery$PrevPage = {$: 'PrevPage'};
var $elm$html$Html$ul = _VirtualDom_node('ul');
var $author$project$BriefGallery$GenerateFromBrief = function (a) {
	return {$: 'GenerateFromBrief', a: a};
};
var $author$project$BriefGallery$GenerateImageFromBrief = function (a) {
	return {$: 'GenerateImageFromBrief', a: a};
};
var $author$project$BriefGallery$GenerateVideoFromBrief = function (a) {
	return {$: 'GenerateVideoFromBrief', a: a};
};
var $author$project$BriefGallery$SelectBrief = function (a) {
	return {$: 'SelectBrief', a: a};
};
var $author$project$BriefGallery$viewBriefCard = function (brief) {
	return A2(
		$elm$html$Html$div,
		_List_fromArray(
			[
				$elm$html$Html$Attributes$class('brief-card'),
				$elm$html$Html$Events$onClick(
				$author$project$BriefGallery$SelectBrief(brief.id))
			]),
		_List_fromArray(
			[
				A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('brief-header')
					]),
				_List_fromArray(
					[
						A2(
						$elm$html$Html$h3,
						_List_Nil,
						_List_fromArray(
							[
								$elm$html$Html$text(
								A2($elm$core$Maybe$withDefault, 'Untitled Brief', brief.promptText))
							])),
						A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('brief-meta')
							]),
						_List_fromArray(
							[
								$elm$html$Html$text(
								'Scenes: ' + $elm$core$String$fromInt(
									$elm$core$List$length(brief.scenes))),
								function () {
								var _v0 = brief.confidenceScore;
								if (_v0.$ === 'Just') {
									var score = _v0.a;
									return $elm$html$Html$text(
										' | Confidence: ' + $elm$core$String$fromFloat(score));
								} else {
									return $elm$html$Html$text('');
								}
							}()
							]))
					])),
				A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('brief-preview')
					]),
				_List_fromArray(
					[
						function () {
						var _v1 = $elm$core$List$head(brief.scenes);
						if (_v1.$ === 'Just') {
							var firstScene = _v1.a;
							return A2(
								$elm$html$Html$div,
								_List_fromArray(
									[
										$elm$html$Html$Attributes$class('scene-preview')
									]),
								_List_fromArray(
									[
										$elm$html$Html$text(
										'First scene: ' + (firstScene.purpose + (' (' + ($elm$core$String$fromFloat(firstScene.duration) + 's)'))))
									]));
						} else {
							return $elm$html$Html$text('No scenes');
						}
					}()
					])),
				A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('brief-actions')
					]),
				_List_fromArray(
					[
						A2(
						$elm$html$Html$button,
						_List_fromArray(
							[
								$elm$html$Html$Events$onClick(
								$author$project$BriefGallery$GenerateFromBrief(brief.id)),
								$elm$html$Html$Attributes$class('generate-btn')
							]),
						_List_fromArray(
							[
								$elm$html$Html$text('Generate Scene')
							])),
						A2(
						$elm$html$Html$button,
						_List_fromArray(
							[
								$elm$html$Html$Events$onClick(
								$author$project$BriefGallery$GenerateImageFromBrief(brief.id)),
								$elm$html$Html$Attributes$class('generate-btn')
							]),
						_List_fromArray(
							[
								$elm$html$Html$text('Generate Image')
							])),
						A2(
						$elm$html$Html$button,
						_List_fromArray(
							[
								$elm$html$Html$Events$onClick(
								$author$project$BriefGallery$GenerateVideoFromBrief(brief.id)),
								$elm$html$Html$Attributes$class('generate-btn')
							]),
						_List_fromArray(
							[
								$elm$html$Html$text('Generate Video')
							]))
					]))
			]));
};
var $author$project$BriefGallery$view = function (model) {
	return A2(
		$elm$html$Html$div,
		_List_fromArray(
			[
				A2($elm$html$Html$Attributes$style, 'padding', '20px'),
				A2($elm$html$Html$Attributes$style, 'max-width', '800px'),
				A2($elm$html$Html$Attributes$style, 'margin', '0 auto')
			]),
		_List_fromArray(
			[
				A2(
				$elm$html$Html$h2,
				_List_Nil,
				_List_fromArray(
					[
						$elm$html$Html$text('Brief Gallery')
					])),
				model.isLoading ? A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						A2($elm$html$Html$Attributes$style, 'text-align', 'center'),
						A2($elm$html$Html$Attributes$style, 'color', '#666')
					]),
				_List_fromArray(
					[
						$elm$html$Html$text('Loading briefs...')
					])) : A2(
				$elm$html$Html$div,
				_List_Nil,
				_List_fromArray(
					[
						A2(
						$elm$html$Html$button,
						_List_fromArray(
							[
								$elm$html$Html$Events$onClick(
								$author$project$BriefGallery$NavigateTo($author$project$Route$CreativeBriefEditor)),
								A2($elm$html$Html$Attributes$style, 'background-color', '#4CAF50'),
								A2($elm$html$Html$Attributes$style, 'color', 'white'),
								A2($elm$html$Html$Attributes$style, 'padding', '10px 16px'),
								A2($elm$html$Html$Attributes$style, 'border', 'none'),
								A2($elm$html$Html$Attributes$style, 'border-radius', '4px'),
								A2($elm$html$Html$Attributes$style, 'margin-bottom', '10px')
							]),
						_List_fromArray(
							[
								$elm$html$Html$text('New Brief')
							])),
						A2(
						$elm$html$Html$ul,
						_List_fromArray(
							[
								A2($elm$html$Html$Attributes$style, 'list-style', 'none'),
								A2($elm$html$Html$Attributes$style, 'padding', '0')
							]),
						A2($elm$core$List$map, $author$project$BriefGallery$viewBriefCard, model.briefs)),
						A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								A2($elm$html$Html$Attributes$style, 'margin-top', '20px'),
								A2($elm$html$Html$Attributes$style, 'display', 'flex'),
								A2($elm$html$Html$Attributes$style, 'justify-content', 'space-between')
							]),
						_List_fromArray(
							[
								A2(
								$elm$html$Html$button,
								_List_fromArray(
									[
										$elm$html$Html$Events$onClick($author$project$BriefGallery$PrevPage),
										A2($elm$html$Html$Attributes$style, 'padding', '10px 16px'),
										A2($elm$html$Html$Attributes$style, 'border', '1px solid #ccc'),
										A2($elm$html$Html$Attributes$style, 'border-radius', '4px')
									]),
								_List_fromArray(
									[
										$elm$html$Html$text('Previous')
									])),
								A2(
								$elm$html$Html$p,
								_List_Nil,
								_List_fromArray(
									[
										$elm$html$Html$text(
										'Page ' + $elm$core$String$fromInt(model.currentPage))
									])),
								A2(
								$elm$html$Html$button,
								_List_fromArray(
									[
										$elm$html$Html$Events$onClick($author$project$BriefGallery$NextPage),
										A2($elm$html$Html$Attributes$style, 'padding', '10px 16px'),
										A2($elm$html$Html$Attributes$style, 'border', '1px solid #ccc'),
										A2($elm$html$Html$Attributes$style, 'border-radius', '4px')
									]),
								_List_fromArray(
									[
										$elm$html$Html$text('Next')
									]))
							]))
					])),
				function () {
				var _v0 = model.error;
				if (_v0.$ === 'Just') {
					var err = _v0.a;
					return A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								A2($elm$html$Html$Attributes$style, 'color', 'red'),
								A2($elm$html$Html$Attributes$style, 'margin-top', '10px'),
								A2($elm$html$Html$Attributes$style, 'padding', '10px'),
								A2($elm$html$Html$Attributes$style, 'background', '#ffebee'),
								A2($elm$html$Html$Attributes$style, 'border-radius', '4px')
							]),
						_List_fromArray(
							[
								$elm$html$Html$text('Error: ' + err)
							]));
				} else {
					return $elm$html$Html$text('');
				}
			}()
			]));
};
var $author$project$CreativeBriefEditor$GenerateImages = {$: 'GenerateImages'};
var $author$project$CreativeBriefEditor$GenerateScene = {$: 'GenerateScene'};
var $author$project$CreativeBriefEditor$GenerateVideo = {$: 'GenerateVideo'};
var $author$project$CreativeBriefEditor$RefineBrief = {$: 'RefineBrief'};
var $author$project$CreativeBriefEditor$SelectImageModel = function (a) {
	return {$: 'SelectImageModel', a: a};
};
var $author$project$CreativeBriefEditor$SubmitBrief = function (a) {
	return {$: 'SubmitBrief', a: a};
};
var $author$project$CreativeBriefEditor$UpdateCategory = function (a) {
	return {$: 'UpdateCategory', a: a};
};
var $author$project$CreativeBriefEditor$UpdateLLMProvider = function (a) {
	return {$: 'UpdateLLMProvider', a: a};
};
var $author$project$CreativeBriefEditor$UpdatePlatform = function (a) {
	return {$: 'UpdatePlatform', a: a};
};
var $author$project$CreativeBriefEditor$UpdateText = function (a) {
	return {$: 'UpdateText', a: a};
};
var $author$project$CreativeBriefEditor$UploadMedia = {$: 'UploadMedia'};
var $elm$html$Html$Attributes$accept = $elm$html$Html$Attributes$stringProperty('accept');
var $elm$html$Html$Attributes$cols = function (n) {
	return A2(
		_VirtualDom_attribute,
		'cols',
		$elm$core$String$fromInt(n));
};
var $elm$file$File$name = _File_name;
var $elm$html$Html$Attributes$rows = function (n) {
	return A2(
		_VirtualDom_attribute,
		'rows',
		$elm$core$String$fromInt(n));
};
var $author$project$CreativeBriefEditor$viewImageModelOption = function (model) {
	return A2(
		$elm$html$Html$option,
		_List_fromArray(
			[
				$elm$html$Html$Attributes$value(model.owner + ('/' + model.name))
			]),
		_List_fromArray(
			[
				$elm$html$Html$text(model.owner + ('/' + model.name))
			]));
};
var $author$project$CreativeBriefEditor$viewScene = function (scene) {
	return A2(
		$elm$html$Html$div,
		_List_fromArray(
			[
				$elm$html$Html$Attributes$class('scene-item')
			]),
		_List_fromArray(
			[
				A2(
				$elm$html$Html$h4,
				_List_Nil,
				_List_fromArray(
					[
						$elm$html$Html$text(
						'Scene ' + ($elm$core$String$fromInt(scene.sceneNumber) + (': ' + scene.purpose)))
					])),
				A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('scene-details')
					]),
				_List_fromArray(
					[
						$elm$html$Html$text(
						'Duration: ' + ($elm$core$String$fromFloat(scene.duration) + 's')),
						function () {
						var _v0 = scene.visual;
						if (_v0.$ === 'Just') {
							var visual = _v0.a;
							var _v1 = visual.generationPrompt;
							if (_v1.$ === 'Just') {
								var prompt = _v1.a;
								return A2(
									$elm$html$Html$div,
									_List_Nil,
									_List_fromArray(
										[
											$elm$html$Html$text('Generation Prompt: '),
											$elm$html$Html$text(prompt)
										]));
							} else {
								return $elm$html$Html$text('');
							}
						} else {
							return $elm$html$Html$text('');
						}
					}()
					]))
			]));
};
var $author$project$CreativeBriefEditor$view = function (model) {
	return A2(
		$elm$html$Html$div,
		_List_fromArray(
			[
				A2($elm$html$Html$Attributes$style, 'padding', '20px'),
				A2($elm$html$Html$Attributes$style, 'max-width', '800px'),
				A2($elm$html$Html$Attributes$style, 'margin', '0 auto')
			]),
		_List_fromArray(
			[
				A2(
				$elm$html$Html$h2,
				_List_Nil,
				_List_fromArray(
					[
						$elm$html$Html$text('Creative Brief Editor')
					])),
				model.isLoading ? A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						A2($elm$html$Html$Attributes$style, 'text-align', 'center'),
						A2($elm$html$Html$Attributes$style, 'color', '#666')
					]),
				_List_fromArray(
					[
						$elm$html$Html$text('Generating brief...')
					])) : A2(
				$elm$html$Html$div,
				_List_Nil,
				_List_fromArray(
					[
						A2(
						$elm$html$Html$form,
						_List_Nil,
						_List_fromArray(
							[
								A2(
								$elm$html$Html$div,
								_List_fromArray(
									[
										A2($elm$html$Html$Attributes$style, 'margin-bottom', '10px')
									]),
								_List_fromArray(
									[
										A2(
										$elm$html$Html$label,
										_List_fromArray(
											[
												A2($elm$html$Html$Attributes$style, 'display', 'block'),
												A2($elm$html$Html$Attributes$style, 'margin-bottom', '5px')
											]),
										_List_fromArray(
											[
												$elm$html$Html$text('Prompt Text')
											])),
										A2(
										$elm$html$Html$textarea,
										_List_fromArray(
											[
												$elm$html$Html$Attributes$placeholder('Enter your creative prompt...'),
												$elm$html$Html$Attributes$rows(5),
												$elm$html$Html$Attributes$cols(50),
												$elm$html$Html$Attributes$value(model.text),
												$elm$html$Html$Events$onInput($author$project$CreativeBriefEditor$UpdateText),
												A2($elm$html$Html$Attributes$style, 'width', '100%'),
												A2($elm$html$Html$Attributes$style, 'padding', '8px'),
												A2($elm$html$Html$Attributes$style, 'border', '1px solid #ccc'),
												A2($elm$html$Html$Attributes$style, 'border-radius', '4px')
											]),
										_List_Nil)
									])),
								A2(
								$elm$html$Html$div,
								_List_fromArray(
									[
										A2($elm$html$Html$Attributes$style, 'display', 'flex'),
										A2($elm$html$Html$Attributes$style, 'gap', '20px'),
										A2($elm$html$Html$Attributes$style, 'margin-bottom', '10px')
									]),
								_List_fromArray(
									[
										A2(
										$elm$html$Html$div,
										_List_Nil,
										_List_fromArray(
											[
												A2(
												$elm$html$Html$label,
												_List_fromArray(
													[
														A2($elm$html$Html$Attributes$style, 'display', 'block'),
														A2($elm$html$Html$Attributes$style, 'margin-bottom', '5px')
													]),
												_List_fromArray(
													[
														$elm$html$Html$text('Platform')
													])),
												A2(
												$elm$html$Html$select,
												_List_fromArray(
													[
														$elm$html$Html$Events$onInput($author$project$CreativeBriefEditor$UpdatePlatform)
													]),
												_List_fromArray(
													[
														A2(
														$elm$html$Html$option,
														_List_fromArray(
															[
																$elm$html$Html$Attributes$value('tiktok')
															]),
														_List_fromArray(
															[
																$elm$html$Html$text('TikTok')
															])),
														A2(
														$elm$html$Html$option,
														_List_fromArray(
															[
																$elm$html$Html$Attributes$value('instagram')
															]),
														_List_fromArray(
															[
																$elm$html$Html$text('Instagram')
															]))
													]))
											])),
										A2(
										$elm$html$Html$div,
										_List_Nil,
										_List_fromArray(
											[
												A2(
												$elm$html$Html$label,
												_List_fromArray(
													[
														A2($elm$html$Html$Attributes$style, 'display', 'block'),
														A2($elm$html$Html$Attributes$style, 'margin-bottom', '5px')
													]),
												_List_fromArray(
													[
														$elm$html$Html$text('Category')
													])),
												A2(
												$elm$html$Html$select,
												_List_fromArray(
													[
														$elm$html$Html$Events$onInput($author$project$CreativeBriefEditor$UpdateCategory)
													]),
												_List_fromArray(
													[
														A2(
														$elm$html$Html$option,
														_List_fromArray(
															[
																$elm$html$Html$Attributes$value('luxury')
															]),
														_List_fromArray(
															[
																$elm$html$Html$text('Luxury')
															])),
														A2(
														$elm$html$Html$option,
														_List_fromArray(
															[
																$elm$html$Html$Attributes$value('tech')
															]),
														_List_fromArray(
															[
																$elm$html$Html$text('Tech')
															]))
													]))
											])),
										A2(
										$elm$html$Html$div,
										_List_Nil,
										_List_fromArray(
											[
												A2(
												$elm$html$Html$label,
												_List_fromArray(
													[
														A2($elm$html$Html$Attributes$style, 'display', 'block'),
														A2($elm$html$Html$Attributes$style, 'margin-bottom', '5px')
													]),
												_List_fromArray(
													[
														$elm$html$Html$text('LLM Provider')
													])),
												A2(
												$elm$html$Html$select,
												_List_fromArray(
													[
														$elm$html$Html$Events$onInput($author$project$CreativeBriefEditor$UpdateLLMProvider),
														$elm$html$Html$Attributes$value(model.llmProvider)
													]),
												_List_fromArray(
													[
														A2(
														$elm$html$Html$option,
														_List_fromArray(
															[
																$elm$html$Html$Attributes$value('openrouter')
															]),
														_List_fromArray(
															[
																$elm$html$Html$text('OpenRouter (GPT-5-nano)')
															])),
														A2(
														$elm$html$Html$option,
														_List_fromArray(
															[
																$elm$html$Html$Attributes$value('openai')
															]),
														_List_fromArray(
															[
																$elm$html$Html$text('OpenAI (GPT-4o)')
															])),
														A2(
														$elm$html$Html$option,
														_List_fromArray(
															[
																$elm$html$Html$Attributes$value('claude')
															]),
														_List_fromArray(
															[
																$elm$html$Html$text('Claude')
															]))
													]))
											]))
									])),
								A2(
								$elm$html$Html$div,
								_List_fromArray(
									[
										A2($elm$html$Html$Attributes$style, 'margin-bottom', '10px')
									]),
								_List_fromArray(
									[
										A2(
										$elm$html$Html$input,
										_List_fromArray(
											[
												$elm$html$Html$Attributes$type_('file'),
												$elm$html$Html$Attributes$id('media-upload'),
												$elm$html$Html$Attributes$accept('image/*,video/*')
											]),
										_List_Nil),
										A2(
										$elm$html$Html$button,
										_List_fromArray(
											[
												$elm$html$Html$Attributes$type_('button'),
												$elm$html$Html$Events$onClick($author$project$CreativeBriefEditor$UploadMedia),
												A2($elm$html$Html$Attributes$style, 'margin-left', '10px'),
												A2($elm$html$Html$Attributes$style, 'padding', '8px 12px'),
												A2($elm$html$Html$Attributes$style, 'background', '#4CAF50'),
												A2($elm$html$Html$Attributes$style, 'color', 'white'),
												A2($elm$html$Html$Attributes$style, 'border', 'none'),
												A2($elm$html$Html$Attributes$style, 'border-radius', '4px')
											]),
										_List_fromArray(
											[
												$elm$html$Html$text('Upload Media')
											]))
									])),
								A2(
								$elm$html$Html$button,
								_List_fromArray(
									[
										$elm$html$Html$Attributes$type_('button'),
										$elm$html$Html$Events$onClick(
										$author$project$CreativeBriefEditor$SubmitBrief(false)),
										A2($elm$html$Html$Attributes$style, 'background-color', '#4CAF50'),
										A2($elm$html$Html$Attributes$style, 'color', 'white'),
										A2($elm$html$Html$Attributes$style, 'padding', '10px 16px'),
										A2($elm$html$Html$Attributes$style, 'border', 'none'),
										A2($elm$html$Html$Attributes$style, 'border-radius', '4px'),
										A2($elm$html$Html$Attributes$style, 'margin-right', '10px')
									]),
								_List_fromArray(
									[
										$elm$html$Html$text('Generate Brief')
									])),
								A2(
								$elm$html$Html$button,
								_List_fromArray(
									[
										$elm$html$Html$Attributes$type_('button'),
										$elm$html$Html$Events$onClick(
										$author$project$CreativeBriefEditor$SubmitBrief(true)),
										A2($elm$html$Html$Attributes$style, 'background-color', '#ff9800'),
										A2($elm$html$Html$Attributes$style, 'color', 'white'),
										A2($elm$html$Html$Attributes$style, 'padding', '10px 16px'),
										A2($elm$html$Html$Attributes$style, 'border', 'none'),
										A2($elm$html$Html$Attributes$style, 'border-radius', '4px')
									]),
								_List_fromArray(
									[
										$elm$html$Html$text('Generate (Bypass Cache)')
									]))
							])),
						function () {
						var _v0 = model.selectedFile;
						if (_v0.$ === 'Just') {
							var file = _v0.a;
							return A2(
								$elm$html$Html$p,
								_List_fromArray(
									[
										A2($elm$html$Html$Attributes$style, 'color', '#666'),
										A2($elm$html$Html$Attributes$style, 'margin-top', '10px')
									]),
								_List_fromArray(
									[
										$elm$html$Html$text(
										'Selected: ' + $elm$file$File$name(file))
									]));
						} else {
							return $elm$html$Html$text('');
						}
					}(),
						function () {
						var _v1 = model.response;
						if (_v1.$ === 'Just') {
							var response = _v1.a;
							return A2(
								$elm$html$Html$div,
								_List_fromArray(
									[
										A2($elm$html$Html$Attributes$style, 'margin-top', '20px'),
										A2($elm$html$Html$Attributes$style, 'border', '1px solid #ccc'),
										A2($elm$html$Html$Attributes$style, 'padding', '15px'),
										A2($elm$html$Html$Attributes$style, 'border-radius', '8px'),
										A2($elm$html$Html$Attributes$style, 'background', '#f9f9f9')
									]),
								_List_fromArray(
									[
										A2(
										$elm$html$Html$h3,
										_List_Nil,
										_List_fromArray(
											[
												$elm$html$Html$text('Generated Brief')
											])),
										A2(
										$elm$html$Html$p,
										_List_Nil,
										_List_fromArray(
											[
												$elm$html$Html$text(
												'ID: ' + A2($elm$core$Maybe$withDefault, 'Unknown', model.briefId))
											])),
										function () {
										var _v2 = response.metadata.confidenceScore;
										if (_v2.$ === 'Just') {
											var score = _v2.a;
											return A2(
												$elm$html$Html$p,
												_List_Nil,
												_List_fromArray(
													[
														$elm$html$Html$text(
														'Confidence: ' + $elm$core$String$fromFloat(score))
													]));
										} else {
											return $elm$html$Html$text('');
										}
									}(),
										A2(
										$elm$html$Html$h4,
										_List_Nil,
										_List_fromArray(
											[
												$elm$html$Html$text('Creative Direction')
											])),
										A2(
										$elm$html$Html$pre,
										_List_fromArray(
											[
												A2($elm$html$Html$Attributes$style, 'background', '#f4f4f4'),
												A2($elm$html$Html$Attributes$style, 'padding', '10px'),
												A2($elm$html$Html$Attributes$style, 'border-radius', '4px'),
												A2($elm$html$Html$Attributes$style, 'overflow-x', 'auto')
											]),
										_List_fromArray(
											[
												$elm$html$Html$text(
												A2($elm$json$Json$Encode$encode, 2, response.creativeDirection))
											])),
										A2(
										$elm$html$Html$h4,
										_List_Nil,
										_List_fromArray(
											[
												$elm$html$Html$text('Scenes')
											])),
										A2(
										$elm$html$Html$div,
										_List_Nil,
										A2($elm$core$List$map, $author$project$CreativeBriefEditor$viewScene, response.scenes)),
										$elm$core$String$isEmpty(model.autoScenePrompt) ? $elm$html$Html$text('') : A2(
										$elm$html$Html$div,
										_List_fromArray(
											[
												A2($elm$html$Html$Attributes$style, 'margin-top', '10px'),
												A2($elm$html$Html$Attributes$style, 'padding', '10px'),
												A2($elm$html$Html$Attributes$style, 'background', '#e8f5e8'),
												A2($elm$html$Html$Attributes$style, 'border-radius', '4px')
											]),
										_List_fromArray(
											[
												A2(
												$elm$html$Html$h4,
												_List_Nil,
												_List_fromArray(
													[
														$elm$html$Html$text('Auto-Filled Scene Prompt')
													])),
												A2(
												$elm$html$Html$p,
												_List_Nil,
												_List_fromArray(
													[
														$elm$html$Html$text(model.autoScenePrompt)
													])),
												A2(
												$elm$html$Html$button,
												_List_fromArray(
													[
														$elm$html$Html$Events$onClick($author$project$CreativeBriefEditor$GenerateScene),
														A2($elm$html$Html$Attributes$style, 'background-color', '#2196F3'),
														A2($elm$html$Html$Attributes$style, 'color', 'white'),
														A2($elm$html$Html$Attributes$style, 'padding', '8px 12px'),
														A2($elm$html$Html$Attributes$style, 'border', 'none'),
														A2($elm$html$Html$Attributes$style, 'border-radius', '4px')
													]),
												_List_fromArray(
													[
														$elm$html$Html$text('Generate Scene')
													]))
											])),
										A2(
										$elm$html$Html$button,
										_List_fromArray(
											[
												$elm$html$Html$Events$onClick($author$project$CreativeBriefEditor$GenerateVideo),
												A2($elm$html$Html$Attributes$style, 'background-color', '#9C27B0'),
												A2($elm$html$Html$Attributes$style, 'color', 'white'),
												A2($elm$html$Html$Attributes$style, 'padding', '10px 16px'),
												A2($elm$html$Html$Attributes$style, 'border', 'none'),
												A2($elm$html$Html$Attributes$style, 'border-radius', '4px'),
												A2($elm$html$Html$Attributes$style, 'margin-top', '10px')
											]),
										_List_fromArray(
											[
												$elm$html$Html$text('Generate Video from Brief')
											])),
										A2(
										$elm$html$Html$button,
										_List_fromArray(
											[
												$elm$html$Html$Events$onClick($author$project$CreativeBriefEditor$RefineBrief),
												A2($elm$html$Html$Attributes$style, 'background-color', '#f44336'),
												A2($elm$html$Html$Attributes$style, 'color', 'white'),
												A2($elm$html$Html$Attributes$style, 'padding', '10px 16px'),
												A2($elm$html$Html$Attributes$style, 'border', 'none'),
												A2($elm$html$Html$Attributes$style, 'border-radius', '4px'),
												A2($elm$html$Html$Attributes$style, 'margin-left', '10px')
											]),
										_List_fromArray(
											[
												$elm$html$Html$text('Refine Brief')
											])),
										A2(
										$elm$html$Html$div,
										_List_fromArray(
											[
												A2($elm$html$Html$Attributes$style, 'margin-top', '20px'),
												A2($elm$html$Html$Attributes$style, 'padding', '15px'),
												A2($elm$html$Html$Attributes$style, 'background', '#f0f8ff'),
												A2($elm$html$Html$Attributes$style, 'border-radius', '4px')
											]),
										_List_fromArray(
											[
												A2(
												$elm$html$Html$h4,
												_List_Nil,
												_List_fromArray(
													[
														$elm$html$Html$text('Generate Images from Brief')
													])),
												model.loadingImageModels ? A2(
												$elm$html$Html$p,
												_List_Nil,
												_List_fromArray(
													[
														$elm$html$Html$text('Loading image models...')
													])) : A2(
												$elm$html$Html$div,
												_List_Nil,
												_List_fromArray(
													[
														A2(
														$elm$html$Html$div,
														_List_fromArray(
															[
																A2($elm$html$Html$Attributes$style, 'margin-bottom', '10px')
															]),
														_List_fromArray(
															[
																A2(
																$elm$html$Html$label,
																_List_fromArray(
																	[
																		A2($elm$html$Html$Attributes$style, 'display', 'block'),
																		A2($elm$html$Html$Attributes$style, 'margin-bottom', '5px')
																	]),
																_List_fromArray(
																	[
																		$elm$html$Html$text('Select Image Model:')
																	])),
																A2(
																$elm$html$Html$select,
																_List_fromArray(
																	[
																		$elm$html$Html$Events$onInput($author$project$CreativeBriefEditor$SelectImageModel),
																		A2($elm$html$Html$Attributes$style, 'width', '100%'),
																		A2($elm$html$Html$Attributes$style, 'padding', '8px'),
																		A2($elm$html$Html$Attributes$style, 'border', '1px solid #ccc'),
																		A2($elm$html$Html$Attributes$style, 'border-radius', '4px'),
																		$elm$html$Html$Attributes$disabled(model.generatingImages)
																	]),
																A2($elm$core$List$map, $author$project$CreativeBriefEditor$viewImageModelOption, model.imageModels))
															])),
														A2(
														$elm$html$Html$button,
														_List_fromArray(
															[
																$elm$html$Html$Events$onClick($author$project$CreativeBriefEditor$GenerateImages),
																A2($elm$html$Html$Attributes$style, 'background-color', '#FF5722'),
																A2($elm$html$Html$Attributes$style, 'color', 'white'),
																A2($elm$html$Html$Attributes$style, 'padding', '10px 16px'),
																A2($elm$html$Html$Attributes$style, 'border', 'none'),
																A2($elm$html$Html$Attributes$style, 'border-radius', '4px'),
																$elm$html$Html$Attributes$disabled(
																model.generatingImages || $elm$core$List$isEmpty(model.imageModels))
															]),
														_List_fromArray(
															[
																model.generatingImages ? $elm$html$Html$text('Generating Images...') : $elm$html$Html$text('Generate Images from All Scenes')
															])),
														($elm$core$List$isEmpty(model.imageModels) && (!model.loadingImageModels)) ? A2(
														$elm$html$Html$p,
														_List_fromArray(
															[
																A2($elm$html$Html$Attributes$style, 'color', '#999'),
																A2($elm$html$Html$Attributes$style, 'margin-top', '10px')
															]),
														_List_fromArray(
															[
																$elm$html$Html$text('No image models available')
															])) : $elm$html$Html$text('')
													]))
											]))
									]));
						} else {
							return $elm$html$Html$text('');
						}
					}(),
						function () {
						var _v3 = model.error;
						if (_v3.$ === 'Just') {
							var err = _v3.a;
							return A2(
								$elm$html$Html$div,
								_List_fromArray(
									[
										A2($elm$html$Html$Attributes$style, 'color', 'red'),
										A2($elm$html$Html$Attributes$style, 'margin-top', '10px'),
										A2($elm$html$Html$Attributes$style, 'padding', '10px'),
										A2($elm$html$Html$Attributes$style, 'background', '#ffebee'),
										A2($elm$html$Html$Attributes$style, 'border-radius', '4px')
									]),
								_List_fromArray(
									[
										$elm$html$Html$text('Error: ' + err)
									]));
						} else {
							return $elm$html$Html$text('');
						}
					}()
					]))
			]));
};
var $author$project$Image$FetchModels = {$: 'FetchModels'};
var $author$project$Image$GenerateImage = {$: 'GenerateImage'};
var $author$project$Image$SelectCollection = function (a) {
	return {$: 'SelectCollection', a: a};
};
var $author$project$Image$UpdateSearch = function (a) {
	return {$: 'UpdateSearch', a: a};
};
var $author$project$Image$hasEmptyRequiredParameters = F2(
	function (params, requiredFields) {
		return A2(
			$elm$core$List$any,
			function (param) {
				return A2($elm$core$List$member, param.key, requiredFields) && $elm$core$String$isEmpty(
					$elm$core$String$trim(param.value));
			},
			params);
	});
var $elm$html$Html$img = _VirtualDom_node('img');
var $author$project$Image$SelectModel = function (a) {
	return {$: 'SelectModel', a: a};
};
var $author$project$Image$viewModelOption = function (model) {
	return A2(
		$elm$html$Html$div,
		_List_fromArray(
			[
				$elm$html$Html$Attributes$class('model-option'),
				$elm$html$Html$Events$onClick(
				$author$project$Image$SelectModel(model.id))
			]),
		_List_fromArray(
			[
				A2(
				$elm$html$Html$h3,
				_List_Nil,
				_List_fromArray(
					[
						$elm$html$Html$text(model.name)
					])),
				A2(
				$elm$html$Html$p,
				_List_Nil,
				_List_fromArray(
					[
						$elm$html$Html$text(model.description)
					]))
			]));
};
var $author$project$Image$UpdateParameter = F2(
	function (a, b) {
		return {$: 'UpdateParameter', a: a, b: b};
	});
var $author$project$Image$FileSelected = F2(
	function (a, b) {
		return {$: 'FileSelected', a: a, b: b};
	});
var $elm$file$File$decoder = _File_decoder;
var $author$project$Image$fileDecoder = function (paramKey) {
	return A2(
		$elm$json$Json$Decode$map,
		$author$project$Image$FileSelected(paramKey),
		A2(
			$elm$json$Json$Decode$at,
			_List_fromArray(
				['target', 'files', '0']),
			$elm$file$File$decoder));
};
var $author$project$Image$capitalize = function (str) {
	var _v0 = $elm$core$String$uncons(str);
	if (_v0.$ === 'Just') {
		var _v1 = _v0.a;
		var first = _v1.a;
		var rest = _v1.b;
		return _Utils_ap(
			$elm$core$String$fromChar(
				$elm$core$Char$toUpper(first)),
			rest);
	} else {
		return str;
	}
};
var $author$project$Image$formatParameterName = function (name) {
	return A2(
		$elm$core$String$join,
		' ',
		A2(
			$elm$core$List$map,
			$author$project$Image$capitalize,
			A2($elm$core$String$split, '_', name)));
};
var $author$project$Image$viewParameter = F2(
	function (model, param) {
		var rangeText = function () {
			var _v3 = _Utils_Tuple2(param.minimum, param.maximum);
			if (_v3.a.$ === 'Just') {
				if (_v3.b.$ === 'Just') {
					var min = _v3.a.a;
					var max = _v3.b.a;
					return ' (' + ($elm$core$String$fromFloat(min) + (' - ' + ($elm$core$String$fromFloat(max) + ')')));
				} else {
					var min = _v3.a.a;
					var _v4 = _v3.b;
					return ' (min: ' + ($elm$core$String$fromFloat(min) + ')');
				}
			} else {
				if (_v3.b.$ === 'Just') {
					var _v5 = _v3.a;
					var max = _v3.b.a;
					return ' (max: ' + ($elm$core$String$fromFloat(max) + ')');
				} else {
					var _v6 = _v3.a;
					var _v7 = _v3.b;
					return '';
				}
			}
		}();
		var isUploading = _Utils_eq(
			model.uploadingFile,
			$elm$core$Maybe$Just(param.key));
		var isRequired = A2($elm$core$List$member, param.key, model.requiredFields);
		var labelText = _Utils_ap(
			$author$project$Image$formatParameterName(param.key),
			isRequired ? ' *' : '');
		var isImageField = _Utils_eq(
			param.format,
			$elm$core$Maybe$Just('uri')) || A2(
			$elm$core$String$contains,
			'image',
			$elm$core$String$toLower(param.key));
		var isDisabled = model.isGenerating;
		var fullDescription = function () {
			var _v2 = param.description;
			if (_v2.$ === 'Just') {
				var desc = _v2.a;
				return _Utils_ap(desc, rangeText);
			} else {
				return (rangeText !== '') ? $elm$core$String$trim(rangeText) : '';
			}
		}();
		var defaultHint = function () {
			var _v1 = param._default;
			if (_v1.$ === 'Just') {
				var def = _v1.a;
				return (fullDescription !== '') ? (fullDescription + (' (default: ' + (def + ')'))) : ('default: ' + def);
			} else {
				return fullDescription;
			}
		}();
		return A2(
			$elm$html$Html$div,
			_List_fromArray(
				[
					$elm$html$Html$Attributes$class('parameter-field')
				]),
			_List_fromArray(
				[
					A2(
					$elm$html$Html$label,
					_List_fromArray(
						[
							$elm$html$Html$Attributes$class('parameter-label')
						]),
					_List_fromArray(
						[
							$elm$html$Html$text(labelText),
							(defaultHint !== '') ? A2(
							$elm$html$Html$span,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$class('parameter-hint')
								]),
							_List_fromArray(
								[
									$elm$html$Html$text(' — ' + defaultHint)
								])) : $elm$html$Html$text('')
						])),
					function () {
					var _v0 = param._enum;
					if (_v0.$ === 'Just') {
						var options = _v0.a;
						return A2(
							$elm$html$Html$select,
							_List_fromArray(
								[
									$elm$html$Html$Events$onInput(
									$author$project$Image$UpdateParameter(param.key)),
									$elm$html$Html$Attributes$disabled(isDisabled),
									$elm$html$Html$Attributes$class('parameter-select'),
									$elm$html$Html$Attributes$value(param.value)
								]),
							A2(
								$elm$core$List$cons,
								A2(
									$elm$html$Html$option,
									_List_fromArray(
										[
											$elm$html$Html$Attributes$value('')
										]),
									_List_fromArray(
										[
											$elm$html$Html$text('-- Select --')
										])),
								A2(
									$elm$core$List$map,
									function (opt) {
										return A2(
											$elm$html$Html$option,
											_List_fromArray(
												[
													$elm$html$Html$Attributes$value(opt)
												]),
											_List_fromArray(
												[
													$elm$html$Html$text(opt)
												]));
									},
									options)));
					} else {
						return isImageField ? A2(
							$elm$html$Html$div,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$class('image-upload-container')
								]),
							_List_fromArray(
								[
									A2(
									$elm$html$Html$input,
									_List_fromArray(
										[
											$elm$html$Html$Attributes$type_('file'),
											$elm$html$Html$Attributes$accept('image/*'),
											$elm$html$Html$Attributes$disabled(isDisabled || isUploading),
											$elm$html$Html$Attributes$class('parameter-file-input'),
											$elm$html$Html$Attributes$id('file-' + param.key),
											A2(
											$elm$html$Html$Events$on,
											'change',
											$author$project$Image$fileDecoder(param.key))
										]),
									_List_Nil),
									isUploading ? A2(
									$elm$html$Html$div,
									_List_fromArray(
										[
											$elm$html$Html$Attributes$class('upload-status')
										]),
									_List_fromArray(
										[
											$elm$html$Html$text('Uploading...')
										])) : $elm$html$Html$text(''),
									A2(
									$elm$html$Html$input,
									_List_fromArray(
										[
											$elm$html$Html$Attributes$type_('text'),
											$elm$html$Html$Attributes$placeholder('Or enter image URL...'),
											$elm$html$Html$Attributes$value(param.value),
											$elm$html$Html$Events$onInput(
											$author$project$Image$UpdateParameter(param.key)),
											$elm$html$Html$Attributes$disabled(isDisabled || isUploading),
											$elm$html$Html$Attributes$class('parameter-input')
										]),
									_List_Nil)
								])) : ((param.key === 'prompt') ? A2(
							$elm$html$Html$textarea,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$placeholder(
									A2($elm$core$Maybe$withDefault, 'Enter prompt...', param._default)),
									$elm$html$Html$Attributes$value(param.value),
									$elm$html$Html$Events$onInput(
									$author$project$Image$UpdateParameter(param.key)),
									$elm$html$Html$Attributes$disabled(isDisabled),
									$elm$html$Html$Attributes$class('parameter-input parameter-textarea')
								]),
							_List_Nil) : ((param.paramType === 'array') ? A2(
							$elm$html$Html$textarea,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$placeholder(
									A2($elm$core$Maybe$withDefault, '[\"item1\", \"item2\"] or enter single value', param._default)),
									$elm$html$Html$Attributes$value(param.value),
									$elm$html$Html$Events$onInput(
									$author$project$Image$UpdateParameter(param.key)),
									$elm$html$Html$Attributes$disabled(isDisabled),
									$elm$html$Html$Attributes$class('parameter-input parameter-textarea'),
									$elm$html$Html$Attributes$rows(3)
								]),
							_List_Nil) : A2(
							$elm$html$Html$input,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$type_(
									((param.paramType === 'number') || (param.paramType === 'integer')) ? 'number' : 'text'),
									$elm$html$Html$Attributes$placeholder(
									A2($elm$core$Maybe$withDefault, 'Enter ' + (param.key + '...'), param._default)),
									$elm$html$Html$Attributes$value(param.value),
									$elm$html$Html$Events$onInput(
									$author$project$Image$UpdateParameter(param.key)),
									$elm$html$Html$Attributes$disabled(isDisabled),
									$elm$html$Html$Attributes$class('parameter-input')
								]),
							_List_Nil)));
					}
				}()
				]));
	});
var $author$project$Image$view = function (model) {
	return A2(
		$elm$html$Html$div,
		_List_fromArray(
			[
				$elm$html$Html$Attributes$class('image-page')
			]),
		_List_fromArray(
			[
				A2(
				$elm$html$Html$h1,
				_List_Nil,
				_List_fromArray(
					[
						$elm$html$Html$text('Image Models Explorer')
					])),
				A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('collection-buttons')
					]),
				_List_fromArray(
					[
						A2(
						$elm$html$Html$button,
						_List_fromArray(
							[
								$elm$html$Html$Events$onClick(
								$author$project$Image$SelectCollection('text-to-image')),
								$elm$html$Html$Attributes$class(
								(model.selectedCollection === 'text-to-image') ? 'collection-button active' : 'collection-button')
							]),
						_List_fromArray(
							[
								$elm$html$Html$text('Text to Image')
							])),
						A2(
						$elm$html$Html$button,
						_List_fromArray(
							[
								$elm$html$Html$Events$onClick(
								$author$project$Image$SelectCollection('image-editing')),
								$elm$html$Html$Attributes$class(
								(model.selectedCollection === 'image-editing') ? 'collection-button active' : 'collection-button')
							]),
						_List_fromArray(
							[
								$elm$html$Html$text('Image Editing')
							])),
						A2(
						$elm$html$Html$button,
						_List_fromArray(
							[
								$elm$html$Html$Events$onClick(
								$author$project$Image$SelectCollection('super-resolution')),
								$elm$html$Html$Attributes$class(
								(model.selectedCollection === 'super-resolution') ? 'collection-button active' : 'collection-button')
							]),
						_List_fromArray(
							[
								$elm$html$Html$text('Super Resolution / Upscalers')
							]))
					])),
				A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('search-section')
					]),
				_List_fromArray(
					[
						A2(
						$elm$html$Html$input,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$type_('text'),
								$elm$html$Html$Attributes$placeholder('Search image models...'),
								$elm$html$Html$Attributes$value(model.searchQuery),
								$elm$html$Html$Events$onInput($author$project$Image$UpdateSearch)
							]),
						_List_Nil),
						A2(
						$elm$html$Html$button,
						_List_fromArray(
							[
								$elm$html$Html$Events$onClick($author$project$Image$FetchModels),
								$elm$html$Html$Attributes$disabled(
								!_Utils_eq(model.models, _List_Nil))
							]),
						_List_fromArray(
							[
								$elm$html$Html$text(
								_Utils_eq(model.models, _List_Nil) ? 'Loading...' : 'Refresh Models')
							]))
					])),
				$elm$core$List$isEmpty(model.models) ? A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('loading-text')
					]),
				_List_fromArray(
					[
						$elm$html$Html$text('Loading models...')
					])) : A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('models-list')
					]),
				A2(
					$elm$core$List$map,
					$author$project$Image$viewModelOption,
					A2(
						$elm$core$List$filter,
						function (m) {
							return A2(
								$elm$core$String$contains,
								$elm$core$String$toLower(model.searchQuery),
								$elm$core$String$toLower(m.name));
						},
						model.models))),
				function () {
				var _v0 = model.selectedModel;
				if (_v0.$ === 'Just') {
					var selected = _v0.a;
					return A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('selected-model'),
								$elm$html$Html$Attributes$id('selected-model-section')
							]),
						_List_fromArray(
							[
								A2(
								$elm$html$Html$h2,
								_List_Nil,
								_List_fromArray(
									[
										$elm$html$Html$text(selected.name)
									])),
								A2(
								$elm$html$Html$p,
								_List_Nil,
								_List_fromArray(
									[
										$elm$html$Html$text(selected.description)
									])),
								A2(
								$elm$html$Html$div,
								_List_fromArray(
									[
										$elm$html$Html$Attributes$class('parameters-form-grid')
									]),
								A2(
									$elm$core$List$map,
									$author$project$Image$viewParameter(model),
									model.parameters)),
								A2(
								$elm$html$Html$button,
								_List_fromArray(
									[
										$elm$html$Html$Events$onClick($author$project$Image$GenerateImage),
										$elm$html$Html$Attributes$disabled(
										A2($author$project$Image$hasEmptyRequiredParameters, model.parameters, model.requiredFields) || model.isGenerating),
										$elm$html$Html$Attributes$class('generate-button')
									]),
								_List_fromArray(
									[
										$elm$html$Html$text(
										model.isGenerating ? 'Generating...' : 'Generate Image')
									]))
							]));
				} else {
					return (!$elm$core$List$isEmpty(model.models)) ? A2(
						$elm$html$Html$div,
						_List_Nil,
						_List_fromArray(
							[
								$elm$html$Html$text('Select a model from the list above')
							])) : $elm$html$Html$text('');
				}
			}(),
				function () {
				var _v1 = model.outputImage;
				if (_v1.$ === 'Just') {
					var url = _v1.a;
					return A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('image-output')
							]),
						_List_fromArray(
							[
								A2(
								$elm$html$Html$img,
								_List_fromArray(
									[
										$elm$html$Html$Attributes$src(url),
										A2($elm$html$Html$Attributes$attribute, 'width', '100%'),
										A2($elm$html$Html$Attributes$style, 'max-width', '800px')
									]),
								_List_Nil)
							]));
				} else {
					return $elm$html$Html$text('');
				}
			}(),
				function () {
				var _v2 = model.error;
				if (_v2.$ === 'Just') {
					var err = _v2.a;
					return A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('error')
							]),
						_List_fromArray(
							[
								$elm$html$Html$text(err)
							]));
				} else {
					return $elm$html$Html$text('');
				}
			}()
			]));
};
var $author$project$ImageDetail$extractErrorMessage = function (imageRecord) {
	var _v0 = imageRecord.metadata;
	if (_v0.$ === 'Just') {
		var metadataValue = _v0.a;
		return $elm$core$Result$toMaybe(
			A2(
				$elm$json$Json$Decode$decodeValue,
				A2($elm$json$Json$Decode$field, 'error', $elm$json$Json$Decode$string),
				metadataValue));
	} else {
		return $elm$core$Maybe$Nothing;
	}
};
var $author$project$ImageDetail$statusText = function (status) {
	switch (status) {
		case 'processing':
			return '⏳ Processing...';
		case 'completed':
			return '✅ Completed';
		case 'failed':
			return '❌ Failed';
		case 'canceled':
			return '🚫 Canceled';
		default:
			return status;
	}
};
var $author$project$ImageDetail$viewImageDetail = function (image) {
	return A2(
		$elm$html$Html$div,
		_List_fromArray(
			[
				$elm$html$Html$Attributes$class('image-detail')
			]),
		_List_fromArray(
			[
				A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('image-info')
					]),
				_List_fromArray(
					[
						A2(
						$elm$html$Html$h2,
						_List_Nil,
						_List_fromArray(
							[
								$elm$html$Html$text('Image Details')
							])),
						A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('info-row')
							]),
						_List_fromArray(
							[
								A2(
								$elm$html$Html$span,
								_List_fromArray(
									[
										$elm$html$Html$Attributes$class('label')
									]),
								_List_fromArray(
									[
										$elm$html$Html$text('Status: ')
									])),
								A2(
								$elm$html$Html$span,
								_List_fromArray(
									[
										$elm$html$Html$Attributes$class(
										'status status-' + $elm$core$String$toLower(image.status))
									]),
								_List_fromArray(
									[
										$elm$html$Html$text(
										$author$project$ImageDetail$statusText(image.status))
									]))
							])),
						A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('info-row')
							]),
						_List_fromArray(
							[
								A2(
								$elm$html$Html$span,
								_List_fromArray(
									[
										$elm$html$Html$Attributes$class('label')
									]),
								_List_fromArray(
									[
										$elm$html$Html$text('Model: ')
									])),
								A2(
								$elm$html$Html$span,
								_List_Nil,
								_List_fromArray(
									[
										$elm$html$Html$text(image.modelId)
									]))
							])),
						A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('info-row')
							]),
						_List_fromArray(
							[
								A2(
								$elm$html$Html$span,
								_List_fromArray(
									[
										$elm$html$Html$Attributes$class('label')
									]),
								_List_fromArray(
									[
										$elm$html$Html$text('Prompt: ')
									])),
								A2(
								$elm$html$Html$p,
								_List_fromArray(
									[
										$elm$html$Html$Attributes$class('prompt')
									]),
								_List_fromArray(
									[
										$elm$html$Html$text(image.prompt)
									]))
							])),
						A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('info-row')
							]),
						_List_fromArray(
							[
								A2(
								$elm$html$Html$span,
								_List_fromArray(
									[
										$elm$html$Html$Attributes$class('label')
									]),
								_List_fromArray(
									[
										$elm$html$Html$text('Created: ')
									])),
								A2(
								$elm$html$Html$span,
								_List_Nil,
								_List_fromArray(
									[
										$elm$html$Html$text(image.createdAt)
									]))
							]))
					])),
				function () {
				var _v0 = image.status;
				switch (_v0) {
					case 'completed':
						return $elm$core$String$isEmpty(image.imageUrl) ? A2(
							$elm$html$Html$div,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$class('error')
								]),
							_List_fromArray(
								[
									$elm$html$Html$text('Image completed but no URL available')
								])) : A2(
							$elm$html$Html$div,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$class('image-viewer')
								]),
							_List_fromArray(
								[
									A2(
									$elm$html$Html$h3,
									_List_Nil,
									_List_fromArray(
										[
											$elm$html$Html$text('Generated Image')
										])),
									A2(
									$elm$html$Html$img,
									_List_fromArray(
										[
											$elm$html$Html$Attributes$src(image.imageUrl),
											A2($elm$html$Html$Attributes$attribute, 'width', '100%'),
											A2($elm$html$Html$Attributes$attribute, 'style', 'max-width: 800px; border-radius: 8px;')
										]),
									_List_Nil),
									A2(
									$elm$html$Html$div,
									_List_fromArray(
										[
											$elm$html$Html$Attributes$class('image-actions')
										]),
									_List_fromArray(
										[
											A2(
											$elm$html$Html$a,
											_List_fromArray(
												[
													$elm$html$Html$Attributes$href(image.imageUrl),
													$elm$html$Html$Attributes$download(''),
													$elm$html$Html$Attributes$class('download-button')
												]),
											_List_fromArray(
												[
													$elm$html$Html$text('Download Image')
												]))
										]))
								]));
					case 'processing':
						return A2(
							$elm$html$Html$div,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$class('processing')
								]),
							_List_fromArray(
								[
									A2(
									$elm$html$Html$div,
									_List_fromArray(
										[
											$elm$html$Html$Attributes$class('spinner')
										]),
									_List_Nil),
									A2(
									$elm$html$Html$p,
									_List_Nil,
									_List_fromArray(
										[
											$elm$html$Html$text('Your image is being generated... This may take 30-60 seconds.')
										]))
								]));
					case 'failed':
						return A2(
							$elm$html$Html$div,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$class('error')
								]),
							_List_fromArray(
								[
									$elm$html$Html$text(
									function () {
										var _v1 = $author$project$ImageDetail$extractErrorMessage(image);
										if (_v1.$ === 'Just') {
											var errorMsg = _v1.a;
											return 'Image generation failed: ' + errorMsg;
										} else {
											return 'Image generation failed. Please try again with different parameters.';
										}
									}())
								]));
					case 'canceled':
						return A2(
							$elm$html$Html$div,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$class('info')
								]),
							_List_fromArray(
								[
									$elm$html$Html$text('Image generation was canceled.')
								]));
					default:
						return A2(
							$elm$html$Html$div,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$class('info')
								]),
							_List_fromArray(
								[
									$elm$html$Html$text('Status: ' + image.status)
								]));
				}
			}()
			]));
};
var $author$project$ImageDetail$view = function (model) {
	return A2(
		$elm$html$Html$div,
		_List_fromArray(
			[
				$elm$html$Html$Attributes$class('image-detail-page')
			]),
		_List_fromArray(
			[
				A2(
				$elm$html$Html$h1,
				_List_Nil,
				_List_fromArray(
					[
						$elm$html$Html$text('Image Generation Status')
					])),
				function () {
				var _v0 = model.error;
				if (_v0.$ === 'Just') {
					var err = _v0.a;
					return A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('error')
							]),
						_List_fromArray(
							[
								$elm$html$Html$text(err)
							]));
				} else {
					return $elm$html$Html$text('');
				}
			}(),
				function () {
				var _v1 = model.image;
				if (_v1.$ === 'Just') {
					var image = _v1.a;
					return $author$project$ImageDetail$viewImageDetail(image);
				} else {
					return A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('loading')
							]),
						_List_fromArray(
							[
								$elm$html$Html$text('Loading image information...')
							]));
				}
			}()
			]));
};
var $author$project$ImageGallery$SelectImage = function (a) {
	return {$: 'SelectImage', a: a};
};
var $author$project$ImageGallery$extractErrorMessage = function (imageRecord) {
	var _v0 = imageRecord.metadata;
	if (_v0.$ === 'Just') {
		var metadataValue = _v0.a;
		return $elm$core$Result$toMaybe(
			A2(
				$elm$json$Json$Decode$decodeValue,
				A2($elm$json$Json$Decode$field, 'error', $elm$json$Json$Decode$string),
				metadataValue));
	} else {
		return $elm$core$Maybe$Nothing;
	}
};
var $author$project$ImageGallery$formatDate = function (dateStr) {
	return A2($elm$core$String$left, 19, dateStr);
};
var $author$project$ImageGallery$truncateString = F2(
	function (maxLength, str) {
		return (_Utils_cmp(
			$elm$core$String$length(str),
			maxLength) < 1) ? str : (A2($elm$core$String$left, maxLength - 3, str) + '...');
	});
var $author$project$ImageGallery$viewImageCard = function (imageRecord) {
	var errorMessage = $author$project$ImageGallery$extractErrorMessage(imageRecord);
	return A2(
		$elm$html$Html$div,
		_List_fromArray(
			[
				$elm$html$Html$Attributes$class('image-card'),
				$elm$html$Html$Events$onClick(
				$author$project$ImageGallery$SelectImage(imageRecord))
			]),
		_List_fromArray(
			[
				A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('image-thumbnail')
					]),
				_List_fromArray(
					[
						$elm$core$String$isEmpty(imageRecord.imageUrl) ? A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								A2($elm$html$Html$Attributes$style, 'width', '100%'),
								A2($elm$html$Html$Attributes$style, 'height', '100%'),
								A2($elm$html$Html$Attributes$style, 'display', 'flex'),
								A2($elm$html$Html$Attributes$style, 'flex-direction', 'column'),
								A2($elm$html$Html$Attributes$style, 'align-items', 'center'),
								A2($elm$html$Html$Attributes$style, 'justify-content', 'center'),
								A2(
								$elm$html$Html$Attributes$style,
								'background',
								(imageRecord.status === 'failed') ? '#c33' : '#333'),
								A2($elm$html$Html$Attributes$style, 'color', '#fff'),
								A2($elm$html$Html$Attributes$style, 'padding', '10px')
							]),
						_List_fromArray(
							[
								A2(
								$elm$html$Html$div,
								_List_fromArray(
									[
										A2($elm$html$Html$Attributes$style, 'font-weight', 'bold'),
										A2($elm$html$Html$Attributes$style, 'margin-bottom', '5px')
									]),
								_List_fromArray(
									[
										$elm$html$Html$text(
										$elm$core$String$toUpper(imageRecord.status))
									])),
								function () {
								if (errorMessage.$ === 'Just') {
									var err = errorMessage.a;
									return A2(
										$elm$html$Html$div,
										_List_fromArray(
											[
												A2($elm$html$Html$Attributes$style, 'font-size', '12px'),
												A2($elm$html$Html$Attributes$style, 'text-align', 'center')
											]),
										_List_fromArray(
											[
												$elm$html$Html$text(
												A2($author$project$ImageGallery$truncateString, 60, err))
											]));
								} else {
									return $elm$html$Html$text('');
								}
							}()
							])) : A2(
						$elm$html$Html$img,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$src(imageRecord.thumbnailUrl),
								A2($elm$html$Html$Attributes$style, 'width', '100%'),
								A2($elm$html$Html$Attributes$style, 'height', '100%'),
								A2($elm$html$Html$Attributes$style, 'object-fit', 'cover')
							]),
						_List_Nil)
					])),
				A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('image-card-info')
					]),
				_List_fromArray(
					[
						A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('image-prompt')
							]),
						_List_fromArray(
							[
								$elm$html$Html$text(imageRecord.prompt)
							])),
						A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('image-meta')
							]),
						_List_fromArray(
							[
								A2(
								$elm$html$Html$span,
								_List_fromArray(
									[
										$elm$html$Html$Attributes$class('image-model')
									]),
								_List_fromArray(
									[
										$elm$html$Html$text(imageRecord.modelId)
									])),
								A2(
								$elm$html$Html$span,
								_List_fromArray(
									[
										$elm$html$Html$Attributes$class('image-date')
									]),
								_List_fromArray(
									[
										$elm$html$Html$text(
										$author$project$ImageGallery$formatDate(imageRecord.createdAt))
									]))
							]))
					]))
			]));
};
var $author$project$ImageGallery$CloseImage = {$: 'CloseImage'};
var $author$project$ImageGallery$CreateVideoFromImage = F2(
	function (a, b) {
		return {$: 'CreateVideoFromImage', a: a, b: b};
	});
var $author$project$ImageGallery$SelectVideoModel = function (a) {
	return {$: 'SelectVideoModel', a: a};
};
var $author$project$ImageGallery$ToggleRawData = {$: 'ToggleRawData'};
var $author$project$ImageGallery$NoOp = {$: 'NoOp'};
var $author$project$ImageGallery$onClickNoBubble = A2(
	$elm$html$Html$Events$stopPropagationOn,
	'click',
	$elm$json$Json$Decode$succeed(
		_Utils_Tuple2($author$project$ImageGallery$NoOp, true)));
var $elm$html$Html$Attributes$selected = $elm$html$Html$Attributes$boolProperty('selected');
var $author$project$ImageGallery$viewRawDataField = F2(
	function (label, maybeValue) {
		if (maybeValue.$ === 'Just') {
			var value = maybeValue.a;
			return A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('raw-data-field')
					]),
				_List_fromArray(
					[
						A2(
						$elm$html$Html$h4,
						_List_Nil,
						_List_fromArray(
							[
								$elm$html$Html$text(label)
							])),
						A2(
						$elm$html$Html$pre,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('raw-json')
							]),
						_List_fromArray(
							[
								$elm$html$Html$text(
								A2(
									$elm$core$Result$withDefault,
									'Invalid JSON',
									A2(
										$elm$core$Result$map,
										$elm$json$Json$Encode$encode(2),
										A2($elm$json$Json$Decode$decodeValue, $elm$json$Json$Decode$value, value))))
							]))
					]));
		} else {
			return $elm$html$Html$text('');
		}
	});
var $author$project$ImageGallery$viewImageModal = F2(
	function (model, imageRecord) {
		var errorMessage = $author$project$ImageGallery$extractErrorMessage(imageRecord);
		return A2(
			$elm$html$Html$div,
			_List_fromArray(
				[
					$elm$html$Html$Attributes$class('modal-overlay'),
					$elm$html$Html$Events$onClick($author$project$ImageGallery$CloseImage)
				]),
			_List_fromArray(
				[
					A2(
					$elm$html$Html$div,
					_List_fromArray(
						[
							$elm$html$Html$Attributes$class('modal-content'),
							$author$project$ImageGallery$onClickNoBubble
						]),
					_List_fromArray(
						[
							A2(
							$elm$html$Html$button,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$class('modal-close'),
									$elm$html$Html$Events$onClick($author$project$ImageGallery$CloseImage)
								]),
							_List_fromArray(
								[
									$elm$html$Html$text('×')
								])),
							A2(
							$elm$html$Html$h2,
							_List_Nil,
							_List_fromArray(
								[
									$elm$html$Html$text('Generated Image')
								])),
							function () {
							if (errorMessage.$ === 'Just') {
								var err = errorMessage.a;
								return A2(
									$elm$html$Html$div,
									_List_fromArray(
										[
											A2($elm$html$Html$Attributes$style, 'background', '#fee'),
											A2($elm$html$Html$Attributes$style, 'color', '#c33'),
											A2($elm$html$Html$Attributes$style, 'padding', '15px'),
											A2($elm$html$Html$Attributes$style, 'border-radius', '4px'),
											A2($elm$html$Html$Attributes$style, 'margin-bottom', '15px'),
											A2($elm$html$Html$Attributes$style, 'border', '1px solid #fcc')
										]),
									_List_fromArray(
										[
											A2(
											$elm$html$Html$strong,
											_List_Nil,
											_List_fromArray(
												[
													$elm$html$Html$text('Error: ')
												])),
											$elm$html$Html$text(err)
										]));
							} else {
								return $elm$html$Html$text('');
							}
						}(),
							(!$elm$core$String$isEmpty(imageRecord.imageUrl)) ? A2(
							$elm$html$Html$img,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$src(imageRecord.imageUrl),
									A2($elm$html$Html$Attributes$style, 'width', '100%'),
									A2($elm$html$Html$Attributes$style, 'max-width', '800px'),
									$elm$html$Html$Attributes$class('modal-image')
								]),
							_List_Nil) : A2(
							$elm$html$Html$div,
							_List_fromArray(
								[
									A2($elm$html$Html$Attributes$style, 'background', '#333'),
									A2($elm$html$Html$Attributes$style, 'color', '#fff'),
									A2($elm$html$Html$Attributes$style, 'padding', '40px'),
									A2($elm$html$Html$Attributes$style, 'text-align', 'center'),
									A2($elm$html$Html$Attributes$style, 'border-radius', '4px'),
									A2($elm$html$Html$Attributes$style, 'margin-bottom', '15px')
								]),
							_List_fromArray(
								[
									$elm$html$Html$text(
									'Image ' + $elm$core$String$toUpper(imageRecord.status))
								])),
							A2(
							$elm$html$Html$div,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$class('modal-details')
								]),
							_List_fromArray(
								[
									A2(
									$elm$html$Html$div,
									_List_fromArray(
										[
											$elm$html$Html$Attributes$class('detail-row')
										]),
									_List_fromArray(
										[
											A2(
											$elm$html$Html$strong,
											_List_Nil,
											_List_fromArray(
												[
													$elm$html$Html$text('Prompt: ')
												])),
											$elm$html$Html$text(imageRecord.prompt)
										])),
									A2(
									$elm$html$Html$div,
									_List_fromArray(
										[
											$elm$html$Html$Attributes$class('detail-row')
										]),
									_List_fromArray(
										[
											A2(
											$elm$html$Html$strong,
											_List_Nil,
											_List_fromArray(
												[
													$elm$html$Html$text('Model: ')
												])),
											$elm$html$Html$text(imageRecord.modelId)
										])),
									function () {
									var _v1 = imageRecord.collection;
									if (_v1.$ === 'Just') {
										var coll = _v1.a;
										return A2(
											$elm$html$Html$div,
											_List_fromArray(
												[
													$elm$html$Html$Attributes$class('detail-row')
												]),
											_List_fromArray(
												[
													A2(
													$elm$html$Html$strong,
													_List_Nil,
													_List_fromArray(
														[
															$elm$html$Html$text('Collection: ')
														])),
													$elm$html$Html$text(coll)
												]));
									} else {
										return $elm$html$Html$text('');
									}
								}(),
									A2(
									$elm$html$Html$div,
									_List_fromArray(
										[
											$elm$html$Html$Attributes$class('detail-row')
										]),
									_List_fromArray(
										[
											A2(
											$elm$html$Html$strong,
											_List_Nil,
											_List_fromArray(
												[
													$elm$html$Html$text('Created: ')
												])),
											$elm$html$Html$text(imageRecord.createdAt)
										])),
									A2(
									$elm$html$Html$div,
									_List_fromArray(
										[
											$elm$html$Html$Attributes$class('detail-row')
										]),
									_List_fromArray(
										[
											A2(
											$elm$html$Html$strong,
											_List_Nil,
											_List_fromArray(
												[
													$elm$html$Html$text('Status: ')
												])),
											A2(
											$elm$html$Html$span,
											_List_fromArray(
												[
													A2(
													$elm$html$Html$Attributes$style,
													'color',
													(imageRecord.status === 'failed') ? '#c33' : 'inherit'),
													A2(
													$elm$html$Html$Attributes$style,
													'font-weight',
													(imageRecord.status === 'failed') ? 'bold' : 'normal')
												]),
											_List_fromArray(
												[
													$elm$html$Html$text(imageRecord.status)
												]))
										]))
								])),
							((!$elm$core$String$isEmpty(imageRecord.imageUrl)) && (imageRecord.status === 'completed')) ? A2(
							$elm$html$Html$div,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$class('modal-actions'),
									A2($elm$html$Html$Attributes$style, 'margin', '20px 0')
								]),
							_List_fromArray(
								[
									A2(
									$elm$html$Html$div,
									_List_fromArray(
										[
											A2($elm$html$Html$Attributes$style, 'margin-bottom', '10px')
										]),
									_List_fromArray(
										[
											A2(
											$elm$html$Html$strong,
											_List_Nil,
											_List_fromArray(
												[
													$elm$html$Html$text('Select Image-to-Video Model:')
												]))
										])),
									model.loadingModels ? A2(
									$elm$html$Html$div,
									_List_fromArray(
										[
											A2($elm$html$Html$Attributes$style, 'padding', '10px')
										]),
									_List_fromArray(
										[
											$elm$html$Html$text('Loading models...')
										])) : ($elm$core$List$isEmpty(model.videoModels) ? A2(
									$elm$html$Html$div,
									_List_fromArray(
										[
											A2($elm$html$Html$Attributes$style, 'padding', '10px'),
											A2($elm$html$Html$Attributes$style, 'color', '#999')
										]),
									_List_fromArray(
										[
											$elm$html$Html$text('No image-to-video models available')
										])) : A2(
									$elm$html$Html$div,
									_List_fromArray(
										[
											A2($elm$html$Html$Attributes$style, 'margin-bottom', '10px')
										]),
									_List_fromArray(
										[
											A2(
											$elm$html$Html$select,
											_List_fromArray(
												[
													$elm$html$Html$Events$onInput($author$project$ImageGallery$SelectVideoModel),
													A2($elm$html$Html$Attributes$style, 'width', '100%'),
													A2($elm$html$Html$Attributes$style, 'padding', '8px'),
													A2($elm$html$Html$Attributes$style, 'border', '1px solid #ccc'),
													A2($elm$html$Html$Attributes$style, 'border-radius', '4px'),
													A2($elm$html$Html$Attributes$style, 'font-size', '14px')
												]),
											A2(
												$elm$core$List$map,
												function (videoModel) {
													return A2(
														$elm$html$Html$option,
														_List_fromArray(
															[
																$elm$html$Html$Attributes$value(videoModel.id),
																$elm$html$Html$Attributes$selected(
																_Utils_eq(
																	model.selectedVideoModel,
																	$elm$core$Maybe$Just(videoModel.id)))
															]),
														_List_fromArray(
															[
																$elm$html$Html$text(videoModel.name + (' - ' + videoModel.description))
															]));
												},
												model.videoModels))
										]))),
									function () {
									var _v2 = model.selectedVideoModel;
									if (_v2.$ === 'Just') {
										var modelId = _v2.a;
										return A2(
											$elm$html$Html$button,
											_List_fromArray(
												[
													$elm$html$Html$Events$onClick(
													A2($author$project$ImageGallery$CreateVideoFromImage, modelId, imageRecord.imageUrl)),
													$elm$html$Html$Attributes$class('create-video-button'),
													A2($elm$html$Html$Attributes$style, 'background', '#4CAF50'),
													A2($elm$html$Html$Attributes$style, 'color', 'white'),
													A2($elm$html$Html$Attributes$style, 'padding', '10px 20px'),
													A2($elm$html$Html$Attributes$style, 'border', 'none'),
													A2($elm$html$Html$Attributes$style, 'border-radius', '4px'),
													A2($elm$html$Html$Attributes$style, 'cursor', 'pointer'),
													A2($elm$html$Html$Attributes$style, 'font-size', '16px'),
													A2($elm$html$Html$Attributes$style, 'width', '100%')
												]),
											_List_fromArray(
												[
													$elm$html$Html$text('Create Video from This Image')
												]));
									} else {
										return A2(
											$elm$html$Html$button,
											_List_fromArray(
												[
													$elm$html$Html$Attributes$disabled(true),
													$elm$html$Html$Attributes$class('create-video-button'),
													A2($elm$html$Html$Attributes$style, 'background', '#ccc'),
													A2($elm$html$Html$Attributes$style, 'color', '#666'),
													A2($elm$html$Html$Attributes$style, 'padding', '10px 20px'),
													A2($elm$html$Html$Attributes$style, 'border', 'none'),
													A2($elm$html$Html$Attributes$style, 'border-radius', '4px'),
													A2($elm$html$Html$Attributes$style, 'cursor', 'not-allowed'),
													A2($elm$html$Html$Attributes$style, 'font-size', '16px'),
													A2($elm$html$Html$Attributes$style, 'width', '100%')
												]),
											_List_fromArray(
												[
													$elm$html$Html$text('Select a model first')
												]));
									}
								}()
								])) : $elm$html$Html$text(''),
							A2(
							$elm$html$Html$div,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$class('raw-data-section')
								]),
							_List_fromArray(
								[
									A2(
									$elm$html$Html$button,
									_List_fromArray(
										[
											$elm$html$Html$Events$onClick($author$project$ImageGallery$ToggleRawData),
											$elm$html$Html$Attributes$class('toggle-raw-data')
										]),
									_List_fromArray(
										[
											$elm$html$Html$text(
											model.showRawData ? '▼ Hide Raw Data' : '▶ Show Raw Data')
										])),
									model.showRawData ? A2(
									$elm$html$Html$div,
									_List_fromArray(
										[
											$elm$html$Html$Attributes$class('raw-data-content')
										]),
									_List_fromArray(
										[
											A2($author$project$ImageGallery$viewRawDataField, 'Parameters', imageRecord.parameters),
											A2($author$project$ImageGallery$viewRawDataField, 'Metadata', imageRecord.metadata)
										])) : $elm$html$Html$text('')
								]))
						]))
				]));
	});
var $author$project$ImageGallery$view = function (model) {
	return A2(
		$elm$html$Html$div,
		_List_fromArray(
			[
				$elm$html$Html$Attributes$class('image-gallery-page')
			]),
		_List_fromArray(
			[
				A2(
				$elm$html$Html$h1,
				_List_Nil,
				_List_fromArray(
					[
						$elm$html$Html$text('Generated Images')
					])),
				A2(
				$elm$html$Html$button,
				_List_fromArray(
					[
						$elm$html$Html$Events$onClick($author$project$ImageGallery$FetchImages),
						$elm$html$Html$Attributes$disabled(model.loading),
						$elm$html$Html$Attributes$class('refresh-button')
					]),
				_List_fromArray(
					[
						$elm$html$Html$text(
						model.loading ? 'Loading...' : 'Refresh')
					])),
				function () {
				var _v0 = model.error;
				if (_v0.$ === 'Just') {
					var err = _v0.a;
					return A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('error')
							]),
						_List_fromArray(
							[
								$elm$html$Html$text(err)
							]));
				} else {
					return $elm$html$Html$text('');
				}
			}(),
				(model.loading && $elm$core$List$isEmpty(model.images)) ? A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('loading-text')
					]),
				_List_fromArray(
					[
						$elm$html$Html$text('Loading images...')
					])) : ($elm$core$List$isEmpty(model.images) ? A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('empty-state')
					]),
				_List_fromArray(
					[
						$elm$html$Html$text('No images generated yet. Go to the Video Models page to generate some!')
					])) : A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('images-grid')
					]),
				A2($elm$core$List$map, $author$project$ImageGallery$viewImageCard, model.images))),
				function () {
				var _v1 = model.selectedImage;
				if (_v1.$ === 'Just') {
					var video = _v1.a;
					return A2($author$project$ImageGallery$viewImageModal, model, video);
				} else {
					return $elm$html$Html$text('');
				}
			}()
			]));
};
var $author$project$SimulationGallery$SelectVideo = function (a) {
	return {$: 'SelectVideo', a: a};
};
var $author$project$SimulationGallery$formatDate = function (dateStr) {
	return A2($elm$core$String$left, 19, dateStr);
};
var $elm$html$Html$video = _VirtualDom_node('video');
var $elm$core$String$replace = F3(
	function (before, after, string) {
		return A2(
			$elm$core$String$join,
			after,
			A2($elm$core$String$split, before, string));
	});
var $author$project$SimulationGallery$videoUrlFromPath = function (path) {
	return A3($elm$core$String$replace, 'backend/DATA/', '/data/', path);
};
var $author$project$SimulationGallery$viewVideoCard = function (videoRecord) {
	return A2(
		$elm$html$Html$div,
		_List_fromArray(
			[
				$elm$html$Html$Attributes$class('video-card simulation-card'),
				$elm$html$Html$Events$onClick(
				$author$project$SimulationGallery$SelectVideo(videoRecord))
			]),
		_List_fromArray(
			[
				A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('video-thumbnail')
					]),
				_List_fromArray(
					[
						A2(
						$elm$html$Html$video,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$src(
								$author$project$SimulationGallery$videoUrlFromPath(videoRecord.videoPath)),
								A2($elm$html$Html$Attributes$attribute, 'preload', 'metadata')
							]),
						_List_Nil)
					])),
				A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('video-card-info')
					]),
				_List_fromArray(
					[
						A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('video-prompt')
							]),
						_List_fromArray(
							[
								function () {
								var _v0 = videoRecord.sceneContext;
								if (_v0.$ === 'Just') {
									var context = _v0.a;
									return $elm$html$Html$text(context);
								} else {
									return $elm$html$Html$text(
										'Genesis Simulation #' + $elm$core$String$fromInt(videoRecord.id));
								}
							}()
							])),
						A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('video-meta')
							]),
						_List_fromArray(
							[
								A2(
								$elm$html$Html$span,
								_List_fromArray(
									[
										$elm$html$Html$Attributes$class('video-quality')
									]),
								_List_fromArray(
									[
										$elm$html$Html$text(
										$elm$core$String$toUpper(videoRecord.quality) + ' quality')
									])),
								A2(
								$elm$html$Html$span,
								_List_fromArray(
									[
										$elm$html$Html$Attributes$class('video-duration')
									]),
								_List_fromArray(
									[
										$elm$html$Html$text(
										$elm$core$String$fromFloat(videoRecord.duration) + ('s @ ' + ($elm$core$String$fromInt(videoRecord.fps) + 'fps')))
									])),
								A2(
								$elm$html$Html$span,
								_List_fromArray(
									[
										$elm$html$Html$Attributes$class('video-resolution')
									]),
								_List_fromArray(
									[
										$elm$html$Html$text(videoRecord.resolution)
									])),
								A2(
								$elm$html$Html$span,
								_List_fromArray(
									[
										$elm$html$Html$Attributes$class('video-date')
									]),
								_List_fromArray(
									[
										$elm$html$Html$text(
										$author$project$SimulationGallery$formatDate(videoRecord.createdAt))
									]))
							]))
					]))
			]));
};
var $author$project$SimulationGallery$CloseVideo = {$: 'CloseVideo'};
var $author$project$SimulationGallery$ToggleRawData = {$: 'ToggleRawData'};
var $author$project$SimulationGallery$NoOp = {$: 'NoOp'};
var $author$project$SimulationGallery$onClickNoBubble = A2(
	$elm$html$Html$Events$stopPropagationOn,
	'click',
	$elm$json$Json$Decode$succeed(
		_Utils_Tuple2($author$project$SimulationGallery$NoOp, true)));
var $elm$html$Html$li = _VirtualDom_node('li');
var $author$project$SimulationGallery$viewObjectDescriptions = function (descriptionsValue) {
	var _v0 = A2(
		$elm$json$Json$Decode$decodeValue,
		$elm$json$Json$Decode$dict($elm$json$Json$Decode$string),
		descriptionsValue);
	if (_v0.$ === 'Ok') {
		var descriptions = _v0.a;
		return A2(
			$elm$html$Html$ul,
			_List_fromArray(
				[
					$elm$html$Html$Attributes$class('object-descriptions-list')
				]),
			A2(
				$elm$core$List$map,
				function (_v1) {
					var objId = _v1.a;
					var desc = _v1.b;
					return A2(
						$elm$html$Html$li,
						_List_Nil,
						_List_fromArray(
							[
								A2(
								$elm$html$Html$strong,
								_List_Nil,
								_List_fromArray(
									[
										$elm$html$Html$text(objId + ': ')
									])),
								$elm$html$Html$text(desc)
							]));
				},
				$elm$core$Dict$toList(descriptions)));
	} else {
		return A2(
			$elm$html$Html$pre,
			_List_fromArray(
				[
					$elm$html$Html$Attributes$class('raw-json')
				]),
			_List_fromArray(
				[
					$elm$html$Html$text(
					A2($elm$json$Json$Encode$encode, 2, descriptionsValue))
				]));
	}
};
var $author$project$SimulationGallery$viewRawDataField = F2(
	function (label, maybeValue) {
		if (maybeValue.$ === 'Just') {
			var value = maybeValue.a;
			return A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('raw-data-field')
					]),
				_List_fromArray(
					[
						A2(
						$elm$html$Html$h4,
						_List_Nil,
						_List_fromArray(
							[
								$elm$html$Html$text(label)
							])),
						A2(
						$elm$html$Html$pre,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('raw-json')
							]),
						_List_fromArray(
							[
								$elm$html$Html$text(
								A2($elm$json$Json$Encode$encode, 2, value))
							]))
					]));
		} else {
			return $elm$html$Html$text('');
		}
	});
var $author$project$SimulationGallery$viewVideoModal = F2(
	function (model, videoRecord) {
		return A2(
			$elm$html$Html$div,
			_List_fromArray(
				[
					$elm$html$Html$Attributes$class('modal-overlay'),
					$elm$html$Html$Events$onClick($author$project$SimulationGallery$CloseVideo)
				]),
			_List_fromArray(
				[
					A2(
					$elm$html$Html$div,
					_List_fromArray(
						[
							$elm$html$Html$Attributes$class('modal-content simulation-modal'),
							$author$project$SimulationGallery$onClickNoBubble
						]),
					_List_fromArray(
						[
							A2(
							$elm$html$Html$button,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$class('modal-close'),
									$elm$html$Html$Events$onClick($author$project$SimulationGallery$CloseVideo)
								]),
							_List_fromArray(
								[
									$elm$html$Html$text('×')
								])),
							A2(
							$elm$html$Html$h2,
							_List_Nil,
							_List_fromArray(
								[
									$elm$html$Html$text('Genesis Simulation')
								])),
							A2(
							$elm$html$Html$video,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$src(
									$author$project$SimulationGallery$videoUrlFromPath(videoRecord.videoPath)),
									$elm$html$Html$Attributes$controls(true),
									A2($elm$html$Html$Attributes$attribute, 'width', '100%'),
									$elm$html$Html$Attributes$class('modal-video'),
									A2($elm$html$Html$Attributes$attribute, 'loop', 'true')
								]),
							_List_Nil),
							A2(
							$elm$html$Html$div,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$class('modal-details')
								]),
							_List_fromArray(
								[
									function () {
									var _v0 = videoRecord.sceneContext;
									if (_v0.$ === 'Just') {
										var context = _v0.a;
										return A2(
											$elm$html$Html$div,
											_List_fromArray(
												[
													$elm$html$Html$Attributes$class('detail-row')
												]),
											_List_fromArray(
												[
													A2(
													$elm$html$Html$strong,
													_List_Nil,
													_List_fromArray(
														[
															$elm$html$Html$text('Scene Context: ')
														])),
													$elm$html$Html$text(context)
												]));
									} else {
										return $elm$html$Html$text('');
									}
								}(),
									A2(
									$elm$html$Html$div,
									_List_fromArray(
										[
											$elm$html$Html$Attributes$class('detail-row')
										]),
									_List_fromArray(
										[
											A2(
											$elm$html$Html$strong,
											_List_Nil,
											_List_fromArray(
												[
													$elm$html$Html$text('Quality: ')
												])),
											$elm$html$Html$text(
											$elm$core$String$toUpper(videoRecord.quality))
										])),
									A2(
									$elm$html$Html$div,
									_List_fromArray(
										[
											$elm$html$Html$Attributes$class('detail-row')
										]),
									_List_fromArray(
										[
											A2(
											$elm$html$Html$strong,
											_List_Nil,
											_List_fromArray(
												[
													$elm$html$Html$text('Duration: ')
												])),
											$elm$html$Html$text(
											$elm$core$String$fromFloat(videoRecord.duration) + (' seconds @ ' + ($elm$core$String$fromInt(videoRecord.fps) + ' fps')))
										])),
									A2(
									$elm$html$Html$div,
									_List_fromArray(
										[
											$elm$html$Html$Attributes$class('detail-row')
										]),
									_List_fromArray(
										[
											A2(
											$elm$html$Html$strong,
											_List_Nil,
											_List_fromArray(
												[
													$elm$html$Html$text('Resolution: ')
												])),
											$elm$html$Html$text(videoRecord.resolution)
										])),
									A2(
									$elm$html$Html$div,
									_List_fromArray(
										[
											$elm$html$Html$Attributes$class('detail-row')
										]),
									_List_fromArray(
										[
											A2(
											$elm$html$Html$strong,
											_List_Nil,
											_List_fromArray(
												[
													$elm$html$Html$text('Created: ')
												])),
											$elm$html$Html$text(videoRecord.createdAt)
										])),
									A2(
									$elm$html$Html$div,
									_List_fromArray(
										[
											$elm$html$Html$Attributes$class('detail-row')
										]),
									_List_fromArray(
										[
											A2(
											$elm$html$Html$strong,
											_List_Nil,
											_List_fromArray(
												[
													$elm$html$Html$text('Status: ')
												])),
											$elm$html$Html$text(videoRecord.status)
										])),
									function () {
									var _v1 = videoRecord.objectDescriptions;
									if (_v1.$ === 'Just') {
										var descriptions = _v1.a;
										return A2(
											$elm$html$Html$div,
											_List_fromArray(
												[
													$elm$html$Html$Attributes$class('detail-row object-descriptions')
												]),
											_List_fromArray(
												[
													A2(
													$elm$html$Html$strong,
													_List_Nil,
													_List_fromArray(
														[
															$elm$html$Html$text('Object Descriptions:')
														])),
													$author$project$SimulationGallery$viewObjectDescriptions(descriptions)
												]));
									} else {
										return $elm$html$Html$text('');
									}
								}()
								])),
							A2(
							$elm$html$Html$div,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$class('raw-data-section')
								]),
							_List_fromArray(
								[
									A2(
									$elm$html$Html$button,
									_List_fromArray(
										[
											$elm$html$Html$Events$onClick($author$project$SimulationGallery$ToggleRawData),
											$elm$html$Html$Attributes$class('toggle-raw-data')
										]),
									_List_fromArray(
										[
											$elm$html$Html$text(
											model.showRawData ? '▼ Hide Raw Data' : '▶ Show Raw Data')
										])),
									model.showRawData ? A2(
									$elm$html$Html$div,
									_List_fromArray(
										[
											$elm$html$Html$Attributes$class('raw-data-content')
										]),
									_List_fromArray(
										[
											A2($author$project$SimulationGallery$viewRawDataField, 'Object Descriptions', videoRecord.objectDescriptions),
											A2($author$project$SimulationGallery$viewRawDataField, 'Metadata', videoRecord.metadata)
										])) : $elm$html$Html$text('')
								]))
						]))
				]));
	});
var $author$project$SimulationGallery$view = function (model) {
	return A2(
		$elm$html$Html$div,
		_List_fromArray(
			[
				$elm$html$Html$Attributes$class('video-gallery-page simulation-gallery-page')
			]),
		_List_fromArray(
			[
				A2(
				$elm$html$Html$h1,
				_List_Nil,
				_List_fromArray(
					[
						$elm$html$Html$text('Genesis Simulation Gallery')
					])),
				A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('gallery-header')
					]),
				_List_fromArray(
					[
						A2(
						$elm$html$Html$p,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('gallery-description')
							]),
						_List_fromArray(
							[
								$elm$html$Html$text('Photorealistic simulations rendered with Genesis physics engine and LLM semantic augmentation')
							])),
						A2(
						$elm$html$Html$button,
						_List_fromArray(
							[
								$elm$html$Html$Events$onClick($author$project$SimulationGallery$FetchVideos),
								$elm$html$Html$Attributes$disabled(model.loading),
								$elm$html$Html$Attributes$class('refresh-button')
							]),
						_List_fromArray(
							[
								$elm$html$Html$text(
								model.loading ? 'Loading...' : 'Refresh')
							]))
					])),
				function () {
				var _v0 = model.error;
				if (_v0.$ === 'Just') {
					var err = _v0.a;
					return A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('error')
							]),
						_List_fromArray(
							[
								$elm$html$Html$text(err)
							]));
				} else {
					return $elm$html$Html$text('');
				}
			}(),
				(model.loading && $elm$core$List$isEmpty(model.videos)) ? A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('loading-text')
					]),
				_List_fromArray(
					[
						$elm$html$Html$text('Loading simulations...')
					])) : ($elm$core$List$isEmpty(model.videos) ? A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('empty-state')
					]),
				_List_fromArray(
					[
						$elm$html$Html$text('No simulations generated yet. Create a scene in the editor and click \'Render with Genesis\' to generate your first photorealistic simulation!')
					])) : A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('videos-grid')
					]),
				A2($elm$core$List$map, $author$project$SimulationGallery$viewVideoCard, model.videos))),
				function () {
				var _v1 = model.selectedVideo;
				if (_v1.$ === 'Just') {
					var video = _v1.a;
					return A2($author$project$SimulationGallery$viewVideoModal, model, video);
				} else {
					return $elm$html$Html$text('');
				}
			}()
			]));
};
var $author$project$Video$FetchModels = {$: 'FetchModels'};
var $author$project$Video$GenerateVideo = {$: 'GenerateVideo'};
var $author$project$Video$UpdateSearch = function (a) {
	return {$: 'UpdateSearch', a: a};
};
var $author$project$Video$hasEmptyRequiredParameters = F2(
	function (params, requiredFields) {
		return A2(
			$elm$core$List$any,
			function (param) {
				return A2($elm$core$List$member, param.key, requiredFields) && $elm$core$String$isEmpty(
					$elm$core$String$trim(param.value));
			},
			params);
	});
var $author$project$Video$viewModelOption = function (model) {
	return A2(
		$elm$html$Html$div,
		_List_fromArray(
			[
				$elm$html$Html$Attributes$class('model-option'),
				$elm$html$Html$Events$onClick(
				$author$project$Video$SelectModel(model.id))
			]),
		_List_fromArray(
			[
				A2(
				$elm$html$Html$h3,
				_List_Nil,
				_List_fromArray(
					[
						$elm$html$Html$text(model.name)
					])),
				A2(
				$elm$html$Html$p,
				_List_Nil,
				_List_fromArray(
					[
						$elm$html$Html$text(model.description)
					]))
			]));
};
var $author$project$Video$FileSelected = F2(
	function (a, b) {
		return {$: 'FileSelected', a: a, b: b};
	});
var $author$project$Video$fileDecoder = function (paramKey) {
	return A2(
		$elm$json$Json$Decode$map,
		$author$project$Video$FileSelected(paramKey),
		A2(
			$elm$json$Json$Decode$at,
			_List_fromArray(
				['target', 'files', '0']),
			$elm$file$File$decoder));
};
var $author$project$Video$capitalize = function (str) {
	var _v0 = $elm$core$String$uncons(str);
	if (_v0.$ === 'Just') {
		var _v1 = _v0.a;
		var first = _v1.a;
		var rest = _v1.b;
		return _Utils_ap(
			$elm$core$String$fromChar(
				$elm$core$Char$toUpper(first)),
			rest);
	} else {
		return str;
	}
};
var $author$project$Video$formatParameterName = function (name) {
	return A2(
		$elm$core$String$join,
		' ',
		A2(
			$elm$core$List$map,
			$author$project$Video$capitalize,
			A2($elm$core$String$split, '_', name)));
};
var $author$project$Video$viewParameter = F2(
	function (model, param) {
		var rangeText = function () {
			var _v3 = _Utils_Tuple2(param.minimum, param.maximum);
			if (_v3.a.$ === 'Just') {
				if (_v3.b.$ === 'Just') {
					var min = _v3.a.a;
					var max = _v3.b.a;
					return ' (' + ($elm$core$String$fromFloat(min) + (' - ' + ($elm$core$String$fromFloat(max) + ')')));
				} else {
					var min = _v3.a.a;
					var _v4 = _v3.b;
					return ' (min: ' + ($elm$core$String$fromFloat(min) + ')');
				}
			} else {
				if (_v3.b.$ === 'Just') {
					var _v5 = _v3.a;
					var max = _v3.b.a;
					return ' (max: ' + ($elm$core$String$fromFloat(max) + ')');
				} else {
					var _v6 = _v3.a;
					var _v7 = _v3.b;
					return '';
				}
			}
		}();
		var isUploading = _Utils_eq(
			model.uploadingFile,
			$elm$core$Maybe$Just(param.key));
		var isRequired = A2($elm$core$List$member, param.key, model.requiredFields);
		var labelText = _Utils_ap(
			$author$project$Video$formatParameterName(param.key),
			isRequired ? ' *' : '');
		var isImageField = _Utils_eq(
			param.format,
			$elm$core$Maybe$Just('uri')) || A2(
			$elm$core$String$contains,
			'image',
			$elm$core$String$toLower(param.key));
		var isDisabled = model.isGenerating;
		var fullDescription = function () {
			var _v2 = param.description;
			if (_v2.$ === 'Just') {
				var desc = _v2.a;
				return _Utils_ap(desc, rangeText);
			} else {
				return (rangeText !== '') ? $elm$core$String$trim(rangeText) : '';
			}
		}();
		var defaultHint = function () {
			var _v1 = param._default;
			if (_v1.$ === 'Just') {
				var def = _v1.a;
				return (fullDescription !== '') ? (fullDescription + (' (default: ' + (def + ')'))) : ('default: ' + def);
			} else {
				return fullDescription;
			}
		}();
		return A2(
			$elm$html$Html$div,
			_List_fromArray(
				[
					$elm$html$Html$Attributes$class('parameter-field')
				]),
			_List_fromArray(
				[
					A2(
					$elm$html$Html$label,
					_List_fromArray(
						[
							$elm$html$Html$Attributes$class('parameter-label')
						]),
					_List_fromArray(
						[
							$elm$html$Html$text(labelText),
							(defaultHint !== '') ? A2(
							$elm$html$Html$span,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$class('parameter-hint')
								]),
							_List_fromArray(
								[
									$elm$html$Html$text(' — ' + defaultHint)
								])) : $elm$html$Html$text('')
						])),
					function () {
					var _v0 = param._enum;
					if (_v0.$ === 'Just') {
						var options = _v0.a;
						return A2(
							$elm$html$Html$select,
							_List_fromArray(
								[
									$elm$html$Html$Events$onInput(
									$author$project$Video$UpdateParameter(param.key)),
									$elm$html$Html$Attributes$disabled(isDisabled),
									$elm$html$Html$Attributes$class('parameter-select'),
									$elm$html$Html$Attributes$value(param.value)
								]),
							A2(
								$elm$core$List$cons,
								A2(
									$elm$html$Html$option,
									_List_fromArray(
										[
											$elm$html$Html$Attributes$value('')
										]),
									_List_fromArray(
										[
											$elm$html$Html$text('-- Select --')
										])),
								A2(
									$elm$core$List$map,
									function (opt) {
										return A2(
											$elm$html$Html$option,
											_List_fromArray(
												[
													$elm$html$Html$Attributes$value(opt)
												]),
											_List_fromArray(
												[
													$elm$html$Html$text(opt)
												]));
									},
									options)));
					} else {
						return isImageField ? A2(
							$elm$html$Html$div,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$class('image-upload-container')
								]),
							_List_fromArray(
								[
									A2(
									$elm$html$Html$input,
									_List_fromArray(
										[
											$elm$html$Html$Attributes$type_('file'),
											$elm$html$Html$Attributes$accept('image/*'),
											$elm$html$Html$Attributes$disabled(isDisabled || isUploading),
											$elm$html$Html$Attributes$class('parameter-file-input'),
											$elm$html$Html$Attributes$id('file-' + param.key),
											A2(
											$elm$html$Html$Events$on,
											'change',
											$author$project$Video$fileDecoder(param.key))
										]),
									_List_Nil),
									isUploading ? A2(
									$elm$html$Html$div,
									_List_fromArray(
										[
											$elm$html$Html$Attributes$class('upload-status')
										]),
									_List_fromArray(
										[
											$elm$html$Html$text('Uploading...')
										])) : $elm$html$Html$text(''),
									A2(
									$elm$html$Html$input,
									_List_fromArray(
										[
											$elm$html$Html$Attributes$type_('text'),
											$elm$html$Html$Attributes$placeholder('Or enter image URL...'),
											$elm$html$Html$Attributes$value(param.value),
											$elm$html$Html$Events$onInput(
											$author$project$Video$UpdateParameter(param.key)),
											$elm$html$Html$Attributes$disabled(isDisabled || isUploading),
											$elm$html$Html$Attributes$class('parameter-input')
										]),
									_List_Nil)
								])) : ((param.key === 'prompt') ? A2(
							$elm$html$Html$textarea,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$placeholder(
									A2($elm$core$Maybe$withDefault, 'Enter prompt...', param._default)),
									$elm$html$Html$Attributes$value(param.value),
									$elm$html$Html$Events$onInput(
									$author$project$Video$UpdateParameter(param.key)),
									$elm$html$Html$Attributes$disabled(isDisabled),
									$elm$html$Html$Attributes$class('parameter-input parameter-textarea')
								]),
							_List_Nil) : A2(
							$elm$html$Html$input,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$type_(
									((param.paramType === 'number') || (param.paramType === 'integer')) ? 'number' : 'text'),
									$elm$html$Html$Attributes$placeholder(
									A2($elm$core$Maybe$withDefault, 'Enter ' + (param.key + '...'), param._default)),
									$elm$html$Html$Attributes$value(param.value),
									$elm$html$Html$Events$onInput(
									$author$project$Video$UpdateParameter(param.key)),
									$elm$html$Html$Attributes$disabled(isDisabled),
									$elm$html$Html$Attributes$class('parameter-input')
								]),
							_List_Nil));
					}
				}()
				]));
	});
var $author$project$Video$view = function (model) {
	return A2(
		$elm$html$Html$div,
		_List_fromArray(
			[
				$elm$html$Html$Attributes$class('video-page')
			]),
		_List_fromArray(
			[
				A2(
				$elm$html$Html$h1,
				_List_Nil,
				_List_fromArray(
					[
						$elm$html$Html$text('Video Models Explorer')
					])),
				A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('collection-buttons')
					]),
				_List_fromArray(
					[
						A2(
						$elm$html$Html$button,
						_List_fromArray(
							[
								$elm$html$Html$Events$onClick(
								$author$project$Video$SelectCollection('text-to-video')),
								$elm$html$Html$Attributes$class(
								(model.selectedCollection === 'text-to-video') ? 'collection-button active' : 'collection-button')
							]),
						_List_fromArray(
							[
								$elm$html$Html$text('Text to Video')
							])),
						A2(
						$elm$html$Html$button,
						_List_fromArray(
							[
								$elm$html$Html$Events$onClick(
								$author$project$Video$SelectCollection('image-to-video')),
								$elm$html$Html$Attributes$class(
								(model.selectedCollection === 'image-to-video') ? 'collection-button active' : 'collection-button')
							]),
						_List_fromArray(
							[
								$elm$html$Html$text('Image to Video')
							]))
					])),
				A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('search-section')
					]),
				_List_fromArray(
					[
						A2(
						$elm$html$Html$input,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$type_('text'),
								$elm$html$Html$Attributes$placeholder('Search video models...'),
								$elm$html$Html$Attributes$value(model.searchQuery),
								$elm$html$Html$Events$onInput($author$project$Video$UpdateSearch)
							]),
						_List_Nil),
						A2(
						$elm$html$Html$button,
						_List_fromArray(
							[
								$elm$html$Html$Events$onClick($author$project$Video$FetchModels),
								$elm$html$Html$Attributes$disabled(
								!_Utils_eq(model.models, _List_Nil))
							]),
						_List_fromArray(
							[
								$elm$html$Html$text(
								_Utils_eq(model.models, _List_Nil) ? 'Loading...' : 'Refresh Models')
							]))
					])),
				$elm$core$List$isEmpty(model.models) ? A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('loading-text')
					]),
				_List_fromArray(
					[
						$elm$html$Html$text('Loading models...')
					])) : A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('models-list')
					]),
				A2(
					$elm$core$List$map,
					$author$project$Video$viewModelOption,
					A2(
						$elm$core$List$filter,
						function (m) {
							return A2(
								$elm$core$String$contains,
								$elm$core$String$toLower(model.searchQuery),
								$elm$core$String$toLower(m.name));
						},
						model.models))),
				function () {
				var _v0 = model.selectedModel;
				if (_v0.$ === 'Just') {
					var selected = _v0.a;
					return A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('selected-model'),
								$elm$html$Html$Attributes$id('selected-model-section')
							]),
						_List_fromArray(
							[
								A2(
								$elm$html$Html$h2,
								_List_Nil,
								_List_fromArray(
									[
										$elm$html$Html$text(selected.name)
									])),
								A2(
								$elm$html$Html$p,
								_List_Nil,
								_List_fromArray(
									[
										$elm$html$Html$text(selected.description)
									])),
								A2(
								$elm$html$Html$div,
								_List_fromArray(
									[
										$elm$html$Html$Attributes$class('parameters-form-grid')
									]),
								A2(
									$elm$core$List$map,
									$author$project$Video$viewParameter(model),
									model.parameters)),
								A2(
								$elm$html$Html$button,
								_List_fromArray(
									[
										$elm$html$Html$Events$onClick($author$project$Video$GenerateVideo),
										$elm$html$Html$Attributes$disabled(
										A2($author$project$Video$hasEmptyRequiredParameters, model.parameters, model.requiredFields) || model.isGenerating),
										$elm$html$Html$Attributes$class('generate-button')
									]),
								_List_fromArray(
									[
										$elm$html$Html$text(
										model.isGenerating ? 'Generating...' : 'Generate Video')
									]))
							]));
				} else {
					return (!$elm$core$List$isEmpty(model.models)) ? A2(
						$elm$html$Html$div,
						_List_Nil,
						_List_fromArray(
							[
								$elm$html$Html$text('Select a model from the list above')
							])) : $elm$html$Html$text('');
				}
			}(),
				function () {
				var _v1 = model.outputVideo;
				if (_v1.$ === 'Just') {
					var url = _v1.a;
					return A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('video-output')
							]),
						_List_fromArray(
							[
								A2(
								$elm$html$Html$video,
								_List_fromArray(
									[
										$elm$html$Html$Attributes$src(url),
										$elm$html$Html$Attributes$controls(true),
										A2($elm$html$Html$Attributes$attribute, 'width', '100%')
									]),
								_List_Nil)
							]));
				} else {
					return $elm$html$Html$text('');
				}
			}(),
				function () {
				var _v2 = model.error;
				if (_v2.$ === 'Just') {
					var err = _v2.a;
					return A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('error')
							]),
						_List_fromArray(
							[
								$elm$html$Html$text(err)
							]));
				} else {
					return $elm$html$Html$text('');
				}
			}()
			]));
};
var $author$project$VideoDetail$statusText = function (status) {
	switch (status) {
		case 'processing':
			return '⏳ Processing...';
		case 'completed':
			return '✅ Completed';
		case 'failed':
			return '❌ Failed';
		case 'canceled':
			return '🚫 Canceled';
		default:
			return status;
	}
};
var $author$project$VideoDetail$viewVideoDetail = function (video) {
	return A2(
		$elm$html$Html$div,
		_List_fromArray(
			[
				$elm$html$Html$Attributes$class('video-detail')
			]),
		_List_fromArray(
			[
				A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('video-info')
					]),
				_List_fromArray(
					[
						A2(
						$elm$html$Html$h2,
						_List_Nil,
						_List_fromArray(
							[
								$elm$html$Html$text('Video Details')
							])),
						A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('info-row')
							]),
						_List_fromArray(
							[
								A2(
								$elm$html$Html$span,
								_List_fromArray(
									[
										$elm$html$Html$Attributes$class('label')
									]),
								_List_fromArray(
									[
										$elm$html$Html$text('Status: ')
									])),
								A2(
								$elm$html$Html$span,
								_List_fromArray(
									[
										$elm$html$Html$Attributes$class(
										'status status-' + $elm$core$String$toLower(video.status))
									]),
								_List_fromArray(
									[
										$elm$html$Html$text(
										$author$project$VideoDetail$statusText(video.status))
									]))
							])),
						A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('info-row')
							]),
						_List_fromArray(
							[
								A2(
								$elm$html$Html$span,
								_List_fromArray(
									[
										$elm$html$Html$Attributes$class('label')
									]),
								_List_fromArray(
									[
										$elm$html$Html$text('Model: ')
									])),
								A2(
								$elm$html$Html$span,
								_List_Nil,
								_List_fromArray(
									[
										$elm$html$Html$text(video.modelId)
									]))
							])),
						A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('info-row')
							]),
						_List_fromArray(
							[
								A2(
								$elm$html$Html$span,
								_List_fromArray(
									[
										$elm$html$Html$Attributes$class('label')
									]),
								_List_fromArray(
									[
										$elm$html$Html$text('Prompt: ')
									])),
								A2(
								$elm$html$Html$p,
								_List_fromArray(
									[
										$elm$html$Html$Attributes$class('prompt')
									]),
								_List_fromArray(
									[
										$elm$html$Html$text(video.prompt)
									]))
							])),
						A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('info-row')
							]),
						_List_fromArray(
							[
								A2(
								$elm$html$Html$span,
								_List_fromArray(
									[
										$elm$html$Html$Attributes$class('label')
									]),
								_List_fromArray(
									[
										$elm$html$Html$text('Created: ')
									])),
								A2(
								$elm$html$Html$span,
								_List_Nil,
								_List_fromArray(
									[
										$elm$html$Html$text(video.createdAt)
									]))
							]))
					])),
				function () {
				var _v0 = video.status;
				switch (_v0) {
					case 'completed':
						return $elm$core$String$isEmpty(video.videoUrl) ? A2(
							$elm$html$Html$div,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$class('error')
								]),
							_List_fromArray(
								[
									$elm$html$Html$text('Video completed but no URL available')
								])) : A2(
							$elm$html$Html$div,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$class('video-player')
								]),
							_List_fromArray(
								[
									A2(
									$elm$html$Html$h3,
									_List_Nil,
									_List_fromArray(
										[
											$elm$html$Html$text('Generated Video')
										])),
									A3(
									$elm$html$Html$node,
									'video',
									_List_fromArray(
										[
											$elm$html$Html$Attributes$src(video.videoUrl),
											$elm$html$Html$Attributes$controls(true),
											A2($elm$html$Html$Attributes$attribute, 'width', '100%'),
											A2($elm$html$Html$Attributes$attribute, 'style', 'max-width: 800px; border-radius: 8px;')
										]),
									_List_Nil),
									A2(
									$elm$html$Html$div,
									_List_fromArray(
										[
											$elm$html$Html$Attributes$class('video-actions')
										]),
									_List_fromArray(
										[
											A2(
											$elm$html$Html$a,
											_List_fromArray(
												[
													$elm$html$Html$Attributes$href(video.videoUrl),
													$elm$html$Html$Attributes$download(''),
													$elm$html$Html$Attributes$class('download-button')
												]),
											_List_fromArray(
												[
													$elm$html$Html$text('Download Video')
												]))
										]))
								]));
					case 'processing':
						return A2(
							$elm$html$Html$div,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$class('processing')
								]),
							_List_fromArray(
								[
									A2(
									$elm$html$Html$div,
									_List_fromArray(
										[
											$elm$html$Html$Attributes$class('spinner')
										]),
									_List_Nil),
									A2(
									$elm$html$Html$p,
									_List_Nil,
									_List_fromArray(
										[
											$elm$html$Html$text('Your video is being generated... This may take 30-60 seconds.')
										]))
								]));
					case 'failed':
						return A2(
							$elm$html$Html$div,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$class('error')
								]),
							_List_fromArray(
								[
									$elm$html$Html$text('Video generation failed. Please try again with different parameters.')
								]));
					case 'canceled':
						return A2(
							$elm$html$Html$div,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$class('info')
								]),
							_List_fromArray(
								[
									$elm$html$Html$text('Video generation was canceled.')
								]));
					default:
						return A2(
							$elm$html$Html$div,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$class('info')
								]),
							_List_fromArray(
								[
									$elm$html$Html$text('Status: ' + video.status)
								]));
				}
			}()
			]));
};
var $author$project$VideoDetail$view = function (model) {
	return A2(
		$elm$html$Html$div,
		_List_fromArray(
			[
				$elm$html$Html$Attributes$class('video-detail-page')
			]),
		_List_fromArray(
			[
				A2(
				$elm$html$Html$h1,
				_List_Nil,
				_List_fromArray(
					[
						$elm$html$Html$text('Video Generation Status')
					])),
				function () {
				var _v0 = model.error;
				if (_v0.$ === 'Just') {
					var err = _v0.a;
					return A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('error')
							]),
						_List_fromArray(
							[
								$elm$html$Html$text(err)
							]));
				} else {
					return $elm$html$Html$text('');
				}
			}(),
				function () {
				var _v1 = model.video;
				if (_v1.$ === 'Just') {
					var video = _v1.a;
					return $author$project$VideoDetail$viewVideoDetail(video);
				} else {
					return A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('loading')
							]),
						_List_fromArray(
							[
								$elm$html$Html$text('Loading video information...')
							]));
				}
			}()
			]));
};
var $author$project$VideoGallery$NextPage = {$: 'NextPage'};
var $author$project$VideoGallery$PrevPage = {$: 'PrevPage'};
var $author$project$VideoGallery$viewPagination = F4(
	function (currentPage, maxPage, hasPrevPage, hasNextPage) {
		return A2(
			$elm$html$Html$div,
			_List_fromArray(
				[
					$elm$html$Html$Attributes$class('pagination')
				]),
			_List_fromArray(
				[
					A2(
					$elm$html$Html$button,
					_List_fromArray(
						[
							$elm$html$Html$Events$onClick($author$project$VideoGallery$PrevPage),
							$elm$html$Html$Attributes$disabled(!hasPrevPage),
							$elm$html$Html$Attributes$class('pagination-button')
						]),
					_List_fromArray(
						[
							$elm$html$Html$text('← Previous')
						])),
					A2(
					$elm$html$Html$div,
					_List_fromArray(
						[
							$elm$html$Html$Attributes$class('pagination-info')
						]),
					_List_fromArray(
						[
							$elm$html$Html$text(
							'Page ' + ($elm$core$String$fromInt(currentPage) + (' of ' + $elm$core$String$fromInt(maxPage))))
						])),
					A2(
					$elm$html$Html$button,
					_List_fromArray(
						[
							$elm$html$Html$Events$onClick($author$project$VideoGallery$NextPage),
							$elm$html$Html$Attributes$disabled(!hasNextPage),
							$elm$html$Html$Attributes$class('pagination-button')
						]),
					_List_fromArray(
						[
							$elm$html$Html$text('Next →')
						]))
				]));
	});
var $author$project$VideoGallery$SelectVideo = function (a) {
	return {$: 'SelectVideo', a: a};
};
var $author$project$VideoGallery$extractErrorMessage = function (videoRecord) {
	var _v0 = videoRecord.metadata;
	if (_v0.$ === 'Just') {
		var metadataValue = _v0.a;
		return $elm$core$Result$toMaybe(
			A2(
				$elm$json$Json$Decode$decodeValue,
				A2($elm$json$Json$Decode$field, 'error', $elm$json$Json$Decode$string),
				metadataValue));
	} else {
		return $elm$core$Maybe$Nothing;
	}
};
var $author$project$VideoGallery$formatDate = function (dateStr) {
	return A2($elm$core$String$left, 19, dateStr);
};
var $author$project$VideoGallery$truncateString = F2(
	function (maxLength, str) {
		return (_Utils_cmp(
			$elm$core$String$length(str),
			maxLength) < 1) ? str : (A2($elm$core$String$left, maxLength - 3, str) + '...');
	});
var $author$project$VideoGallery$viewVideoCard = function (videoRecord) {
	var errorMessage = $author$project$VideoGallery$extractErrorMessage(videoRecord);
	return A2(
		$elm$html$Html$div,
		_List_fromArray(
			[
				$elm$html$Html$Attributes$class('video-card'),
				$elm$html$Html$Events$onClick(
				$author$project$VideoGallery$SelectVideo(videoRecord))
			]),
		_List_fromArray(
			[
				A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('video-thumbnail')
					]),
				_List_fromArray(
					[
						$elm$core$String$isEmpty(videoRecord.videoUrl) ? A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								A2($elm$html$Html$Attributes$style, 'width', '100%'),
								A2($elm$html$Html$Attributes$style, 'height', '100%'),
								A2($elm$html$Html$Attributes$style, 'display', 'flex'),
								A2($elm$html$Html$Attributes$style, 'flex-direction', 'column'),
								A2($elm$html$Html$Attributes$style, 'align-items', 'center'),
								A2($elm$html$Html$Attributes$style, 'justify-content', 'center'),
								A2(
								$elm$html$Html$Attributes$style,
								'background',
								(videoRecord.status === 'failed') ? '#c33' : '#333'),
								A2($elm$html$Html$Attributes$style, 'color', '#fff'),
								A2($elm$html$Html$Attributes$style, 'padding', '10px')
							]),
						_List_fromArray(
							[
								A2(
								$elm$html$Html$div,
								_List_fromArray(
									[
										A2($elm$html$Html$Attributes$style, 'font-weight', 'bold'),
										A2($elm$html$Html$Attributes$style, 'margin-bottom', '5px')
									]),
								_List_fromArray(
									[
										$elm$html$Html$text(
										$elm$core$String$toUpper(videoRecord.status))
									])),
								function () {
								if (errorMessage.$ === 'Just') {
									var err = errorMessage.a;
									return A2(
										$elm$html$Html$div,
										_List_fromArray(
											[
												A2($elm$html$Html$Attributes$style, 'font-size', '12px'),
												A2($elm$html$Html$Attributes$style, 'text-align', 'center')
											]),
										_List_fromArray(
											[
												$elm$html$Html$text(
												A2($author$project$VideoGallery$truncateString, 60, err))
											]));
								} else {
									return $elm$html$Html$text('');
								}
							}()
							])) : A2(
						$elm$html$Html$img,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$src(videoRecord.thumbnailUrl),
								A2($elm$html$Html$Attributes$style, 'width', '100%'),
								A2($elm$html$Html$Attributes$style, 'height', '100%'),
								A2($elm$html$Html$Attributes$style, 'object-fit', 'cover')
							]),
						_List_Nil)
					])),
				A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('video-card-info')
					]),
				_List_fromArray(
					[
						A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('video-prompt')
							]),
						_List_fromArray(
							[
								$elm$html$Html$text(videoRecord.prompt)
							])),
						A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('video-meta')
							]),
						_List_fromArray(
							[
								A2(
								$elm$html$Html$span,
								_List_fromArray(
									[
										$elm$html$Html$Attributes$class('video-model')
									]),
								_List_fromArray(
									[
										$elm$html$Html$text(videoRecord.modelId)
									])),
								A2(
								$elm$html$Html$span,
								_List_fromArray(
									[
										$elm$html$Html$Attributes$class('video-date')
									]),
								_List_fromArray(
									[
										$elm$html$Html$text(
										$author$project$VideoGallery$formatDate(videoRecord.createdAt))
									]))
							]))
					]))
			]));
};
var $author$project$VideoGallery$CloseVideo = {$: 'CloseVideo'};
var $author$project$VideoGallery$ToggleRawData = {$: 'ToggleRawData'};
var $author$project$VideoGallery$NoOp = {$: 'NoOp'};
var $author$project$VideoGallery$onClickNoBubble = A2(
	$elm$html$Html$Events$stopPropagationOn,
	'click',
	$elm$json$Json$Decode$succeed(
		_Utils_Tuple2($author$project$VideoGallery$NoOp, true)));
var $author$project$VideoGallery$viewRawDataField = F2(
	function (label, maybeValue) {
		if (maybeValue.$ === 'Just') {
			var value = maybeValue.a;
			return A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('raw-data-field')
					]),
				_List_fromArray(
					[
						A2(
						$elm$html$Html$h4,
						_List_Nil,
						_List_fromArray(
							[
								$elm$html$Html$text(label)
							])),
						A2(
						$elm$html$Html$pre,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('raw-json')
							]),
						_List_fromArray(
							[
								$elm$html$Html$text(
								A2(
									$elm$core$Result$withDefault,
									'Invalid JSON',
									A2(
										$elm$core$Result$map,
										$elm$json$Json$Encode$encode(2),
										A2($elm$json$Json$Decode$decodeValue, $elm$json$Json$Decode$value, value))))
							]))
					]));
		} else {
			return $elm$html$Html$text('');
		}
	});
var $author$project$VideoGallery$viewVideoModal = F2(
	function (model, videoRecord) {
		var errorMessage = $author$project$VideoGallery$extractErrorMessage(videoRecord);
		return A2(
			$elm$html$Html$div,
			_List_fromArray(
				[
					$elm$html$Html$Attributes$class('modal-overlay'),
					$elm$html$Html$Events$onClick($author$project$VideoGallery$CloseVideo)
				]),
			_List_fromArray(
				[
					A2(
					$elm$html$Html$div,
					_List_fromArray(
						[
							$elm$html$Html$Attributes$class('modal-content'),
							$author$project$VideoGallery$onClickNoBubble
						]),
					_List_fromArray(
						[
							A2(
							$elm$html$Html$button,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$class('modal-close'),
									$elm$html$Html$Events$onClick($author$project$VideoGallery$CloseVideo)
								]),
							_List_fromArray(
								[
									$elm$html$Html$text('×')
								])),
							A2(
							$elm$html$Html$h2,
							_List_Nil,
							_List_fromArray(
								[
									$elm$html$Html$text('Generated Video')
								])),
							function () {
							if (errorMessage.$ === 'Just') {
								var err = errorMessage.a;
								return A2(
									$elm$html$Html$div,
									_List_fromArray(
										[
											A2($elm$html$Html$Attributes$style, 'background', '#fee'),
											A2($elm$html$Html$Attributes$style, 'color', '#c33'),
											A2($elm$html$Html$Attributes$style, 'padding', '15px'),
											A2($elm$html$Html$Attributes$style, 'border-radius', '4px'),
											A2($elm$html$Html$Attributes$style, 'margin-bottom', '15px'),
											A2($elm$html$Html$Attributes$style, 'border', '1px solid #fcc')
										]),
									_List_fromArray(
										[
											A2(
											$elm$html$Html$strong,
											_List_Nil,
											_List_fromArray(
												[
													$elm$html$Html$text('Error: ')
												])),
											$elm$html$Html$text(err)
										]));
							} else {
								return $elm$html$Html$text('');
							}
						}(),
							(!$elm$core$String$isEmpty(videoRecord.videoUrl)) ? A2(
							$elm$html$Html$video,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$src(videoRecord.videoUrl),
									$elm$html$Html$Attributes$controls(true),
									A2($elm$html$Html$Attributes$attribute, 'width', '100%'),
									A2($elm$html$Html$Attributes$attribute, 'preload', 'metadata'),
									A2($elm$html$Html$Attributes$attribute, 'poster', videoRecord.thumbnailUrl),
									$elm$html$Html$Attributes$class('modal-video')
								]),
							_List_Nil) : A2(
							$elm$html$Html$div,
							_List_fromArray(
								[
									A2($elm$html$Html$Attributes$style, 'background', '#333'),
									A2($elm$html$Html$Attributes$style, 'color', '#fff'),
									A2($elm$html$Html$Attributes$style, 'padding', '40px'),
									A2($elm$html$Html$Attributes$style, 'text-align', 'center'),
									A2($elm$html$Html$Attributes$style, 'border-radius', '4px'),
									A2($elm$html$Html$Attributes$style, 'margin-bottom', '15px')
								]),
							_List_fromArray(
								[
									$elm$html$Html$text(
									'Video ' + $elm$core$String$toUpper(videoRecord.status))
								])),
							A2(
							$elm$html$Html$div,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$class('modal-details')
								]),
							_List_fromArray(
								[
									A2(
									$elm$html$Html$div,
									_List_fromArray(
										[
											$elm$html$Html$Attributes$class('detail-row')
										]),
									_List_fromArray(
										[
											A2(
											$elm$html$Html$strong,
											_List_Nil,
											_List_fromArray(
												[
													$elm$html$Html$text('Prompt: ')
												])),
											$elm$html$Html$text(videoRecord.prompt)
										])),
									A2(
									$elm$html$Html$div,
									_List_fromArray(
										[
											$elm$html$Html$Attributes$class('detail-row')
										]),
									_List_fromArray(
										[
											A2(
											$elm$html$Html$strong,
											_List_Nil,
											_List_fromArray(
												[
													$elm$html$Html$text('Model: ')
												])),
											$elm$html$Html$text(videoRecord.modelId)
										])),
									function () {
									var _v1 = videoRecord.collection;
									if (_v1.$ === 'Just') {
										var coll = _v1.a;
										return A2(
											$elm$html$Html$div,
											_List_fromArray(
												[
													$elm$html$Html$Attributes$class('detail-row')
												]),
											_List_fromArray(
												[
													A2(
													$elm$html$Html$strong,
													_List_Nil,
													_List_fromArray(
														[
															$elm$html$Html$text('Collection: ')
														])),
													$elm$html$Html$text(coll)
												]));
									} else {
										return $elm$html$Html$text('');
									}
								}(),
									A2(
									$elm$html$Html$div,
									_List_fromArray(
										[
											$elm$html$Html$Attributes$class('detail-row')
										]),
									_List_fromArray(
										[
											A2(
											$elm$html$Html$strong,
											_List_Nil,
											_List_fromArray(
												[
													$elm$html$Html$text('Created: ')
												])),
											$elm$html$Html$text(videoRecord.createdAt)
										])),
									A2(
									$elm$html$Html$div,
									_List_fromArray(
										[
											$elm$html$Html$Attributes$class('detail-row')
										]),
									_List_fromArray(
										[
											A2(
											$elm$html$Html$strong,
											_List_Nil,
											_List_fromArray(
												[
													$elm$html$Html$text('Status: ')
												])),
											A2(
											$elm$html$Html$span,
											_List_fromArray(
												[
													A2(
													$elm$html$Html$Attributes$style,
													'color',
													(videoRecord.status === 'failed') ? '#c33' : 'inherit'),
													A2(
													$elm$html$Html$Attributes$style,
													'font-weight',
													(videoRecord.status === 'failed') ? 'bold' : 'normal')
												]),
											_List_fromArray(
												[
													$elm$html$Html$text(videoRecord.status)
												]))
										]))
								])),
							A2(
							$elm$html$Html$div,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$class('raw-data-section')
								]),
							_List_fromArray(
								[
									A2(
									$elm$html$Html$button,
									_List_fromArray(
										[
											$elm$html$Html$Events$onClick($author$project$VideoGallery$ToggleRawData),
											$elm$html$Html$Attributes$class('toggle-raw-data')
										]),
									_List_fromArray(
										[
											$elm$html$Html$text(
											model.showRawData ? '▼ Hide Raw Data' : '▶ Show Raw Data')
										])),
									model.showRawData ? A2(
									$elm$html$Html$div,
									_List_fromArray(
										[
											$elm$html$Html$Attributes$class('raw-data-content')
										]),
									_List_fromArray(
										[
											A2($author$project$VideoGallery$viewRawDataField, 'Parameters', videoRecord.parameters),
											A2($author$project$VideoGallery$viewRawDataField, 'Metadata', videoRecord.metadata)
										])) : $elm$html$Html$text('')
								]))
						]))
				]));
	});
var $author$project$VideoGallery$view = function (model) {
	var maxPage = $elm$core$Basics$ceiling(model.totalVideos / model.pageSize);
	var hasPrevPage = model.currentPage > 1;
	var hasNextPage = _Utils_cmp(model.currentPage, maxPage) < 0;
	return A2(
		$elm$html$Html$div,
		_List_fromArray(
			[
				$elm$html$Html$Attributes$class('video-gallery-page')
			]),
		_List_fromArray(
			[
				A2(
				$elm$html$Html$h1,
				_List_Nil,
				_List_fromArray(
					[
						$elm$html$Html$text('Generated Videos')
					])),
				A2(
				$elm$html$Html$button,
				_List_fromArray(
					[
						$elm$html$Html$Events$onClick($author$project$VideoGallery$FetchVideos),
						$elm$html$Html$Attributes$disabled(model.loading),
						$elm$html$Html$Attributes$class('refresh-button')
					]),
				_List_fromArray(
					[
						$elm$html$Html$text(
						model.loading ? 'Loading...' : 'Refresh')
					])),
				function () {
				var _v0 = model.error;
				if (_v0.$ === 'Just') {
					var err = _v0.a;
					return A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('error')
							]),
						_List_fromArray(
							[
								$elm$html$Html$text(err)
							]));
				} else {
					return $elm$html$Html$text('');
				}
			}(),
				(model.loading && $elm$core$List$isEmpty(model.videos)) ? A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('loading-text')
					]),
				_List_fromArray(
					[
						$elm$html$Html$text('Loading videos...')
					])) : ($elm$core$List$isEmpty(model.videos) ? A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('empty-state')
					]),
				_List_fromArray(
					[
						$elm$html$Html$text('No videos generated yet. Go to the Video Models page to generate some!')
					])) : A2(
				$elm$html$Html$div,
				_List_Nil,
				_List_fromArray(
					[
						A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('videos-grid')
							]),
						A2($elm$core$List$map, $author$project$VideoGallery$viewVideoCard, model.videos)),
						A4($author$project$VideoGallery$viewPagination, model.currentPage, maxPage, hasPrevPage, hasNextPage)
					]))),
				function () {
				var _v1 = model.selectedVideo;
				if (_v1.$ === 'Just') {
					var video = _v1.a;
					return A2($author$project$VideoGallery$viewVideoModal, model, video);
				} else {
					return $elm$html$Html$text('');
				}
			}()
			]));
};
var $author$project$VideoToText$FetchModels = {$: 'FetchModels'};
var $author$project$VideoToText$GenerateText = {$: 'GenerateText'};
var $author$project$VideoToText$UpdateSearch = function (a) {
	return {$: 'UpdateSearch', a: a};
};
var $author$project$VideoToText$hasEmptyRequiredParameters = F2(
	function (params, requiredFields) {
		return A2(
			$elm$core$List$any,
			function (param) {
				return A2($elm$core$List$member, param.key, requiredFields) && $elm$core$String$isEmpty(
					$elm$core$String$trim(param.value));
			},
			params);
	});
var $author$project$VideoToText$SelectModel = function (a) {
	return {$: 'SelectModel', a: a};
};
var $author$project$VideoToText$viewModelOption = function (model) {
	return A2(
		$elm$html$Html$div,
		_List_fromArray(
			[
				$elm$html$Html$Attributes$class('model-option'),
				$elm$html$Html$Events$onClick(
				$author$project$VideoToText$SelectModel(model.id))
			]),
		_List_fromArray(
			[
				A2(
				$elm$html$Html$h3,
				_List_Nil,
				_List_fromArray(
					[
						$elm$html$Html$text(model.name)
					])),
				A2(
				$elm$html$Html$p,
				_List_Nil,
				_List_fromArray(
					[
						$elm$html$Html$text(model.description)
					]))
			]));
};
var $author$project$VideoToText$UpdateParameter = F2(
	function (a, b) {
		return {$: 'UpdateParameter', a: a, b: b};
	});
var $author$project$VideoToText$FileSelected = F2(
	function (a, b) {
		return {$: 'FileSelected', a: a, b: b};
	});
var $author$project$VideoToText$fileDecoder = function (paramKey) {
	return A2(
		$elm$json$Json$Decode$map,
		$author$project$VideoToText$FileSelected(paramKey),
		A2(
			$elm$json$Json$Decode$at,
			_List_fromArray(
				['target', 'files', '0']),
			$elm$file$File$decoder));
};
var $author$project$VideoToText$capitalize = function (str) {
	var _v0 = $elm$core$String$uncons(str);
	if (_v0.$ === 'Just') {
		var _v1 = _v0.a;
		var first = _v1.a;
		var rest = _v1.b;
		return _Utils_ap(
			$elm$core$String$fromChar(
				$elm$core$Char$toUpper(first)),
			rest);
	} else {
		return str;
	}
};
var $author$project$VideoToText$formatParameterName = function (name) {
	return A2(
		$elm$core$String$join,
		' ',
		A2(
			$elm$core$List$map,
			$author$project$VideoToText$capitalize,
			A2($elm$core$String$split, '_', name)));
};
var $author$project$VideoToText$viewParameter = F2(
	function (model, param) {
		var rangeText = function () {
			var _v3 = _Utils_Tuple2(param.minimum, param.maximum);
			if (_v3.a.$ === 'Just') {
				if (_v3.b.$ === 'Just') {
					var min = _v3.a.a;
					var max = _v3.b.a;
					return ' (' + ($elm$core$String$fromFloat(min) + (' - ' + ($elm$core$String$fromFloat(max) + ')')));
				} else {
					var min = _v3.a.a;
					var _v4 = _v3.b;
					return ' (min: ' + ($elm$core$String$fromFloat(min) + ')');
				}
			} else {
				if (_v3.b.$ === 'Just') {
					var _v5 = _v3.a;
					var max = _v3.b.a;
					return ' (max: ' + ($elm$core$String$fromFloat(max) + ')');
				} else {
					var _v6 = _v3.a;
					var _v7 = _v3.b;
					return '';
				}
			}
		}();
		var isVideoField = _Utils_eq(
			param.format,
			$elm$core$Maybe$Just('uri')) || A2(
			$elm$core$String$contains,
			'video',
			$elm$core$String$toLower(param.key));
		var isUploading = _Utils_eq(
			model.uploadingFile,
			$elm$core$Maybe$Just(param.key));
		var isRequired = A2($elm$core$List$member, param.key, model.requiredFields);
		var labelText = _Utils_ap(
			$author$project$VideoToText$formatParameterName(param.key),
			isRequired ? ' *' : '');
		var isDisabled = model.isGenerating;
		var fullDescription = function () {
			var _v2 = param.description;
			if (_v2.$ === 'Just') {
				var desc = _v2.a;
				return _Utils_ap(desc, rangeText);
			} else {
				return (rangeText !== '') ? $elm$core$String$trim(rangeText) : '';
			}
		}();
		var defaultHint = function () {
			var _v1 = param._default;
			if (_v1.$ === 'Just') {
				var def = _v1.a;
				return (fullDescription !== '') ? (fullDescription + (' (default: ' + (def + ')'))) : ('default: ' + def);
			} else {
				return fullDescription;
			}
		}();
		return A2(
			$elm$html$Html$div,
			_List_fromArray(
				[
					$elm$html$Html$Attributes$class('parameter-field')
				]),
			_List_fromArray(
				[
					A2(
					$elm$html$Html$label,
					_List_fromArray(
						[
							$elm$html$Html$Attributes$class('parameter-label')
						]),
					_List_fromArray(
						[
							$elm$html$Html$text(labelText),
							(defaultHint !== '') ? A2(
							$elm$html$Html$span,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$class('parameter-hint')
								]),
							_List_fromArray(
								[
									$elm$html$Html$text(' — ' + defaultHint)
								])) : $elm$html$Html$text('')
						])),
					function () {
					var _v0 = param._enum;
					if (_v0.$ === 'Just') {
						var options = _v0.a;
						return A2(
							$elm$html$Html$select,
							_List_fromArray(
								[
									$elm$html$Html$Events$onInput(
									$author$project$VideoToText$UpdateParameter(param.key)),
									$elm$html$Html$Attributes$disabled(isDisabled),
									$elm$html$Html$Attributes$class('parameter-select'),
									$elm$html$Html$Attributes$value(param.value)
								]),
							A2(
								$elm$core$List$cons,
								A2(
									$elm$html$Html$option,
									_List_fromArray(
										[
											$elm$html$Html$Attributes$value('')
										]),
									_List_fromArray(
										[
											$elm$html$Html$text('-- Select --')
										])),
								A2(
									$elm$core$List$map,
									function (opt) {
										return A2(
											$elm$html$Html$option,
											_List_fromArray(
												[
													$elm$html$Html$Attributes$value(opt)
												]),
											_List_fromArray(
												[
													$elm$html$Html$text(opt)
												]));
									},
									options)));
					} else {
						return isVideoField ? A2(
							$elm$html$Html$div,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$class('image-upload-container')
								]),
							_List_fromArray(
								[
									A2(
									$elm$html$Html$input,
									_List_fromArray(
										[
											$elm$html$Html$Attributes$type_('file'),
											$elm$html$Html$Attributes$accept('video/*'),
											$elm$html$Html$Attributes$disabled(isDisabled || isUploading),
											$elm$html$Html$Attributes$class('parameter-file-input'),
											$elm$html$Html$Attributes$id('file-' + param.key),
											A2(
											$elm$html$Html$Events$on,
											'change',
											$author$project$VideoToText$fileDecoder(param.key))
										]),
									_List_Nil),
									isUploading ? A2(
									$elm$html$Html$div,
									_List_fromArray(
										[
											$elm$html$Html$Attributes$class('upload-status')
										]),
									_List_fromArray(
										[
											$elm$html$Html$text('Uploading...')
										])) : $elm$html$Html$text(''),
									A2(
									$elm$html$Html$input,
									_List_fromArray(
										[
											$elm$html$Html$Attributes$type_('text'),
											$elm$html$Html$Attributes$placeholder('Or enter video URL...'),
											$elm$html$Html$Attributes$value(param.value),
											$elm$html$Html$Events$onInput(
											$author$project$VideoToText$UpdateParameter(param.key)),
											$elm$html$Html$Attributes$disabled(isDisabled || isUploading),
											$elm$html$Html$Attributes$class('parameter-input')
										]),
									_List_Nil)
								])) : ((param.key === 'prompt') ? A2(
							$elm$html$Html$textarea,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$placeholder(
									A2($elm$core$Maybe$withDefault, 'Enter prompt...', param._default)),
									$elm$html$Html$Attributes$value(param.value),
									$elm$html$Html$Events$onInput(
									$author$project$VideoToText$UpdateParameter(param.key)),
									$elm$html$Html$Attributes$disabled(isDisabled),
									$elm$html$Html$Attributes$class('parameter-input parameter-textarea')
								]),
							_List_Nil) : A2(
							$elm$html$Html$input,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$type_(
									((param.paramType === 'number') || (param.paramType === 'integer')) ? 'number' : 'text'),
									$elm$html$Html$Attributes$placeholder(
									A2($elm$core$Maybe$withDefault, 'Enter ' + (param.key + '...'), param._default)),
									$elm$html$Html$Attributes$value(param.value),
									$elm$html$Html$Events$onInput(
									$author$project$VideoToText$UpdateParameter(param.key)),
									$elm$html$Html$Attributes$disabled(isDisabled),
									$elm$html$Html$Attributes$class('parameter-input')
								]),
							_List_Nil));
					}
				}()
				]));
	});
var $author$project$VideoToText$view = function (model) {
	return A2(
		$elm$html$Html$div,
		_List_fromArray(
			[
				$elm$html$Html$Attributes$class('video-page')
			]),
		_List_fromArray(
			[
				A2(
				$elm$html$Html$h1,
				_List_Nil,
				_List_fromArray(
					[
						$elm$html$Html$text('Video to Text Models Explorer')
					])),
				A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('search-section')
					]),
				_List_fromArray(
					[
						A2(
						$elm$html$Html$input,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$type_('text'),
								$elm$html$Html$Attributes$placeholder('Search video-to-text models...'),
								$elm$html$Html$Attributes$value(model.searchQuery),
								$elm$html$Html$Events$onInput($author$project$VideoToText$UpdateSearch)
							]),
						_List_Nil),
						A2(
						$elm$html$Html$button,
						_List_fromArray(
							[
								$elm$html$Html$Events$onClick($author$project$VideoToText$FetchModels),
								$elm$html$Html$Attributes$disabled(
								!_Utils_eq(model.models, _List_Nil))
							]),
						_List_fromArray(
							[
								$elm$html$Html$text(
								_Utils_eq(model.models, _List_Nil) ? 'Loading...' : 'Refresh Models')
							]))
					])),
				$elm$core$List$isEmpty(model.models) ? A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('loading-text')
					]),
				_List_fromArray(
					[
						$elm$html$Html$text('Loading models...')
					])) : A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('models-list')
					]),
				A2(
					$elm$core$List$map,
					$author$project$VideoToText$viewModelOption,
					A2(
						$elm$core$List$filter,
						function (m) {
							return A2(
								$elm$core$String$contains,
								$elm$core$String$toLower(model.searchQuery),
								$elm$core$String$toLower(m.name));
						},
						model.models))),
				function () {
				var _v0 = model.selectedModel;
				if (_v0.$ === 'Just') {
					var selected = _v0.a;
					return A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('selected-model'),
								$elm$html$Html$Attributes$id('selected-model-section')
							]),
						_List_fromArray(
							[
								A2(
								$elm$html$Html$h2,
								_List_Nil,
								_List_fromArray(
									[
										$elm$html$Html$text(selected.name)
									])),
								A2(
								$elm$html$Html$p,
								_List_Nil,
								_List_fromArray(
									[
										$elm$html$Html$text(selected.description)
									])),
								A2(
								$elm$html$Html$div,
								_List_fromArray(
									[
										$elm$html$Html$Attributes$class('parameters-form-grid')
									]),
								A2(
									$elm$core$List$map,
									$author$project$VideoToText$viewParameter(model),
									model.parameters)),
								A2(
								$elm$html$Html$button,
								_List_fromArray(
									[
										$elm$html$Html$Events$onClick($author$project$VideoToText$GenerateText),
										$elm$html$Html$Attributes$disabled(
										A2($author$project$VideoToText$hasEmptyRequiredParameters, model.parameters, model.requiredFields) || model.isGenerating),
										$elm$html$Html$Attributes$class('generate-button')
									]),
								_List_fromArray(
									[
										$elm$html$Html$text(
										model.isGenerating ? 'Generating...' : 'Generate Text')
									]))
							]));
				} else {
					return (!$elm$core$List$isEmpty(model.models)) ? A2(
						$elm$html$Html$div,
						_List_Nil,
						_List_fromArray(
							[
								$elm$html$Html$text('Select a model from the list above')
							])) : $elm$html$Html$text('');
				}
			}(),
				function () {
				var _v1 = model.outputText;
				if (_v1.$ === 'Just') {
					var textOutput = _v1.a;
					return A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('text-output')
							]),
						_List_fromArray(
							[
								A2(
								$elm$html$Html$h3,
								_List_Nil,
								_List_fromArray(
									[
										$elm$html$Html$text('Generated Text')
									])),
								A2(
								$elm$html$Html$pre,
								_List_fromArray(
									[
										$elm$html$Html$Attributes$class('output-text-content')
									]),
								_List_fromArray(
									[
										$elm$html$Html$text(textOutput)
									]))
							]));
				} else {
					return $elm$html$Html$text('');
				}
			}(),
				function () {
				var _v2 = model.error;
				if (_v2.$ === 'Just') {
					var err = _v2.a;
					return A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('error')
							]),
						_List_fromArray(
							[
								$elm$html$Html$text(err)
							]));
				} else {
					return $elm$html$Html$text('');
				}
			}()
			]));
};
var $author$project$VideoToTextGallery$NextPage = {$: 'NextPage'};
var $author$project$VideoToTextGallery$PrevPage = {$: 'PrevPage'};
var $author$project$VideoToTextGallery$viewPagination = F4(
	function (currentPage, maxPage, hasPrevPage, hasNextPage) {
		return A2(
			$elm$html$Html$div,
			_List_fromArray(
				[
					$elm$html$Html$Attributes$class('pagination')
				]),
			_List_fromArray(
				[
					A2(
					$elm$html$Html$button,
					_List_fromArray(
						[
							$elm$html$Html$Events$onClick($author$project$VideoToTextGallery$PrevPage),
							$elm$html$Html$Attributes$disabled(!hasPrevPage),
							$elm$html$Html$Attributes$class('pagination-button')
						]),
					_List_fromArray(
						[
							$elm$html$Html$text('← Previous')
						])),
					A2(
					$elm$html$Html$div,
					_List_fromArray(
						[
							$elm$html$Html$Attributes$class('pagination-info')
						]),
					_List_fromArray(
						[
							$elm$html$Html$text(
							'Page ' + ($elm$core$String$fromInt(currentPage) + (' of ' + $elm$core$String$fromInt(maxPage))))
						])),
					A2(
					$elm$html$Html$button,
					_List_fromArray(
						[
							$elm$html$Html$Events$onClick($author$project$VideoToTextGallery$NextPage),
							$elm$html$Html$Attributes$disabled(!hasNextPage),
							$elm$html$Html$Attributes$class('pagination-button')
						]),
					_List_fromArray(
						[
							$elm$html$Html$text('Next →')
						]))
				]));
	});
var $author$project$VideoToTextGallery$SelectVideo = function (a) {
	return {$: 'SelectVideo', a: a};
};
var $author$project$VideoToTextGallery$extractErrorMessage = function (record) {
	var _v0 = record.metadata;
	if (_v0.$ === 'Just') {
		var metadataValue = _v0.a;
		return $elm$core$Result$toMaybe(
			A2(
				$elm$json$Json$Decode$decodeValue,
				A2($elm$json$Json$Decode$field, 'error', $elm$json$Json$Decode$string),
				metadataValue));
	} else {
		return $elm$core$Maybe$Nothing;
	}
};
var $author$project$VideoToTextGallery$formatDate = function (dateStr) {
	return A2($elm$core$String$left, 19, dateStr);
};
var $author$project$VideoToTextGallery$truncateString = F2(
	function (maxLength, str) {
		return (_Utils_cmp(
			$elm$core$String$length(str),
			maxLength) < 1) ? str : (A2($elm$core$String$left, maxLength - 3, str) + '...');
	});
var $author$project$VideoToTextGallery$viewVideoCard = function (record) {
	var textPreview = $elm$core$String$isEmpty(record.outputText) ? '(No text generated)' : A2($author$project$VideoToTextGallery$truncateString, 100, record.outputText);
	var errorMessage = $author$project$VideoToTextGallery$extractErrorMessage(record);
	return A2(
		$elm$html$Html$div,
		_List_fromArray(
			[
				$elm$html$Html$Attributes$class('video-card'),
				$elm$html$Html$Events$onClick(
				$author$project$VideoToTextGallery$SelectVideo(record))
			]),
		_List_fromArray(
			[
				A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('video-thumbnail')
					]),
				_List_fromArray(
					[
						$elm$core$String$isEmpty(record.outputText) ? A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								A2($elm$html$Html$Attributes$style, 'width', '100%'),
								A2($elm$html$Html$Attributes$style, 'height', '100%'),
								A2($elm$html$Html$Attributes$style, 'display', 'flex'),
								A2($elm$html$Html$Attributes$style, 'flex-direction', 'column'),
								A2($elm$html$Html$Attributes$style, 'align-items', 'center'),
								A2($elm$html$Html$Attributes$style, 'justify-content', 'center'),
								A2(
								$elm$html$Html$Attributes$style,
								'background',
								(record.status === 'failed') ? '#c33' : '#333'),
								A2($elm$html$Html$Attributes$style, 'color', '#fff'),
								A2($elm$html$Html$Attributes$style, 'padding', '10px')
							]),
						_List_fromArray(
							[
								A2(
								$elm$html$Html$div,
								_List_fromArray(
									[
										A2($elm$html$Html$Attributes$style, 'font-weight', 'bold'),
										A2($elm$html$Html$Attributes$style, 'margin-bottom', '5px')
									]),
								_List_fromArray(
									[
										$elm$html$Html$text(
										$elm$core$String$toUpper(record.status))
									])),
								function () {
								if (errorMessage.$ === 'Just') {
									var err = errorMessage.a;
									return A2(
										$elm$html$Html$div,
										_List_fromArray(
											[
												A2($elm$html$Html$Attributes$style, 'font-size', '12px'),
												A2($elm$html$Html$Attributes$style, 'text-align', 'center')
											]),
										_List_fromArray(
											[
												$elm$html$Html$text(
												A2($author$project$VideoToTextGallery$truncateString, 60, err))
											]));
								} else {
									return $elm$html$Html$text('');
								}
							}()
							])) : A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								A2($elm$html$Html$Attributes$style, 'width', '100%'),
								A2($elm$html$Html$Attributes$style, 'height', '100%'),
								A2($elm$html$Html$Attributes$style, 'padding', '15px'),
								A2($elm$html$Html$Attributes$style, 'background', '#f5f5f5'),
								A2($elm$html$Html$Attributes$style, 'overflow', 'hidden'),
								A2($elm$html$Html$Attributes$style, 'display', 'flex'),
								A2($elm$html$Html$Attributes$style, 'align-items', 'center'),
								A2($elm$html$Html$Attributes$style, 'justify-content', 'center')
							]),
						_List_fromArray(
							[
								A2(
								$elm$html$Html$div,
								_List_fromArray(
									[
										A2($elm$html$Html$Attributes$style, 'font-size', '14px'),
										A2($elm$html$Html$Attributes$style, 'color', '#333'),
										A2($elm$html$Html$Attributes$style, 'text-align', 'center')
									]),
								_List_fromArray(
									[
										$elm$html$Html$text(textPreview)
									]))
							]))
					])),
				A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('video-card-info')
					]),
				_List_fromArray(
					[
						A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('video-prompt')
							]),
						_List_fromArray(
							[
								$elm$html$Html$text(record.prompt)
							])),
						A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('video-meta')
							]),
						_List_fromArray(
							[
								A2(
								$elm$html$Html$span,
								_List_fromArray(
									[
										$elm$html$Html$Attributes$class('video-model')
									]),
								_List_fromArray(
									[
										$elm$html$Html$text(record.modelId)
									])),
								A2(
								$elm$html$Html$span,
								_List_fromArray(
									[
										$elm$html$Html$Attributes$class('video-date')
									]),
								_List_fromArray(
									[
										$elm$html$Html$text(
										$author$project$VideoToTextGallery$formatDate(record.createdAt))
									]))
							]))
					]))
			]));
};
var $author$project$VideoToTextGallery$CloseVideo = {$: 'CloseVideo'};
var $author$project$VideoToTextGallery$ToggleRawData = {$: 'ToggleRawData'};
var $author$project$VideoToTextGallery$NoOp = {$: 'NoOp'};
var $author$project$VideoToTextGallery$onClickNoBubble = A2(
	$elm$html$Html$Events$stopPropagationOn,
	'click',
	$elm$json$Json$Decode$succeed(
		_Utils_Tuple2($author$project$VideoToTextGallery$NoOp, true)));
var $author$project$VideoToTextGallery$viewRawDataField = F2(
	function (label, maybeValue) {
		if (maybeValue.$ === 'Just') {
			var value = maybeValue.a;
			return A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('raw-data-field')
					]),
				_List_fromArray(
					[
						A2(
						$elm$html$Html$h4,
						_List_Nil,
						_List_fromArray(
							[
								$elm$html$Html$text(label)
							])),
						A2(
						$elm$html$Html$pre,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('raw-json')
							]),
						_List_fromArray(
							[
								$elm$html$Html$text(
								A2(
									$elm$core$Result$withDefault,
									'Invalid JSON',
									A2(
										$elm$core$Result$map,
										$elm$json$Json$Encode$encode(2),
										A2($elm$json$Json$Decode$decodeValue, $elm$json$Json$Decode$value, value))))
							]))
					]));
		} else {
			return $elm$html$Html$text('');
		}
	});
var $author$project$VideoToTextGallery$viewVideoModal = F2(
	function (model, record) {
		var errorMessage = $author$project$VideoToTextGallery$extractErrorMessage(record);
		return A2(
			$elm$html$Html$div,
			_List_fromArray(
				[
					$elm$html$Html$Attributes$class('modal-overlay'),
					$elm$html$Html$Events$onClick($author$project$VideoToTextGallery$CloseVideo)
				]),
			_List_fromArray(
				[
					A2(
					$elm$html$Html$div,
					_List_fromArray(
						[
							$elm$html$Html$Attributes$class('modal-content'),
							$author$project$VideoToTextGallery$onClickNoBubble
						]),
					_List_fromArray(
						[
							A2(
							$elm$html$Html$button,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$class('modal-close'),
									$elm$html$Html$Events$onClick($author$project$VideoToTextGallery$CloseVideo)
								]),
							_List_fromArray(
								[
									$elm$html$Html$text('×')
								])),
							A2(
							$elm$html$Html$h2,
							_List_Nil,
							_List_fromArray(
								[
									$elm$html$Html$text('Generated Text Result')
								])),
							function () {
							if (errorMessage.$ === 'Just') {
								var err = errorMessage.a;
								return A2(
									$elm$html$Html$div,
									_List_fromArray(
										[
											A2($elm$html$Html$Attributes$style, 'background', '#fee'),
											A2($elm$html$Html$Attributes$style, 'color', '#c33'),
											A2($elm$html$Html$Attributes$style, 'padding', '15px'),
											A2($elm$html$Html$Attributes$style, 'border-radius', '4px'),
											A2($elm$html$Html$Attributes$style, 'margin-bottom', '15px'),
											A2($elm$html$Html$Attributes$style, 'border', '1px solid #fcc')
										]),
									_List_fromArray(
										[
											A2(
											$elm$html$Html$strong,
											_List_Nil,
											_List_fromArray(
												[
													$elm$html$Html$text('Error: ')
												])),
											$elm$html$Html$text(err)
										]));
							} else {
								return $elm$html$Html$text('');
							}
						}(),
							(!$elm$core$String$isEmpty(record.outputText)) ? A2(
							$elm$html$Html$div,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$class('text-output-container')
								]),
							_List_fromArray(
								[
									A2(
									$elm$html$Html$h3,
									_List_Nil,
									_List_fromArray(
										[
											$elm$html$Html$text('Generated Text')
										])),
									A2(
									$elm$html$Html$pre,
									_List_fromArray(
										[
											$elm$html$Html$Attributes$class('output-text-content'),
											A2($elm$html$Html$Attributes$style, 'background', '#f5f5f5'),
											A2($elm$html$Html$Attributes$style, 'padding', '20px'),
											A2($elm$html$Html$Attributes$style, 'border-radius', '4px'),
											A2($elm$html$Html$Attributes$style, 'border', '1px solid #ddd'),
											A2($elm$html$Html$Attributes$style, 'white-space', 'pre-wrap'),
											A2($elm$html$Html$Attributes$style, 'word-wrap', 'break-word'),
											A2($elm$html$Html$Attributes$style, 'max-height', '400px'),
											A2($elm$html$Html$Attributes$style, 'overflow-y', 'auto'),
											A2($elm$html$Html$Attributes$style, 'font-family', 'monospace'),
											A2($elm$html$Html$Attributes$style, 'font-size', '14px'),
											A2($elm$html$Html$Attributes$style, 'line-height', '1.5')
										]),
									_List_fromArray(
										[
											$elm$html$Html$text(record.outputText)
										]))
								])) : A2(
							$elm$html$Html$div,
							_List_fromArray(
								[
									A2($elm$html$Html$Attributes$style, 'background', '#333'),
									A2($elm$html$Html$Attributes$style, 'color', '#fff'),
									A2($elm$html$Html$Attributes$style, 'padding', '40px'),
									A2($elm$html$Html$Attributes$style, 'text-align', 'center'),
									A2($elm$html$Html$Attributes$style, 'border-radius', '4px'),
									A2($elm$html$Html$Attributes$style, 'margin-bottom', '15px')
								]),
							_List_fromArray(
								[
									$elm$html$Html$text(
									'Generation ' + $elm$core$String$toUpper(record.status))
								])),
							A2(
							$elm$html$Html$div,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$class('modal-details')
								]),
							_List_fromArray(
								[
									A2(
									$elm$html$Html$div,
									_List_fromArray(
										[
											$elm$html$Html$Attributes$class('detail-row')
										]),
									_List_fromArray(
										[
											A2(
											$elm$html$Html$strong,
											_List_Nil,
											_List_fromArray(
												[
													$elm$html$Html$text('Prompt: ')
												])),
											$elm$html$Html$text(record.prompt)
										])),
									A2(
									$elm$html$Html$div,
									_List_fromArray(
										[
											$elm$html$Html$Attributes$class('detail-row')
										]),
									_List_fromArray(
										[
											A2(
											$elm$html$Html$strong,
											_List_Nil,
											_List_fromArray(
												[
													$elm$html$Html$text('Model: ')
												])),
											$elm$html$Html$text(record.modelId)
										])),
									function () {
									var _v1 = record.collection;
									if (_v1.$ === 'Just') {
										var coll = _v1.a;
										return A2(
											$elm$html$Html$div,
											_List_fromArray(
												[
													$elm$html$Html$Attributes$class('detail-row')
												]),
											_List_fromArray(
												[
													A2(
													$elm$html$Html$strong,
													_List_Nil,
													_List_fromArray(
														[
															$elm$html$Html$text('Collection: ')
														])),
													$elm$html$Html$text(coll)
												]));
									} else {
										return $elm$html$Html$text('');
									}
								}(),
									A2(
									$elm$html$Html$div,
									_List_fromArray(
										[
											$elm$html$Html$Attributes$class('detail-row')
										]),
									_List_fromArray(
										[
											A2(
											$elm$html$Html$strong,
											_List_Nil,
											_List_fromArray(
												[
													$elm$html$Html$text('Created: ')
												])),
											$elm$html$Html$text(record.createdAt)
										])),
									A2(
									$elm$html$Html$div,
									_List_fromArray(
										[
											$elm$html$Html$Attributes$class('detail-row')
										]),
									_List_fromArray(
										[
											A2(
											$elm$html$Html$strong,
											_List_Nil,
											_List_fromArray(
												[
													$elm$html$Html$text('Status: ')
												])),
											A2(
											$elm$html$Html$span,
											_List_fromArray(
												[
													A2(
													$elm$html$Html$Attributes$style,
													'color',
													(record.status === 'failed') ? '#c33' : 'inherit'),
													A2(
													$elm$html$Html$Attributes$style,
													'font-weight',
													(record.status === 'failed') ? 'bold' : 'normal')
												]),
											_List_fromArray(
												[
													$elm$html$Html$text(record.status)
												]))
										]))
								])),
							A2(
							$elm$html$Html$div,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$class('raw-data-section')
								]),
							_List_fromArray(
								[
									A2(
									$elm$html$Html$button,
									_List_fromArray(
										[
											$elm$html$Html$Events$onClick($author$project$VideoToTextGallery$ToggleRawData),
											$elm$html$Html$Attributes$class('toggle-raw-data')
										]),
									_List_fromArray(
										[
											$elm$html$Html$text(
											model.showRawData ? '▼ Hide Raw Data' : '▶ Show Raw Data')
										])),
									model.showRawData ? A2(
									$elm$html$Html$div,
									_List_fromArray(
										[
											$elm$html$Html$Attributes$class('raw-data-content')
										]),
									_List_fromArray(
										[
											A2($author$project$VideoToTextGallery$viewRawDataField, 'Parameters', record.parameters),
											A2($author$project$VideoToTextGallery$viewRawDataField, 'Metadata', record.metadata)
										])) : $elm$html$Html$text('')
								]))
						]))
				]));
	});
var $author$project$VideoToTextGallery$view = function (model) {
	var maxPage = $elm$core$Basics$ceiling(model.totalVideos / model.pageSize);
	var hasPrevPage = model.currentPage > 1;
	var hasNextPage = _Utils_cmp(model.currentPage, maxPage) < 0;
	return A2(
		$elm$html$Html$div,
		_List_fromArray(
			[
				$elm$html$Html$Attributes$class('video-gallery-page')
			]),
		_List_fromArray(
			[
				A2(
				$elm$html$Html$h1,
				_List_Nil,
				_List_fromArray(
					[
						$elm$html$Html$text('Generated Video-to-Text Results')
					])),
				A2(
				$elm$html$Html$button,
				_List_fromArray(
					[
						$elm$html$Html$Events$onClick($author$project$VideoToTextGallery$FetchVideos),
						$elm$html$Html$Attributes$disabled(model.loading),
						$elm$html$Html$Attributes$class('refresh-button')
					]),
				_List_fromArray(
					[
						$elm$html$Html$text(
						model.loading ? 'Loading...' : 'Refresh')
					])),
				function () {
				var _v0 = model.error;
				if (_v0.$ === 'Just') {
					var err = _v0.a;
					return A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('error')
							]),
						_List_fromArray(
							[
								$elm$html$Html$text(err)
							]));
				} else {
					return $elm$html$Html$text('');
				}
			}(),
				(model.loading && $elm$core$List$isEmpty(model.videos)) ? A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('loading-text')
					]),
				_List_fromArray(
					[
						$elm$html$Html$text('Loading results...')
					])) : ($elm$core$List$isEmpty(model.videos) ? A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('empty-state')
					]),
				_List_fromArray(
					[
						$elm$html$Html$text('No video-to-text results yet. Go to the Video to Text page to generate some!')
					])) : A2(
				$elm$html$Html$div,
				_List_Nil,
				_List_fromArray(
					[
						A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('videos-grid')
							]),
						A2($elm$core$List$map, $author$project$VideoToTextGallery$viewVideoCard, model.videos)),
						A4($author$project$VideoToTextGallery$viewPagination, model.currentPage, maxPage, hasPrevPage, hasNextPage)
					]))),
				function () {
				var _v1 = model.selectedVideo;
				if (_v1.$ === 'Just') {
					var video = _v1.a;
					return A2($author$project$VideoToTextGallery$viewVideoModal, model, video);
				} else {
					return $elm$html$Html$text('');
				}
			}()
			]));
};
var $author$project$Main$LoadScene = {$: 'LoadScene'};
var $author$project$Main$Redo = {$: 'Redo'};
var $author$project$Main$ResetSimulation = {$: 'ResetSimulation'};
var $author$project$Main$Rotate = {$: 'Rotate'};
var $author$project$Main$SaveScene = {$: 'SaveScene'};
var $author$project$Main$Scale = {$: 'Scale'};
var $author$project$Main$SetTransformMode = function (a) {
	return {$: 'SetTransformMode', a: a};
};
var $author$project$Main$ToggleSimulation = {$: 'ToggleSimulation'};
var $author$project$Main$Undo = {$: 'Undo'};
var $author$project$Main$viewBottomBar = function (model) {
	return A2(
		$elm$html$Html$div,
		_List_fromArray(
			[
				$elm$html$Html$Attributes$class('bottom-bar')
			]),
		_List_fromArray(
			[
				A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('simulation-controls')
					]),
				_List_fromArray(
					[
						A2(
						$elm$html$Html$button,
						_List_fromArray(
							[
								$elm$html$Html$Events$onClick($author$project$Main$ToggleSimulation),
								$elm$html$Html$Attributes$class(
								model.simulationState.isRunning ? 'active' : '')
							]),
						_List_fromArray(
							[
								$elm$html$Html$text(
								model.simulationState.isRunning ? 'Pause' : 'Play')
							])),
						A2(
						$elm$html$Html$button,
						_List_fromArray(
							[
								$elm$html$Html$Events$onClick($author$project$Main$ResetSimulation)
							]),
						_List_fromArray(
							[
								$elm$html$Html$text('Reset')
							]))
					])),
				A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('transform-controls')
					]),
				_List_fromArray(
					[
						A2(
						$elm$html$Html$button,
						_List_fromArray(
							[
								$elm$html$Html$Events$onClick(
								$author$project$Main$SetTransformMode($author$project$Main$Translate)),
								$elm$html$Html$Attributes$class(
								_Utils_eq(model.simulationState.transformMode, $author$project$Main$Translate) ? 'active' : '')
							]),
						_List_fromArray(
							[
								$elm$html$Html$text('Move (G)')
							])),
						A2(
						$elm$html$Html$button,
						_List_fromArray(
							[
								$elm$html$Html$Events$onClick(
								$author$project$Main$SetTransformMode($author$project$Main$Rotate)),
								$elm$html$Html$Attributes$class(
								_Utils_eq(model.simulationState.transformMode, $author$project$Main$Rotate) ? 'active' : '')
							]),
						_List_fromArray(
							[
								$elm$html$Html$text('Rotate (R)')
							])),
						A2(
						$elm$html$Html$button,
						_List_fromArray(
							[
								$elm$html$Html$Events$onClick(
								$author$project$Main$SetTransformMode($author$project$Main$Scale)),
								$elm$html$Html$Attributes$class(
								_Utils_eq(model.simulationState.transformMode, $author$project$Main$Scale) ? 'active' : '')
							]),
						_List_fromArray(
							[
								$elm$html$Html$text('Scale (S)')
							]))
					])),
				A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('history-controls')
					]),
				_List_fromArray(
					[
						A2(
						$elm$html$Html$button,
						_List_fromArray(
							[
								$elm$html$Html$Events$onClick($author$project$Main$Undo),
								$elm$html$Html$Attributes$disabled(
								$elm$core$List$isEmpty(model.history))
							]),
						_List_fromArray(
							[
								$elm$html$Html$text('Undo')
							])),
						A2(
						$elm$html$Html$button,
						_List_fromArray(
							[
								$elm$html$Html$Events$onClick($author$project$Main$Redo),
								$elm$html$Html$Attributes$disabled(
								$elm$core$List$isEmpty(model.future))
							]),
						_List_fromArray(
							[
								$elm$html$Html$text('Redo')
							])),
						A2(
						$elm$html$Html$button,
						_List_fromArray(
							[
								$elm$html$Html$Events$onClick($author$project$Main$SaveScene)
							]),
						_List_fromArray(
							[
								$elm$html$Html$text('Save')
							])),
						A2(
						$elm$html$Html$button,
						_List_fromArray(
							[
								$elm$html$Html$Events$onClick($author$project$Main$LoadScene)
							]),
						_List_fromArray(
							[
								$elm$html$Html$text('Load')
							]))
					]))
			]));
};
var $author$project$Main$viewCanvasContainer = A2(
	$elm$html$Html$div,
	_List_fromArray(
		[
			$elm$html$Html$Attributes$id('canvas-container'),
			$elm$html$Html$Attributes$class('canvas-container')
		]),
	_List_Nil);
var $author$project$Main$ClearError = {$: 'ClearError'};
var $author$project$Main$GenerateScene = {$: 'GenerateScene'};
var $author$project$Main$RefineScene = {$: 'RefineScene'};
var $author$project$Main$UpdateRefineInput = function (a) {
	return {$: 'UpdateRefineInput', a: a};
};
var $author$project$Main$UpdateTextInput = function (a) {
	return {$: 'UpdateTextInput', a: a};
};
var $elm$core$Dict$isEmpty = function (dict) {
	if (dict.$ === 'RBEmpty_elm_builtin') {
		return true;
	} else {
		return false;
	}
};
var $author$project$Main$viewLeftPanel = function (model) {
	return A2(
		$elm$html$Html$div,
		_List_fromArray(
			[
				$elm$html$Html$Attributes$class('left-panel')
			]),
		_List_fromArray(
			[
				A2(
				$elm$html$Html$h2,
				_List_Nil,
				_List_fromArray(
					[
						$elm$html$Html$text('Generation')
					])),
				A2(
				$elm$html$Html$textarea,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$placeholder('Describe a scene to generate...'),
						$elm$html$Html$Attributes$value(model.uiState.textInput),
						$elm$html$Html$Events$onInput($author$project$Main$UpdateTextInput),
						$elm$html$Html$Attributes$disabled(model.uiState.isGenerating)
					]),
				_List_Nil),
				A2(
				$elm$html$Html$button,
				_List_fromArray(
					[
						$elm$html$Html$Events$onClick($author$project$Main$GenerateScene),
						$elm$html$Html$Attributes$disabled(
						$elm$core$String$isEmpty(
							$elm$core$String$trim(model.uiState.textInput)) || model.uiState.isGenerating)
					]),
				_List_fromArray(
					[
						model.uiState.isGenerating ? A2(
						$elm$html$Html$span,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('loading')
							]),
						_List_Nil) : $elm$html$Html$text(''),
						$elm$html$Html$text(
						model.uiState.isGenerating ? 'Generating...' : 'Generate Scene')
					])),
				function () {
				var _v0 = model.uiState.errorMessage;
				if (_v0.$ === 'Just') {
					var error = _v0.a;
					return A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('error')
							]),
						_List_fromArray(
							[
								$elm$html$Html$text(error),
								A2(
								$elm$html$Html$button,
								_List_fromArray(
									[
										$elm$html$Html$Events$onClick($author$project$Main$ClearError)
									]),
								_List_fromArray(
									[
										$elm$html$Html$text('×')
									]))
							]));
				} else {
					return $elm$html$Html$text('');
				}
			}(),
				A2(
				$elm$html$Html$h2,
				_List_Nil,
				_List_fromArray(
					[
						$elm$html$Html$text('Refinement')
					])),
				A2(
				$elm$html$Html$textarea,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$placeholder('Describe how to modify the current scene...'),
						$elm$html$Html$Attributes$value(model.uiState.refineInput),
						$elm$html$Html$Events$onInput($author$project$Main$UpdateRefineInput),
						$elm$html$Html$Attributes$disabled(
						$elm$core$Dict$isEmpty(model.scene.objects) || model.uiState.isRefining)
					]),
				_List_Nil),
				A2(
				$elm$html$Html$button,
				_List_fromArray(
					[
						$elm$html$Html$Events$onClick($author$project$Main$RefineScene),
						$elm$html$Html$Attributes$disabled(
						$elm$core$String$isEmpty(
							$elm$core$String$trim(model.uiState.refineInput)) || ($elm$core$Dict$isEmpty(model.scene.objects) || model.uiState.isRefining))
					]),
				_List_fromArray(
					[
						model.uiState.isRefining ? A2(
						$elm$html$Html$span,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('loading')
							]),
						_List_Nil) : $elm$html$Html$text(''),
						$elm$html$Html$text(
						model.uiState.isRefining ? 'Refining...' : 'Refine Scene')
					]))
			]));
};
var $author$project$Main$UpdateObjectDescription = F2(
	function (a, b) {
		return {$: 'UpdateObjectDescription', a: a, b: b};
	});
var $author$project$Main$UpdateObjectProperty = F3(
	function (a, b, c) {
		return {$: 'UpdateObjectProperty', a: a, b: b, c: c};
	});
var $author$project$Main$UpdateObjectTransform = F2(
	function (a, b) {
		return {$: 'UpdateObjectTransform', a: a, b: b};
	});
var $author$project$Main$shapeToString = function (shape) {
	switch (shape.$) {
		case 'Box':
			return 'Box';
		case 'Sphere':
			return 'Sphere';
		default:
			return 'Cylinder';
	}
};
var $elm$html$Html$Attributes$step = function (n) {
	return A2($elm$html$Html$Attributes$stringProperty, 'step', n);
};
var $author$project$Main$viewFloatInput = F3(
	function (labelText, value, msgConstructor) {
		return A2(
			$elm$html$Html$div,
			_List_fromArray(
				[
					$elm$html$Html$Attributes$class('float-input')
				]),
			_List_fromArray(
				[
					A2(
					$elm$html$Html$div,
					_List_Nil,
					_List_fromArray(
						[
							$elm$html$Html$text(labelText)
						])),
					A2(
					$elm$html$Html$input,
					_List_fromArray(
						[
							$elm$html$Html$Attributes$type_('number'),
							$elm$html$Html$Attributes$step('0.1'),
							$elm$html$Html$Attributes$value(
							$elm$core$String$fromFloat(value)),
							$elm$html$Html$Events$onInput(
							function (val) {
								return msgConstructor(
									A2(
										$elm$core$Maybe$withDefault,
										value,
										$elm$core$String$toFloat(val)));
							})
						]),
					_List_Nil)
				]));
	});
var $author$project$Main$viewVec3Input = F3(
	function (labelText, vec3, msgConstructor) {
		return A2(
			$elm$html$Html$div,
			_List_fromArray(
				[
					$elm$html$Html$Attributes$class('vec3-input')
				]),
			_List_fromArray(
				[
					A2(
					$elm$html$Html$div,
					_List_Nil,
					_List_fromArray(
						[
							$elm$html$Html$text(labelText)
						])),
					A2(
					$elm$html$Html$div,
					_List_fromArray(
						[
							$elm$html$Html$Attributes$class('input-row')
						]),
					_List_fromArray(
						[
							A2(
							$elm$html$Html$input,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$type_('number'),
									$elm$html$Html$Attributes$step('0.1'),
									$elm$html$Html$Attributes$value(
									$elm$core$String$fromFloat(vec3.x)),
									$elm$html$Html$Events$onInput(
									function (x) {
										return msgConstructor(
											_Utils_update(
												vec3,
												{
													x: A2(
														$elm$core$Maybe$withDefault,
														vec3.x,
														$elm$core$String$toFloat(x))
												}));
									})
								]),
							_List_Nil),
							A2(
							$elm$html$Html$input,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$type_('number'),
									$elm$html$Html$Attributes$step('0.1'),
									$elm$html$Html$Attributes$value(
									$elm$core$String$fromFloat(vec3.y)),
									$elm$html$Html$Events$onInput(
									function (y) {
										return msgConstructor(
											_Utils_update(
												vec3,
												{
													y: A2(
														$elm$core$Maybe$withDefault,
														vec3.y,
														$elm$core$String$toFloat(y))
												}));
									})
								]),
							_List_Nil),
							A2(
							$elm$html$Html$input,
							_List_fromArray(
								[
									$elm$html$Html$Attributes$type_('number'),
									$elm$html$Html$Attributes$step('0.1'),
									$elm$html$Html$Attributes$value(
									$elm$core$String$fromFloat(vec3.z)),
									$elm$html$Html$Events$onInput(
									function (z) {
										return msgConstructor(
											_Utils_update(
												vec3,
												{
													z: A2(
														$elm$core$Maybe$withDefault,
														vec3.z,
														$elm$core$String$toFloat(z))
												}));
									})
								]),
							_List_Nil)
						]))
				]));
	});
var $author$project$Main$viewObjectProperties = function (object) {
	return A2(
		$elm$html$Html$div,
		_List_Nil,
		_List_fromArray(
			[
				A2(
				$elm$html$Html$h3,
				_List_Nil,
				_List_fromArray(
					[
						$elm$html$Html$text('Object: ' + object.id)
					])),
				A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('property-section')
					]),
				_List_fromArray(
					[
						A2(
						$elm$html$Html$h4,
						_List_Nil,
						_List_fromArray(
							[
								$elm$html$Html$text('Transform')
							])),
						A3(
						$author$project$Main$viewVec3Input,
						'Position',
						object.transform.position,
						function (vec) {
							return A2(
								$author$project$Main$UpdateObjectTransform,
								object.id,
								{position: vec, rotation: object.transform.rotation, scale: object.transform.scale});
						}),
						A3(
						$author$project$Main$viewVec3Input,
						'Rotation',
						object.transform.rotation,
						function (vec) {
							return A2(
								$author$project$Main$UpdateObjectTransform,
								object.id,
								{position: object.transform.position, rotation: vec, scale: object.transform.scale});
						}),
						A3(
						$author$project$Main$viewVec3Input,
						'Scale',
						object.transform.scale,
						function (vec) {
							return A2(
								$author$project$Main$UpdateObjectTransform,
								object.id,
								{position: object.transform.position, rotation: object.transform.rotation, scale: vec});
						})
					])),
				A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('property-section')
					]),
				_List_fromArray(
					[
						A2(
						$elm$html$Html$h4,
						_List_Nil,
						_List_fromArray(
							[
								$elm$html$Html$text('Physics')
							])),
						A3(
						$author$project$Main$viewFloatInput,
						'Mass',
						object.physicsProperties.mass,
						function (val) {
							return A3($author$project$Main$UpdateObjectProperty, object.id, 'mass', val);
						}),
						A3(
						$author$project$Main$viewFloatInput,
						'Friction',
						object.physicsProperties.friction,
						function (val) {
							return A3($author$project$Main$UpdateObjectProperty, object.id, 'friction', val);
						}),
						A3(
						$author$project$Main$viewFloatInput,
						'Restitution',
						object.physicsProperties.restitution,
						function (val) {
							return A3($author$project$Main$UpdateObjectProperty, object.id, 'restitution', val);
						})
					])),
				A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('property-section')
					]),
				_List_fromArray(
					[
						A2(
						$elm$html$Html$h4,
						_List_Nil,
						_List_fromArray(
							[
								$elm$html$Html$text('Visual')
							])),
						A2(
						$elm$html$Html$div,
						_List_Nil,
						_List_fromArray(
							[
								$elm$html$Html$text('Color: ' + object.visualProperties.color)
							])),
						A2(
						$elm$html$Html$div,
						_List_Nil,
						_List_fromArray(
							[
								$elm$html$Html$text(
								'Shape: ' + $author$project$Main$shapeToString(object.visualProperties.shape))
							]))
					])),
				A2(
				$elm$html$Html$div,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$class('property-section')
					]),
				_List_fromArray(
					[
						A2(
						$elm$html$Html$h4,
						_List_Nil,
						_List_fromArray(
							[
								$elm$html$Html$text('Description (for Genesis)')
							])),
						A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('description-help')
							]),
						_List_fromArray(
							[
								$elm$html$Html$text('Describe what this object should look like (e.g., \'blue corvette\', \'wooden table\')')
							])),
						A2(
						$elm$html$Html$textarea,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('description-input'),
								$elm$html$Html$Attributes$placeholder('e.g., blue corvette, light pole, wooden coffee table...'),
								$elm$html$Html$Attributes$value(
								A2($elm$core$Maybe$withDefault, '', object.description)),
								$elm$html$Html$Events$onInput(
								function (desc) {
									return A2($author$project$Main$UpdateObjectDescription, object.id, desc);
								}),
								$elm$html$Html$Attributes$rows(3)
							]),
						_List_Nil)
					]))
			]));
};
var $author$project$Main$viewRightPanel = function (model) {
	return A2(
		$elm$html$Html$div,
		_List_fromArray(
			[
				$elm$html$Html$Attributes$class('right-panel')
			]),
		_List_fromArray(
			[
				A2(
				$elm$html$Html$h2,
				_List_Nil,
				_List_fromArray(
					[
						$elm$html$Html$text('Properties')
					])),
				function () {
				var _v0 = model.scene.selectedObject;
				if (_v0.$ === 'Just') {
					var objectId = _v0.a;
					var _v1 = A2($elm$core$Dict$get, objectId, model.scene.objects);
					if (_v1.$ === 'Just') {
						var object = _v1.a;
						return $author$project$Main$viewObjectProperties(object);
					} else {
						return $elm$html$Html$text('Object not found');
					}
				} else {
					return $elm$html$Html$text('No object selected');
				}
			}()
			]));
};
var $author$project$Main$viewTabs = function (model) {
	return A2(
		$elm$html$Html$div,
		_List_fromArray(
			[
				$elm$html$Html$Attributes$class('tabs')
			]),
		_List_fromArray(
			[
				A2(
				$elm$html$Html$a,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$href('/videos'),
						$elm$html$Html$Attributes$class(
						_Utils_eq(
							model.route,
							$elm$core$Maybe$Just($author$project$Route$Videos)) ? 'active' : '')
					]),
				_List_fromArray(
					[
						$elm$html$Html$text('Video Models')
					])),
				A2(
				$elm$html$Html$a,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$href('/gallery'),
						$elm$html$Html$Attributes$class(
						_Utils_eq(
							model.route,
							$elm$core$Maybe$Just($author$project$Route$Gallery)) ? 'active' : '')
					]),
				_List_fromArray(
					[
						$elm$html$Html$text('Video Gallery')
					])),
				A2(
				$elm$html$Html$a,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$href('/images'),
						$elm$html$Html$Attributes$class(
						_Utils_eq(
							model.route,
							$elm$core$Maybe$Just($author$project$Route$Images)) ? 'active' : '')
					]),
				_List_fromArray(
					[
						$elm$html$Html$text('Image Models')
					])),
				A2(
				$elm$html$Html$a,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$href('/image-gallery'),
						$elm$html$Html$Attributes$class(
						_Utils_eq(
							model.route,
							$elm$core$Maybe$Just($author$project$Route$ImageGallery)) ? 'active' : '')
					]),
				_List_fromArray(
					[
						$elm$html$Html$text('Image Gallery')
					])),
				A2(
				$elm$html$Html$a,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$href('/audio'),
						$elm$html$Html$Attributes$class(
						_Utils_eq(
							model.route,
							$elm$core$Maybe$Just($author$project$Route$Audio)) ? 'active' : '')
					]),
				_List_fromArray(
					[
						$elm$html$Html$text('Audio Models')
					])),
				A2(
				$elm$html$Html$a,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$href('/audio-gallery'),
						$elm$html$Html$Attributes$class(
						_Utils_eq(
							model.route,
							$elm$core$Maybe$Just($author$project$Route$AudioGallery)) ? 'active' : '')
					]),
				_List_fromArray(
					[
						$elm$html$Html$text('Audio Gallery')
					])),
				A2(
				$elm$html$Html$a,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$href('/video-to-text'),
						$elm$html$Html$Attributes$class(
						_Utils_eq(
							model.route,
							$elm$core$Maybe$Just($author$project$Route$VideoToText)) ? 'active' : '')
					]),
				_List_fromArray(
					[
						$elm$html$Html$text('Video to Text')
					])),
				A2(
				$elm$html$Html$a,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$href('/video-to-text-gallery'),
						$elm$html$Html$Attributes$class(
						_Utils_eq(
							model.route,
							$elm$core$Maybe$Just($author$project$Route$VideoToTextGallery)) ? 'active' : '')
					]),
				_List_fromArray(
					[
						$elm$html$Html$text('VTT Gallery')
					])),
				A2(
				$elm$html$Html$a,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$href('/simulations'),
						$elm$html$Html$Attributes$class(
						_Utils_eq(
							model.route,
							$elm$core$Maybe$Just($author$project$Route$SimulationGallery)) ? 'active' : '')
					]),
				_List_fromArray(
					[
						$elm$html$Html$text('Simulation Gallery')
					])),
				A2(
				$elm$html$Html$a,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$href('/physics'),
						$elm$html$Html$Attributes$class(
						_Utils_eq(
							model.route,
							$elm$core$Maybe$Just($author$project$Route$Physics)) ? 'active' : '')
					]),
				_List_fromArray(
					[
						$elm$html$Html$text('Physics Simulator')
					])),
				A2(
				$elm$html$Html$a,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$href('/auth'),
						$elm$html$Html$Attributes$class(
						_Utils_eq(
							model.route,
							$elm$core$Maybe$Just($author$project$Route$Auth)) ? 'active' : '')
					]),
				_List_fromArray(
					[
						$elm$html$Html$text('Auth')
					])),
				A2(
				$elm$html$Html$a,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$href('/briefs'),
						$elm$html$Html$Attributes$class(
						_Utils_eq(
							model.route,
							$elm$core$Maybe$Just($author$project$Route$BriefGallery)) ? 'active' : '')
					]),
				_List_fromArray(
					[
						$elm$html$Html$text('Brief Gallery')
					])),
				A2(
				$elm$html$Html$a,
				_List_fromArray(
					[
						$elm$html$Html$Attributes$href('/creative'),
						$elm$html$Html$Attributes$class(
						_Utils_eq(
							model.route,
							$elm$core$Maybe$Just($author$project$Route$CreativeBriefEditor)) ? 'active' : '')
					]),
				_List_fromArray(
					[
						$elm$html$Html$text('Creative Brief Editor')
					]))
			]));
};
var $author$project$Main$viewMainContent = function (model) {
	return A2(
		$elm$html$Html$div,
		_List_Nil,
		_List_fromArray(
			[
				$author$project$Main$viewTabs(model),
				function () {
				var _v0 = model.route;
				if (_v0.$ === 'Just') {
					switch (_v0.a.$) {
						case 'Physics':
							var _v1 = _v0.a;
							return A2(
								$elm$html$Html$div,
								_List_fromArray(
									[
										$elm$html$Html$Attributes$class('app-container')
									]),
								_List_fromArray(
									[
										$author$project$Main$viewLeftPanel(model),
										$author$project$Main$viewCanvasContainer,
										$author$project$Main$viewRightPanel(model),
										$author$project$Main$viewBottomBar(model)
									]));
						case 'Videos':
							var _v2 = _v0.a;
							return A2(
								$elm$html$Html$map,
								$author$project$Main$VideoMsg,
								$author$project$Video$view(model.videoModel));
						case 'VideoDetail':
							var _v3 = model.videoDetailModel;
							if (_v3.$ === 'Just') {
								var videoDetailModel = _v3.a;
								return A2(
									$elm$html$Html$map,
									$author$project$Main$VideoDetailMsg,
									$author$project$VideoDetail$view(videoDetailModel));
							} else {
								return A2(
									$elm$html$Html$div,
									_List_fromArray(
										[
											$elm$html$Html$Attributes$class('loading')
										]),
									_List_fromArray(
										[
											$elm$html$Html$text('Loading video detail...')
										]));
							}
						case 'Gallery':
							var _v4 = _v0.a;
							return A2(
								$elm$html$Html$map,
								$author$project$Main$GalleryMsg,
								$author$project$VideoGallery$view(model.galleryModel));
						case 'SimulationGallery':
							var _v5 = _v0.a;
							return A2(
								$elm$html$Html$map,
								$author$project$Main$SimulationGalleryMsg,
								$author$project$SimulationGallery$view(model.simulationGalleryModel));
						case 'Images':
							var _v6 = _v0.a;
							return A2(
								$elm$html$Html$map,
								$author$project$Main$ImageMsg,
								$author$project$Image$view(model.imageModel));
						case 'ImageDetail':
							var _v7 = model.imageDetailModel;
							if (_v7.$ === 'Just') {
								var imageDetailModel = _v7.a;
								return A2(
									$elm$html$Html$map,
									$author$project$Main$ImageDetailMsg,
									$author$project$ImageDetail$view(imageDetailModel));
							} else {
								return A2(
									$elm$html$Html$div,
									_List_fromArray(
										[
											$elm$html$Html$Attributes$class('loading')
										]),
									_List_fromArray(
										[
											$elm$html$Html$text('Loading image detail...')
										]));
							}
						case 'ImageGallery':
							var _v8 = _v0.a;
							return A2(
								$elm$html$Html$map,
								$author$project$Main$ImageGalleryMsg,
								$author$project$ImageGallery$view(model.imageGalleryModel));
						case 'Audio':
							var _v9 = _v0.a;
							return A2(
								$elm$html$Html$map,
								$author$project$Main$AudioMsg,
								$author$project$Audio$view(model.audioModel));
						case 'AudioDetail':
							var _v10 = model.audioDetailModel;
							if (_v10.$ === 'Just') {
								var audioDetailModel = _v10.a;
								return A2(
									$elm$html$Html$map,
									$author$project$Main$AudioDetailMsg,
									$author$project$AudioDetail$view(audioDetailModel));
							} else {
								return A2(
									$elm$html$Html$div,
									_List_fromArray(
										[
											$elm$html$Html$Attributes$class('loading')
										]),
									_List_fromArray(
										[
											$elm$html$Html$text('Loading audio detail...')
										]));
							}
						case 'AudioGallery':
							var _v11 = _v0.a;
							return A2(
								$elm$html$Html$map,
								$author$project$Main$AudioGalleryMsg,
								$author$project$AudioGallery$view(model.audioGalleryModel));
						case 'VideoToText':
							var _v12 = _v0.a;
							return A2(
								$elm$html$Html$map,
								$author$project$Main$VideoToTextMsg,
								$author$project$VideoToText$view(model.videoToTextModel));
						case 'VideoToTextGallery':
							var _v13 = _v0.a;
							return A2(
								$elm$html$Html$map,
								$author$project$Main$VideoToTextGalleryMsg,
								$author$project$VideoToTextGallery$view(model.videoToTextGalleryModel));
						case 'Auth':
							var _v14 = _v0.a;
							return A2(
								$elm$html$Html$map,
								$author$project$Main$AuthMsg,
								$author$project$Auth$view(model.authModel));
						case 'BriefGallery':
							var _v15 = _v0.a;
							return A2(
								$elm$html$Html$map,
								$author$project$Main$BriefGalleryMsg,
								$author$project$BriefGallery$view(model.briefGalleryModel));
						default:
							var _v16 = _v0.a;
							return A2(
								$elm$html$Html$map,
								$author$project$Main$CreativeBriefEditorMsg,
								$author$project$CreativeBriefEditor$view(model.creativeBriefEditorModel));
					}
				} else {
					return A2(
						$elm$html$Html$div,
						_List_fromArray(
							[
								$elm$html$Html$Attributes$class('app-container')
							]),
						_List_fromArray(
							[
								$author$project$Main$viewLeftPanel(model),
								$author$project$Main$viewCanvasContainer,
								$author$project$Main$viewRightPanel(model),
								$author$project$Main$viewBottomBar(model)
							]));
				}
			}()
			]));
};
var $author$project$Main$view = function (model) {
	return {
		body: function () {
			var _v0 = model.authModel.loginState;
			switch (_v0.$) {
				case 'Checking':
					return _List_fromArray(
						[
							A2(
							$elm$html$Html$div,
							_List_fromArray(
								[
									A2($elm$html$Html$Attributes$style, 'position', 'relative')
								]),
							_List_fromArray(
								[
									A2(
									$elm$html$Html$div,
									_List_fromArray(
										[
											A2($elm$html$Html$Attributes$style, 'filter', 'blur(4px)'),
											A2($elm$html$Html$Attributes$style, 'pointer-events', 'none')
										]),
									_List_fromArray(
										[
											$author$project$Main$viewMainContent(model)
										])),
									A2(
									$elm$html$Html$div,
									_List_fromArray(
										[
											A2($elm$html$Html$Attributes$style, 'position', 'fixed'),
											A2($elm$html$Html$Attributes$style, 'top', '0'),
											A2($elm$html$Html$Attributes$style, 'left', '0'),
											A2($elm$html$Html$Attributes$style, 'width', '100%'),
											A2($elm$html$Html$Attributes$style, 'height', '100%'),
											A2($elm$html$Html$Attributes$style, 'display', 'flex'),
											A2($elm$html$Html$Attributes$style, 'align-items', 'center'),
											A2($elm$html$Html$Attributes$style, 'justify-content', 'center'),
											A2($elm$html$Html$Attributes$style, 'background', 'rgba(0, 0, 0, 0.3)'),
											A2($elm$html$Html$Attributes$style, 'z-index', '9999')
										]),
									_List_fromArray(
										[
											A2(
											$elm$html$Html$div,
											_List_fromArray(
												[
													A2($elm$html$Html$Attributes$style, 'width', '60px'),
													A2($elm$html$Html$Attributes$style, 'height', '60px'),
													A2($elm$html$Html$Attributes$style, 'border', '6px solid #f3f3f3'),
													A2($elm$html$Html$Attributes$style, 'border-top', '6px solid #667eea'),
													A2($elm$html$Html$Attributes$style, 'border-radius', '50%'),
													A2($elm$html$Html$Attributes$style, 'animation', 'spin 1s linear infinite')
												]),
											_List_Nil)
										]))
								]))
						]);
				case 'NotLoggedIn':
					return _List_fromArray(
						[
							A2(
							$elm$html$Html$map,
							$author$project$Main$AuthMsg,
							$author$project$Auth$view(model.authModel))
						]);
				case 'LoggingIn':
					return _List_fromArray(
						[
							A2(
							$elm$html$Html$map,
							$author$project$Main$AuthMsg,
							$author$project$Auth$view(model.authModel))
						]);
				default:
					return _List_fromArray(
						[
							$author$project$Main$viewMainContent(model)
						]);
			}
		}(),
		title: 'Gauntlet Video Sim POC'
	};
};
var $author$project$Main$main = $elm$browser$Browser$application(
	{init: $author$project$Main$init, onUrlChange: $author$project$Main$UrlChanged, onUrlRequest: $author$project$Main$LinkClicked, subscriptions: $author$project$Main$subscriptions, update: $author$project$Main$update, view: $author$project$Main$view});
_Platform_export({'Main':{'init':$author$project$Main$main(
	$elm$json$Json$Decode$succeed(_Utils_Tuple0))(0)}});}(this));
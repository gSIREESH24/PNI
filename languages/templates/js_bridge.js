const __poly_exports = {};

globalThis.poly_export = function(name, value) {
    __poly_exports[name] = value;
};

globalThis.get_global = function(name, fallback) {
    if (fallback === undefined) { fallback = null; }
    const v = globalThis[name];
    if (v === undefined) return fallback;

    if (v && typeof v === "object" && typeof v.__handle__ === "number") {
        return new Proxy(v, {
            get: function(target, prop) {
                if (prop in target) return target[prop];
                if (typeof prop === "string") {
                    return function() {
                        var _args = Array.prototype.slice.call(arguments);
                        process.stdout.write(
                            "__POLY_METHOD__|" + target.__handle__ + "|" + prop + "|" + JSON.stringify(_args) + "\n"
                        );
                        return globalThis._poly_read_ret();
                    };
                }
            }
        });
    }
    return v;
};

globalThis._poly_read_ret = function() {
    var _fs  = require("fs");
    var _buf = Buffer.alloc(1);
    var _line = "";
    while (true) {
        var _n = _fs.readSync(0, _buf, 0, 1, null);
        if (_n === 0) break;
        var _ch = String.fromCharCode(_buf[0]);
        if (_ch === "\n") break;
        _line += _ch;
    }
    _line = _line.replace(/\r$/, "");

    var _RET = "__POLY_RET__|";
    if (!_line.startsWith(_RET)) return null;
    var _rest = _line.slice(_RET.length);
    var _idx  = _rest.indexOf("|");
    if (_idx < 0) return null;
    var _t = _rest.slice(0, _idx);
    var _v = _rest.slice(_idx + 1);

    if (_t === "int")   return parseInt(_v, 10);
    if (_t === "float") return parseFloat(_v);
    if (_t === "bool")  return _v === "true";
    if (_t === "null")  return null;
    return _v.replace(/\\n/g, "\n")
             .replace(/\\r/g, "\r")
             .replace(/\\\\/g, "\\");
};

globalThis.call_bridge = function() {
    var _name = arguments[0];
    var _args = Array.prototype.slice.call(arguments, 1);
    process.stdout.write(
        "__POLY_CALL__|" + _name + "|" + JSON.stringify(_args) + "\n"
    );
    return globalThis._poly_read_ret();
};

globalThis.poly_export_function = function(name, fn, return_type) {
    var _src     = fn.toString();
    var _wrapped = "var __stub_fn = (" + _src + ");";
    var _ret     = return_type || "auto";
    process.stdout.write(
        "__POLY_REGISTER__|" + name + "|js|" + _ret + "|" +
        JSON.stringify(_wrapped) + "\n"
    );
};

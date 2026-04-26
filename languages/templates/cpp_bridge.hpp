/*
 * cpp_bridge.hpp — PLF bridge glue injected before every user C++ block.
 *
 * Available in user code (via `using namespace polybridge;`):
 *   export_value(name, value)            — publish any scalar to the bridge
 *   call_bridge<T>(name, args)           — call a Python-registered fn (typed)
 *   call_bridge_i/f/b/s(name, args)     — convenience wrappers
 *   call_method<T>(handle, method, args) — invoke a method on a Python object
 *   export_bridge_function(n, src, rt)   — register this C++ function back
 */

#include <iostream>
#include <string>
#include <cstdio>
#include <cstdlib>
#include <cstring>

namespace polybridge {

/* ── Unbuffer stdout/stdin for the pipe protocol ── */
__attribute__((constructor))
static void _poly_unbuffer() {
    setvbuf(stdout, nullptr, _IONBF, 0);
    setvbuf(stdin,  nullptr, _IONBF, 0);
}

/* ── export_value overloads ── */
inline void export_value(const std::string& name, long long v) {
    std::cout << "__POLY_EXPORT__" << name << "|int|"    << v                    << std::endl;
}
inline void export_value(const std::string& name, int v) {
    std::cout << "__POLY_EXPORT__" << name << "|int|"    << v                    << std::endl;
}
inline void export_value(const std::string& name, double v) {
    std::cout << "__POLY_EXPORT__" << name << "|double|" << v                    << std::endl;
}
inline void export_value(const std::string& name, bool v) {
    std::cout << "__POLY_EXPORT__" << name << "|bool|"   << (v ? "true":"false") << std::endl;
}
inline void export_value(const std::string& name, const char* v) {
    std::cout << "__POLY_EXPORT__" << name << "|string|" << (v ? v : "")        << std::endl;
}
inline void export_value(const std::string& name, const std::string& v) {
    std::cout << "__POLY_EXPORT__" << name << "|string|" << v                   << std::endl;
}

/* ── Bridge call helpers ── */
static char __poly_ret_buf[65536];

static void _poly_call_raw(const char *name, const char *args_json) {
    printf("__POLY_CALL__|%s|%s\n", name, args_json);
    fflush(stdout);
    if (!fgets(__poly_ret_buf, (int)sizeof(__poly_ret_buf), stdin))
        __poly_ret_buf[0] = '\0';
}

namespace detail {
    template<typename T> T _parse_ret();

    template<> long long _parse_ret() {
        const char *p;
        if ((p = strstr(__poly_ret_buf, "|int|")))   return (long long)atoll(p + 5);
        if ((p = strstr(__poly_ret_buf, "|float|"))) return (long long)atof(p + 7);
        if ((p = strstr(__poly_ret_buf, "|bool|")))  return strncmp(p + 6, "true", 4) == 0 ? 1LL : 0LL;
        return 0;
    }
    template<> int _parse_ret() { return (int)_parse_ret<long long>(); }
    template<> double _parse_ret() {
        const char *p;
        if ((p = strstr(__poly_ret_buf, "|float|"))) return atof(p + 7);
        if ((p = strstr(__poly_ret_buf, "|int|")))   return (double)atoll(p + 5);
        return 0.0;
    }
    template<> bool _parse_ret() {
        const char *p;
        if ((p = strstr(__poly_ret_buf, "|bool|"))) return strncmp(p + 6, "true", 4) == 0;
        if ((p = strstr(__poly_ret_buf, "|int|")))  return atoll(p + 5) != 0;
        return false;
    }
    template<> std::string _parse_ret() {
        const char *p = strstr(__poly_ret_buf, "|str|");
        if (!p) return "";
        std::string s(p + 5);
        while (!s.empty() && (s.back() == '\n' || s.back() == '\r')) s.pop_back();
        return s;
    }
} // namespace detail

template<typename R>
R call_bridge(const std::string& name, const std::string& args_json = "[]") {
    _poly_call_raw(name.c_str(), args_json.c_str());
    return detail::_parse_ret<R>();
}

inline long long   call_bridge_i(const std::string& n, const std::string& a = "[]") { return call_bridge<long long>(n, a);   }
inline double      call_bridge_f(const std::string& n, const std::string& a = "[]") { return call_bridge<double>(n, a);      }
inline bool        call_bridge_b(const std::string& n, const std::string& a = "[]") { return call_bridge<bool>(n, a);       }
inline std::string call_bridge_s(const std::string& n, const std::string& a = "[]") { return call_bridge<std::string>(n, a);}

/* ── Method proxy (Phase 3E) ── */
static void _poly_method_raw(long long handle, const char *method, const char *args_json) {
    printf("__POLY_METHOD__|%lld|%s|%s\n", handle, method, args_json);
    fflush(stdout);
    if (!fgets(__poly_ret_buf, (int)sizeof(__poly_ret_buf), stdin))
        __poly_ret_buf[0] = '\0';
}

template<typename R>
R call_method(long long handle, const std::string& method, const std::string& args_json = "[]") {
    _poly_method_raw(handle, method.c_str(), args_json.c_str());
    return detail::_parse_ret<R>();
}

inline long long   call_method_i(long long h, const std::string& m, const std::string& a = "[]") { return call_method<long long>(h, m, a);   }
inline double      call_method_f(long long h, const std::string& m, const std::string& a = "[]") { return call_method<double>(h, m, a);      }
inline bool        call_method_b(long long h, const std::string& m, const std::string& a = "[]") { return call_method<bool>(h, m, a);       }
inline std::string call_method_s(long long h, const std::string& m, const std::string& a = "[]") { return call_method<std::string>(h, m, a);}

/* ── JSON string printer (used by class-schema export overloads) ── */
inline void _poly_json_str(const char *s) {
    putchar('"');
    for (; *s; ++s) {
        if      (*s == '"')  { putchar('\\'); putchar('"');  }
        else if (*s == '\\') { putchar('\\'); putchar('\\'); }
        else if (*s == '\n') { putchar('\\'); putchar('n');  }
        else if (*s == '\r') { putchar('\\'); putchar('r');  }
        else if (*s == '\t') { putchar('\\'); putchar('t');  }
        else                 { putchar(*s); }
    }
    putchar('"');
}

/* ── Function stub registration ── */
#define export_bridge_function(name, source, return_type)         \
    do {                                                           \
        printf("__POLY_REGISTER__|%s|cpp|%s|", name, return_type);\
        polybridge::_poly_json_str(source);                        \
        puts("");                                                   \
        fflush(stdout);                                            \
    } while(0)

} // namespace polybridge

using namespace polybridge;

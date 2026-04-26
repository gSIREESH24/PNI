#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>

static void _poly_json_str(const char *s);

__attribute__((constructor))
static void _poly_unbuffer(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stdin,  NULL, _IONBF, 0);
}

static void _poly_int   (const char *n, long long  v) { printf("__POLY_EXPORT__%s|int|%lld\n",     n, v); }
static void _poly_double(const char *n, double     v) { printf("__POLY_EXPORT__%s|double|%.17g\n", n, v); }
static void _poly_bool  (const char *n, int        v) { printf("__POLY_EXPORT__%s|bool|%s\n",     n, v ? "true" : "false"); }
static void _poly_str   (const char *n, const char *v){ printf("__POLY_EXPORT__%s|string|%s\n",   n, v ? v : ""); }

#define export_value(name, value) _Generic((value),     \
    _Bool:        _poly_bool,                            \
    char *:       _poly_str,                             \
    const char *: _poly_str,                             \
    float:        _poly_double,                          \
    double:       _poly_double,                          \
    default:      _poly_int                              \
)(name, value)

static char __poly_ret_buf[65536];

static void _poly_call_raw(const char *name, const char *args_json) {
    printf("__POLY_CALL__|%s|%s\n", name, args_json);
    fflush(stdout);
    if (!fgets(__poly_ret_buf, (int)sizeof(__poly_ret_buf), stdin))
        __poly_ret_buf[0] = '\0';
}

static long long _parse_ret_i(void) {
    char *p;
    if ((p = strstr(__poly_ret_buf, "|int|")))   return atoll(p + 5);
    if ((p = strstr(__poly_ret_buf, "|float|"))) return (long long)atof(p + 7);
    if ((p = strstr(__poly_ret_buf, "|bool|")))  return strncmp(p + 6, "true", 4) == 0 ? 1LL : 0LL;
    return 0;
}
static double _parse_ret_f(void) {
    char *p;
    if ((p = strstr(__poly_ret_buf, "|float|"))) return atof(p + 7);
    if ((p = strstr(__poly_ret_buf, "|int|")))   return (double)atoll(p + 5);
    if ((p = strstr(__poly_ret_buf, "|bool|")))  return strncmp(p + 6, "true", 4) == 0 ? 1.0 : 0.0;
    return 0.0;
}
static int _parse_ret_b(void) {
    char *p;
    if ((p = strstr(__poly_ret_buf, "|bool|"))) return strncmp(p + 6, "true", 4) == 0 ? 1 : 0;
    if ((p = strstr(__poly_ret_buf, "|int|")))  return atoll(p + 5) != 0 ? 1 : 0;
    return 0;
}
static const char *_parse_ret_s(void) {
    char *p = strstr(__poly_ret_buf, "|str|");
    if (!p) return "";
    p += 5;
    size_t len = strlen(p);
    while (len > 0 && (p[len-1] == '\n' || p[len-1] == '\r')) p[--len] = '\0';
    return p;
}

static long long   call_bridge_i(const char *n, const char *a) { _poly_call_raw(n, a); return _parse_ret_i(); }
static double      call_bridge_f(const char *n, const char *a) { _poly_call_raw(n, a); return _parse_ret_f(); }
static int         call_bridge_b(const char *n, const char *a) { _poly_call_raw(n, a); return _parse_ret_b(); }
static const char *call_bridge_s(const char *n, const char *a) { _poly_call_raw(n, a); return _parse_ret_s(); }

static void _poly_method_raw(long long handle, const char *method, const char *args_json) {
    printf("__POLY_METHOD__|%lld|%s|%s\n", handle, method, args_json);
    fflush(stdout);
    if (!fgets(__poly_ret_buf, (int)sizeof(__poly_ret_buf), stdin))
        __poly_ret_buf[0] = '\0';
}

static long long   call_method_i(long long h, const char *m, const char *a) { _poly_method_raw(h, m, a); return _parse_ret_i(); }
static double      call_method_f(long long h, const char *m, const char *a) { _poly_method_raw(h, m, a); return _parse_ret_f(); }
static int         call_method_b(long long h, const char *m, const char *a) { _poly_method_raw(h, m, a); return _parse_ret_b(); }
static const char *call_method_s(long long h, const char *m, const char *a) { _poly_method_raw(h, m, a); return _parse_ret_s(); }

static void _poly_json_str(const char *s) {
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

#define export_bridge_function(name, source, return_type)  \
    do {                                                    \
        printf("__POLY_REGISTER__|%s|c|%s|", name, return_type); \
        _poly_json_str(source);                             \
        puts("");                                           \
        fflush(stdout);                                     \
    } while(0)

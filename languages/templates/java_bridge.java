/*
 * java_bridge.java — PLF bridge members injected into every user Java block.
 *
 * This file is NOT compiled directly. The runner reads it and injects its
 * contents at the top of the `Main` class body before compilation.
 *
 * Available in user code (all methods are static on Main):
 *   export_value(String name, <type> value)    — publish scalar to bridge
 *   get_global(String name)                    — read any bridge-shared value
 *   call_bridge(String name, Object... args)   — call a Python-registered fn
 *   call_method(long handle, String m, ...)    — invoke method on Python object
 *   export_bridge_function(name, src, retType) — register Java fn back to Python
 *
 * Shared globals and class schemas are injected by adapters.py ABOVE this block.
 */

    /* ── PolyBridge stdin reader ── */
    private static final java.io.BufferedReader __bridge_stdin =
        new java.io.BufferedReader(new java.io.InputStreamReader(System.in));

    /* ── Read and decode a __POLY_RET__ response ── */
    private static Object _parse_ret(String line) {
        if (line == null || !line.startsWith("__POLY_RET__|")) return null;
        String rest = line.substring("__POLY_RET__|".length());
        int idx = rest.indexOf('|');
        if (idx < 0) return null;
        String type = rest.substring(0, idx);
        String val  = rest.substring(idx + 1);
        switch (type) {
            case "int":   return Long.parseLong(val.trim());
            case "float": return Double.parseDouble(val.trim());
            case "bool":  return val.trim().equals("true");
            case "null":  return null;
            default:      return val
                .replace("\\n", "\n")
                .replace("\\r", "\r")
                .replace("\\\\", "\\");
        }
    }

    /* ── Format args as a JSON array for __POLY_CALL__ ── */
    private static String _format_args(Object... args) {
        StringBuilder sb = new StringBuilder("[");
        for (int i = 0; i < args.length; i++) {
            if (i > 0) sb.append(",");
            Object a = args[i];
            if (a instanceof String) {
                sb.append("\"")
                  .append(((String) a).replace("\\", "\\\\").replace("\"", "\\\""))
                  .append("\"");
            } else if (a == null) {
                sb.append("null");
            } else {
                sb.append(a);
            }
        }
        sb.append("]");
        return sb.toString();
    }

    /* ── export_value overloads ── */
    public static void export_value(String name, int value) {
        System.out.println("__POLY_EXPORT__" + name + "|int|" + value);
        System.out.flush();
    }
    public static void export_value(String name, long value) {
        System.out.println("__POLY_EXPORT__" + name + "|int|" + value);
        System.out.flush();
    }
    public static void export_value(String name, double value) {
        System.out.println("__POLY_EXPORT__" + name + "|double|" + value);
        System.out.flush();
    }
    public static void export_value(String name, boolean value) {
        System.out.println("__POLY_EXPORT__" + name + "|bool|" + value);
        System.out.flush();
    }
    public static void export_value(String name, String value) {
        String safe = (value == null) ? "" : value
            .replace("\\", "\\\\")
            .replace("|",  "\\|")
            .replace("\n", "\\n")
            .replace("\r", "\\r");
        System.out.println("__POLY_EXPORT__" + name + "|string|" + safe);
        System.out.flush();
    }
    public static void export_value(String name, Object value) {
        export_value(name, value == null ? "null" : String.valueOf(value));
    }

    /* ── call_bridge ── */
    public static Object call_bridge(String name, Object... args) {
        System.out.println("__POLY_CALL__|" + name + "|" + _format_args(args));
        System.out.flush();
        try { return _parse_ret(__bridge_stdin.readLine()); }
        catch (Exception e) { return null; }
    }

    /* ── call_method (Phase 3E) ── */
    public static Object call_method(long handle, String method, Object... args) {
        System.out.println("__POLY_METHOD__|" + handle + "|" + method + "|" + _format_args(args));
        System.out.flush();
        try { return _parse_ret(__bridge_stdin.readLine()); }
        catch (Exception e) { return null; }
    }

    /* ── export_bridge_function ── */
    public static void export_bridge_function(String name, String source, String returnType) {
        String safe = source
            .replace("\\", "\\\\")
            .replace("\"", "\\\"")
            .replace("\n", "\\n")
            .replace("\r", "\\r")
            .replace("\t", "\\t");
        System.out.println("__POLY_REGISTER__|" + name + "|java|" + returnType + "|\"" + safe + "\"");
        System.out.flush();
    }

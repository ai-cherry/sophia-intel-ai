async def handle(method: str, params: Dict[str, Any]) -> Any:
    if method == "health/get":
        return {"status": "healthy"}

    if method == "fs/file_read":
        # params: path (relative to repo root), max_bytes?
        p = safe_path(params["path"])
        if not p.exists() or not p.is_file():
            raise RPCError(-32010, f"file not found: {p}")
        if p.stat().st_size > MAX_FILE_BYTES:
            raise RPCError(-32011, "file too large")
        with open(p, "r", encoding="utf-8", errors="ignore") as fh:
            return {"path": str(p.relative_to(REPO_ROOT)), "content": fh.read()}

    if method == "code/grep":
        # params: pattern (regex), case_sensitive (bool, default True), literal (bool, default False), dir (optional)
        pattern = params["pattern"]
        case_sensitive = bool(params.get("case_sensitive", True))
        literal = bool(params.get("literal", False))
        cwd = safe_path(params.get("dir", "."))
        if is_vendor(cwd):
            cwd = REPO_ROOT
        # try ripgrep first
        hits = await run_ripgrep(pattern, cwd, literal=literal)
        if hits:
            return [{"path": h[0], "line": h[1], "text": h[2]} for h in hits]
        # fallback to pure Python regex
        flags = 0 if case_sensitive else re.IGNORECASE
        hits = await py_grep(pattern if not literal else re.escape(pattern), cwd, flags=flags)
        return [{"path": h[0], "line": h[1], "text": h[2]} for h in hits]

    if method == "code/code_search":
        # alias for literal search
        q = params["query"]
        cwd = safe_path(params.get("dir", "."))
        hits = await run_ripgrep(q, cwd, literal=True)
        if not hits:
            hits = await py_grep(re.escape(q), cwd, flags=0)
        return [{"path": h[0], "line": h[1], "text": h[2]} for h in hits]

    if method == "code/symbol_search":
        # params: dir (optional)
        cwd = safe_path(params.get("dir", "."))
        results = []
        for p in list_files(cwd):
            if p.suffix not in {".py", ".ts", ".tsx", ".js"}:
                continue
            if p.stat().st_size > MAX_FILE_BYTES:
                continue
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as fh:
                    text = fh.read()
                if p.suffix == ".py":
                    for _, ln, snip in python_symbols(text):
                        results.append(
                            {"path": str(p.relative_to(cwd)), "line": ln, "symbol": snip})
                else:
                    for _, ln, snip in ts_js_symbols(text):
                        results.append(
                            {"path": str(p.relative_to(cwd)), "line": ln, "symbol": snip})
            except Exception:
                continue
        return results

    raise RPCError(-32601, f"unknown method: {method}")


async def rpc_loop() -> None:
    # Simple line-delimited JSON-RPC 2.0 over stdio
    while True:
        line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
        if not line:
            await asyncio.sleep(0.01)
            continue
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            method = req.get("method")
            params = req.get("params", {}) or {}
            req_id = req.get("id")
            try:
                result = await asyncio.wait_for(handle(method, params), timeout=REQUEST_TIMEOUT)
                resp = {"jsonrpc": "2.0", "id": req_id, "result": result}
            except RPCError as e:
                resp = {"jsonrpc": "2.0", "id": req_id, "error": {
                    "code": e.code, "message": e.message, "data": e.data}}
            except Exception as e:
                log("Unhandled error:", repr(e))
                log(traceback.format_exc())
                resp = {"jsonrpc": "2.0", "id": req_id, "error": {
                    "code": -32000, "message": "internal error"}}
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()
        except Exception as e:
            log("Bad JSON:", line[:200])
            err = {"jsonrpc": "2.0", "id": None, "error": {
                "code": -32700, "message": "parse error"}}
            sys.stdout.write(json.dumps(err) + "\n")
            sys.stdout.flush()


def cli_health() -> int:
    try:
        # Quick filesystem probe
        _ = REPO_ROOT.exists()
        print(json.dumps({"status": "healthy"}))
        return 0
    except Exception as e:
        print(json.dumps({"status": "unhealthy", "error": str(e)}))
        return 1


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "--health":
        raise SystemExit(cli_health())
    try:
        asyncio.run(rpc_loop())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

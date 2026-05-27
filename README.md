Ось професійний, детальний та структурований файл `README.md` англійською мовою. Він розбитий за стандартами Open Source проєктів, описує проблему, твоє архітектурне рішення, процес запуску та тестування.

---

### `README.md`

```markdown
# PAC (Proxy Auto-Configuration) Server for Ontology Time Machine

This component introduces a dynamic PAC (Proxy Auto-Configuration) server for the Ontology Time Machine proxy built on top of `proxy.py`. It addresses the traffic routing efficiency issues, specifically preventing performance bottlenecks when running the proxy in `restrictedAccess` mode.

---

## The Problem (Issue #90)

When using the ontology proxy, routing **all** global internet traffic (videos, images, general web pages) through the proxy server introduces massive bandwidth overhead and stability risks. 

To solve this, a **Restricted Mode** was introduced to filter out non-ontology traffic. However:
1. **Tooling Limitations:** Traditional CLI tools (`curl`), Java applications, and RDF frameworks (e.g., Apache Jena, RDFLib) do not natively execute or respect JavaScript-based PAC files. They rely entirely on environment variables like `HTTP_PROXY`.
2. **Stateless PAC Overhead:** The dataset containing Archivo ontology domains can grow exponentially large (tens of thousands of items). Iterating through a massive array using standard loops (`for...in`) inside a stateless PAC file for *every single HTTP request* severely degrades client-side browser performance.

---

## Architectural Solution

This implementation solves both challenges through a hybrid and highly optimized approach:

### 1. Main-Process Server Spawning
Because `proxy.py` operates in a multi-processing threadless architecture (spawning multiple isolated worker acceptors), running a background thread within a plugin hook would cause race conditions and `Address already in use` crashes. 
The PAC HTTP server is safely bound and spawned on port `8000` from the **main process** prior to initiating the `proxy.py` engine loop.

### 2. O(1) JavaScript Optimization
Instead of linear array scanning, the generator transforms the python domain config into a JavaScript **Hash-Table (Object lookup)**. Subdomain matching is handled by popping domain segments using `.split('.')` rather than checking string suffixes against thousands of entries. This guarantees an $O(1)$ average complexity lookup, protecting client machine resources.

### 3. Smart Fallback Routing
* **Browsers:** Fetch the configuration from `http://localhost:8000/proxy.pac` and handle routing efficiently on the client-side.
* **Non-JS Tools (`curl`, JVM):** When pointing these tools to the proxy port directly, the internal `OntologyTimeMachinePlugin` fallback hooks intercepts the traffic and passes non-ontology requests transparently (`DIRECT`), fulfilling the stateless failsafe promise.

---

## Generated PAC Code Behavior

Depending on your configuration, the PAC server dynamically switches between two states:

### A. Normal Mode (`restrictedAccess = False`)
Instructs the client to route all traffic directly through the proxy endpoint.
```javascript
function FindProxyForURL(url, host) {
    return "PROXY 127.0.0.1:8898";
}

```

### B. Restricted Mode (`restrictedAccess = True`)

Injects the optimized hash-table lookup. Only matched ontology domains go to the proxy; the rest bypass it instantly via `DIRECT`.

```javascript
var archivoDomains = {
    "dbpedia.org": true,
    "w3.org": true,
    "wikipedia.org": true
};

function isOntologyHost(host) {
    if (!host) return false;
    host = host.toLowerCase();

    // 1. Instant O(1) Hash-Table Check
    if (archivoDomains[host]) return true;

    // 2. High-performance Subdomain Slicing
    var parts = host.split('.');
    while (parts.length > 1) {
        parts.shift();
        var parentDomain = parts.join('.');
        if (archivoDomains[parentDomain]) return true;
    }

    return false;
}

function FindProxyForURL(url, host) {
    if (isOntologyHost(host)) {
        return "PROXY 127.0.0.1:8898";
    }
    return "DIRECT";
}

```

---

## How to Run & Verify

1. Run your proxy server using your custom proxy startup script:
```bash
python custom_proxy.py

```


2. Verify the PAC server thread log in your console:
```text
[PAC] Starting PAC server thread from main process...
[PAC] http://localhost:8000/proxy.pac
[PAC] PAC server thread successfully spawned

```


3. Open your browser or use `curl` to inspect the generated routing rules:
```bash
curl http://localhost:8000/proxy.pac

```



---

## Testing

Comprehensive unit tests cover the PAC generator logic, ensuring strict syntax validation and checking correct interface IP mapping (e.g., transforming `0.0.0.0` or `::` interface arrays into a browser-compliant `127.0.0.1` single endpoint).

Execute the test suite using `pytest`:

```bash
pytest -v tests/pac/test_pac.py

```

```

```
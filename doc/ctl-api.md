# Control API Documentation

The following contains the documentation regarding the Control API. These calls
are done with HTTP requests sent to Zproxy's control socket.

## Statistics

You can receive statistics and other general data on the current state of Zproxy
and its logical components. This can be done by sending a GET request specifying
in the path the component you wish to enquire of.

- Get the stats for a listener with 'listener\_id'

```
GET /listener/<listener_id>
```

- Get the stats for the services belonging to 'listener\_id'

```
GET /listener/<listener_id>/services/
```

- Get the stats for a service with 'service\_name'

```
GET /listener/<listener_id>/service/<service_name>
```

- Get the stats for the backends belonging to 'service\_name'

```
GET /listener/<listener_id>/service/<service_name>/backends
```

- Get the stats for the sessions belonging to 'service\_name'

```
GET /listener/<listener_id>/service/<service_name>/sessions
```

- Get the stats for a backend with 'backend\_id'

```
GET /listener/<listener_id>/service/<service_name>/backend/<backend_id>
```

### Attributes

The following are the attributes that you can find pertaining to the different
components of Zproxy.

#### Listener

- **3xx-code-hits** "integer": The number of 3xx codes that the listener
  generated and responded to the clients. These responses don't come from the
  backends.
- **4xx-code-hits** "integer": The number of 4xx codes that the listener
  generated and responded to the clients. These responses don't come from the
  backends.
- **5xx-code-hits** "integer": The number of 5xx codes that the listener
  generated and responded to the clients. These responses don't come from the
  backends.
- **waf-hits** "integer": The number of requests rejected by Zproxy. They will
  be counted in *xxx-code-hits* depending on the response code.
- **address** "string": The IPv4/IPv6 address used by the listener to listen to
  HTTP requests. This parameter can be modified through a configuration file
  directive.
- **connections** "integer": The number of currently established connections
  that the listener has established with the clients (on the VIP).
- **https** "bool": Informs if the listener is configured with SSL. This
  parameter can be modified through a configuration file directive.
- **id** "integer": The listener identifier.
- **name** "string": A friendly name for the listener. This parameter can be
  modified through a configuration file directive.
- **pending-connections** "integer": The number of connections that the listener
  has received but they are not established in any backend.
- **port** "integer": The virtual port open on the system where Zproxy is
  listening. This parameter can be modified through a configuration file
  directive.
- **services** "service list": A list of the service objects with their
  configuration and status.

#### Service

- **backends** "backend list": A list of the backend objects with their
  configuration and status.
- **name** "string": A friendly name for the service. This parameter can be
  modified through a configuration file directive.
- **priority** "integer": Current priority setting of the service (based on how
  many backends are up). This parameter can be modified through a configuration
  file directive.
- **sessions** "session list": A list of the session objects registered in the
  service.

#### Backend

- **2xx-code-hits** "integer": The number of 2xx codes that Zproxy forwarded
  from the backend to the client.
- **3xx-code-hits** "integer": The number of 3xx codes that Zproxy forwarded
  from the backend to the client.
- **4xx-code-hits** "integer": The number of 4xx codes that Zproxy forwarded
  from the backend to the client.
- **5xx-code-hits** "integer": The number of 5xx codes that Zproxy forwarded
  from the backend to the client.
- **address** "string": The IPv4/IPv6 of the backend. This parameter can be
  modified through a configuration file directive.
- **connect-time** "floating": The average time that Zproxy takes to connect
  with this backend in seconds.
- **connections** "integer": The number of currently established connections
  that Zproxy has with this backend.
- **connections-limit** "integer": The number of maximum concurrent connections
  that Zproxy will send to this backend. This parameter can be modified through
  a configuration file directive. A limit of 0 means there is no limit.
- **https** "bool": Informs if the backend is configured with SSL. This
  parameter can be modified through a configuration file directive.
- **id** "string": A unique backend identifier. The standard format for this ID
  is `<address>-<port>`.
- **pending-connections** "integer": The number of connections that were sent to
  this backend and they are not accepted yet.
- **port** "integer": The port in the backend where Zproxy will send the HTTP
  requests. This parameter can be modified through a configuration file
  directive.
- **priority** "integer": Establishes a backend priority which will determine
  whether or not the service will use it depending on the service priority. If
  the service priority is less than the backend priority, the backend *will not
  be used*.
- **response-time** "floating": The average time that a backend takes to respond
  a request in seconds.
- **cookie-key** "string": Key used in a cookie to associate sessions with a
  backend. It's format is `4-<address>-<port>` where `<address>` and `<port>`
  are the address and port respectively of the backend, formatted in the network
  byte order long integer hexidecimal format.
- **status** "string": Informs about the backend status. It can be *active*,
  *down*, or *disabled*:
  - *active*: The backend is up and running.
  - *down*: Zproxy cannot connect to the backend.
  - *disabled*: The backend has been manually disabled and Zproxy will not
    attempt to send any requests to it.
- **type** "integer": Informs about the kind of backend 0 (it's a remote
  backend) or 1 (it's a redirect).
- **nfmark** "integer": the value of the NfMark configuration. This
  parameter can be modified through a configuration file directive.
- **weight** "integer": A value to select more a backend than others. This
  parameter can be modified through a configuration file directive.

#### Session

- **id** "integer": A unique identifier for the session. Can be set in
  configuration if URL session type is used.
- **backend-id** "string": A unique backend identifier. The standard format for
  this ID is `<address>-<port>`.
- **last-seen** "integer": The number of seconds since the last packet regarding
  this session was managed by Zproxy.

## Configuration/Manipulation

It is possible to manipulate and configure many of the components of a running
Zproxy process via the control API. Upon success a JSON will be returned as
follows:

```json
{
        "result": "ok"
}
```

On error, it will return the following:

```json
{
        "result": "error",
        "reason": "<reason>"
}
```

### Global

- Reload configuration

```
PATCH /config
```

### Backend

- Disable a backend

```
PATCH '{"status":"disabled"}' /listener/<listener_id>/service/<service_id>/backend/<backend_id>/status
```

- Enable a backend

```
PATCH '{"status":"active"}' /listener/<listener_id>/service/<service_id>/backend/<backend_id>/status
```

- Add backend in runtime

```
PUT '{"id":"<backend_id>","address":"<address>","https":<bool>, "port": <port>, "weight": <weight>}' /listener/<listener_id>/service/<service_id>/backends
```

### Session

- Create new session

```
PUT '{"backend-id":"<backend_id>","id":"<session_id>","last-seen":<last_seen>}' /listener/<listener_id>/service/<service_id>/sessions
```

- Flush service sessions

```
DELETE /listener/<listener_id>/service/<service_id>/sessions
```

- Flush service session with ID 'session\_id'

```
DELETE '{"id":"value"}' /listener/<listener_id>/service/<service_id>/sessions
```

- Flush service sessions with 'backend\_id'

```
DELETE '{"backend-id":"<backend_id>"}' /listener/<listener_id>/service/<service_id>/sessions
```

- Modify session

```
PATCH '{"backend-id":"<backend_id>","last-seen":<last_seen>}' /listener/<listener_id>/service/<service_id>/session/<session_id>
```

- Synchronize sessions from JSON array

```
PATCH '[{"backend-id":"<backend_id>","last-seen":<last_seen>},...]' /listener/<listener_id>/service/<service_id>/sessions
```

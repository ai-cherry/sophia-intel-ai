## WebSocket Endpoints for Swarm Coordination

- **Endpoint**: `ws://localhost:8005/ws/swarm`

  - **Purpose**: Real-time communication for swarm agent coordination
  - **Usage**: Connects agents to the swarm management system
  - **Example**:

    ```javascript
    const socket = new WebSocket("ws://localhost:8005/ws/swarm");
    socket.onmessage = (event) => {
      console.log("Swarm update:", event.data);
    };
    ```

- **Endpoint**: `ws://localhost:8005/ws/teams`

  - **Purpose**: Team-level coordination and status updates
  - **Usage**: Used by team managers to broadcast updates
  - **Example**:

    ```javascript
    const teamSocket = new WebSocket("ws://localhost:8005/ws/teams");
    teamSocket.send(JSON.stringify({ team: "team-1", status: "active" }));
    ```

- **Endpoint**: `ws://localhost:8005/ws/monitoring`

  - **Purpose**: Real-time monitoring and metrics streaming
  - **Usage**: For Grafana and Prometheus integration
  - **Example**:

    ```javascript
    const monitorSocket = new WebSocket("ws://localhost:8005/ws/monitoring");
    monitorSocket.onmessage = (event) => {
      const metrics = JSON.parse(event.data);
      console.log("New metrics:", metrics);
    };
    ```

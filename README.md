# HACCP Smart Cooking System for Thingsboard

This project implements a HACCP-compliant cooking monitoring system using Thingsboard. It includes a Rule Chain for logic processing, a Custom Widget for user interaction, and a Python simulation script.

## 1. Architecture Proposal

### Database Strategy for Cooking History
The user requirement asks for "Cooking History" to be stored in a database.
**Proposed Solution**: Use Thingsboard's native **Time-series Database (Telemetry)**.
Instead of setting up an external SQL database, we will utilize Thingsboard's ability to store JSON telemetry. When a cooking session finishes, the Rule Chain will generate a specific telemetry data point named `cooking_history`.

*   **Key**: `cooking_history`
*   **Value**: A JSON object containing the summary of the session (Start Time, End Time, Average Temp, Min/Max Temp, Alarm Status).

This allows the Widget to query history using standard Thingsboard APIs (`/api/plugins/telemetry/{entityId}/values/timeseries`) without needing external connectors.

## 2. Data Model

### Shared Attributes (Configuration)
These attributes are set by the Widget and read by the Rule Chain/Device.

| Attribute Name | Type | Description |
| :--- | :--- | :--- |
| `targetTemp` | Double | The required cooking temperature (e.g., 100°C). |
| `cookingDuration` | Integer | Duration in seconds (e.g., 600 for 10 mins). |
| `startMode` | String | `'manual'` or `'auto'`. |
| `upperLimit` | Double | **Mandatory**. Temperature threshold for Over-heat alarm. |
| `lowerLimit` | Double | **Optional**. Temperature threshold for Under-heat alarm. |
| `useLowerLimit` | Boolean | Checks lower limit only if `true`. |
| `isCooking` | Boolean | Current state control (Set `true` to start manually). |

### Server-side Attributes (Internal State)
Maintained by the Rule Chain.

| Attribute Name | Type | Description |
| :--- | :--- | :--- |
| `cookingStartTime` | Long | Timestamp when the current session started. |
| `activeAlarms` | String | List or flag of active alarms. |

### Telemetry (Data)
| Key | Type | Description |
| :--- | :--- | :--- |
| `temperature` | Double | Real-time sensor reading. |
| `cooking_history` | JSON | Record of a finished session. |

## 3. Features

### Rule Chain
*   **Auto Start**: Triggers when `temperature >= targetTemp` if `startMode` is `'auto'`.
*   **Manual Start**: Triggers when `isCooking` becomes `true`.
*   **Monitoring**: Continuously checks `upperLimit` (and `lowerLimit` if enabled).
*   **Alarms**: Generates 'Critical' alarm if limits are breached.
*   **Completion**: Stops when time elapses, saves history, and resets state.

### Widget
*   **Settings**: Inputs for all Shared Attributes.
*   **Real-time**: Gauge for temperature, visual indicator for State (Cooking/Idle).
*   **Chart**: Live graph of temperature.
*   **History**: Table displaying `cooking_history` data.

### Simulation
*   Python script mimicking a thermostat.

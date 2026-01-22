import json
import uuid

def generate_uuid():
    return str(uuid.uuid4())

# Unique IDs
bundle_id = generate_uuid()
widget_type_id = generate_uuid()

html_code = """
<div class="haccp-container">
    <div class="header">
        <div class="metric">
            <span class="label">Temperature</span>
            <span class="value" id="temp-value">--</span>
            <span class="unit">°C</span>
        </div>
        <div class="metric">
            <span class="label">Status</span>
            <span class="value" id="status-value">IDLE</span>
        </div>
        <div class="controls">
            <button id="btn-toggle" class="btn-primary">Start</button>
        </div>
    </div>

    <div class="tabs">
        <button class="tab-btn active" data-tab="monitor">Monitor</button>
        <button class="tab-btn" data-tab="settings">Settings</button>
        <button class="tab-btn" data-tab="history">History</button>
    </div>

    <div id="tab-monitor" class="tab-content active">
        <div class="chart-container">
            <canvas id="tempChart"></canvas>
        </div>
    </div>

    <div id="tab-settings" class="tab-content">
        <div class="form-group">
            <label>Start Mode</label>
            <select id="set-mode">
                <option value="manual">Manual</option>
                <option value="auto">Auto (Threshold)</option>
            </select>
        </div>
        <div class="form-group">
            <label>Target Temp (°C)</label>
            <input type="number" id="set-target">
        </div>
        <div class="form-group">
            <label>Duration (Seconds)</label>
            <input type="number" id="set-duration">
        </div>
        <div class="form-group">
            <label>Upper Limit (°C) (Mandatory)</label>
            <input type="number" id="set-upper">
        </div>
        <div class="form-group">
            <label>Lower Limit (°C)</label>
            <input type="number" id="set-lower">
        </div>
        <div class="form-group">
            <label>Use Lower Limit</label>
            <input type="checkbox" id="set-use-lower">
        </div>
        <button class="btn-save" id="btn-save">Save Configuration</button>
    </div>

    <div id="tab-history" class="tab-content">
        <button class="btn-refresh" id="btn-refresh-history">Refresh History</button>
        <table class="history-table">
            <thead>
                <tr>
                    <th>Time</th>
                    <th>Duration</th>
                    <th>Max Temp</th>
                    <th>Result</th>
                </tr>
            </thead>
            <tbody id="history-body">
            </tbody>
        </table>
    </div>
</div>
"""

css_code = """
.haccp-container { font-family: sans-serif; padding: 10px; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; background: #f0f0f0; padding: 10px; border-radius: 5px; }
.metric { display: flex; flex-direction: column; }
.metric .label { font-size: 0.8em; color: #666; }
.metric .value { font-size: 1.5em; font-weight: bold; }
.btn-primary { background: #007bff; color: white; border: none; padding: 10px 20px; cursor: pointer; border-radius: 3px; }
.btn-save { background: #28a745; color: white; border: none; padding: 10px; width: 100%; cursor: pointer; margin-top: 10px; }
.btn-refresh { background: #17a2b8; color: white; border: none; padding: 5px 10px; cursor: pointer; margin-bottom: 5px; }
.tabs { margin-bottom: 10px; border-bottom: 1px solid #ccc; }
.tab-btn { background: none; border: none; padding: 10px; cursor: pointer; }
.tab-btn.active { border-bottom: 2px solid #007bff; font-weight: bold; }
.tab-content { display: none; }
.tab-content.active { display: block; }
.form-group { margin-bottom: 10px; }
.form-group label { display: block; margin-bottom: 5px; }
.form-group input, .form-group select { width: 100%; padding: 5px; box-sizing: border-box; }
.history-table { width: 100%; border-collapse: collapse; }
.history-table th, .history-table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
.chart-container { position: relative; height: 300px; width: 100%; }
"""

js_code = """
self.onInit = function() {
    var ctx = self.ctx;
    var $scope = ctx.$scope;

    // UI Elements
    var elTemp = $('#temp-value', ctx.$container);
    var elStatus = $('#status-value', ctx.$container);
    var btnToggle = $('#btn-toggle', ctx.$container);

    // Chart (Using simple canvas drawing or Chart.js if available)
    // Assuming Chart.js is loaded in TB environment usually.
    // If not, we fall back to simple text.
    var chartCtx = document.getElementById('tempChart').getContext('2d');
    var chart = new Chart(chartCtx, {
        type: 'line',
        data: { labels: [], datasets: [{ label: 'Temp', data: [], borderColor: 'red', fill: false }] },
        options: { responsive: true, maintainAspectRatio: false }
    });

    // Global State
    var currentSettings = {};
    var isCooking = false;

    // Helper: Open Tabs
    $('.tab-btn', ctx.$container).on('click', function() {
        var tabName = $(this).data('tab');
        $('.tab-content', ctx.$container).removeClass('active');
        $('.tab-btn', ctx.$container).removeClass('active');
        $(this).addClass('active');
        $('#tab-' + tabName, ctx.$container).addClass('active');
    });

    // Check if subscription exists
    if (!ctx.defaultSubscription || !ctx.defaultSubscription.targetDeviceId) {
        elStatus.text("No Device");
        return;
    }

    var targetDeviceId = ctx.defaultSubscription.targetDeviceId;

    // 1. Subscribe to Telemetry (Temp)
    var telemetrySubscription = {
        entityId: targetDeviceId,
        keys: ['temperature'],
        type: 'timeseries'
    };

    ctx.subscriptionApi.createSubscription(telemetrySubscription).subscribe(
        (data) => {
            if(data.data.temperature) {
                var val = data.data.temperature[0][1];
                var time = data.data.temperature[0][0];
                elTemp.text(parseFloat(val).toFixed(1));

                // Update Chart
                // Keep enough data for the cooking duration. Assuming 1 sec updates.
                // We use a safe buffer size (e.g. 3600 for 1 hour).
                if(chart.data.labels.length > 3600) {
                    chart.data.labels.shift();
                    chart.data.datasets[0].data.shift();
                }
                chart.data.labels.push(new Date(time).toLocaleTimeString());
                chart.data.datasets[0].data.push(val);
                chart.update();
            }
        }
    );

    // 2. Load & Subscribe Attributes (Settings & State)
    var attributes = ['targetTemp', 'upperLimit', 'lowerLimit', 'useLowerLimit', 'cookingDuration', 'startMode', 'isCooking', 'cookingState'];

    var attrSubscription = {
        entityId: targetDeviceId,
        keys: attributes,
        type: 'attributes'
    };

    ctx.subscriptionApi.createSubscription(attrSubscription).subscribe(
        (data) => {
            // Flatten the structure: data.data is { key: [ [ts, val], ... ] }
            var simplified = [];
            for (var key in data.data) {
                if (data.data.hasOwnProperty(key)) {
                    simplified.push({ key: key, value: data.data[key][0][1] });
                }
            }
            updateSettingsUI(simplified);
            updateStateUI(simplified);
        }
    );

    function updateSettingsUI(data) {
        if (!data) return;
        data.forEach(attr => {
            currentSettings[attr.key] = attr.value;
            if (attr.key === 'targetTemp') $('#set-target', ctx.$container).val(attr.value);
            if (attr.key === 'upperLimit') $('#set-upper', ctx.$container).val(attr.value);
            if (attr.key === 'lowerLimit') $('#set-lower', ctx.$container).val(attr.value);
            if (attr.key === 'cookingDuration') $('#set-duration', ctx.$container).val(attr.value);
            if (attr.key === 'startMode') $('#set-mode', ctx.$container).val(attr.value);
            if (attr.key === 'useLowerLimit') $('#set-use-lower', ctx.$container).prop('checked', attr.value === 'true');
            if (attr.key === 'isCooking') isCooking = (attr.value === 'true');
        });
        updateBtnLabel();
    }

    function updateStateUI(data) {
         if(!data) return;
         var stateAttr = data.find(x => x.key === 'cookingState');
         if(stateAttr) {
             elStatus.text(stateAttr.value);
         }
    }

    function updateBtnLabel() {
        btnToggle.text(isCooking ? "Stop Cooking" : "Start Cooking");
        if(currentSettings.startMode === 'auto') {
             btnToggle.prop('disabled', true).text("Auto Mode Active");
        } else {
             btnToggle.prop('disabled', false);
        }
    }

    // 3. Actions
    $('#btn-save', ctx.$container).on('click', function() {
        var newAttrs = [
            { key: 'targetTemp', value: $('#set-target', ctx.$container).val() },
            { key: 'upperLimit', value: $('#set-upper', ctx.$container).val() },
            { key: 'lowerLimit', value: $('#set-lower', ctx.$container).val() },
            { key: 'cookingDuration', value: $('#set-duration', ctx.$container).val() },
            { key: 'startMode', value: $('#set-mode', ctx.$container).val() },
            { key: 'useLowerLimit', value: $('#set-use-lower', ctx.$container).prop('checked') ? 'true' : 'false' }
        ];
        ctx.attributeService.saveEntityAttributes(targetDeviceId, 'SHARED_SCOPE', newAttrs).subscribe(
            () => { alert('Settings Saved'); }
        );
    });

    btnToggle.on('click', function() {
        var newState = !isCooking;
        ctx.attributeService.saveEntityAttributes(targetDeviceId, 'SHARED_SCOPE', [{key: 'isCooking', value: newState}]).subscribe(
            () => { isCooking = newState; updateBtnLabel(); }
        );
    });

    // 4. History
    $('#btn-refresh-history', ctx.$container).on('click', loadHistory);

    function loadHistory() {
        var end = Date.now();
        var start = end - (7 * 24 * 60 * 60 * 1000); // Last 7 days
        ctx.telemetryWebsocketService.getEntityTimeseriesValues(
            targetDeviceId,
            start, end, 100, ['cooking_history']
        ).subscribe((data) => {
            var tbody = $('#history-body', ctx.$container);
            tbody.empty();
            if(data.cooking_history) {
                data.cooking_history.forEach(pt => {
                    var rec = JSON.parse(pt.value);
                    var row = `<tr>
                        <td>${new Date(rec.start).toLocaleString()}</td>
                        <td>${rec.duration} ms</td>
                        <td>${rec.maxTemp || '-'}</td>
                        <td>${rec.result}</td>
                    </tr>`;
                    tbody.append(row);
                });
            }
        });
    }

    // Initial Load
    loadHistory();
}
"""

widget_json = {
    "widgetsBundle": {
        "alias": "haccp_widgets",
        "title": "HACCP Widgets",
        "image": None
    },
    "widgetTypes": [
        {
            "alias": "haccp_monitor",
            "name": "HACCP Smart Monitor",
            "descriptor": {
                "type": "static",
                "sizeX": 8,
                "sizeY": 6,
                "resources": [
                    {"url": "https://cdnjs.cloudflare.com/ajax/libs/Chart.js/2.9.4/Chart.min.js"}
                ],
                "templateHtml": html_code,
                "templateCss": css_code,
                "controllerScript": js_code,
                "settingsSchema": "{}",
                "dataKeySettingsSchema": "{}",
                "defaultConfig": "{\"datasources\":[{\"type\":\"function\",\"name\":\"function\",\"dataKeys\":[{\"name\":\"f(x)\",\"type\":\"function\",\"label\":\"Temperature\",\"color\":\"#2196f3\",\"settings\":{},\"_hash\":0.15463935298135753,\"funcBody\":\"var value = prevValue + Math.random() * 100 - 50;\\nvar multiplier = Math.pow(10, 2 || 0);\\nvar value = Math.round(value * multiplier) / multiplier;\\nif (value < -1000) {\\n\\tvalue = -1000;\\n} else if (value > 1000) {\\n\\tvalue = 1000;\\n}\\nreturn value;\"}]}],\"timewindow\":{\"realtime\":{\"timewindowMs\":60000}},\"showTitle\":true,\"backgroundColor\":\"#fff\",\"color\":\"rgba(0, 0, 0, 0.87)\",\"padding\":\"8px\",\"settings\":{},\"title\":\"HACCP Monitor\"}"
            }
        }
    ]
}

with open("haccp_widget.json", "w") as f:
    json.dump(widget_json, f, indent=2)

print("Widget JSON generated.")

import json
import uuid

def generate_uuid():
    return str(uuid.uuid4())

# Node IDs
id_input = generate_uuid()
id_enrich = generate_uuid()
id_script = generate_uuid()
id_switch = generate_uuid()
id_save_attr = generate_uuid()
id_create_alarm = generate_uuid()
id_save_telemetry = generate_uuid()
id_log = generate_uuid()

# Script Content (The core logic)
script_js = """
var newMsg = {};
var newMetadata = metadata;

// Log input for debug
// return {msg: msg, metadata: metadata, msgType: msgType};

// Helper to get attribute
function getAttr(name, defaultVal) {
    return metadata['cs_' + name] || metadata['ss_' + name] || defaultVal;
}

var mode = getAttr('startMode', 'manual');
var target = parseFloat(getAttr('targetTemp', 100));
var duration = parseInt(getAttr('cookingDuration', 600)) * 1000;
var upper = parseFloat(getAttr('upperLimit', 110));
var lower = parseFloat(getAttr('lowerLimit', 90));
var useLower = getAttr('useLowerLimit', 'false') === 'true';
var isCookingAttr = getAttr('isCooking', 'false') === 'true';

var state = metadata.ss_cookingState || 'IDLE';
var startTime = parseInt(metadata.ss_cookingStartTime || 0);

newMetadata.should_save_attributes = 'false';
newMetadata.should_create_alarm = 'false';
newMetadata.should_save_history = 'false';

if (msgType === 'POST_TELEMETRY' && msg.temperature) {
    var temp = parseFloat(msg.temperature);

    // --- IDLE STATE ---
    if (state === 'IDLE') {
        var start = false;
        if (mode === 'auto' && temp >= target) {
            start = true;
        }
        // Manual start is handled via Attribute Update usually, but if isCooking is set
        // and we are in IDLE, we should transition.
        if (isCookingAttr) {
           start = true;
        }

        if (start) {
            newMetadata.ss_cookingState = 'COOKING';
            newMetadata.ss_cookingStartTime = Date.now();
            newMetadata.should_save_attributes = 'true';
        }
    }

    // --- COOKING STATE ---
    else if (state === 'COOKING') {
        // Check Stop (Manual)
        if (!isCookingAttr && mode === 'manual') {
             // User stopped it manually
             newMetadata.ss_cookingState = 'IDLE';
             newMetadata.should_save_attributes = 'true';
        } else {
            var elapsed = Date.now() - startTime;

            // 1. Check Alarms
            if (temp > upper) {
                newMetadata.should_create_alarm = 'true';
                newMetadata.alarm_type = 'HACCP_HIGH_TEMP';
            } else if (useLower && temp < lower) {
                newMetadata.should_create_alarm = 'true';
                newMetadata.alarm_type = 'HACCP_LOW_TEMP';
            }

            // 2. Check Completion
            if (elapsed >= duration) {
                newMetadata.ss_cookingState = 'IDLE';
                newMetadata.ss_isCooking = 'false'; // Reset client flag if possible (server side override)
                newMetadata.should_save_attributes = 'true';
                newMetadata.should_save_history = 'true';

                newMsg.cooking_history = {
                    start: startTime,
                    end: Date.now(),
                    duration: elapsed,
                    final_temp: temp,
                    result: 'COMPLETED'
                };
            }
        }
    }
} else if (msgType === 'POST_ATTRIBUTES_REQUEST' || msgType === 'ATTRIBUTES_UPDATED') {
    // Handle manual start/stop toggles from widget
    // Note: ATTRIBUTES_UPDATED usually comes from the Widget (Shared Attributes).
    if (msg.isCooking !== undefined) {
         if (msg.isCooking === true && state === 'IDLE') {
             newMetadata.ss_cookingState = 'COOKING';
             newMetadata.ss_cookingStartTime = Date.now();
             newMetadata.should_save_attributes = 'true';
         } else if (msg.isCooking === false && state === 'COOKING') {
             newMetadata.ss_cookingState = 'IDLE';
             newMetadata.should_save_attributes = 'true';
         }
    }
}

return {msg: newMsg, metadata: newMetadata, msgType: msgType};
"""

rule_chain = {
    "ruleChain": {
        "name": "HACCP Monitoring",
        "firstRuleNodeId": {"id": id_enrich, "entityType": "RULE_NODE"},
        "root": False,
        "debugMode": False
    },
    "metadata": {
        "firstNodeIndex": 0,
        "nodes": [
            {
                "id": {"id": id_enrich, "entityType": "RULE_NODE"},
                "type": "org.thingsboard.rule.engine.metadata.TbGetAttributesNode",
                "name": "Fetch Config",
                "configuration": {
                    "clientAttributeNames": ["targetTemp", "upperLimit", "lowerLimit", "useLowerLimit", "cookingDuration", "startMode", "isCooking"],
                    "serverAttributeNames": ["cookingState", "cookingStartTime"],
                    "sharedAttributeNames": ["targetTemp", "upperLimit", "lowerLimit", "useLowerLimit", "cookingDuration", "startMode", "isCooking"]
                }
            },
            {
                "id": {"id": id_script, "entityType": "RULE_NODE"},
                "type": "org.thingsboard.rule.engine.transform.TbTransformMsgNode",
                "name": "HACCP Logic",
                "configuration": {
                    "jsScript": script_js
                }
            },
            {
                "id": {"id": id_switch, "entityType": "RULE_NODE"},
                "type": "org.thingsboard.rule.engine.filter.TbJsSwitchNode",
                "name": "Route Actions",
                "configuration": {
                    "jsScript": """
                        var routes = [];
                        if (metadata.should_save_attributes === 'true') routes.push('SAVE_ATTR');
                        if (metadata.should_create_alarm === 'true') routes.push('ALARM');
                        if (metadata.should_save_history === 'true') routes.push('HISTORY');
                        return routes;
                    """
                }
            },
            {
                "id": {"id": id_save_attr, "entityType": "RULE_NODE"},
                "type": "org.thingsboard.rule.engine.telemetry.TbMsgAttributesNode",
                "name": "Update State",
                "configuration": {
                    "scope": "SERVER_SCOPE"
                }
            },
            {
                "id": {"id": id_create_alarm, "entityType": "RULE_NODE"},
                "type": "org.thingsboard.rule.engine.action.TbCreateAlarmNode",
                "name": "Trigger Alarm",
                "configuration": {
                    "alarmType": "HACCP_CRITICAL",
                    "severity": "CRITICAL",
                    "propagate": False,
                    "alarmDetailsBuildJs": "var details = {}; details.temp = msg.temperature; return details;"
                }
            },
            {
                "id": {"id": id_save_telemetry, "entityType": "RULE_NODE"},
                "type": "org.thingsboard.rule.engine.telemetry.TbMsgTimeseriesNode",
                "name": "Save History",
                "configuration": {
                    "defaultTTL": 0
                }
            }
        ],
        "connections": [
            {"fromIndex": 0, "toIndex": 1, "type": "Success"}, # Enrich -> Script
            {"fromIndex": 1, "toIndex": 2, "type": "Success"}, # Script -> Switch
            {"fromIndex": 2, "toIndex": 3, "type": "SAVE_ATTR"}, # Switch -> Save Attr
            {"fromIndex": 2, "toIndex": 4, "type": "ALARM"}, # Switch -> Alarm
            {"fromIndex": 2, "toIndex": 5, "type": "HISTORY"} # Switch -> Save Telemetry
        ]
    }
}

with open("haccp_rule_chain.json", "w") as f:
    json.dump(rule_chain, f, indent=2)

print("Rule Chain JSON generated.")

# ------------------------------------------------------------
# Team / Namespace
# ------------------------------------------------------------

TEAM = 'EGR314/Team202/CGE'


# ------------------------------------------------------------
# MQTT Topics
# ------------------------------------------------------------

# Directional topics (MAIN SYSTEM)
TOPIC_C_TO_W = TEAM + '/c_to_w'   # Controller → Rover
TOPIC_W_TO_C = TEAM + '/w_to_c'   # Rover → Controller

# Optional: keep lab/demo topics (not required for final system)
TOPIC_HB  = TEAM + '/heartbeat'
TOPIC_PUB = TEAM + '/pub'
TOPIC_SUB = TEAM + '/sub'


# ------------------------------------------------------------
# MQTT Server Credentials
# ------------------------------------------------------------

MQTT_SERVER   = '34.210.232.255'
MQTT_USER     = 'student'
MQTT_PASSWORD = 'egr3x4'


# ------------------------------------------------------------
# WiFi Credentials
# ------------------------------------------------------------

WIFI_SSID = 'asu guest'
WIFI_PASSWORD = ''
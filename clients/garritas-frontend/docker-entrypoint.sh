#!/bin/sh
set -e

CONFIG=/usr/share/nginx/html/config.json

# If GATEWAY_URL is set, rewrite config.json so the frontend talks
# directly to the public gateway (needed on Railway where nginx
# cannot reverse-proxy to the gateway by Docker hostname).
if [ -n "${GATEWAY_URL:-}" ]; then
  sed -i '/location [/]api[/]/,/^  }/d' /etc/nginx/conf.d/default.conf
  gateway_url=${GATEWAY_URL%/}
  cat > "$CONFIG" <<EOF
{
  "apiUrl": "${gateway_url}/api/v1",
  "keycloakUrl": "${KEYCLOAK_URL:-http://localhost:18180}",
  "realm": "${KC_REALM:-garritas}",
  "clientId": "${KC_CLIENT:-garritas-frontend}"
}
EOF
fi

exec "$@"

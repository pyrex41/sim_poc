# n8n Dockerfile for Fly.io
FROM n8nio/n8n:latest

# Set user to root for installation
USER root

# Install additional packages if needed
RUN apk add --no-cache \
    python3 \
    py3-pip \
    curl

# Create data directory
RUN mkdir -p /home/node/.n8n && \
    chown -R node:node /home/node/.n8n

# Switch back to node user
USER node

# Expose n8n port
EXPOSE 5678

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s \
  CMD wget --no-verbose --tries=1 --spider http://localhost:5678/healthz || exit 1

# Start n8n
CMD ["n8n"]

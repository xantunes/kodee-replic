# Build stage
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Runtime stage
FROM node:20-alpine
WORKDIR /app

# Create non-root user
RUN addgroup -g 1001 -S fortigate && \
    adduser -S fortigate -u 1001

# Copy built artifacts
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/schemas ./schemas
COPY --from=builder /app/templates ./templates

# Install production dependencies only
RUN npm ci --only=production && npm cache clean --force

# Create audit directory
RUN mkdir -p /app/audit && chown -R fortigate:fortigate /app

USER fortigate

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD node -e "console.log('health check')" || exit 1

ENTRYPOINT ["node", "dist/index.js"]
